from __future__ import annotations

from packages.sdk import PluginContext
from plugins.logistics.backend.router import router
from plugins.logistics.backend.routers.contracts import router as contracts_router
from plugins.logistics.backend.routers.customer_cylinder_summary import (
    router as customer_summary_router,
)
from plugins.logistics.backend.routers.cylinders import router as cylinders_router
from plugins.logistics.backend.routers.load_plans import router as load_plans_router
from plugins.logistics.backend.routers.load_serials import router as load_serials_router
from plugins.logistics.backend.routers.operational_summary import (
    router as operational_summary_router,
)
from plugins.logistics.backend.routers.operations import router as session_operations_router
from plugins.logistics.backend.routers.orders import router as orders_router
from plugins.logistics.backend.routers.planning_reservations import (
    router as planning_reservations_router,
)
from plugins.logistics.backend.routers.reconciliation import router as reconciliation_router
from plugins.logistics.backend.routers.route_context import router as route_context_router
from plugins.logistics.backend.routers.route_control import router as route_control_router
from plugins.logistics.backend.routers.route_operations import router as route_operations_router
from plugins.logistics.backend.routers.route_stop_results import (
    router as route_stop_results_router,
)
from plugins.logistics.backend.routers.routing import router as routing_router
from plugins.logistics.backend.routers.session_console import router as session_console_router
from plugins.logistics.backend.routers.session_waybills import router as session_waybills_router
from plugins.logistics.backend.routers.sessions import router as sessions_router
from plugins.logistics.backend.routers.traceability import router as traceability_router
from plugins.logistics.backend.services.catalog_bootstrap import ensure_logistics_catalogs

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
    "logistics.session.read",
    "logistics.session.manage",
    "logistics.session.route_execute",
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
    "logistics.planning.reservation_created",
    "logistics.planning.reservation_updated",
    "logistics.planning.reservation_activated",
    "logistics.planning.reservation_completed",
    "logistics.planning.reservation_cancelled",
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
    "logistics.cylinder_contract.excess_detected",
    "logistics.cylinder_contract.auto_created",
    "logistics.cylinder_contract.excess_resolved",
    "logistics.cylinder_contract.soft_limit_confirm",
    "logistics.cylinder.traceability_viewed",
    "logistics.vehicle_session.created",
    "logistics.vehicle_session.loading_started",
    "logistics.vehicle_session.ready",
    "logistics.vehicle_session.outbound",
    "logistics.vehicle_session.returning",
    "logistics.vehicle_session.cancelled",
    "logistics.vehicle_location.recorded",
    "logistics.route_control.status_changed",
    "logistics.route_control.stop_arrived_manually",
    "logistics.route_control.stop_departed_manually",
]


def _run_catalog_bootstrap(context: PluginContext) -> None:
    if context.db_session_provider is None:
        raise RuntimeError("logistics lifecycle hook requires db_session_provider")

    with context.db_session_provider() as db:
        ensure_logistics_catalogs(db)
        db.commit()


def on_install(context: PluginContext) -> None:
    _run_catalog_bootstrap(context)


def on_enable(context: PluginContext) -> None:
    _run_catalog_bootstrap(context)


def register(context: PluginContext) -> None:
    context.register_router(traceability_router)
    context.register_router(contracts_router)
    context.register_router(cylinders_router)
    context.register_router(customer_summary_router)
    context.register_router(planning_reservations_router)
    context.register_router(sessions_router)
    context.register_router(operational_summary_router)
    context.register_router(orders_router)
    context.register_router(routing_router)
    context.register_router(route_control_router)
    context.register_router(route_context_router)
    context.register_router(route_operations_router)
    context.register_router(route_stop_results_router)
    context.register_router(session_waybills_router)
    context.register_router(session_console_router)
    context.register_router(load_plans_router)
    context.register_router(load_serials_router)
    context.register_router(session_operations_router)
    context.register_router(reconciliation_router)
    context.register_router(router)
    context.register_permissions(LOGISTICS_PERMISSIONS)
    context.register_events(LOGISTICS_EVENTS)
