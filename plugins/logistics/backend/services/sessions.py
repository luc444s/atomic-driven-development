from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.kernel.auth.models import User
from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsRoute,
    LogisticsVehicle,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.logistics.backend.services.resources import get_vehicle, get_warehouse
from plugins.logistics.backend.services.rules import (
    ACTIVE_SESSION_STATUSES,
    ensure_session_can_be_ready,
    ensure_session_can_depart,
    ensure_session_can_mark_returning,
    ensure_session_can_start_loading,
    ensure_single_live_session,
    get_session_start_queue_blocker,
)


def list_driver_options(db: Session, *, tenant_id: str) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .where(User.tenant_id == tenant_id, User.is_active.is_(True))
            .order_by(User.full_name.asc())
        ).all()
    )


def _ensure_mobile_warehouse_for_vehicle(
    db: Session,
    *,
    tenant_id: str,
    vehicle: LogisticsVehicle,
    origin_warehouse_id: str,
) -> LogisticsWarehouse:
    if vehicle.mobile_warehouse_id:
        existing = get_warehouse(db, tenant_id=tenant_id, warehouse_id=vehicle.mobile_warehouse_id)
        if existing is not None:
            return existing

    code = f"MOB-{vehicle.plate.strip().upper()}"
    existing = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.tenant_id == tenant_id,
            LogisticsWarehouse.code == code,
        )
    )
    if existing is None:
        origin = get_warehouse(db, tenant_id=tenant_id, warehouse_id=origin_warehouse_id)
        if origin is None:
            raise LookupError("Warehouse origen no encontrado")
        existing = LogisticsWarehouse(
            tenant_id=tenant_id,
            branch_id=origin.branch_id,
            name=f"Movil {vehicle.plate.strip().upper()}",
            code=code,
            warehouse_type="MOBILE",
            is_active=True,
        )
        db.add(existing)
        db.flush()

    vehicle.mobile_warehouse_id = existing.id
    db.add(vehicle)
    db.flush()
    return existing


def create_vehicle_session(
    db: Session,
    *,
    tenant_id: str,
    payload,
    action_context: LogisticsActionContext,
    opened_at: datetime | None = None,
) -> LogisticsVehicleSession:
    vehicle = get_vehicle(db, tenant_id=tenant_id, vehicle_id=payload.vehicle_id)
    if vehicle is None:
        raise LookupError("Vehiculo no encontrado")
    driver = db.scalar(
        select(User).where(
            User.id == payload.driver_id,
            User.tenant_id == tenant_id,
            User.is_active.is_(True),
        )
    )
    if driver is None:
        raise LookupError("Conductor no encontrado")
    origin_warehouse_id = payload.origin_warehouse_id or vehicle.warehouse_id
    if not origin_warehouse_id:
        raise ValueError(
            "El vehiculo necesita warehouse de origen o debe indicarse uno en la jornada"
        )
    origin = get_warehouse(db, tenant_id=tenant_id, warehouse_id=origin_warehouse_id)
    if origin is None:
        raise LookupError("Warehouse origen no encontrado")
    if payload.route_id is not None:
        route = db.scalar(
            select(LogisticsRoute).where(
                LogisticsRoute.id == payload.route_id,
                LogisticsRoute.tenant_id == tenant_id,
            )
        )
        if route is None:
            raise LookupError("Ruta no encontrada")
    mobile = _ensure_mobile_warehouse_for_vehicle(
        db,
        tenant_id=tenant_id,
        vehicle=vehicle,
        origin_warehouse_id=origin.id,
    )

    session = LogisticsVehicleSession(
        tenant_id=tenant_id,
        branch_id=action_context.branch_id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        origin_warehouse_id=origin.id,
        mobile_warehouse_id=mobile.id,
        route_id=payload.route_id,
        status="DRAFT",
        opened_at=opened_at or datetime.now(UTC),
        created_by=action_context.actor_user_id,
        updated_by=action_context.actor_user_id,
    )
    db.add(session)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.create",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "vehicle_id": vehicle.id,
            "driver_id": payload.driver_id,
            "route_id": payload.route_id,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.vehicle_session.created",
        entity_type="vehicle_session",
        entity_id=session.id,
        payload={"vehicle_id": vehicle.id, "mobile_warehouse_id": mobile.id},
    )
    return session


