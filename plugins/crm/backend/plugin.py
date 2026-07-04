from __future__ import annotations

from packages.sdk import PluginContext
from plugins.crm.backend.router import router

CRM_PERMISSIONS = [
    "crm.customer.read",
    "crm.customer.create",
    "crm.customer.update",
    "crm.commercial.read",
    "crm.commercial.manage",
    "crm.financial.read",
    "crm.financial.manage",
    "crm.pricing.read",
    "crm.pricing.manage",
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
    "crm.customer.contact_added",
    "crm.customer.contact_updated",
    "crm.customer.contact_removed",
    "crm.customer.commercial_assignment_added",
    "crm.customer.commercial_assignment_updated",
    "crm.customer.commercial_assignment_removed",
    "crm.customer.bank_account_added",
    "crm.customer.bank_account_updated",
    "crm.customer.bank_account_removed",
    "crm.customer.pricing_term_added",
    "crm.customer.pricing_term_updated",
    "crm.customer.pricing_term_removed",
]


def register(context: PluginContext) -> None:
    context.register_router(router)
    context.register_permissions(CRM_PERMISSIONS)
    context.register_events(CRM_EVENTS)
