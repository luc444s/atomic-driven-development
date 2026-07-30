from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.dto.operational_summary import (
    AttentionReason,
    BlockingReason,
    SessionOperationalSummaryCompositionRead,
    SessionOperationalSummaryIncidentIssueRead,
    SessionOperationalSummaryIncidentsRead,
    SessionOperationalSummaryLastActivityRead,
    SessionOperationalSummaryRead,
    SessionOperationalSummaryRouteActivityRead,
    SessionOperationalSummaryStopCountersRead,
    SessionOperationalSummaryStopIssueRead,
    SessionOperationalSummaryWaybillRead,
)
from plugins.logistics.backend.models import (
    LogisticsDeliveryPoint,
    LogisticsRouteIncident,
    LogisticsRouteOperation,
    LogisticsRouteStop,
    LogisticsSessionWaybillVersion,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.services.route_operations import build_current_composition
from plugins.logistics.backend.services.route_stop_results import build_route_stop_progress_snapshot
from plugins.logistics.backend.services.session_waybills import (
    REGENERABLE_STATUSES,
    build_current_session_waybill,
)

ROUTE_REQUIRED_STATUSES = {"OUTBOUND", "RETURNING", "AWAITING_RECONCILIATION", "CLOSED"}


def _count_incidents(db: Session, *, session_id: str) -> SessionOperationalSummaryIncidentsRead:
    rows = db.execute(
        select(LogisticsRouteIncident.status, func.count(LogisticsRouteIncident.id))
        .where(LogisticsRouteIncident.session_id == session_id)
        .group_by(LogisticsRouteIncident.status)
    ).all()
    counts = {status: int(total) for status, total in rows}
    return SessionOperationalSummaryIncidentsRead(
        open_total=counts.get("OPEN", 0),
        corrected_total=counts.get("CORRECTED", 0),
        resolved_total=counts.get("RESOLVED", 0),
    )


def _load_open_incidents(
    db: Session, *, session_id: str
) -> list[SessionOperationalSummaryIncidentIssueRead]:
    rows = db.execute(
        select(
            LogisticsRouteIncident.id,
            LogisticsRouteIncident.incident_type,
            LogisticsRouteIncident.status,
            LogisticsRouteIncident.route_stop_id,
            LogisticsRouteIncident.notes,
            LogisticsRouteIncident.created_at,
            LogisticsRouteIncident.updated_at,
            LogisticsRouteStop.stop_order,
            LogisticsDeliveryPoint.customer_name,
        )
        .select_from(LogisticsRouteIncident)
        .outerjoin(
            LogisticsRouteStop,
            LogisticsRouteStop.id == LogisticsRouteIncident.route_stop_id,
        )
        .outerjoin(
            LogisticsDeliveryPoint,
            LogisticsDeliveryPoint.id == LogisticsRouteStop.delivery_point_id,
        )
        .where(
            LogisticsRouteIncident.session_id == session_id,
            LogisticsRouteIncident.status == "OPEN",
        )
        .order_by(LogisticsRouteIncident.created_at.desc())
    ).all()
    return [
        SessionOperationalSummaryIncidentIssueRead(
            id=row.id,
            type=row.incident_type,
            status=row.status,
            route_stop_id=row.route_stop_id,
            stop_label=(
                f"Parada {int(row.stop_order)} · {row.customer_name}"
                if row.stop_order is not None
                else None
            ),
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


def _latest_route_operation_activity(
    db: Session, *, session_id: str
) -> SessionOperationalSummaryLastActivityRead | None:
    row = db.execute(
        select(
            LogisticsRouteOperation.operation_type,
            LogisticsRouteOperation.performed_at,
            LogisticsRouteOperation.created_at,
        )
        .where(
            LogisticsRouteOperation.session_id == session_id,
            LogisticsRouteOperation.status == "CONFIRMED",
        )
        .order_by(
            LogisticsRouteOperation.performed_at.desc().nulls_last(),
            LogisticsRouteOperation.created_at.desc(),
        )
    ).first()
    if row is None:
        return None
    occurred_at = row.performed_at or row.created_at
    return SessionOperationalSummaryLastActivityRead(
        type="OPERATION",
        label=f"Operación {row.operation_type} confirmada",
        at=occurred_at,
    )


def _latest_incident_activity(
    db: Session, *, session_id: str
) -> SessionOperationalSummaryLastActivityRead | None:
    row = db.execute(
        select(
            LogisticsRouteIncident.incident_type,
            LogisticsRouteIncident.status,
            LogisticsRouteIncident.updated_at,
            LogisticsRouteIncident.created_at,
        )
        .where(LogisticsRouteIncident.session_id == session_id)
        .order_by(
            LogisticsRouteIncident.updated_at.desc(),
            LogisticsRouteIncident.created_at.desc(),
        )
    ).first()
    if row is None:
        return None
    prefix = {
        "OPEN": "Incidencia abierta",
        "RESOLVED": "Incidencia resuelta",
        "CORRECTED": "Incidencia corregida",
    }.get(row.status, "Incidencia")
    return SessionOperationalSummaryLastActivityRead(
        type="INCIDENT",
        label=f"{prefix} {row.incident_type}",
        at=row.updated_at or row.created_at,
    )


def _latest_document_activity(
    db: Session, *, session_id: str
) -> SessionOperationalSummaryLastActivityRead | None:
    version = db.scalar(
        select(LogisticsSessionWaybillVersion)
        .where(LogisticsSessionWaybillVersion.session_id == session_id)
        .order_by(LogisticsSessionWaybillVersion.generated_at.desc())
    )
    if version is None:
        return None
    return SessionOperationalSummaryLastActivityRead(
        type="DOCUMENT",
        label=f"Carta porte v{version.version} generada",
        at=version.generated_at,
    )


def _resolve_last_activity(
    *activities: SessionOperationalSummaryLastActivityRead | None,
) -> SessionOperationalSummaryLastActivityRead | None:
    present = [activity for activity in activities if activity is not None]
    if not present:
        return None
    return max(present, key=lambda activity: activity.at)


def _build_waybill_summary(
    db: Session, *, session: LogisticsVehicleSession
) -> SessionOperationalSummaryWaybillRead:
    active = db.scalar(
        select(LogisticsSessionWaybillVersion)
        .where(
            LogisticsSessionWaybillVersion.session_id == session.id,
            LogisticsSessionWaybillVersion.status == "ACTIVE",
        )
        .order_by(LogisticsSessionWaybillVersion.version.desc())
    )
    if active is None:
        return SessionOperationalSummaryWaybillRead(
            has_active_version=False,
            sync_status="MISSING",
            active_version=None,
        )

    try:
        current = build_current_session_waybill(db, session=session)
    except Exception:
        return SessionOperationalSummaryWaybillRead(
            has_active_version=True,
            sync_status="MISSING",
            active_version=active.version,
        )

    return SessionOperationalSummaryWaybillRead(
        has_active_version=True,
        sync_status=(
            "SYNCED" if active.operational_hash == current.operational_hash else "OUTDATED"
        ),
        active_version=active.version,
    )


def build_operational_summary(
    db: Session, *, session: LogisticsVehicleSession
) -> SessionOperationalSummaryRead:
    stop_snapshots = build_route_stop_progress_snapshot(db, session=session)
    stop_counters = SessionOperationalSummaryStopCountersRead(
        total=len(stop_snapshots),
        pending=sum(1 for item in stop_snapshots if item.progress_status == "PENDING"),
        in_progress=sum(1 for item in stop_snapshots if item.progress_status == "IN_PROGRESS"),
        partial=sum(1 for item in stop_snapshots if item.progress_status == "PARTIAL"),
        completed=sum(1 for item in stop_snapshots if item.progress_status == "COMPLETED"),
        failed=sum(1 for item in stop_snapshots if item.progress_status == "FAILED"),
    )
    incidents = _count_incidents(db, session_id=session.id)
    open_incidents = _load_open_incidents(db, session_id=session.id)
    confirmed_operations = int(
        db.scalar(
            select(func.count(LogisticsRouteOperation.id)).where(
                LogisticsRouteOperation.session_id == session.id,
                LogisticsRouteOperation.status == "CONFIRMED",
            )
        )
        or 0
    )
    composition = build_current_composition(db, session=session)
    waybill = _build_waybill_summary(db, session=session)

    route_required = session.status in ROUTE_REQUIRED_STATUSES
    blocking_reasons: list[BlockingReason] = []
    attention_reasons: list[AttentionReason] = []
    if stop_counters.failed > 0:
        blocking_reasons.append("FAILED_STOP")
    if route_required and session.route_id is None:
        blocking_reasons.append("NO_ROUTE_ASSIGNED")
    if (
        session.status in REGENERABLE_STATUSES
        and session.route_id is not None
        and waybill.sync_status == "MISSING"
    ):
        blocking_reasons.append("WAYBILL_MISSING")
    if stop_counters.partial > 0:
        attention_reasons.append("PARTIAL_STOP")
    if incidents.open_total > 0:
        attention_reasons.append("OPEN_INCIDENT")
    if waybill.sync_status == "OUTDATED":
        attention_reasons.append("WAYBILL_OUTDATED")

    if stop_counters.failed > 0:
        health_status = "BLOCKED"
    elif (
        session.status in REGENERABLE_STATUSES
        and session.route_id is not None
        and waybill.sync_status == "MISSING"
    ):
        health_status = "BLOCKED"
    elif stop_counters.partial > 0:
        health_status = "ATTENTION"
    elif incidents.open_total > 0:
        health_status = "ATTENTION"
    elif waybill.sync_status == "OUTDATED":
        health_status = "ATTENTION"
    elif route_required and session.route_id is None:
        health_status = "ATTENTION"
    else:
        health_status = "HEALTHY"

    data_completeness = (
        "PARTIAL"
        if (route_required and session.route_id is None)
        or (
            session.status in REGENERABLE_STATUSES
            and session.route_id is not None
            and waybill.sync_status == "MISSING"
        )
        else "FULL"
    )

    last_activity = _resolve_last_activity(
        _latest_route_operation_activity(db, session_id=session.id),
        _latest_incident_activity(db, session_id=session.id),
        _latest_document_activity(db, session_id=session.id),
    )

    return SessionOperationalSummaryRead(
        session_id=session.id,
        session_status=session.status,
        data_completeness=data_completeness,
        health_status=health_status,
        stop_counters=stop_counters,
        incidents=incidents,
        route_activity=SessionOperationalSummaryRouteActivityRead(
            confirmed_operations=confirmed_operations,
            last_activity=last_activity,
        ),
        composition=SessionOperationalSummaryCompositionRead(
            total_products=len(composition.product_lines),
            total_units=composition.totals.total_packages,
            total_weight_kg=composition.totals.total_weight_kg,
            total_adr_points=composition.totals.total_adr_points,
        ),
        waybill=waybill,
        blocking_reasons=blocking_reasons,
        attention_reasons=attention_reasons,
        problematic_stops=[
            SessionOperationalSummaryStopIssueRead(
                route_stop_id=item.route_stop_id,
                stop_order=item.stop_order,
                label=item.label,
                progress_status=item.progress_status,
                open_incidents=item.open_incidents,
                last_operation_at=item.last_operation_at,
                completion_percent=item.completion_percent,
                outcome_type=item.outcome_type,
                driver_note=item.driver_note,
            )
            for item in stop_snapshots
            if item.progress_status in {"IN_PROGRESS", "PARTIAL", "FAILED"}
        ],
        open_incidents=open_incidents,
    )
