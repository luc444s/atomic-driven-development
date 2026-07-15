from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import (
    LogisticsInventoryDiscrepancy,
    LogisticsVehicle,
    LogisticsVehicleSession,
)

ACTIVE_SESSION_STATUSES = {
    "DRAFT",
    "LOADING",
    "READY_TO_DEPART",
    "OUTBOUND",
    "RETURNING",
    "AWAITING_RECONCILIATION",
}


def ensure_single_active_session(db: Session, *, tenant_id: str, vehicle_id: str) -> None:
    existing = db.scalar(
        select(LogisticsVehicleSession.id).where(
            LogisticsVehicleSession.tenant_id == tenant_id,
            LogisticsVehicleSession.vehicle_id == vehicle_id,
            LogisticsVehicleSession.status.in_(ACTIVE_SESSION_STATUSES),
        )
    )
    if existing is not None:
        raise ValueError("El vehiculo ya tiene una jornada activa")


def ensure_session_editable(session: LogisticsVehicleSession) -> None:
    if session.status in {"CLOSED", "CANCELLED"}:
        raise ValueError("La jornada ya no puede modificarse")


def ensure_session_can_start_loading(session: LogisticsVehicleSession) -> None:
    ensure_session_editable(session)
    if session.status != "DRAFT":
        raise ValueError("Solo una jornada en DRAFT puede iniciar carga")


def ensure_session_can_be_ready(session: LogisticsVehicleSession) -> None:
    ensure_session_editable(session)
    if session.status != "LOADING":
        raise ValueError("Solo una jornada en LOADING puede pasar a READY_TO_DEPART")
    if not session.loaded_weight_kg or session.loaded_weight_kg <= 0:
        raise ValueError("La jornada necesita carga confirmada antes de quedar lista")


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
) -> str | None:
    try:
        if session.status == "DRAFT":
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
