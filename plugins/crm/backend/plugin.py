from __future__ import annotations

from packages.sdk import PluginContext
from plugins.crm.backend.router import router

CRM_PERMISSIONS = [
    "crm.customer.read",
    "crm.customer.create",
    "crm.customer.update",
    "crm.catalog.read",
    "crm.geography.read",
    "crm.geography.manage",
]

CRM_EVENTS = [
    "crm.customer.created",
    "crm.customer.updated",
    "crm.customer.status_changed",
    "crm.customer.address_added",
    "crm.customer.address_removed",
]


def register(context: PluginContext) -> None:
    context.register_router(router)
    context.register_permissions(CRM_PERMISSIONS)
    context.register_events(CRM_EVENTS)
