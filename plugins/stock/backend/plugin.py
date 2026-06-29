from __future__ import annotations

from packages.sdk import PluginContext
from plugins.stock.backend.router import router

STOCK_PERMISSIONS = [
    "stock.balance.read",
    "stock.balance.adjust",
    "stock.transfer.create",
    "stock.config.read",
    "stock.config.manage",
]

STOCK_EVENTS = [
    "stock.balance.adjusted",
    "stock.transfer.completed",
]


def register(context: PluginContext) -> None:
    context.register_router(router)
    context.register_permissions(STOCK_PERMISSIONS)
    context.register_events(STOCK_EVENTS)
