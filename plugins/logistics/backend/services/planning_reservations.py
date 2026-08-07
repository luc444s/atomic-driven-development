from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from apps.api.app.kernel.auth.models import User
from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsPlanningReservation,
    LogisticsRoute,
    LogisticsVehicle,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import (
    PlanningExpectedLoadSummary,
    PlanningReservationRead,
)
from plugins.logistics.backend.services.rules import LIVE_SESSION_STATUSES
from plugins.logistics.backend.services.sessions import create_vehicle_session, get_vehicle_session

OPEN_RESERVATION_STATUSES = {"PLANNED", "READY", "IN_PROGRESS"}


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _get_vehicle(db: Session, *, tenant_id: str, vehicle_id: str) -> LogisticsVehicle:
    vehicle = db.scalar(
        select(LogisticsVehicle).where(
            LogisticsVehicle.tenant_id == tenant_id,
            LogisticsVehicle.id == vehicle_id,
        )
    )
    if vehicle is None:
        raise LookupError("Vehiculo no encontrado")
    return vehicle


def _get_warehouse(db: Session, *, tenant_id: str, warehouse_id: str) -> LogisticsWarehouse:
    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.tenant_id == tenant_id,
            LogisticsWarehouse.id == warehouse_id,
        )
    )
    if warehouse is None:
        raise LookupError("Warehouse origen no encontrado")
    return warehouse


def _get_driver(db: Session, *, tenant_id: str, driver_id: str | None) -> User | None:
    if driver_id is None:
        return None
    driver = db.scalar(
        select(User).where(
            User.id == driver_id,
            User.tenant_id == tenant_id,
            User.is_active.is_(True),
        )
    )
    if driver is None:
        raise LookupError("Conductor no encontrado")
    return driver


def _ensure_route_exists(db: Session, *, tenant_id: str, route_id: str | None) -> None:
    if route_id is None:
        return
    route = db.scalar(
        select(LogisticsRoute).where(
            LogisticsRoute.id == route_id,
            LogisticsRoute.tenant_id == tenant_id,
        )
    )
    if route is None:
        raise LookupError("Ruta no encontrada")


def _summary_to_dict(summary: PlanningExpectedLoadSummary | dict[str, object]) -> dict[str, object]:
    if isinstance(summary, PlanningExpectedLoadSummary):
        data = summary.model_dump()
    else:
        data = summary
    items = data.get("items")
    if not isinstance(items, list):
        return data
    if len(items) == 0:
        return data
    total_units = 0.0
    known_weight = 0.0
    missing_weight = False
    normalized_items: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        quantity = float(item.get("quantity") or 0)
        unit_weight = item.get("unit_weight_kg")
        unit_weight_value = float(unit_weight) if isinstance(unit_weight, (int, float)) else None
        total_weight = unit_weight_value * quantity if unit_weight_value is not None else None
        if unit_weight_value is None:
            missing_weight = True
        else:
            known_weight += total_weight or 0
        total_units += quantity
        normalized_items.append(
            {
                **item,
                "quantity": quantity,
                "adr_required": bool(item.get("adr_required", False)),
                "unit_weight_kg": unit_weight_value,
                "total_weight_kg": total_weight,
            }
        )
    positive_items = 0
    for item in normalized_items:
        quantity_value = item.get("quantity")
        if isinstance(quantity_value, (int, float)) and quantity_value > 0:
            positive_items += 1
    data["items"] = normalized_items
    data["total_products"] = positive_items
    data["total_units"] = total_units
    data["total_weight_kg"] = None if missing_weight and normalized_items else known_weight
    return data


def _summary_from_dict(summary: dict[str, object] | None) -> PlanningExpectedLoadSummary | None:
    if summary is None:
        return None
    return PlanningExpectedLoadSummary.model_validate(summary)


def _reservation_stmt(tenant_id: str) -> Select[tuple[LogisticsPlanningReservation]]:
    return select(LogisticsPlanningReservation).where(
        LogisticsPlanningReservation.tenant_id == tenant_id
    )


def _overlap_exists(
    db: Session,
    *,
    tenant_id: str,
    vehicle_id: str,
    planned_start_at: datetime,
    planned_end_at: datetime,
    exclude_reservation_id: str | None = None,
) -> bool:
    stmt = _reservation_stmt(tenant_id).where(
        LogisticsPlanningReservation.vehicle_id == vehicle_id,
        LogisticsPlanningReservation.status.in_(OPEN_RESERVATION_STATUSES),
        LogisticsPlanningReservation.planned_start_at < planned_end_at,
        LogisticsPlanningReservation.planned_end_at > planned_start_at,
    )
    if exclude_reservation_id is not None:
        stmt = stmt.where(LogisticsPlanningReservation.id != exclude_reservation_id)
    return db.scalar(select(stmt.exists())) or False


