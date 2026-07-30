from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.dto.route_control import (
    RouteControlStateRead,
    VehicleLocationEventRead,
)
from plugins.logistics.backend.models import (
    LogisticsRouteControlState,
    LogisticsRouteStop,
    LogisticsVehicleLocationEvent,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.services.route_stop_results import build_route_stop_progress_snapshot

TRACKING_ACCEPTED_SESSION_STATUSES = {
    "DRAFT",
    "LOADING",
    "READY_TO_DEPART",
    "OUTBOUND",
    "RETURNING",
}
ACTIVE_ROUTE_SESSION_STATUSES = {"OUTBOUND", "RETURNING"}
STOPPED_SPEED_THRESHOLD = 1.0


@dataclass
class DerivedRouteControlState:
    route_id: str | None
    vehicle_id: str
    active_stop_id: str | None
    active_stop_started_at: datetime | None
    current_stop_id: str | None
    current_stop_index: int | None
    status: str
    last_lat: float | None
    last_lng: float | None
    last_speed: float | None
    last_heading: float | None
    last_recorded_at: datetime | None
    completed_stops: int
    total_stops: int
    progress_percent: float
    off_route: bool
    next_stop_eta_minutes: int | None
    geofence_state: str | None


def _build_location_event_read(event: LogisticsVehicleLocationEvent) -> VehicleLocationEventRead:
    return VehicleLocationEventRead(
        id=event.id,
        session_id=event.session_id,
        route_id=event.route_id,
        vehicle_id=event.vehicle_id,
        driver_id=event.driver_id,
        lat=float(event.lat),
        lng=float(event.lng),
        speed=float(event.speed) if event.speed is not None else None,
        heading=float(event.heading) if event.heading is not None else None,
        accuracy_meters=float(event.accuracy_meters) if event.accuracy_meters is not None else None,
        source=event.source,
        recorded_at=event.recorded_at,
        received_at=event.received_at,
    )


def get_latest_vehicle_location_event(
    db: Session, *, session_id: str
) -> LogisticsVehicleLocationEvent | None:
    return db.scalar(
        select(LogisticsVehicleLocationEvent)
        .where(LogisticsVehicleLocationEvent.session_id == session_id)
        .order_by(
            LogisticsVehicleLocationEvent.recorded_at.desc(),
            LogisticsVehicleLocationEvent.created_at.desc(),
        )
        .limit(1)
    )


def list_vehicle_location_history(
    db: Session,
    *,
    session_id: str,
    from_recorded_at: datetime | None = None,
    to_recorded_at: datetime | None = None,
    limit: int = 200,
) -> list[VehicleLocationEventRead]:
    stmt = select(LogisticsVehicleLocationEvent).where(
        LogisticsVehicleLocationEvent.session_id == session_id
    )
    if from_recorded_at is not None:
        stmt = stmt.where(LogisticsVehicleLocationEvent.recorded_at >= from_recorded_at)
    if to_recorded_at is not None:
        stmt = stmt.where(LogisticsVehicleLocationEvent.recorded_at <= to_recorded_at)
    events = list(
        db.scalars(
            stmt.order_by(
                LogisticsVehicleLocationEvent.recorded_at.desc(),
                LogisticsVehicleLocationEvent.created_at.desc(),
            ).limit(limit)
        ).all()
    )
    events.reverse()
    return [_build_location_event_read(event) for event in events]


def _get_active_stop(session: LogisticsVehicleSession, db: Session) -> LogisticsRouteStop | None:
    if session.route_id is None:
        return None
    return db.scalar(
        select(LogisticsRouteStop)
        .where(
            LogisticsRouteStop.route_id == session.route_id,
            LogisticsRouteStop.arrival_time.is_not(None),
            LogisticsRouteStop.departure_time.is_(None),
        )
        .order_by(LogisticsRouteStop.arrival_time.desc())
        .limit(1)
    )


def _derive_route_control_state(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    latest_event: LogisticsVehicleLocationEvent | None,
) -> DerivedRouteControlState:
    stop_snapshots = build_route_stop_progress_snapshot(db, session=session)
    total_stops = len(stop_snapshots)
    completed_stops = sum(1 for item in stop_snapshots if item.progress_status == "COMPLETED")
    progress_percent = round((completed_stops / total_stops) * 100, 2) if total_stops else 0.0

    active_stop = _get_active_stop(session, db)
    current_stop_id: str | None = None
    current_stop_index: int | None = None
    if active_stop is not None:
        current_stop_id = active_stop.id
        current_stop_index = max(active_stop.stop_order - 1, 0)
    else:
        for index, snapshot in enumerate(stop_snapshots):
            if snapshot.progress_status != "COMPLETED":
                current_stop_id = snapshot.route_stop_id
                current_stop_index = index
                break

    if session.route_id is None:
        status = "NO_ROUTE_ASSIGNED"
    elif session.status in {"DRAFT", "LOADING", "READY_TO_DEPART"}:
        status = "PENDING_START"
    elif session.status in {"AWAITING_RECONCILIATION", "CLOSED"}:
        status = "COMPLETADO"
    elif active_stop is not None:
        status = "EN_PARADA"
    else:
        speed = (
            float(latest_event.speed)
            if latest_event is not None and latest_event.speed is not None
            else None
        )
        status = "DETENIDO" if speed is not None and speed <= STOPPED_SPEED_THRESHOLD else "EN_RUTA"

    return DerivedRouteControlState(
        route_id=session.route_id,
        vehicle_id=session.vehicle_id,
        active_stop_id=active_stop.id if active_stop is not None else None,
        active_stop_started_at=active_stop.arrival_time if active_stop is not None else None,
        current_stop_id=current_stop_id,
        current_stop_index=current_stop_index,
        status=status,
        last_lat=float(latest_event.lat) if latest_event is not None else None,
        last_lng=float(latest_event.lng) if latest_event is not None else None,
        last_speed=(
            float(latest_event.speed)
            if latest_event is not None and latest_event.speed is not None
            else None
        ),
        last_heading=(
            float(latest_event.heading)
            if latest_event is not None and latest_event.heading is not None
            else None
        ),
        last_recorded_at=latest_event.recorded_at if latest_event is not None else None,
        completed_stops=completed_stops,
        total_stops=total_stops,
        progress_percent=progress_percent,
        off_route=False,
        next_stop_eta_minutes=None,
        geofence_state="INSIDE" if active_stop is not None else None,
    )


def _upsert_route_control_state(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    derived: DerivedRouteControlState,
) -> tuple[LogisticsRouteControlState, bool]:
    state = db.get(LogisticsRouteControlState, session.id)
    previous_status = state.status if state is not None else None
    if state is None:
        state = LogisticsRouteControlState(session_id=session.id, tenant_id=session.tenant_id)
        db.add(state)
    state.route_id = derived.route_id
    state.vehicle_id = derived.vehicle_id
    state.active_stop_id = derived.active_stop_id
    state.active_stop_started_at = derived.active_stop_started_at
    state.current_stop_id = derived.current_stop_id
    state.current_stop_index = derived.current_stop_index
    state.status = derived.status
    state.last_lat = derived.last_lat
    state.last_lng = derived.last_lng
    state.last_speed = derived.last_speed
    state.last_heading = derived.last_heading
    state.last_recorded_at = derived.last_recorded_at
    state.completed_stops = derived.completed_stops
    state.total_stops = derived.total_stops
    state.progress_percent = derived.progress_percent
    state.off_route = derived.off_route
    state.next_stop_eta_minutes = derived.next_stop_eta_minutes
    state.geofence_state = derived.geofence_state
    db.add(state)
    db.flush()
    return state, previous_status != derived.status


def _build_route_control_state_read(
    state: LogisticsRouteControlState,
) -> RouteControlStateRead:
    return RouteControlStateRead(
        session_id=state.session_id,
        route_id=state.route_id,
        vehicle_id=state.vehicle_id,
        active_stop_id=state.active_stop_id,
        active_stop_started_at=state.active_stop_started_at,
        current_stop_id=state.current_stop_id,
        current_stop_index=state.current_stop_index,
        status=state.status,
        last_lat=float(state.last_lat) if state.last_lat is not None else None,
        last_lng=float(state.last_lng) if state.last_lng is not None else None,
        last_speed=float(state.last_speed) if state.last_speed is not None else None,
        last_heading=float(state.last_heading) if state.last_heading is not None else None,
        last_recorded_at=state.last_recorded_at,
        completed_stops=state.completed_stops,
        total_stops=state.total_stops,
        progress_percent=float(state.progress_percent),
        off_route=state.off_route,
        next_stop_eta_minutes=state.next_stop_eta_minutes,
        geofence_state=state.geofence_state,
        updated_at=state.updated_at,
    )


def get_route_control_state(
    db: Session, *, session: LogisticsVehicleSession
) -> RouteControlStateRead:
    latest_event = get_latest_vehicle_location_event(db, session_id=session.id)
    derived = _derive_route_control_state(db, session=session, latest_event=latest_event)
    state, _ = _upsert_route_control_state(db, session=session, derived=derived)
    return _build_route_control_state_read(state)


def record_vehicle_location(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    payload,
    action_context: LogisticsActionContext,
) -> VehicleLocationEventRead:
    if session.status not in TRACKING_ACCEPTED_SESSION_STATUSES:
        raise ValueError("La jornada no admite telemetría en este estado")

    latest_event = get_latest_vehicle_location_event(db, session_id=session.id)
    if (
        latest_event is not None
        and float(latest_event.lat) == float(payload.lat)
        and float(latest_event.lng) == float(payload.lng)
        and latest_event.recorded_at == payload.recorded_at
    ):
        return _build_location_event_read(latest_event)

    event = LogisticsVehicleLocationEvent(
        tenant_id=session.tenant_id,
        branch_id=session.branch_id,
        session_id=session.id,
        route_id=session.route_id,
        vehicle_id=session.vehicle_id,
        driver_id=session.driver_id,
        lat=payload.lat,
        lng=payload.lng,
        speed=payload.speed,
        heading=payload.heading,
        accuracy_meters=payload.accuracy_meters,
        source=payload.source,
        recorded_at=payload.recorded_at,
        received_at=datetime.now(UTC),
    )
    db.add(event)
    db.flush()

    derived = _derive_route_control_state(db, session=session, latest_event=event)
    state, status_changed = _upsert_route_control_state(db, session=session, derived=derived)
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.location.record",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "location_event_id": event.id,
            "lat": payload.lat,
            "lng": payload.lng,
            "source": payload.source,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.vehicle_location.recorded",
        entity_type="vehicle_session",
        entity_id=session.id,
        payload={"location_event_id": event.id, "route_id": session.route_id},
    )
    if status_changed:
        emit_logistics_event(
            db,
            context=action_context,
            event_name="logistics.route_control.status_changed",
            entity_type="vehicle_session",
            entity_id=session.id,
            payload={"status": state.status, "route_id": session.route_id},
        )
    return _build_location_event_read(event)


