from packages.sdk import PluginContext
from plugins.commerce.purchase.backend.router import router

COMPRAS_PERMISSIONS = [
    "compras.supplier.read",
    "compras.supplier.manage",
    "compras.order.read",
    "compras.order.create",
    "compras.order.manage",
    "compras.order.receive",
]

COMPRAS_EVENTS = [
    "compras.order.created",
    "compras.order.received",
    "compras.order.cancelled",
]


def register(context: PluginContext) -> None:
    context.register_router(router)
    context.register_permissions(COMPRAS_PERMISSIONS)
    context.register_events(COMPRAS_EVENTS)