def _has_live_session_now(db: Session, *, tenant_id: str, vehicle_id: str) -> bool:
    now = _utc_now()
    existing = db.scalar(
        select(LogisticsVehicleSession.id).where(
            LogisticsVehicleSession.tenant_id == tenant_id,
            LogisticsVehicleSession.vehicle_id == vehicle_id,
            LogisticsVehicleSession.status.in_(LIVE_SESSION_STATUSES),
            LogisticsVehicleSession.opened_at <= now,
        )
    )
    return existing is not None


def _resolve_status(
    db: Session,
    *,
    tenant_id: str,
    vehicle: LogisticsVehicle,
    planned_start_at: datetime,
    planned_end_at: datetime,
    expected_weight_total: float | None,
    expected_load_summary: dict[str, object],
    adr_required: bool,
    exclude_reservation_id: str | None = None,
) -> tuple[str, str | None]:
    max_weight = float(vehicle.useful_load or vehicle.capacity_weight or 0)
    summary_weight = expected_load_summary.get("total_weight_kg")
    total_weight = expected_weight_total or (
        float(summary_weight) if isinstance(summary_weight, (float, int)) else None
    )
    if total_weight is not None and max_weight > 0 and total_weight > max_weight:
        return "CONFLICT", "CAPACITY_EXCEEDED"
    if adr_required and not vehicle.adr_class:
        return "CONFLICT", "ADR_INCOMPATIBLE"
    if _overlap_exists(
        db,
        tenant_id=tenant_id,
        vehicle_id=vehicle.id,
        planned_start_at=planned_start_at,
        planned_end_at=planned_end_at,
        exclude_reservation_id=exclude_reservation_id,
    ):
        return "CONFLICT", "TIME_OVERLAP"
    start_at = _coerce_utc(planned_start_at)
    end_at = _coerce_utc(planned_end_at)
    if start_at <= _utc_now() <= end_at and _has_live_session_now(
        db, tenant_id=tenant_id, vehicle_id=vehicle.id
    ):
        return "CONFLICT", "VEHICLE_IN_USE"
    total_units = expected_load_summary.get("total_units")
    total_products = expected_load_summary.get("total_products")
    if (isinstance(total_units, (int, float)) and total_units > 0) or (
        isinstance(total_products, int) and total_products > 0
    ):
        return "READY", None
    return "PLANNED", None


def build_reservation_read(
    db: Session,
    *,
    reservation: LogisticsPlanningReservation,
) -> PlanningReservationRead:
    vehicle = _get_vehicle(db, tenant_id=reservation.tenant_id, vehicle_id=reservation.vehicle_id)
    warehouse = _get_warehouse(
        db,
        tenant_id=reservation.tenant_id,
        warehouse_id=reservation.origin_warehouse_id,
    )
    driver = _get_driver(db, tenant_id=reservation.tenant_id, driver_id=reservation.driver_id)
    return PlanningReservationRead(
        id=reservation.id,
        tenant_id=reservation.tenant_id,
        branch_id=reservation.branch_id,
        vehicle_id=reservation.vehicle_id,
        vehicle_plate=vehicle.plate,
        origin_warehouse_id=reservation.origin_warehouse_id,
        origin_warehouse_name=warehouse.name,
        planned_start_at=reservation.planned_start_at,
        planned_end_at=reservation.planned_end_at,
        expected_load_summary=PlanningExpectedLoadSummary.model_validate(
            reservation.expected_load_summary
        ),
        expected_weight_total=(
            float(reservation.expected_weight_total)
            if reservation.expected_weight_total is not None
            else None
        ),
        expected_volume_total=(
            float(reservation.expected_volume_total)
            if reservation.expected_volume_total is not None
            else None
        ),
        service_type=reservation.service_type,
        route_id=reservation.route_id,
        driver_id=reservation.driver_id,
        driver_name=driver.full_name if driver else None,
        adr_required=reservation.adr_required,
        notes=reservation.notes,
        status=reservation.status,
        conflict_reason=reservation.conflict_reason,
        permit_override=reservation.permit_override,
        override_reason=reservation.override_reason,
        linked_session_id=reservation.linked_session_id,
        actual_start_at=reservation.actual_start_at,
        actual_end_at=reservation.actual_end_at,
        actual_load_summary=_summary_from_dict(reservation.actual_load_summary),
        created_at=reservation.created_at,
        updated_at=reservation.updated_at,
    )


