# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from systutor.kernel.audit.models import AuditLog

from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderLabelHistory,
    LogisticsCylinderOwnership,
    LogisticsCylinderRetimbrado,
    LogisticsCylinderService,
    LogisticsCylinderStateLog,
    LogisticsCylinderWarranty,
    LogisticsHydrostaticTest,
    LogisticsScanLog,
)
from plugins.logistics.backend.schemas import (
    CylinderTraceabilityRead,
    TraceabilityEventRead,
    TraceabilityPagination,
    TraceabilitySummary,
)


def _fmt_actor(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) == 36 and value.count("-") == 4:
        return None
    return value


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def get_cylinder_traceability(
    db: Session,
    *,
    tenant_id: str,
    cylinder_id: str,
    page: int = 1,
    per_page: int = 20,
) -> CylinderTraceabilityRead:
    cylinder = db.scalar(
        select(LogisticsCylinder).where(
            LogisticsCylinder.id == cylinder_id,
            LogisticsCylinder.tenant_id == tenant_id,
        )
    )
    if cylinder is None:
        raise LookupError("Cylinder not found")

    events: list[TraceabilityEventRead] = []
    _collect_created_event(cylinder, events)
    _collect_state_logs(db, cylinder_id, events)
    _collect_scans(db, cylinder_id, events)
    _collect_hydrotests(db, cylinder_id, events)
    _collect_retimbrados(db, cylinder_id, events)
    _collect_services(db, cylinder_id, events)
    _collect_warranties(db, cylinder_id, events)
    _collect_ownerships(db, cylinder_id, events)
    _collect_label_prints(db, cylinder_id, events)
    _collect_medical_flag_changes(db, tenant_id, cylinder_id, events)

    events.sort(key=lambda e: _as_utc(e.timestamp), reverse=True)

    total = len(events)
    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page
    page_events = events[offset : offset + per_page]

    summary = _build_summary(db, cylinder, events)

    return CylinderTraceabilityRead(
        cylinder_id=cylinder.id,
        serial=cylinder.serial,
        events=page_events,
        pagination=TraceabilityPagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
        summary=summary,
    )


def _collect_created_event(
    cylinder: LogisticsCylinder, events: list[TraceabilityEventRead]
) -> None:
    events.append(
        TraceabilityEventRead(
            timestamp=_as_utc(cylinder.created_at),
            event_type="created",
            description="Cilindro creado",
            actor=None,
            metadata={
                "serial": cylinder.serial,
                "origin": "PLUGIN_CREATE",
                "notes": "Initial cylinder registration",
            },
        )
    )


def _collect_state_logs(db: Session, cylinder_id: str, events: list[TraceabilityEventRead]) -> None:
    for row in db.scalars(
        select(LogisticsCylinderStateLog)
        .where(LogisticsCylinderStateLog.cylinder_id == cylinder_id)
        .order_by(LogisticsCylinderStateLog.created_at)
    ).all():
        events.append(
            TraceabilityEventRead(
                timestamp=_as_utc(row.created_at),
                event_type="state_change",
                description=f"{row.from_state} → {row.to_state}",
                actor=_fmt_actor(row.changed_by),
                metadata={
                    "from_state": row.from_state,
                    "to_state": row.to_state,
                    "origin": row.origin,
                    "notes": row.notes,
                },
            )
        )


def _collect_scans(db: Session, cylinder_id: str, events: list[TraceabilityEventRead]) -> None:
    for row in db.scalars(
        select(LogisticsScanLog)
        .where(LogisticsScanLog.cylinder_id == cylinder_id)
        .order_by(LogisticsScanLog.created_at)
    ).all():
        events.append(
            TraceabilityEventRead(
                timestamp=_as_utc(row.created_at),
                event_type="scan",
                description=f"Escaneado: {row.barcode_scanned}",
                actor=None,
                metadata={
                    "action": row.service_type,
                    "gps_lat": row.gps_lat,
                    "gps_lng": row.gps_lng,
                    "result": row.result,
                },
            )
        )


def _collect_hydrotests(db: Session, cylinder_id: str, events: list[TraceabilityEventRead]) -> None:
    for row in db.scalars(
        select(LogisticsHydrostaticTest)
        .where(LogisticsHydrostaticTest.cylinder_id == cylinder_id)
        .order_by(LogisticsHydrostaticTest.test_date)
    ).all():
        events.append(
            TraceabilityEventRead(
                timestamp=_as_utc(datetime.combine(row.test_date, datetime.min.time())),
                event_type="hydrotest",
                description=f"Prueba hidrostática: {row.status}",
                actor=_fmt_actor(row.modified_by),
                metadata={
                    "status": row.status,
                    "previous_test": row.previous_test_date.isoformat()
                    if row.previous_test_date
                    else None,
                },
            )
        )


def _collect_retimbrados(
    db: Session, cylinder_id: str, events: list[TraceabilityEventRead]
) -> None:
    for row in db.scalars(
        select(LogisticsCylinderRetimbrado)
        .where(LogisticsCylinderRetimbrado.cylinder_id == cylinder_id)
        .order_by(LogisticsCylinderRetimbrado.created_at)
    ).all():
        events.append(
            TraceabilityEventRead(
                timestamp=_as_utc(row.created_at),
                event_type="retimbrado",
                description=f"Retimbrado: {row.approval_number or 'N/A'}",
                actor=_fmt_actor(row.created_by),
                metadata={
                    "approval_number": row.approval_number,
                    "test_pressure": row.test_pressure,
                    "un_number": row.un_number,
                },
            )
        )


