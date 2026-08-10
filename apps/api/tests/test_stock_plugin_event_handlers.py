from __future__ import annotations

from plugins.stock.backend import plugin as stock_plugin


def test_stock_plugin_registers_product_created_listener(app) -> None:
    discovered = app.state.plugin_registry.get("stock")
    assert discovered is not None
    assert discovered.manifest is not None

    context = app.state.plugin_runtime.context_builder(discovered.manifest)
    stock_plugin.register(context)

    handlers = context.registration.event_handlers.get("productos.product.created")
    assert handlers is not None
    assert len(handlers) == 1
