from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.crm.backend.services.customers import get_customer
from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsAgendaTask,
    LogisticsDeliveryPoint,
    LogisticsLoad,
    LogisticsRoute,
    LogisticsRouteStop,
    LogisticsRouteWeekday,
)
from plugins.logistics.backend.schemas import (
    CylinderTransitionRequest,
    LoadBulkCreateRequest,
    LoadCreateRequest,
    RouteCreateRequest,
    RouteStopCreateRequest,
    RouteStopUpdateRequest,
    RouteUpdateRequest,
)
from plugins.logistics.backend.services.cylinders import get_cylinder, transition_cylinder
from plugins.logistics.backend.services.extensions import (
    validate_route_weight_limit,
    validate_vehicle_for_route,
)


def list_routes(
    db: Session,
    *,
    tenant_id: str,
    status: str | None = None,
    driver_id: str | None = None,
    route_date: date | None = None,
    weekday: int | None = None,
) -> list[LogisticsRoute]:
    stmt = select(LogisticsRoute).where(LogisticsRoute.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(LogisticsRoute.status == status)
    if driver_id:
        stmt = stmt.where(LogisticsRoute.driver_id == driver_id)
    if route_date:
        stmt = stmt.where(LogisticsRoute.route_date == route_date)
    if weekday is not None:
        stmt = stmt.join(
            LogisticsRouteWeekday, LogisticsRouteWeekday.route_id == LogisticsRoute.id
        ).where(LogisticsRouteWeekday.weekday == weekday)
    stmt = stmt.order_by(LogisticsRoute.route_date.desc(), LogisticsRoute.created_at.desc())
    return list(db.scalars(stmt).all())


def get_route(db: Session, *, tenant_id: str, route_id: str) -> LogisticsRoute | None:
    return db.scalar(
        select(LogisticsRoute).where(
            LogisticsRoute.id == route_id,
            LogisticsRoute.tenant_id == tenant_id,
        )
    )


def create_route(
    db: Session,
    *,
    tenant_id: str,
    created_by: str,
    payload: RouteCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsRoute:
    route = LogisticsRoute(
        tenant_id=tenant_id,
        branch_id=payload.branch_id,
        route_date=payload.route_date,
        driver_id=payload.driver_id or action_context.actor_user_id,
        vehicle_id=payload.vehicle_id,
        notes=payload.notes,
        created_by=created_by,
    )
    db.add(route)
    db.flush()
    validate_vehicle_for_route(
        db, tenant_id=tenant_id, vehicle_id=route.vehicle_id, route_id=route.id
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="route.create",
        entity_type="route",
        entity_id=route.id,
        details={"route_date": route.route_date.isoformat(), "driver_id": route.driver_id},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.route.created",
        entity_type="route",
        entity_id=route.id,
        payload={"route_date": route.route_date.isoformat(), "driver_id": route.driver_id},
    )
    return route


def update_route(
    db: Session,
    *,
    route: LogisticsRoute,
    payload: RouteUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsRoute:
    if payload.route_date is not None:
        route.route_date = payload.route_date
    if payload.driver_id is not None:
        route.driver_id = payload.driver_id
    if payload.vehicle_id is not None:
        route.vehicle_id = payload.vehicle_id
    if payload.status is not None:
        route.status = payload.status
    if payload.notes is not None:
        route.notes = payload.notes
    db.add(route)
    db.flush()
    validate_vehicle_for_route(
        db,
        tenant_id=route.tenant_id,
        vehicle_id=route.vehicle_id,
        route_id=route.id,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="route.update",
        entity_type="route",
        entity_id=route.id,
        details={"route_date": route.route_date.isoformat(), "status": route.status},
    )
    return route


def list_route_stops(db: Session, *, route_id: str) -> list[LogisticsRouteStop]:
    return list(
        db.scalars(
            select(LogisticsRouteStop)
            .where(LogisticsRouteStop.route_id == route_id)
            .order_by(LogisticsRouteStop.stop_order)
        ).all()
    )


def get_route_stop(db: Session, *, route_id: str, stop_id: str) -> LogisticsRouteStop | None:
    return db.scalar(
        select(LogisticsRouteStop).where(
            LogisticsRouteStop.id == stop_id,
            LogisticsRouteStop.route_id == route_id,
        )
    )


def _next_stop_order(db: Session, *, route_id: str) -> int:
    current_max = db.scalar(
        select(func.max(LogisticsRouteStop.stop_order)).where(
            LogisticsRouteStop.route_id == route_id
        )
    )
    return int(current_max or 0) + 1


def create_route_stop(
    db: Session,
    *,
    route: LogisticsRoute,
    payload: RouteStopCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsRouteStop:
    stop_order = payload.stop_order or _next_stop_order(db, route_id=route.id)
    stop = LogisticsRouteStop(
        route_id=route.id,
        delivery_point_id=payload.delivery_point_id,
        stop_order=stop_order,
        scheduled_time=payload.scheduled_time,
        gps_coordinates=payload.gps_coordinates,
        notes=payload.notes,
    )
    db.add(stop)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="route_stop.create",
        entity_type="route_stop",
        entity_id=stop.id,
        details={"route_id": route.id, "stop_order": stop.stop_order},
    )
    return stop


def update_route_stop(
    db: Session,
    *,
    stop: LogisticsRouteStop,
    payload: RouteStopUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsRouteStop:
    if payload.stop_order is not None:
        stop.stop_order = payload.stop_order
    if payload.scheduled_time is not None:
        stop.scheduled_time = payload.scheduled_time
    if payload.status is not None:
        stop.status = payload.status
    if payload.notes is not None:
        stop.notes = payload.notes
    db.add(stop)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="route_stop.update",
        entity_type="route_stop",
        entity_id=stop.id,
        details={"route_id": stop.route_id, "status": stop.status, "stop_order": stop.stop_order},
    )
    return stop


def delete_route_stop(
    db: Session, *, stop: LogisticsRouteStop, action_context: LogisticsActionContext
) -> None:
    audit_logistics_action(
        db,
        context=action_context,
        action="route_stop.delete",
        entity_type="route_stop",
        entity_id=stop.id,
        details={"route_id": stop.route_id, "stop_order": stop.stop_order},
    )
    db.delete(stop)


def list_loads(db: Session, *, route_id: str) -> list[LogisticsLoad]:
    return list(
        db.scalars(
            select(LogisticsLoad)
            .where(LogisticsLoad.route_id == route_id)
            .order_by(LogisticsLoad.created_at.asc())
        ).all()
    )


def create_load(
    db: Session,
    *,
    route: LogisticsRoute,
    payload: LoadCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsLoad:
    validate_route_weight_limit(db, route=route, cylinder_id=payload.cylinder_id)
    load = LogisticsLoad(
        route_id=route.id,
        cylinder_id=payload.cylinder_id,
        stop_id=payload.stop_id,
        notes=payload.notes,
    )
    db.add(load)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="load.assign",
        entity_type="load",
        entity_id=load.id,
        details={"route_id": route.id, "cylinder_id": load.cylinder_id},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.load.assigned",
        entity_type="load",
        entity_id=load.id,
        payload={"route_id": route.id, "cylinder_id": load.cylinder_id, "stop_id": load.stop_id},
    )
    return load


def bulk_create_loads(
    db: Session,
    *,
    route: LogisticsRoute,
    payload: LoadBulkCreateRequest,
    action_context: LogisticsActionContext,
) -> list[LogisticsLoad]:
    loads = []
    for cylinder_id in payload.cylinder_ids:
        validate_route_weight_limit(db, route=route, cylinder_id=cylinder_id)
        loads.append(
            create_load(
                db,
                route=route,
                payload=LoadCreateRequest(
                    route_id=route.id,
                    cylinder_id=cylinder_id,
                    stop_id=payload.stop_id,
                    notes=payload.notes,
                ),
                action_context=action_context,
            )
        )
    return loads


def get_load(db: Session, *, route_id: str, load_id: str) -> LogisticsLoad | None:
    return db.scalar(
        select(LogisticsLoad).where(
            LogisticsLoad.id == load_id,
            LogisticsLoad.route_id == route_id,
        )
    )


def get_load_by_id(db: Session, *, load_id: str) -> LogisticsLoad | None:
    return db.scalar(select(LogisticsLoad).where(LogisticsLoad.id == load_id))


def delete_load(
    db: Session, *, load: LogisticsLoad, action_context: LogisticsActionContext
) -> None:
    audit_logistics_action(
        db,
        context=action_context,
        action="load.remove",
        entity_type="load",
        entity_id=load.id,
        details={"route_id": load.route_id, "cylinder_id": load.cylinder_id},
    )
    db.delete(load)


def confirm_loads(
    db: Session,
    *,
    tenant_id: str,
    route: LogisticsRoute,
    action_context: LogisticsActionContext,
) -> list[LogisticsLoad]:
    now = datetime.now(UTC)
    loads = list_loads(db, route_id=route.id)
    for load in loads:
        if load.status == "CARGADO":
            continue
        load.status = "CARGADO"
        load.loaded_at = now
        db.add(load)
        cylinder = get_cylinder(db, tenant_id=tenant_id, cylinder_id=load.cylinder_id)
        if cylinder is not None and cylinder.current_state != "CARGA_EN_VEHICULO":
            transition_cylinder(
                db,
                tenant_id=tenant_id,
                cylinder_id=load.cylinder_id,
                payload=CylinderTransitionRequest(
                    to_state="CARGA_EN_VEHICULO",
                    origin="LOAD_CONFIRM",
                    notes=f"Route {route.id}",
                ),
                action_context=action_context,
            )
    route.status = "EN_CARGA"
    db.add(route)
    db.flush()
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.load.prepared",
        entity_type="route",
        entity_id=route.id,
        payload={"route_id": route.id, "cylinders_count": len(loads)},
    )
    return loads


def start_route(
    db: Session,
    *,
    tenant_id: str,
    route: LogisticsRoute,
    action_context: LogisticsActionContext,
) -> LogisticsRoute:
    route.status = "EN_RUTA"
    db.add(route)
    for load in list_loads(db, route_id=route.id):
        cylinder = get_cylinder(db, tenant_id=tenant_id, cylinder_id=load.cylinder_id)
        if cylinder is not None and cylinder.current_state == "CARGA_EN_VEHICULO":
            transition_cylinder(
                db,
                tenant_id=tenant_id,
                cylinder_id=load.cylinder_id,
                payload=CylinderTransitionRequest(
                    to_state="EN_RUTA",
                    origin="ROUTE_START",
                    notes=f"Route {route.id}",
                ),
                action_context=action_context,
            )
    db.flush()
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.route.started",
        entity_type="route",
        entity_id=route.id,
        payload={
            "route_id": route.id,
            "driver_id": route.driver_id,
            "vehicle_id": route.vehicle_id,
        },
    )
    return route


def complete_route(
    db: Session,
    *,
    route: LogisticsRoute,
    action_context: LogisticsActionContext,
) -> LogisticsRoute:
    route.status = "COMPLETADO"
    db.add(route)
    db.flush()
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.route.completed",
        entity_type="route",
        entity_id=route.id,
        payload={"route_id": route.id},
    )
    return route


