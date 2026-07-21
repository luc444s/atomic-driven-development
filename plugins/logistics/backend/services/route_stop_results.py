from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.dto.route_operations import RouteStopProgressRead
from plugins.logistics.backend.dto.route_stop_results import RouteStopResultRead
from plugins.logistics.backend.models import (
    LogisticsDeliveryPoint,
    LogisticsRouteIncident,
    LogisticsRouteOperation,
    LogisticsRouteStop,
    LogisticsRouteStopResult,
    LogisticsVehicleSession,
)

VALID_STOP_RESULT_STATUSES = {"PENDING", "IN_PROGRESS", "PARTIAL", "COMPLETED", "FAILED"}
VALID_STOP_RESULT_OUTCOME_TYPES = {
    "NORMAL",
    "CUSTOMER_ABSENT",
    "FAILED_DELIVERY",
    "PARTIAL_ATTENDED",
    "UNPLANNED_RETURN",
    "OTHER",
}
MUTABLE_SESSION_STATUSES = {"OUTBOUND", "RETURNING"}
FAILED_INCIDENT_TYPES = {"CUSTOMER_ABSENT", "FAILED_DELIVERY"}


@dataclass
class RouteStopProgressSnapshot:
    route_stop_id: str
    stop_order: int
    label: str
    progress_status: str
    open_incidents: int
    last_operation_at: datetime | None
    completion_percent: float | None
    outcome_type: str | None
    driver_note: str | None


def _build_stop_label(stop_order: int, customer_name: str | None) -> str:
    if customer_name:
        return f"Parada {stop_order} · {customer_name}"
    return f"Parada {stop_order}"


def _build_route_stop_result_read(result: LogisticsRouteStopResult) -> RouteStopResultRead:
    return RouteStopResultRead(
        id=result.id,
        session_id=result.session_id,
        route_stop_id=result.route_stop_id,
        status=result.status,
        completion_percent=float(result.completion_percent),
        outcome_type=result.outcome_type,
        driver_note=result.driver_note,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


def _validate_stop_result_payload(payload) -> None:
    if payload.status not in VALID_STOP_RESULT_STATUSES:
        raise ValueError("Estado de stop result no soportado")
    if payload.outcome_type not in VALID_STOP_RESULT_OUTCOME_TYPES:
        raise ValueError("Tipo de outcome de stop result no soportado")

    percent = float(payload.completion_percent)
    if payload.status == "PENDING" and percent != 0:
        raise ValueError("PENDING exige completion_percent = 0")
    if payload.status == "COMPLETED" and percent != 100:
        raise ValueError("COMPLETED exige completion_percent = 100")
    if payload.status in {"PARTIAL", "IN_PROGRESS"} and not (0 < percent < 100):
        raise ValueError(f"{payload.status} exige completion_percent entre 1 y 99")
    if payload.status == "FAILED" and percent >= 100:
        raise ValueError("FAILED no admite completion_percent = 100")


def _require_route_stop_for_session(
    db: Session, *, session: LogisticsVehicleSession, route_stop_id: str
) -> LogisticsRouteStop:
    if session.route_id is None:
        raise ValueError("La jornada no tiene ruta asignada")
    stop = db.scalar(
        select(LogisticsRouteStop).where(
            LogisticsRouteStop.id == route_stop_id,
            LogisticsRouteStop.route_id == session.route_id,
        )
    )
    if stop is None:
        raise LookupError("Parada no encontrada en la ruta de la jornada")
    return stop


def list_route_stop_results(db: Session, *, session_id: str) -> list[RouteStopResultRead]:
    results = list(
        db.scalars(
            select(LogisticsRouteStopResult)
            .where(LogisticsRouteStopResult.session_id == session_id)
            .order_by(LogisticsRouteStopResult.updated_at.desc())
        ).all()
    )
    return [_build_route_stop_result_read(result) for result in results]


def upsert_route_stop_result(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    route_stop_id: str,
    payload,
    action_context: LogisticsActionContext,
) -> RouteStopResultRead:
    if session.status not in MUTABLE_SESSION_STATUSES:
        raise ValueError("La jornada no permite registrar stop results en este estado")

    _validate_stop_result_payload(payload)
    _require_route_stop_for_session(db, session=session, route_stop_id=route_stop_id)
    result = db.scalar(
        select(LogisticsRouteStopResult).where(
            LogisticsRouteStopResult.session_id == session.id,
            LogisticsRouteStopResult.route_stop_id == route_stop_id,
        )
    )
    if result is None:
        result = LogisticsRouteStopResult(
            tenant_id=session.tenant_id,
            session_id=session.id,
            route_stop_id=route_stop_id,
            created_by=action_context.actor_user_id,
            updated_by=action_context.actor_user_id,
        )
        db.add(result)

    result.status = payload.status
    result.completion_percent = float(payload.completion_percent)
    result.outcome_type = payload.outcome_type
    result.driver_note = payload.driver_note
    result.updated_by = action_context.actor_user_id
    db.add(result)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.route_stop_result.upsert",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "route_stop_id": route_stop_id,
            "status": result.status,
            "completion_percent": float(result.completion_percent),
            "outcome_type": result.outcome_type,
        },
    )
    return _build_route_stop_result_read(result)


