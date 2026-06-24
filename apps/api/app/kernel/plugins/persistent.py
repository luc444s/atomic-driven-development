from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from apps.api.app.core.errors import AppError
from apps.api.app.kernel.plugins.migrations import (
    PluginMigrationError,
    downgrade_plugin_migrations,
    get_latest_plugin_migration_version,
    rollback_plugin_migrations,
    upgrade_plugin_migrations,
)
from apps.api.app.kernel.plugins.models import PluginRegistry, utc_now
from apps.api.app.kernel.plugins.runtime import (
    DiscoveredPlugin,
    PluginManifestRegistry,
    PluginRuntime,
)
from packages.sdk import PluginContext

PLUGIN_STATES = {
    "discovered",
    "validated",
    "installed",
    "enabled",
    "disabled",
    "failed",
    "uninstalled",
}


class PluginStateError(AppError):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message, status_code=status_code, code="plugin_state_error")


def build_persistent_plugin_runtime(
    db: Session,
    *,
    registry: PluginManifestRegistry,
    context_builder: Callable[..., PluginContext],
) -> PluginRuntime:
    sync_plugin_registry_state(db, registry=registry)
    _upgrade_enabled_plugin_migrations(db, registry=registry)

    enabled_plugin_ids = {
        record.plugin_id for record in list_plugin_registry_records(db) if record.state == "enabled"
    }
    valid_plugin_ids = {plugin.plugin_id for plugin in registry.discovered() if plugin.is_valid}
    disabled_plugins = valid_plugin_ids - enabled_plugin_ids

    runtime = PluginRuntime(registry, context_builder=context_builder)
    runtime.load(disabled_plugins=disabled_plugins)
    reconcile_loaded_plugins(db, runtime=runtime)
    db.flush()
    return runtime


def sync_plugin_registry_state(db: Session, *, registry: PluginManifestRegistry) -> None:
    discovered_plugin_ids: set[str] = set()

    for discovered in registry.discovered():
        plugin_id = _resolved_plugin_id(discovered)
        discovered_plugin_ids.add(plugin_id)
        record = get_plugin_registry_record_by_plugin_id(db, plugin_id=plugin_id)
        if record is None:
            record = PluginRegistry(
                plugin_id=plugin_id,
                name=plugin_id,
                version="unknown",
                api_version="unknown",
                state="discovered",
                is_enabled=False,
                requires_json=[],
                permissions_json=[],
                events_json=[],
            )

        _apply_discovered_plugin(record, discovered)
        db.add(record)

    existing_records = list_plugin_registry_records(db)
    for record in existing_records:
        if record.plugin_id in discovered_plugin_ids:
            continue
        _set_plugin_state(
            record,
            "uninstalled",
            error="plugin not found on filesystem",
        )
        db.add(record)

    db.flush()


def install_plugin(
    db: Session,
    *,
    registry: PluginManifestRegistry,
    plugin_id: str,
) -> PluginRegistry:
    sync_plugin_registry_state(db, registry=registry)
    discovered = _require_valid_discovered_plugin(registry, plugin_id)
    record = _require_plugin_record(db, plugin_id)
    _ensure_dependency_exists(registry, discovered)

    try:
        migration_version = upgrade_plugin_migrations(db, record=record, discovered=discovered)
    except Exception as exc:
        _set_plugin_state(record, "failed", error=str(exc))
        db.add(record)
        db.flush()
        raise

    record.migration_version = migration_version
    _set_plugin_state(record, "installed")
    db.add(record)
    db.flush()
    return record


def enable_plugin(
    db: Session,
    *,
    registry: PluginManifestRegistry,
    plugin_id: str,
) -> PluginRegistry:
    record = install_plugin(db, registry=registry, plugin_id=plugin_id)
    discovered = _require_valid_discovered_plugin(registry, plugin_id)
    _ensure_dependency_enabled(db, discovered)

    _set_plugin_state(record, "enabled")
    db.add(record)
    db.flush()
    return record


def disable_plugin(
    db: Session,
    *,
    registry: PluginManifestRegistry,
    plugin_id: str,
) -> PluginRegistry:
    sync_plugin_registry_state(db, registry=registry)
    _ensure_no_enabled_dependents(db, registry=registry, plugin_id=plugin_id)
    record = _require_plugin_record(db, plugin_id)
    _set_plugin_state(record, "disabled")
    db.add(record)
    db.flush()
    return record