def cancel_route(
    db: Session,
    *,
    route: LogisticsRoute,
    action_context: LogisticsActionContext,
) -> LogisticsRoute:
    route.status = "CANCELADO"
    db.add(route)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="route.cancel",
        entity_type="route",
        entity_id=route.id,
        details={"route_id": route.id},
    )
    return route


def deliver_route_stop(
    db: Session,
    *,
    tenant_id: str,
    route: LogisticsRoute,
    stop: LogisticsRouteStop,
    action_context: LogisticsActionContext,
) -> LogisticsRouteStop:
    now = datetime.now(UTC)
    delivery_point = db.scalar(
        select(LogisticsDeliveryPoint).where(
            LogisticsDeliveryPoint.id == stop.delivery_point_id
        )
    )
    stop.status = "ENTREGADO"
    stop.arrival_time = stop.arrival_time or now
    stop.departure_time = now
    db.add(stop)
    route.status = "EN_RUTA"
    db.add(route)

    loads = list(
        db.scalars(
            select(LogisticsLoad).where(
                LogisticsLoad.route_id == route.id,
                LogisticsLoad.stop_id == stop.id,
            )
        ).all()
    )
    for load in loads:
        load.status = "DESCARGADO"
        load.unloaded_at = now
        db.add(load)
        cylinder = get_cylinder(db, tenant_id=tenant_id, cylinder_id=load.cylinder_id)
        if cylinder is not None and cylinder.current_state == "EN_RUTA":
            transition_cylinder(
                db,
                tenant_id=tenant_id,
                cylinder_id=load.cylinder_id,
                payload=CylinderTransitionRequest(
                    to_state="EN_CLIENTE_LLENO",
                    customer_id=(
                        delivery_point.customer_id if delivery_point is not None else None
                    ),
                    customer_name=(
                        delivery_point.customer_name if delivery_point is not None else None
                    ),
                    origin="STOP_DELIVERED",
                    notes=f"Stop {stop.id}",
                ),
                action_context=action_context,
            )
    db.flush()
    return stop