def list_vehicle_sessions(
    db: Session,
    *,
    tenant_id: str,
    status: str | None = None,
    active_only: bool = False,
) -> list[LogisticsVehicleSession]:
    stmt = select(LogisticsVehicleSession).where(LogisticsVehicleSession.tenant_id == tenant_id)
    if active_only:
        stmt = stmt.where(LogisticsVehicleSession.status.in_(ACTIVE_SESSION_STATUSES))
    elif status:
        stmt = stmt.where(LogisticsVehicleSession.status == status)
    return list(db.scalars(stmt.order_by(LogisticsVehicleSession.opened_at.desc())).all())


def get_vehicle_session(
    db: Session,
    *,
    tenant_id: str,
    session_id: str,
) -> LogisticsVehicleSession | None:
    return db.scalar(
        select(LogisticsVehicleSession).where(
            LogisticsVehicleSession.tenant_id == tenant_id,
            LogisticsVehicleSession.id == session_id,
        )
    )


def start_loading_session(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleSession:
    ensure_session_can_start_loading(session)
    start_queue_blocker = get_session_start_queue_blocker(db, session=session)
    if start_queue_blocker is not None:
        raise ValueError(start_queue_blocker)
    ensure_single_live_session(
        db,
        tenant_id=session.tenant_id,
        vehicle_id=session.vehicle_id,
        exclude_session_id=session.id,
    )
    session.status = "LOADING"
    session.updated_by = action_context.actor_user_id
    db.add(session)
    from plugins.logistics.backend.services.planning_reservations import (
        sync_reservation_from_session,
    )

    sync_reservation_from_session(db, session=session)
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.start_loading",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.vehicle_session.loading_started",
        entity_type="vehicle_session",
        entity_id=session.id,
        payload={},
    )
    return session


def mark_session_ready(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleSession:
    ensure_session_can_be_ready(session)
    session.status = "READY_TO_DEPART"
    session.ready_at = datetime.now(UTC)
    session.updated_by = action_context.actor_user_id
    db.add(session)
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.ready",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.vehicle_session.ready",
        entity_type="vehicle_session",
        entity_id=session.id,
        payload={},
    )
    return session


def depart_session(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleSession:
    from plugins.logistics.backend.services.load_serials import (
        mark_confirmed_serials_on_outbound,
    )

    ensure_session_can_depart(session)
    session.status = "OUTBOUND"
    session.departed_at = datetime.now(UTC)
    session.updated_by = action_context.actor_user_id
    db.add(session)
    mark_confirmed_serials_on_outbound(
        db,
        tenant_id=session.tenant_id,
        session_id=session.id,
        action_context=action_context,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.depart",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.vehicle_session.outbound",
        entity_type="vehicle_session",
        entity_id=session.id,
        payload={},
    )
    return session


def mark_session_returning(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleSession:
    ensure_session_can_mark_returning(session)
    session.status = "RETURNING"
    session.returned_at = datetime.now(UTC)
    session.updated_by = action_context.actor_user_id
    db.add(session)
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.returning",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.vehicle_session.returning",
        entity_type="vehicle_session",
        entity_id=session.id,
        payload={},
    )
    return session


def cancel_session(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleSession:
    from plugins.logistics.backend.services.load_serials import (
        release_active_serial_assignments,
    )

    ensure_session_can_start_loading(session) if session.status == "DRAFT" else None
    if session.status not in {"DRAFT", "LOADING", "READY_TO_DEPART"}:
        raise ValueError("Solo una jornada temprana puede cancelarse")
    release_active_serial_assignments(
        db,
        session_id=session.id,
        release_reason="OPERATION_CANCELLED",
    )
    session.status = "CANCELLED"
    session.closing_notes = notes or session.closing_notes
    session.updated_by = action_context.actor_user_id
    db.add(session)
    from plugins.logistics.backend.services.planning_reservations import (
        sync_reservation_from_session,
    )

    sync_reservation_from_session(db, session=session)
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.cancel",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"notes": notes},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.vehicle_session.cancelled",
        entity_type="vehicle_session",
        entity_id=session.id,
        payload={"notes": notes or ""},
    )
    return session


def assign_route_to_session(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    route_id: str,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleSession:
    from plugins.logistics.backend.services.routes import get_route

    if session.status in {"CLOSED", "CANCELLED"}:
        raise ValueError("No se puede asignar ruta a una jornada finalizada o cancelada")

    route = get_route(db, tenant_id=session.tenant_id, route_id=route_id)
    if route is None:
        raise LookupError("Ruta no encontrada")

    old_route_id = session.route_id
    session.route_id = route_id
    session.updated_by = action_context.actor_user_id
    db.add(session)

    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.route.assign",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "previous_route_id": old_route_id,
            "new_route_id": route_id,
        },
    )
    return session