def list_reservations(
    db: Session,
    *,
    tenant_id: str,
    range_start: datetime | None = None,
    range_end: datetime | None = None,
    vehicle_id: str | None = None,
) -> list[PlanningReservationRead]:
    stmt = _reservation_stmt(tenant_id)
    if vehicle_id is not None:
        stmt = stmt.where(LogisticsPlanningReservation.vehicle_id == vehicle_id)
    if range_start is not None:
        stmt = stmt.where(LogisticsPlanningReservation.planned_end_at >= range_start)
    if range_end is not None:
        stmt = stmt.where(LogisticsPlanningReservation.planned_start_at <= range_end)
    reservations = list(
        db.scalars(
            stmt.order_by(
                LogisticsPlanningReservation.planned_start_at.asc(),
                LogisticsPlanningReservation.created_at.asc(),
            )
        ).all()
    )
    return [build_reservation_read(db, reservation=item) for item in reservations]


def get_reservation(
    db: Session,
    *,
    tenant_id: str,
    reservation_id: str,
    for_update: bool = False,
) -> LogisticsPlanningReservation | None:
    stmt = _reservation_stmt(tenant_id).where(LogisticsPlanningReservation.id == reservation_id)
    if for_update:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)


def create_reservation(
    db: Session,
    *,
    tenant_id: str,
    payload,
    action_context: LogisticsActionContext,
) -> LogisticsPlanningReservation:
    vehicle = _get_vehicle(db, tenant_id=tenant_id, vehicle_id=payload.vehicle_id)
    warehouse = _get_warehouse(db, tenant_id=tenant_id, warehouse_id=payload.origin_warehouse_id)
    _get_driver(db, tenant_id=tenant_id, driver_id=payload.driver_id)
    _ensure_route_exists(db, tenant_id=tenant_id, route_id=payload.route_id)
    summary = _summary_to_dict(payload.expected_load_summary)
    status, conflict_reason = _resolve_status(
        db,
        tenant_id=tenant_id,
        vehicle=vehicle,
        planned_start_at=payload.planned_start_at,
        planned_end_at=payload.planned_end_at,
        expected_weight_total=payload.expected_weight_total,
        expected_load_summary=summary,
        adr_required=payload.adr_required,
    )
    reservation = LogisticsPlanningReservation(
        tenant_id=tenant_id,
        branch_id=warehouse.branch_id or action_context.branch_id,
        vehicle_id=vehicle.id,
        origin_warehouse_id=warehouse.id,
        planned_start_at=payload.planned_start_at,
        planned_end_at=payload.planned_end_at,
        expected_load_summary=summary,
        expected_weight_total=payload.expected_weight_total,
        expected_volume_total=payload.expected_volume_total,
        service_type=payload.service_type,
        route_id=payload.route_id,
        driver_id=payload.driver_id,
        adr_required=payload.adr_required,
        notes=payload.notes,
        quote_id=payload.quote_id,
        status=status,
        conflict_reason=conflict_reason,
        permit_override=payload.permit_override,
        override_reason=payload.override_reason,
        created_by=action_context.actor_user_id,
        updated_by=action_context.actor_user_id,
    )
    db.add(reservation)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=reservation.branch_id,
        action="planning.reservation.create",
        entity_type="planning_reservation",
        entity_id=reservation.id,
        details={
            "vehicle_id": reservation.vehicle_id,
            "planned_start_at": reservation.planned_start_at.isoformat(),
            "planned_end_at": reservation.planned_end_at.isoformat(),
            "status": reservation.status,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        branch_id=reservation.branch_id,
        event_name="logistics.planning.reservation_created",
        entity_type="planning_reservation",
        entity_id=reservation.id,
        payload={"vehicle_id": reservation.vehicle_id, "status": reservation.status},
    )
    return reservation


