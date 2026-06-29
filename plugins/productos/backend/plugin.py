from __future__ import annotations

from packages.sdk import PluginContext
from plugins.productos.backend.router import router

PRODUCTOS_PERMISSIONS = [
    "productos.catalog.read",
    "productos.catalog.manage",
    "productos.product.read",
    "productos.product.create",
    "productos.product.update",
    "productos.product.delete",
    "productos.price.read",
    "productos.price.manage",
    "productos.cost.read",
    "productos.cost.manage",
    "productos.adr.read",
    "productos.adr.manage",
    "productos.media.manage",
    "productos.promotion.read",
    "productos.promotion.manage",
]

PRODUCTOS_EVENTS = [
    "productos.product.created",
    "productos.product.updated",
    "productos.product.status_changed",
    "productos.product.price_changed",
    "productos.product.cost_changed",
    "productos.product.adr_updated",
    "productos.product.barcode_added",
    "productos.brand.created",
    "productos.brand.updated",
    "productos.line.created",
    "productos.line.updated",
    "productos.promotion.created",
    "productos.promotion.updated",
    "productos.promotion.expired",
]


def register(context: PluginContext) -> None:
    context.register_router(router)
    context.register_permissions(PRODUCTOS_PERMISSIONS)
    context.register_events(PRODUCTOS_EVENTS)
