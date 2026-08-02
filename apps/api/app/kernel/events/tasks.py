from __future__ import annotations

import importlib
from typing import Any

from apps.api.app.core.config import get_settings
from apps.api.app.core.database import build_session_factory
from apps.api.app.kernel.audit.service import record_audit
from apps.api.app.kernel.events.bus import EventBus, dispatch_pending_outbox_events
from apps.api.app.kernel.plugins.persistent import build_persistent_plugin_runtime
from apps.api.app.kernel.plugins.runtime import PluginManifestRegistry, PluginRuntime
from apps.api.app.kernel.tasks.broker import configure_dramatiq_broker
from apps.api.app.kernel.tasks.dispatcher import build_task_dispatcher
from packages.contracts.events import EventContract
from packages.sdk import PluginContext

settings = get_settings()
configure_dramatiq_broker(settings)


def build_runtime_event_bus() -> EventBus:
    session_factory = build_session_factory(settings)
    registry = PluginManifestRegistry(settings.plugins_dir)
    registry.discover()
    event_bus = EventBus()
    task_dispatcher = build_task_dispatcher(settings)

    def context_builder(manifest):
        return PluginContext(
            manifest,
            config=settings,
            router_registry=None,
            event_bus=event_bus,
            audit_service=record_audit,
            db_session_provider=session_factory,
            task_dispatcher=task_dispatcher,
        )

    try:
        with session_factory() as db:
            runtime = build_persistent_plugin_runtime(
                db,
                registry=registry,
                context_builder=context_builder,
            )
            db.commit()
    except Exception:  # pragma: no cover - same fallback semantics as app bootstrap
        runtime = PluginRuntime(registry, context_builder=context_builder)
        runtime.load()

    for plugin_id, handlers in runtime.collect_event_handlers().items():
        event_bus.register_handlers(handlers, source=plugin_id)

    _register_cross_plugin_integrations(event_bus, session_factory)
    return event_bus


def _register_cross_plugin_integrations(
    event_bus: EventBus, session_factory: Any
) -> None:
    """Integraciones entre plugins (el kernel orquesta; la lógica vive en el plugin)."""

    def _handle_product_created(event: EventContract) -> None:
        # Todo producto nuevo materializa su contador de stock en 0
        # en todos los almacenes (regla de negocio del módulo stock).
        product_id = event.payload.get("product_id")
        tenant_id = event.tenant_id
        if not isinstance(product_id, str) or not isinstance(tenant_id, str):
            return
        from plugins.stock.backend.services.balances import ensure_balances_for_product

        with session_factory() as db:
            ensure_balances_for_product(db, tenant_id=tenant_id, product_id=product_id)
            db.commit()

    event_bus.register_listener(
        "productos.product.created", _handle_product_created, source="kernel:integration"
    )


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