def _collect_services(db: Session, cylinder_id: str, events: list[TraceabilityEventRead]) -> None:
    for row in db.scalars(
        select(LogisticsCylinderService)
        .where(LogisticsCylinderService.cylinder_id == cylinder_id)
        .order_by(LogisticsCylinderService.created_at)
    ).all():
        events.append(
            TraceabilityEventRead(
                timestamp=_as_utc(row.created_at),
                event_type="service",
                description=f"Servicio: {row.service_type_id}",
                actor=None,
                metadata={
                    "service_type": row.service_type_id,
                    "status": row.status,
                },
            )
        )


def _collect_warranties(db: Session, cylinder_id: str, events: list[TraceabilityEventRead]) -> None:
    for row in db.scalars(
        select(LogisticsCylinderWarranty)
        .where(LogisticsCylinderWarranty.cylinder_id == cylinder_id)
        .order_by(LogisticsCylinderWarranty.created_at)
    ).all():
        events.append(
            TraceabilityEventRead(
                timestamp=_as_utc(row.created_at),
                event_type="warranty",
                description=f"Garantía: {row.warranty_type}",
                actor=None,
                metadata={
                    "warranty_type": row.warranty_type,
                    "customer_name": row.customer_name,
                    "status": row.status,
                },
            )
        )


def _collect_ownerships(db: Session, cylinder_id: str, events: list[TraceabilityEventRead]) -> None:
    for row in db.scalars(
        select(LogisticsCylinderOwnership)
        .where(LogisticsCylinderOwnership.cylinder_id == cylinder_id)
        .order_by(LogisticsCylinderOwnership.change_date)
    ).all():
        events.append(
            TraceabilityEventRead(
                timestamp=_as_utc(row.change_date),
                event_type="ownership",
                description=f"Cambio de custodia: {row.customer_name or 'N/A'}",
                actor=None,
                metadata={
                    "condition": row.condition,
                    "customer_name": row.customer_name,
                },
            )
        )


def _collect_label_prints(
    db: Session, cylinder_id: str, events: list[TraceabilityEventRead]
) -> None:
    for row in db.scalars(
        select(LogisticsCylinderLabelHistory)
        .where(LogisticsCylinderLabelHistory.cylinder_id == cylinder_id)
        .order_by(LogisticsCylinderLabelHistory.printed_at)
    ).all():
        events.append(
            TraceabilityEventRead(
                timestamp=_as_utc(row.printed_at),
                event_type="label_print",
                description=f"Etiqueta impresa ({row.copies} copias)",
                actor=_fmt_actor(row.printed_by),
                metadata={
                    "origin": row.origin,
                    "reason": row.reason,
                    "copies": row.copies,
                },
            )
        )


def _collect_medical_flag_changes(
    db: Session,
    tenant_id: str,
    cylinder_id: str,
    events: list[TraceabilityEventRead],
) -> None:
    audit_rows = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.module == "logistics",
            AuditLog.action == "cylinder.update",
            AuditLog.entity_type == "cylinder",
            AuditLog.entity_id == cylinder_id,
        )
        .order_by(AuditLog.occurred_at)
    ).all()
    for row in audit_rows:
        old_value = row.details.get("old_is_medical")
        new_value = row.details.get("new_is_medical")
        if not isinstance(old_value, bool) or not isinstance(new_value, bool):
            continue
        if old_value == new_value:
            continue
        events.append(
            TraceabilityEventRead(
                timestamp=_as_utc(row.occurred_at),
                event_type="medical_flag_changed",
                description=f"Flag medicinal: {str(old_value).lower()} -> {str(new_value).lower()}",
                actor=_fmt_actor(row.actor_user_id),
                metadata={
                    "old_value": old_value,
                    "new_value": new_value,
                    "origin": row.details.get("trace_origin") or "ACTUALIZACION_FICHA",
                    "notes": row.details.get("new_medical_notes"),
                },
            )
        )


def _build_summary(
    db: Session,
    cylinder: LogisticsCylinder,
    events: list[TraceabilityEventRead],
) -> TraceabilitySummary:
    gps_lat: float | None = None
    gps_lng: float | None = None
    location_name: str | None = cylinder.location

    last_scan = db.scalar(
        select(LogisticsScanLog)
        .where(
            LogisticsScanLog.cylinder_id == cylinder.id,
            LogisticsScanLog.gps_lat.isnot(None),
            LogisticsScanLog.gps_lng.isnot(None),
        )
        .order_by(desc(LogisticsScanLog.created_at))
        .limit(1)
    )
    if last_scan is not None and last_scan.gps_lat is not None and last_scan.gps_lng is not None:
        gps_lat = float(last_scan.gps_lat)
        gps_lng = float(last_scan.gps_lng)
        location_name = f"GPS: {gps_lat:.5f}, {gps_lng:.5f}"

    event_timestamps = [_as_utc(event.timestamp) for event in events]

    return TraceabilitySummary(
        total_events=len(events),
        first_event=min(event_timestamps) if event_timestamps else None,
        last_event=max(event_timestamps) if event_timestamps else None,
        current_state=cylinder.current_state,
        current_location=location_name,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
    )