def _require_route_stop_for_session(
    db: Session, *, session: LogisticsVehicleSession, stop_id: str
) -> LogisticsRouteStop:
    if session.route_id is None:
        raise ValueError("La jornada no tiene ruta asignada")
    stop = db.scalar(
        select(LogisticsRouteStop).where(
            LogisticsRouteStop.id == stop_id,
            LogisticsRouteStop.route_id == session.route_id,
        )
    )
    if stop is None:
        raise LookupError("Parada no encontrada en la ruta de la jornada")
    return stop


def mark_route_stop_arrived(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    stop_id: str,
    action_context: LogisticsActionContext,
) -> RouteControlStateRead:
    if session.status not in ACTIVE_ROUTE_SESSION_STATUSES:
        raise ValueError("La jornada no permite marcar llegada en este estado")
    stop = _require_route_stop_for_session(db, session=session, stop_id=stop_id)
    if stop.departure_time is not None:
        raise ValueError("La parada ya fue cerrada y no puede volver a marcarse como llegada")
    stop.arrival_time = stop.arrival_time or datetime.now(UTC)
    db.add(stop)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.route_stop.arrive",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"route_stop_id": stop.id},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.route_control.stop_arrived_manually",
        entity_type="vehicle_session",
        entity_id=session.id,
        payload={"route_stop_id": stop.id, "route_id": session.route_id},
    )
    return get_route_control_state(db, session=session)


def mark_route_stop_departed(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    stop_id: str,
    action_context: LogisticsActionContext,
) -> RouteControlStateRead:
    if session.status not in ACTIVE_ROUTE_SESSION_STATUSES:
        raise ValueError("La jornada no permite marcar salida en este estado")
    stop = _require_route_stop_for_session(db, session=session, stop_id=stop_id)
    now = datetime.now(UTC)
    stop.arrival_time = stop.arrival_time or now
    stop.departure_time = now
    db.add(stop)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.route_stop.depart",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"route_stop_id": stop.id},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.route_control.stop_departed_manually",
        entity_type="vehicle_session",
        entity_id=session.id,
        payload={"route_stop_id": stop.id, "route_id": session.route_id},
    )
    return get_route_control_state(db, session=session)