def update_reservation(
    db: Session,
    *,
    reservation: LogisticsPlanningReservation,
    payload,
    action_context: LogisticsActionContext,
) -> LogisticsPlanningReservation:
    if reservation.linked_session_id is not None:
        raise ValueError("La planificación ya fue materializada en jornada y no puede editarse")
    data = payload.model_dump(exclude_unset=True)
    vehicle_id = data.get("vehicle_id", reservation.vehicle_id)
    warehouse_id = data.get("origin_warehouse_id", reservation.origin_warehouse_id)
    route_id = data.get("route_id", reservation.route_id)
    driver_id = data.get("driver_id", reservation.driver_id)
    vehicle = _get_vehicle(db, tenant_id=reservation.tenant_id, vehicle_id=vehicle_id)
    warehouse = _get_warehouse(db, tenant_id=reservation.tenant_id, warehouse_id=warehouse_id)
    _get_driver(db, tenant_id=reservation.tenant_id, driver_id=driver_id)
    _ensure_route_exists(db, tenant_id=reservation.tenant_id, route_id=route_id)
    planned_start_at = data.get("planned_start_at", reservation.planned_start_at)
    planned_end_at = data.get("planned_end_at", reservation.planned_end_at)
    if planned_end_at <= planned_start_at:
        raise ValueError("La ventana planificada debe terminar después de comenzar")
    summary = _summary_to_dict(data.get("expected_load_summary", reservation.expected_load_summary))
    expected_weight_total = data.get("expected_weight_total", reservation.expected_weight_total)
    status, conflict_reason = _resolve_status(
        db,
        tenant_id=reservation.tenant_id,
        vehicle=vehicle,
        planned_start_at=planned_start_at,
        planned_end_at=planned_end_at,
        expected_weight_total=(
            float(expected_weight_total) if expected_weight_total is not None else None
        ),
        expected_load_summary=summary,
        adr_required=data.get("adr_required", reservation.adr_required),
        exclude_reservation_id=reservation.id,
    )
    reservation.vehicle_id = vehicle.id
    reservation.origin_warehouse_id = warehouse.id
    reservation.branch_id = warehouse.branch_id or reservation.branch_id
    reservation.planned_start_at = planned_start_at
    reservation.planned_end_at = planned_end_at
    reservation.expected_load_summary = summary
    reservation.expected_weight_total = expected_weight_total
    reservation.expected_volume_total = data.get(
        "expected_volume_total",
        reservation.expected_volume_total,
    )
    reservation.service_type = data.get("service_type", reservation.service_type)
    reservation.route_id = route_id
    reservation.driver_id = driver_id
    reservation.adr_required = data.get("adr_required", reservation.adr_required)
    reservation.notes = data.get("notes", reservation.notes)
    reservation.status = status
    reservation.conflict_reason = conflict_reason
    reservation.permit_override = data.get("permit_override", reservation.permit_override)
    reservation.override_reason = data.get("override_reason", reservation.override_reason)
    reservation.updated_by = action_context.actor_user_id
    db.add(reservation)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=reservation.branch_id,
        action="planning.reservation.update",
        entity_type="planning_reservation",
        entity_id=reservation.id,
        details={"status": reservation.status},
    )
    emit_logistics_event(
        db,
        context=action_context,
        branch_id=reservation.branch_id,
        event_name="logistics.planning.reservation_updated",
        entity_type="planning_reservation",
        entity_id=reservation.id,
        payload={"vehicle_id": reservation.vehicle_id, "status": reservation.status},
    )
    return reservation


