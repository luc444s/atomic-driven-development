from packages.sdk import PluginContext
from plugins.stock.backend.router import router

STOCK_PERMISSIONS = [
    "stock.balance.read",
    "stock.balance.adjust",
    "stock.transfer.create",
    "stock.config.read",
    "stock.config.manage",
    "stock.allocation.create",
    "stock.allocation.release",
    "stock.allocation.read",
    "stock.movement.sale_out",
    "stock.movement.purchase_in",
    "stock.movement.return_in",
    "stock.movement.damage_out",
]

STOCK_EVENTS = [
    "stock.balance.adjusted",
    "stock.balance.negative_warning",
    "stock.transfer.completed",
    "stock.allocation.reserved",
    "stock.allocation.released",
    "stock.allocation.expired",
    "stock.movement.sale_out",
    "stock.movement.purchase_in",
    "stock.movement.return_in",
    "stock.movement.damage_out",
]


def register(context: PluginContext) -> None:
    context.register_router(router)
    context.register_permissions(STOCK_PERMISSIONS)
    context.register_events(STOCK_EVENTS)
