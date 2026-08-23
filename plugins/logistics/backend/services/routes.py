from __future__ import annotations

import re
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.crm.backend.models import CrmCustomer
from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsAgendaTask,
    LogisticsDeliveryPoint,
    LogisticsRoute,
    LogisticsRouteStop,
    LogisticsRouteWeekday,
)
from plugins.logistics.backend.schemas import (
    RouteCreateRequest,
    RouteStopCreateRequest,
    RouteStopUpdateRequest,
    RouteUpdateRequest,
)
from plugins.logistics.backend.services.extensions import (
    validate_vehicle_for_route,
)

ROUTE_LABEL_PREFIX_RE = re.compile(r"^\d+\s*·\s*")


def _clean_route_label(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = ROUTE_LABEL_PREFIX_RE.sub("", value).strip()
    return normalized or None


def _split_route_notes(notes: str | None) -> tuple[str | None, str | None]:
    if notes is None or "→" not in notes:
        return None, None
    origin, destination = notes.split("→", 1)
    return _clean_route_label(origin), _clean_route_label(destination)


def _build_destination_label(customer_name: str | None, location: str | None) -> str | None:
    customer_name = _clean_route_label(customer_name)
    location = _clean_route_label(location)
    if customer_name and location and customer_name != location:
        return f"{customer_name} - {location}"
    return customer_name or location


def _resolve_stop_destination_label(db: Session, *, stop: LogisticsRouteStop) -> str | None:
    customer_name = stop.customer_name_snapshot
    location = stop.notes
    if stop.delivery_point_id:
        delivery_point = db.scalar(
            select(LogisticsDeliveryPoint).where(
                LogisticsDeliveryPoint.id == stop.delivery_point_id
            )
        )
        if delivery_point is not None:
            customer_name = customer_name or delivery_point.customer_name
            location = location or delivery_point.address
    if customer_name is None and stop.customer_id is not None:
        customer = db.scalar(select(CrmCustomer).where(CrmCustomer.id == stop.customer_id))
        if customer is not None:
            customer_name = customer_name or customer.legal_name
    return _build_destination_label(customer_name, location)


def sync_route_labels(db: Session, *, route: LogisticsRoute) -> None:
    note_origin, note_destination = _split_route_notes(route.notes)
    if route.origin_label is None:
        route.origin_label = note_origin

    stops = list_route_stops(db, route_id=route.id)
    if stops:
        destination_label = _resolve_stop_destination_label(db, stop=stops[-1])
        if destination_label is not None:
            route.destination_label = destination_label
        elif route.destination_label is None:
            route.destination_label = note_destination
    elif route.destination_label is None:
        route.destination_label = note_destination

    db.add(route)


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
    note_origin, note_destination = _split_route_notes(payload.notes)
    route = LogisticsRoute(
        tenant_id=tenant_id,
        branch_id=payload.branch_id,
        route_date=payload.route_date,
        driver_id=payload.driver_id or action_context.actor_user_id,
        vehicle_id=payload.vehicle_id,
        origin_label=_clean_route_label(payload.origin_label) or note_origin,
        destination_label=_clean_route_label(payload.destination_label) or note_destination,
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
    note_origin, note_destination = _split_route_notes(
        payload.notes if payload.notes is not None else route.notes
    )
    if payload.route_date is not None:
        route.route_date = payload.route_date
    if payload.driver_id is not None:
        route.driver_id = payload.driver_id
    if payload.vehicle_id is not None:
        route.vehicle_id = payload.vehicle_id
    if payload.origin_label is not None:
        route.origin_label = _clean_route_label(payload.origin_label)
    elif payload.notes is not None and note_origin is not None:
        route.origin_label = note_origin
    elif route.origin_label is None:
        route.origin_label = note_origin
    if payload.destination_label is not None:
        route.destination_label = _clean_route_label(payload.destination_label)
    elif payload.notes is not None and note_destination is not None:
        route.destination_label = note_destination
    elif route.destination_label is None:
        route.destination_label = note_destination
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
        customer_id=payload.customer_id,
        customer_name_snapshot=payload.customer_name_snapshot,
        notes=payload.notes,
    )
    db.add(stop)
    db.flush()
    sync_route_labels(db, route=route)
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
    route = db.scalar(select(LogisticsRoute).where(LogisticsRoute.id == stop.route_id))
    if route is not None:
        sync_route_labels(db, route=route)
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
    route = db.scalar(select(LogisticsRoute).where(LogisticsRoute.id == stop.route_id))
    audit_logistics_action(
        db,
        context=action_context,
        action="route_stop.delete",
        entity_type="route_stop",
        entity_id=stop.id,
        details={"route_id": stop.route_id, "stop_order": stop.stop_order},
    )
    db.delete(stop)
    db.flush()
    if route is not None:
        sync_route_labels(db, route=route)


def start_route(
    db: Session,
    *,
    tenant_id: str,
    route: LogisticsRoute,
    action_context: LogisticsActionContext,
) -> LogisticsRoute:
    route.status = "EN_RUTA"
    db.add(route)
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
        customer = db.scalar(
            select(CrmCustomer).where(
                CrmCustomer.id == delivery_point.customer_id,
                CrmCustomer.tenant_id == tenant_id,
            )
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