def build_route_stop_progress_snapshot(
    db: Session, *, session: LogisticsVehicleSession
) -> list[RouteStopProgressSnapshot]:
    if session.route_id is None:
        return []

    operation_counts = (
        select(
            LogisticsRouteOperation.route_stop_id.label("route_stop_id"),
            func.sum(
                case((LogisticsRouteOperation.status == "CONFIRMED", 1), else_=0)
            ).label("confirmed_count"),
            func.sum(
                case((LogisticsRouteOperation.status == "DRAFT", 1), else_=0)
            ).label("draft_count"),
            func.max(
                case(
                    (
                        LogisticsRouteOperation.status == "CONFIRMED",
                        LogisticsRouteOperation.performed_at,
                    ),
                    else_=None,
                )
            ).label("last_operation_at"),
        )
        .where(LogisticsRouteOperation.session_id == session.id)
        .group_by(LogisticsRouteOperation.route_stop_id)
        .subquery()
    )
    incident_counts = (
        select(
            LogisticsRouteIncident.route_stop_id.label("route_stop_id"),
            func.sum(
                case((LogisticsRouteIncident.status == "OPEN", 1), else_=0)
            ).label("open_incidents"),
            func.sum(
                case(
                    (
                        (LogisticsRouteIncident.status == "OPEN")
                        & (LogisticsRouteIncident.incident_type.in_(FAILED_INCIDENT_TYPES)),
                        1,
                    ),
                    else_=0,
                )
            ).label("failed_open_incidents"),
        )
        .where(LogisticsRouteIncident.session_id == session.id)
        .group_by(LogisticsRouteIncident.route_stop_id)
        .subquery()
    )
    stop_results = (
        select(
            LogisticsRouteStopResult.route_stop_id.label("route_stop_id"),
            LogisticsRouteStopResult.status.label("result_status"),
            LogisticsRouteStopResult.completion_percent.label("completion_percent"),
            LogisticsRouteStopResult.outcome_type.label("outcome_type"),
            LogisticsRouteStopResult.driver_note.label("driver_note"),
        )
        .where(LogisticsRouteStopResult.session_id == session.id)
        .subquery()
    )

    rows = db.execute(
        select(
            LogisticsRouteStop.id,
            LogisticsRouteStop.stop_order,
            LogisticsDeliveryPoint.customer_name,
            operation_counts.c.confirmed_count,
            operation_counts.c.draft_count,
            operation_counts.c.last_operation_at,
            incident_counts.c.open_incidents,
            incident_counts.c.failed_open_incidents,
            stop_results.c.result_status,
            stop_results.c.completion_percent,
            stop_results.c.outcome_type,
            stop_results.c.driver_note,
        )
        .select_from(LogisticsRouteStop)
        .outerjoin(
            LogisticsDeliveryPoint,
            LogisticsDeliveryPoint.id == LogisticsRouteStop.delivery_point_id,
        )
        .outerjoin(operation_counts, operation_counts.c.route_stop_id == LogisticsRouteStop.id)
        .outerjoin(incident_counts, incident_counts.c.route_stop_id == LogisticsRouteStop.id)
        .outerjoin(stop_results, stop_results.c.route_stop_id == LogisticsRouteStop.id)
        .where(LogisticsRouteStop.route_id == session.route_id)
        .order_by(LogisticsRouteStop.stop_order.asc())
    ).all()

    snapshots: list[RouteStopProgressSnapshot] = []
    for row in rows:
        result_status = row.result_status
        if result_status is not None:
            progress_status = result_status
        else:
            confirmed_count = int(row.confirmed_count or 0)
            draft_count = int(row.draft_count or 0)
            open_incidents = int(row.open_incidents or 0)
            failed_open_incidents = int(row.failed_open_incidents or 0)
            if failed_open_incidents and not confirmed_count:
                progress_status = "FAILED"
            elif open_incidents:
                progress_status = "PARTIAL"
            elif confirmed_count:
                progress_status = "COMPLETED"
            elif draft_count:
                progress_status = "IN_PROGRESS"
            else:
                progress_status = "PENDING"

        snapshots.append(
            RouteStopProgressSnapshot(
                route_stop_id=row.id,
                stop_order=int(row.stop_order),
                label=_build_stop_label(int(row.stop_order), row.customer_name),
                progress_status=progress_status,
                open_incidents=int(row.open_incidents or 0),
                last_operation_at=row.last_operation_at,
                completion_percent=(
                    float(row.completion_percent) if row.completion_percent is not None else None
                ),
                outcome_type=row.outcome_type,
                driver_note=row.driver_note,
            )
        )
    return snapshots


def build_route_stop_progress(
    db: Session, *, session: LogisticsVehicleSession
) -> list[RouteStopProgressRead]:
    return [
        RouteStopProgressRead(
            route_stop_id=item.route_stop_id,
            progress_status=item.progress_status,
            last_operation_at=item.last_operation_at,
            open_incidents=item.open_incidents,
            completion_percent=item.completion_percent,
            outcome_type=item.outcome_type,
            driver_note=item.driver_note,
        )
        for item in build_route_stop_progress_snapshot(db, session=session)
    ]