def activate_reservation(
    db: Session,
    *,
    reservation: LogisticsPlanningReservation,
    action_context: LogisticsActionContext,
) -> LogisticsPlanningReservation:
    if reservation.status in {"CANCELLED", "COMPLETED", "EXPIRED"}:
        raise ValueError("La planificación ya no puede activarse")
    if reservation.driver_id is None:
        raise ValueError("La planificación necesita conductor antes de activarse")
    if reservation.linked_session_id is not None:
        existing = get_vehicle_session(
            db,
            tenant_id=reservation.tenant_id,
            session_id=reservation.linked_session_id,
        )
        if existing is not None:
            return reservation
    vehicle = _get_vehicle(db, tenant_id=reservation.tenant_id, vehicle_id=reservation.vehicle_id)
    status, conflict_reason = _resolve_status(
        db,
        tenant_id=reservation.tenant_id,
        vehicle=vehicle,
        planned_start_at=reservation.planned_start_at,
        planned_end_at=reservation.planned_end_at,
        expected_weight_total=(
            float(reservation.expected_weight_total)
            if reservation.expected_weight_total is not None
            else None
        ),
        expected_load_summary=reservation.expected_load_summary,
        adr_required=reservation.adr_required,
        exclude_reservation_id=reservation.id,
    )
    if status == "CONFLICT":
        reservation.status = status
        reservation.conflict_reason = conflict_reason
        db.add(reservation)
        raise ValueError("La planificación sigue en conflicto y no puede activarse")
    session_payload = SimpleNamespace(
        vehicle_id=reservation.vehicle_id,
        driver_id=reservation.driver_id,
        origin_warehouse_id=reservation.origin_warehouse_id,
        route_id=reservation.route_id,
    )
    session = create_vehicle_session(
        db,
        tenant_id=reservation.tenant_id,
        payload=session_payload,
        action_context=action_context,
        opened_at=reservation.planned_start_at,
    )
    reservation.linked_session_id = session.id
    reservation.status = "READY"
    reservation.conflict_reason = None
    reservation.updated_by = action_context.actor_user_id
    db.add(reservation)
    db.flush()

    # Crear plan de carga automatico desde los productos de la reserva.
    # El operador puede ajustar cantidades y agregar seriales despues.
    expected_load = (reservation.expected_load_summary or {})
    reservation_items = expected_load.get("items", [])
    if reservation_items:
        from plugins.logistics.backend.services.load_plans import upsert_load_plan

        synthetic_payload = SimpleNamespace(
            items=[
                SimpleNamespace(
                    product_id=item.get("product_id"),
                    planned_quantity=item.get("quantity", 1),
                    source_warehouse_id=reservation.origin_warehouse_id,
                )
                for item in reservation_items
                if item.get("product_id")
            ],
            notes="Carga automatica desde planificacion",
        )
        upsert_load_plan(
            db,
            session=session,
            payload=synthetic_payload,
            action_context=action_context,
        )
    db.flush()

    audit_logistics_action(
        db,
        context=action_context,
        branch_id=reservation.branch_id,
        action="planning.reservation.activate",
        entity_type="planning_reservation",
        entity_id=reservation.id,
        details={"session_id": session.id},
    )
    emit_logistics_event(
        db,
        context=action_context,
        branch_id=reservation.branch_id,
        event_name="logistics.planning.reservation_activated",
        entity_type="planning_reservation",
        entity_id=reservation.id,
        payload={"session_id": session.id},
    )
    return reservation


def cancel_reservation(
    db: Session,
    *,
    reservation: LogisticsPlanningReservation,
    action_context: LogisticsActionContext,
) -> LogisticsPlanningReservation:
    if reservation.linked_session_id is not None:
        raise ValueError("La planificación ya fue materializada en jornada")
    reservation.status = "CANCELLED"
    reservation.updated_by = action_context.actor_user_id
    db.add(reservation)
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=reservation.branch_id,
        action="planning.reservation.cancel",
        entity_type="planning_reservation",
        entity_id=reservation.id,
        details={},
    )
    emit_logistics_event(
        db,
        context=action_context,
        branch_id=reservation.branch_id,
        event_name="logistics.planning.reservation_cancelled",
        entity_type="planning_reservation",
        entity_id=reservation.id,
        payload={},
    )
    return reservation


def sync_reservation_from_session(db: Session, *, session: LogisticsVehicleSession) -> None:
    reservation = db.scalar(
        select(LogisticsPlanningReservation).where(
            LogisticsPlanningReservation.linked_session_id == session.id
        )
    )
    if reservation is None:
        return
    if session.status == "DRAFT":
        reservation.status = "READY"
    elif session.status in LIVE_SESSION_STATUSES:
        reservation.status = "IN_PROGRESS"
        reservation.actual_start_at = reservation.actual_start_at or _utc_now()
    elif session.status == "CLOSED":
        reservation.status = "COMPLETED"
        reservation.actual_start_at = reservation.actual_start_at or session.opened_at
        reservation.actual_end_at = session.closed_at or _utc_now()
        reservation.actual_load_summary = (
            reservation.actual_load_summary or reservation.expected_load_summary
        )
        emit_logistics_event(
            db,
            context=LogisticsActionContext(
                tenant_id=session.tenant_id,
                branch_id=session.branch_id,
                actor_user_id=session.updated_by,
                correlation_id=None,
                request_id=None,
            ),
            branch_id=session.branch_id,
            event_name="logistics.planning.reservation_completed",
            entity_type="planning_reservation",
            entity_id=reservation.id,
            payload={"session_id": session.id},
        )
    elif session.status == "CANCELLED":
        reservation.status = "CANCELLED"
    reservation.updated_by = session.updated_by
    db.add(reservation)
