from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from apps.api.app.kernel.audit.service import record_audit
from apps.api.app.kernel.plugins.models import PluginRegistry
from apps.api.app.kernel.plugins.runtime import LoadedPlugin


def sync_plugin_registry(
    db: Session,
    plugins: list[LoadedPlugin],
    *,
    correlation_id: str | None = None,
) -> None:
    for plugin in plugins:
        manifest = plugin.manifest
        stmt: Select[tuple[PluginRegistry]] = select(PluginRegistry).where(
            PluginRegistry.plugin_id == manifest.id
        )
        record = db.scalar(stmt)
        is_enabled = plugin.status == "enabled"
        if record is None:
            record = PluginRegistry(
                plugin_id=manifest.id,
                name=manifest.name,
                version=manifest.version,
                api_version=manifest.api_version,
                status=plugin.status,
                is_enabled=is_enabled,
                backend_entrypoint=manifest.backend_entrypoint,
                frontend_entrypoint=manifest.frontend_entrypoint,
                requires_json=manifest.requires,
                permissions_json=manifest.permissions,
                events_json=manifest.events,
                description=manifest.description,
                error_message=plugin.error_message,
            )
            db.add(record)
        else:
            record.name = manifest.name
            record.version = manifest.version
            record.api_version = manifest.api_version
            record.backend_entrypoint = manifest.backend_entrypoint
            record.frontend_entrypoint = manifest.frontend_entrypoint
            record.requires_json = manifest.requires
            record.permissions_json = manifest.permissions
            record.events_json = manifest.events
            record.description = manifest.description
            record.is_enabled = is_enabled
            record.status = plugin.status
            record.error_message = plugin.error_message
            db.add(record)

        if plugin.status in {"enabled", "failed", "disabled"}:
            record_audit(
                db,
                tenant_id=None,
                branch_id=None,
                actor_user_id=None,
                actor_type="system",
                module="core",
                action=f"plugin.{plugin.status}",
                entity_type="plugin",
                entity_id=manifest.id,
                result="success" if plugin.status != "failed" else "failure",
                correlation_id=correlation_id,
                request_id=None,
                details={
                    "plugin_id": manifest.id,
                    "version": manifest.version,
                    "api_version": manifest.api_version,
                    "error": plugin.error_message,
                },
            )

    db.flush()