def upgrade_plugin(
    db: Session,
    *,
    registry: PluginManifestRegistry,
    plugin_id: str,
    target_revision: str | None = None,
) -> PluginRegistry:
    sync_plugin_registry_state(db, registry=registry)
    discovered = _require_valid_discovered_plugin(registry, plugin_id)
    record = _require_plugin_record(db, plugin_id)

    try:
        record.migration_version = upgrade_plugin_migrations(
            db,
            record=record,
            discovered=discovered,
            target_revision=target_revision,
        )
    except Exception as exc:
        _set_plugin_state(record, "failed", error=str(exc))
        db.add(record)
        db.flush()
        raise

    if record.state in {"validated", "discovered", "failed"}:
        _set_plugin_state(record, "installed")
    else:
        record.last_error = None
    db.add(record)
    db.flush()
    return record


def downgrade_plugin(
    db: Session,
    *,
    registry: PluginManifestRegistry,
    plugin_id: str,
    target_revision: str | None = None,
) -> PluginRegistry:
    sync_plugin_registry_state(db, registry=registry)
    discovered = _require_valid_discovered_plugin(registry, plugin_id)
    record = _require_plugin_record(db, plugin_id)
    current_state = record.state

    try:
        record.migration_version = downgrade_plugin_migrations(
            db,
            record=record,
            discovered=discovered,
            target_revision=target_revision,
        )
    except Exception as exc:
        _set_plugin_state(record, "failed", error=str(exc))
        db.add(record)
        db.flush()
        raise

    record.last_error = None
    if current_state not in {"enabled", "disabled"}:
        _set_plugin_state(record, "installed")
    db.add(record)
    db.flush()
    return record


def rollback_plugin(
    db: Session,
    *,
    registry: PluginManifestRegistry,
    plugin_id: str,
) -> PluginRegistry:
    sync_plugin_registry_state(db, registry=registry)
    discovered = _require_valid_discovered_plugin(registry, plugin_id)
    record = _require_plugin_record(db, plugin_id)
    current_state = record.state

    try:
        record.migration_version = rollback_plugin_migrations(
            db,
            record=record,
            discovered=discovered,
        )
    except Exception as exc:
        _set_plugin_state(record, "failed", error=str(exc))
        db.add(record)
        db.flush()
        raise

    record.last_error = None
    if current_state not in {"enabled", "disabled"}:
        _set_plugin_state(record, "installed")
    db.add(record)
    db.flush()
    return record


def list_plugin_registry_records(db: Session) -> list[PluginRegistry]:
    stmt: Select[tuple[PluginRegistry]] = select(PluginRegistry).order_by(
        PluginRegistry.plugin_id.asc()
    )
    return list(db.scalars(stmt))


def get_plugin_registry_record_by_plugin_id(
    db: Session,
    *,
    plugin_id: str,
) -> PluginRegistry | None:
    stmt: Select[tuple[PluginRegistry]] = select(PluginRegistry).where(
        PluginRegistry.plugin_id == plugin_id
    )
    return db.scalar(stmt)


def reconcile_loaded_plugins(db: Session, *, runtime: PluginRuntime) -> None:
    for result in runtime.list_results():
        record = get_plugin_registry_record_by_plugin_id(db, plugin_id=result.plugin_id)
        if record is None or result.manifest is None:
            continue

        record.version = result.manifest.version
        record.api_version = result.manifest.api_version
        record.backend_entrypoint = result.manifest.backend_entrypoint
        record.frontend_entrypoint = result.manifest.frontend_entrypoint
        record.requires_json = list(result.manifest.requires)
        record.permissions_json = list(result.manifest.permissions)
        record.events_json = list(result.manifest.events)
        record.description = result.manifest.description

        if result.status == "enabled":
            latest_migration_version = _latest_migration_version_for_result(
                runtime,
                result.plugin_id,
            )
            if latest_migration_version is not None:
                record.migration_version = latest_migration_version
            _set_plugin_state(record, "enabled")
        elif result.status == "failed":
            _set_plugin_state(record, "failed", error=result.error_message)
        elif record.state == "discovered":
            _set_plugin_state(record, "validated")

        db.add(record)


def _apply_discovered_plugin(record: PluginRegistry, discovered: DiscoveredPlugin) -> None:
    manifest = discovered.manifest
    if manifest is None:
        record.name = discovered.plugin_id
        record.last_error = discovered.error_message
        _set_plugin_state(record, "failed", error=discovered.error_message)
        return

    record.plugin_id = manifest.id
    record.name = manifest.name
    record.version = manifest.version
    record.api_version = manifest.api_version
    record.backend_entrypoint = manifest.backend_entrypoint
    record.frontend_entrypoint = manifest.frontend_entrypoint
    record.requires_json = list(manifest.requires)
    record.permissions_json = list(manifest.permissions)
    record.events_json = list(manifest.events)
    record.description = manifest.description

    if discovered.error_message is not None:
        _set_plugin_state(record, "failed", error=discovered.error_message)
        return

    if record.state not in PLUGIN_STATES:
        _set_plugin_state(record, "discovered")

    if record.state == "discovered":
        _set_plugin_state(record, "validated")
    elif record.state == "failed" and record.last_error == "plugin not found on filesystem":
        _set_plugin_state(record, "validated")
    elif record.state != "enabled":
        record.last_error = None


