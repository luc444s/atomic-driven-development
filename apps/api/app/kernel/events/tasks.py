from __future__ import annotations

import importlib

from apps.api.app.core.config import get_settings
from apps.api.app.core.database import build_session_factory
from apps.api.app.kernel.events.bus import EventBus, dispatch_pending_outbox_events
from apps.api.app.kernel.plugins.runtime import PluginManifestRegistry, PluginRuntime
from apps.api.app.kernel.tasks.broker import configure_dramatiq_broker

settings = get_settings()
configure_dramatiq_broker(settings)


def build_runtime_event_bus() -> EventBus:
    registry = PluginManifestRegistry(settings.plugins_dir)
    registry.discover()
    runtime = PluginRuntime(registry)
    runtime.load()
    event_bus = EventBus()
    for plugin_id, handlers in runtime.collect_event_handlers().items():
        event_bus.register_handlers(handlers, source=plugin_id)
    return event_bus


def _dispatch_pending_events_impl() -> dict[str, int]:
    session_factory = build_session_factory(settings)
    event_bus = build_runtime_event_bus()
    with session_factory() as db:
        result = dispatch_pending_outbox_events(
            db,
            event_bus,
            limit=settings.outbox_dispatch_batch_size,
            max_retries=settings.outbox_max_retries,
        )
        db.commit()
        return result


dramatiq = importlib.import_module("dramatiq")
dispatch_pending_events = dramatiq.actor(queue_name="events")(_dispatch_pending_events_impl)
