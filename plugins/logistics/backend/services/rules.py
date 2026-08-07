from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import (
    LogisticsInventoryDiscrepancy,
    LogisticsVehicle,
    LogisticsVehicleSession,
)

PENDING_SESSION_STATUSES = {
    "DRAFT",
}

LIVE_SESSION_STATUSES = {
    "LOADING",
    "READY_TO_DEPART",
    "OUTBOUND",
    "RETURNING",
    "AWAITING_RECONCILIATION",
}

ACTIVE_SESSION_STATUSES = PENDING_SESSION_STATUSES | LIVE_SESSION_STATUSES


def ensure_single_live_session(
    db: Session,
    *,
    tenant_id: str,
    vehicle_id: str,
    exclude_session_id: str | None = None,
) -> None:
    conditions = [
        LogisticsVehicleSession.tenant_id == tenant_id,
        LogisticsVehicleSession.vehicle_id == vehicle_id,
        LogisticsVehicleSession.status.in_(LIVE_SESSION_STATUSES),
    ]
    if exclude_session_id is not None:
        conditions.append(LogisticsVehicleSession.id != exclude_session_id)
    existing = db.scalar(
        select(LogisticsVehicleSession.id).where(*conditions)
    )
    if existing is not None:
        raise ValueError("El vehiculo ya tiene una jornada activa")


def ensure_single_active_session(db: Session, *, tenant_id: str, vehicle_id: str) -> None:
    ensure_single_live_session(db, tenant_id=tenant_id, vehicle_id=vehicle_id)


def ensure_session_editable(session: LogisticsVehicleSession) -> None:
    if session.status in {"CLOSED", "CANCELLED"}:
        raise ValueError("La jornada ya no puede modificarse")


def ensure_session_can_start_loading(session: LogisticsVehicleSession) -> None:
    ensure_session_editable(session)
    if session.status != "DRAFT":
        raise ValueError("Solo una jornada en DRAFT puede iniciar carga")


def get_session_start_queue_blocker(
    db: Session,
    *,
    session: LogisticsVehicleSession,
) -> str | None:
    if session.status != "DRAFT":
        return None

    live_existing = db.scalar(
        select(LogisticsVehicleSession.id).where(
            LogisticsVehicleSession.tenant_id == session.tenant_id,
            LogisticsVehicleSession.vehicle_id == session.vehicle_id,
            LogisticsVehicleSession.id != session.id,
            LogisticsVehicleSession.status.in_(LIVE_SESSION_STATUSES),
        )
    )
    if live_existing is not None:
        return "La jornada está pendiente en cola y no puede iniciar mientras otra jornada usa el vehículo"

    next_draft_id = db.scalar(
        select(LogisticsVehicleSession.id)
        .where(
            LogisticsVehicleSession.tenant_id == session.tenant_id,
            LogisticsVehicleSession.vehicle_id == session.vehicle_id,
            LogisticsVehicleSession.status == "DRAFT",
        )
        .order_by(LogisticsVehicleSession.opened_at.asc(), LogisticsVehicleSession.id.asc())
        .limit(1)
    )
    if next_draft_id is not None and next_draft_id != session.id:
        return "La jornada está pendiente en cola y no puede iniciar hasta que le toque su turno"
    return None


def ensure_session_can_be_ready(session: LogisticsVehicleSession) -> None:
    ensure_session_editable(session)
    if session.status != "LOADING":
        raise ValueError("Solo una jornada en LOADING puede pasar a READY_TO_DEPART")


def ensure_session_can_depart(session: LogisticsVehicleSession) -> None:
    ensure_session_editable(session)
    if session.status != "READY_TO_DEPART":
        raise ValueError("Solo una jornada READY_TO_DEPART puede salir")


def ensure_session_can_mark_returning(session: LogisticsVehicleSession) -> None:
    ensure_session_editable(session)
    if session.status != "OUTBOUND":
        raise ValueError("Solo una jornada OUTBOUND puede pasar a RETURNING")


def ensure_session_can_close(
    session: LogisticsVehicleSession,
    *,
    has_open_discrepancies: bool,
    reconciliation_status: str | None = None,
) -> None:
    ensure_session_editable(session)
    if session.status != "AWAITING_RECONCILIATION":
        raise ValueError("Solo una jornada AWAITING_RECONCILIATION puede cerrarse")
    if reconciliation_status is None:
        raise ValueError("La jornada no tiene conciliacion registrada")
    if reconciliation_status != "MATCHED":
        raise ValueError("La jornada solo puede cerrarse cuando la conciliacion esta MATCHED")
    if has_open_discrepancies:
        raise ValueError("No se puede cerrar con discrepancias abiertas")


def get_next_transition_blocker(
    session: LogisticsVehicleSession,
    *,
    has_open_discrepancies: bool = False,
    reconciliation_status: str | None = None,
    start_queue_blocker: str | None = None,
) -> str | None:
    try:
        if session.status == "DRAFT":
            if start_queue_blocker is not None:
                return start_queue_blocker
            ensure_session_can_start_loading(session)
        elif session.status == "LOADING":
            ensure_session_can_be_ready(session)
        elif session.status == "READY_TO_DEPART":
            ensure_session_can_depart(session)
        elif session.status == "OUTBOUND":
            ensure_session_can_mark_returning(session)
        elif session.status == "RETURNING":
            pass
        elif session.status == "AWAITING_RECONCILIATION":
            ensure_session_can_close(
                session,
                has_open_discrepancies=has_open_discrepancies,
                reconciliation_status=reconciliation_status,
            )
        elif session.status in {"CLOSED", "CANCELLED"}:
            ensure_session_editable(session)
        else:
            return "La jornada tiene un estado invalido"
        return None
    except ValueError as exc:
        return str(exc)


def ensure_capacity_not_exceeded(vehicle: LogisticsVehicle, weight_kg: float) -> None:
    max_weight = vehicle.useful_load or vehicle.capacity_weight
    if max_weight is None:
        return
    if weight_kg > float(max_weight):
        formatted_max_weight = float(max_weight)
        raise ValueError(
            "La carga confirmada "
            f"({weight_kg:.2f} kg) supera la capacidad del vehiculo "
            f"({formatted_max_weight:.2f} kg)"
        )


def has_open_discrepancies(db: Session, *, reconciliation_id: str) -> bool:
    existing = db.scalar(
        select(LogisticsInventoryDiscrepancy.id).where(
            LogisticsInventoryDiscrepancy.reconciliation_id == reconciliation_id,
            LogisticsInventoryDiscrepancy.status.in_(
                {"OPEN", "UNDER_REVIEW", "APPROVED_FOR_ADJUSTMENT"}
            ),
        )
    )
    return existing is not None
