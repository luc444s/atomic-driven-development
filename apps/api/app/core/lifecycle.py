from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.app.core.config import get_settings
from apps.api.app.core.database import build_session_factory
from apps.api.app.core.logging import get_logger
from apps.api.app.kernel.events.bus import EventBus
from apps.api.app.kernel.plugins.runtime import PluginManifestRegistry, PluginRuntime

logger = get_logger(__name__)


def bootstrap_app_state(app: FastAPI, settings=None) -> None:
    effective_settings = settings or get_settings()
    plugin_registry = PluginManifestRegistry(effective_settings.plugins_dir)
    plugin_registry.discover()
    plugin_runtime = PluginRuntime(plugin_registry)
    plugin_runtime.load()
    event_bus = EventBus()
    for plugin_id, handlers in plugin_runtime.collect_event_handlers().items():
        event_bus.register_handlers(handlers, source=plugin_id)
    existing_session_factory = getattr(app.state, "session_factory", None)

    app.state.settings = effective_settings
    app.state.plugin_registry = plugin_registry
    app.state.plugin_runtime = plugin_runtime
    app.state.event_bus = event_bus
    app.state.session_factory = existing_session_factory


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