def create_agenda_tasks_from_route(
    db: Session,
    *,
    tenant_id: str,
    route: LogisticsRoute,
    action_context: LogisticsActionContext,
) -> list[LogisticsAgendaTask]:
    stops = list_route_stops(db, route_id=route.id)
    tasks: list[LogisticsAgendaTask] = []
    for stop in stops:
        delivery_point = db.scalar(
            select(LogisticsDeliveryPoint).where(
                LogisticsDeliveryPoint.id == stop.delivery_point_id
            )
        )
        if delivery_point is None:
            raise ValueError("Punto de entrega no encontrado para la parada de ruta")
        customer = None
        customer = get_customer(
            db,
            tenant_id=tenant_id,
            customer_id=delivery_point.customer_id,
        )
        task = LogisticsAgendaTask(
            tenant_id=tenant_id,
            route_id=route.id,
            driver_id=route.driver_id,
            customer_id=delivery_point.customer_id,
            customer_name=customer.legal_name if customer is not None else None,
            delivery_point_id=stop.delivery_point_id,
            task_type="ENTREGA",
            description=f"Entrega programada de la ruta {route.id}",
            scheduled_date=route.route_date,
            scheduled_time=stop.scheduled_time,
            priority=stop.stop_order,
            delivery_location=stop.notes,
        )
        db.add(task)
        tasks.append(task)
    db.flush()
    return tasks
