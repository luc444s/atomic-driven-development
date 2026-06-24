from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.app.core.config import get_settings
from apps.api.app.core.database import build_session_factory
from apps.api.app.core.logging import get_logger
from apps.api.app.kernel.audit.service import record_audit
from apps.api.app.kernel.events.bus import EventBus
from apps.api.app.kernel.plugins.persistent import build_persistent_plugin_runtime
from apps.api.app.kernel.plugins.runtime import PluginManifestRegistry, PluginRuntime
from packages.sdk import PluginContext

logger = get_logger(__name__)


def bootstrap_app_state(app: FastAPI, settings=None) -> None:
    effective_settings = settings or get_settings()
    existing_session_factory = getattr(app.state, "session_factory", None)
    session_factory = existing_session_factory or build_session_factory(effective_settings)
    plugin_registry = PluginManifestRegistry(effective_settings.plugins_dir)
    plugin_registry.discover()
    event_bus = EventBus()

    def context_builder(manifest):
        return PluginContext(
            manifest,
            config=effective_settings,
            router_registry=app,
            event_bus=event_bus,
            audit_service=record_audit,
            db_session_provider=session_factory,
            task_dispatcher=None,
        )

    try:
        with session_factory() as db:
            plugin_runtime = build_persistent_plugin_runtime(
                db,
                registry=plugin_registry,
                context_builder=context_builder,
            )
            db.commit()
    except Exception as exc:  # pragma: no cover - fallback for environments without migrated DB
        logger.error(
            "plugin_runtime_persistence_unavailable",
            extra={
                "error": str(exc),
                "plugins_dir": str(effective_settings.plugins_dir),
            },
        )
        plugin_runtime = PluginRuntime(plugin_registry, context_builder=context_builder)
        plugin_runtime.load()

    for plugin_id, handlers in plugin_runtime.collect_event_handlers().items():
        event_bus.register_handlers(handlers, source=plugin_id)

    app.state.settings = effective_settings
    app.state.plugin_registry = plugin_registry
    app.state.plugin_runtime = plugin_runtime
    app.state.event_bus = event_bus
    app.state.session_factory = session_factory


def ensure_session_factory(app: FastAPI):
    if app.state.session_factory is None:
        app.state.session_factory = build_session_factory(app.state.settings)
    return app.state.session_factory


@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_app_state(app, getattr(app.state, "settings", None))
    settings = app.state.settings
    plugin_registry = app.state.plugin_registry

    logger.info(
        "application_started",
        extra={
            "app_name": settings.app_name,
            "env": settings.env,
            "plugins_loaded": len(plugin_registry.list()),
            "plugins_enabled": len(
                [
                    item
                    for item in app.state.plugin_runtime.list_results()
                    if item.status == "enabled"
                ]
            ),
        },
    )
    yield
    logger.info("application_stopped", extra={"app_name": settings.app_name, "env": settings.env})