def _ensure_dependency_exists(
    registry: PluginManifestRegistry,
    discovered: DiscoveredPlugin,
) -> None:
    manifest = discovered.manifest
    if manifest is None:
        raise PluginStateError(f"plugin manifest not available: {discovered.plugin_id}")
    missing_dependencies = [
        dependency for dependency in manifest.requires if registry.get(dependency) is None
    ]
    if missing_dependencies:
        raise PluginStateError(
            f"missing dependency: {', '.join(sorted(missing_dependencies))}",
            status_code=409,
        )


def _ensure_dependency_enabled(db: Session, discovered: DiscoveredPlugin) -> None:
    manifest = discovered.manifest
    if manifest is None:
        raise PluginStateError(f"plugin manifest not available: {discovered.plugin_id}")

    missing_dependencies: list[str] = []
    for dependency in manifest.requires:
        record = get_plugin_registry_record_by_plugin_id(db, plugin_id=dependency)
        if record is None or record.state != "enabled":
            missing_dependencies.append(dependency)

    if missing_dependencies:
        raise PluginStateError(
            f"dependency not enabled: {', '.join(sorted(missing_dependencies))}",
            status_code=409,
        )


def _ensure_no_enabled_dependents(
    db: Session,
    *,
    registry: PluginManifestRegistry,
    plugin_id: str,
) -> None:
    dependents: list[str] = []
    for discovered in registry.discovered():
        manifest = discovered.manifest
        if manifest is None or plugin_id not in manifest.requires:
            continue
        record = get_plugin_registry_record_by_plugin_id(db, plugin_id=manifest.id)
        if record is not None and record.state == "enabled":
            dependents.append(manifest.id)

    if dependents:
        raise PluginStateError(
            f"cannot disable plugin with enabled dependents: {', '.join(sorted(dependents))}",
            status_code=409,
        )


def _upgrade_enabled_plugin_migrations(db: Session, *, registry: PluginManifestRegistry) -> None:
    for record in list_plugin_registry_records(db):
        if record.state != "enabled":
            continue

        discovered = registry.get(record.plugin_id)
        if discovered is None:
            _set_plugin_state(record, "uninstalled", error="plugin not found on filesystem")
            db.add(record)
            continue

        try:
            record.migration_version = upgrade_plugin_migrations(
                db,
                record=record,
                discovered=discovered,
            )
            if record.installed_at is None:
                record.installed_at = utc_now()
            record.last_error = None
            db.add(record)
        except PluginMigrationError as exc:
            _set_plugin_state(record, "failed", error=exc.message)
            db.add(record)
        except Exception as exc:
            _set_plugin_state(record, "failed", error=str(exc))
            db.add(record)


def _require_plugin_record(db: Session, plugin_id: str) -> PluginRegistry:
    record = get_plugin_registry_record_by_plugin_id(db, plugin_id=plugin_id)
    if record is None:
        raise PluginStateError(f"plugin not found in registry: {plugin_id}", status_code=404)
    return record


def _require_valid_discovered_plugin(
    registry: PluginManifestRegistry,
    plugin_id: str,
) -> DiscoveredPlugin:
    discovered = registry.get(plugin_id)
    if discovered is None:
        raise PluginStateError(f"plugin not found on filesystem: {plugin_id}", status_code=404)
    if not discovered.is_valid:
        raise PluginStateError(
            discovered.error_message or f"plugin is invalid: {plugin_id}",
            status_code=409,
        )
    return discovered


def _resolved_plugin_id(discovered: DiscoveredPlugin) -> str:
    if discovered.manifest is not None:
        return discovered.manifest.id
    return discovered.plugin_id


def _latest_migration_version_for_result(runtime: PluginRuntime, plugin_id: str) -> str | None:
    discovered = runtime.registry.get(plugin_id)
    if discovered is None:
        return None
    return get_latest_plugin_migration_version(discovered)


def _set_plugin_state(record: PluginRegistry, state: str, *, error: str | None = None) -> None:
    now = utc_now()
    record.state = state

    if state == "enabled":
        record.is_enabled = True
        record.enabled_at = now
        record.disabled_at = None
        record.installed_at = record.installed_at or now
        record.last_error = None
        return

    record.is_enabled = False

    if state == "installed":
        record.installed_at = record.installed_at or now
        record.last_error = None
        return

    if state == "disabled":
        record.disabled_at = now
        record.last_error = None
        return

    if state == "failed":
        record.last_error = (error or record.last_error or "plugin runtime failed")[:500]
        return

    if state == "validated":
        record.last_error = None
        return

    if state == "uninstalled":
        record.disabled_at = now
        record.last_error = error
        return

    if state == "discovered":
        record.last_error = None
