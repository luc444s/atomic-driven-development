from __future__ import annotations

from packages.sdk import PluginContext
from plugins.logistics.backend.router import router
from plugins.logistics.backend.routers.contracts import router as contracts_router
from plugins.logistics.backend.routers.traceability import router as traceability_router

LOGISTICS_PERMISSIONS = [
    "logistics.cylinder.read",
    "logistics.cylinder.create",
    "logistics.cylinder.update",
    "logistics.cylinder.transition",
    "logistics.cylinder.trace",
    "logistics.order.read",
    "logistics.order.create",
    "logistics.order.manage",
    "logistics.route.read",
    "logistics.route.manage",
    "logistics.load.manage",
    "logistics.movement.read",
    "logistics.movement.create",
    "logistics.movement.confirm",
    "logistics.warehouse.read",
    "logistics.warehouse.manage",
    "logistics.vehicle.read",
    "logistics.vehicle.manage",
    "logistics.agenda.read",
    "logistics.agenda.manage",
    "logistics.maintenance.read",
    "logistics.maintenance.manage",
    "logistics.retimbrado.read",
    "logistics.retimbrado.manage",
    "logistics.scan.execute",
    "logistics.scan.read",
    "logistics.label.print",
    "logistics.label.read",
    "logistics.ownership.read",
    "logistics.service.read",
    "logistics.service.manage",
    "logistics.gas.read",
    "logistics.brand.read",
    "logistics.contract.view",
    "logistics.contract.create",
    "logistics.contract.update",
    "logistics.contract.activate",
    "logistics.contract.terminate",
    "logistics.contract.renew",
]

LOGISTICS_EVENTS = [
    "logistics.cylinder.created",
    "logistics.cylinder.updated",
    "logistics.cylinder.state_changed",
    "logistics.cylinder.hydrotest_registered",
    "logistics.cylinder.retimbrado_registered",
    "logistics.cylinder.label_printed",
    "logistics.cylinder.ownership_changed",
    "logistics.cylinder.scanned",
    "logistics.cylinder.service_registered",
    "logistics.cylinder.service_completed",
    "logistics.order.created",
    "logistics.order.updated",
    "logistics.route.created",
    "logistics.route.started",
    "logistics.route.completed",
    "logistics.load.assigned",
    "logistics.load.prepared",
    "logistics.movement.created",
    "logistics.movement.completed",
    "logistics.movement.cancelled",
    "logistics.dispatch.completed",
    "logistics.dispatch.returned",
    "logistics.planning.preload_generated",
    "logistics.planning.preload_accepted",
    "logistics.reception.completed",
    "logistics.agenda.task_completed",
    "logistics.warranty.created",
    "logistics.cylinder_contract.created",
    "logistics.cylinder_contract.issued",
    "logistics.cylinder_contract.signed",
    "logistics.cylinder_contract.updated",
    "logistics.cylinder_contract.activated",
    "logistics.cylinder_contract.terminated",
    "logistics.cylinder_contract.cancelled",
    "logistics.cylinder_contract.renewed",
    "logistics.cylinder_contract_item.delivered",
    "logistics.cylinder_contract_item.returned",
    "logistics.cylinder.traceability_viewed",
]


def register(context: PluginContext) -> None:
    context.register_router(traceability_router)
    context.register_router(contracts_router)
    context.register_router(router)
    context.register_permissions(LOGISTICS_PERMISSIONS)
    context.register_events(LOGISTICS_EVENTS)
