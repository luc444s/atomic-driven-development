# ruff: noqa: E501
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderStateLog,
)
from plugins.logistics.backend.schemas import (
    CylinderCreateRequest,
    CylinderSummaryItem,
    CylinderTransitionRequest,
    CylinderUpdateRequest,
)
from plugins.logistics.backend.services.state_machine import (
    ensure_transition_allowed,
    list_allowed_transitions,
)


def list_cylinders(
    db: Session,
    *,
    tenant_id: str,
    search: str | None = None,
    state: str | None = None,
    active: bool | None = None,
) -> list[LogisticsCylinder]:
    stmt = select(LogisticsCylinder).where(LogisticsCylinder.tenant_id == tenant_id)
    if search:
        normalized_search = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                LogisticsCylinder.serial.ilike(normalized_search),
                LogisticsCylinder.description.ilike(normalized_search),
                LogisticsCylinder.barcode1.ilike(normalized_search),
                LogisticsCylinder.barcode2.ilike(normalized_search),
                LogisticsCylinder.location.ilike(normalized_search),
            )
        )
    if state:
        stmt = stmt.where(LogisticsCylinder.current_state == state)
    if active is not None:
        stmt = stmt.where(LogisticsCylinder.is_active == active)
    stmt = stmt.order_by(LogisticsCylinder.created_at.desc(), LogisticsCylinder.serial.asc())
    return list(db.scalars(stmt).all())


def get_cylinder(db: Session, *, tenant_id: str, cylinder_id: str) -> LogisticsCylinder | None:
    return db.scalar(
        select(LogisticsCylinder).where(
            LogisticsCylinder.id == cylinder_id,
            LogisticsCylinder.tenant_id == tenant_id,
        )
    )


def get_cylinder_by_serial(
    db: Session,
    *,
    tenant_id: str,
    serial_or_barcode: str,
) -> LogisticsCylinder | None:
    normalized = serial_or_barcode.strip().upper()
    return db.scalar(
        select(LogisticsCylinder).where(
            LogisticsCylinder.tenant_id == tenant_id,
            or_(
                LogisticsCylinder.serial == normalized,
                LogisticsCylinder.barcode1 == normalized,
                LogisticsCylinder.barcode2 == normalized,
            ),
        )
    )


def list_cylinder_trace(
    db: Session,
    *,
    tenant_id: str,
    cylinder_id: str,
) -> list[LogisticsCylinderStateLog]:
    return list(
        db.scalars(
            select(LogisticsCylinderStateLog)
            .where(
                LogisticsCylinderStateLog.tenant_id == tenant_id,
                LogisticsCylinderStateLog.cylinder_id == cylinder_id,
            )
            .order_by(
                LogisticsCylinderStateLog.created_at.desc(), LogisticsCylinderStateLog.id.desc()
            )
        ).all()
    )


def summarize_cylinders(db: Session, *, tenant_id: str) -> list[CylinderSummaryItem]:
    rows = db.execute(
        select(LogisticsCylinder.current_state, func.count(LogisticsCylinder.id))
        .where(LogisticsCylinder.tenant_id == tenant_id)
        .group_by(LogisticsCylinder.current_state)
        .order_by(LogisticsCylinder.current_state)
    ).all()
    return [CylinderSummaryItem(state=row[0], count=row[1]) for row in rows]


def create_cylinder(
    db: Session,
    *,
    tenant_id: str,
    payload: CylinderCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinder:
    cylinder = LogisticsCylinder(
        tenant_id=tenant_id,
        serial=payload.serial.strip().upper(),
        is_active=True,
    )
    _apply_cylinder_payload(cylinder, payload)
    db.add(cylinder)
    db.flush()

    db.add(
        LogisticsCylinderStateLog(
            tenant_id=tenant_id,
            cylinder_id=cylinder.id,
            from_state=None,
            to_state=cylinder.current_state,
            changed_by=action_context.actor_user_id,
            origin="PLUGIN_CREATE",
            notes="Initial cylinder registration",
            metadata_json={},
        )
    )

    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.create",
        entity_type="cylinder",
        entity_id=cylinder.id,
        details={"serial": cylinder.serial, "state": cylinder.current_state},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.created",
        entity_type="cylinder",
        entity_id=cylinder.id,
        payload={"serial": cylinder.serial, "current_state": cylinder.current_state},
    )
    return cylinder


def update_cylinder(
    db: Session,
    *,
    cylinder: LogisticsCylinder,
    payload: CylinderUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinder:
    _apply_cylinder_payload(cylinder, payload, partial=True)
    db.add(cylinder)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.update",
        entity_type="cylinder",
        entity_id=cylinder.id,
        details={
            "serial": cylinder.serial,
            "barcode1": cylinder.barcode1,
            "barcode2": cylinder.barcode2,
            "state": cylinder.current_state,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.updated",
        entity_type="cylinder",
        entity_id=cylinder.id,
        payload={
            "serial": cylinder.serial,
            "barcode1": cylinder.barcode1,
            "barcode2": cylinder.barcode2,
        },
    )
    return cylinder


def get_allowed_transitions(
    db: Session,
    *,
    tenant_id: str,
    cylinder_id: str,
):
    cylinder = get_cylinder(db, tenant_id=tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        return None
    return list_allowed_transitions(db, from_state=cylinder.current_state)


def transition_cylinder(
    db: Session,
    *,
    tenant_id: str,
    cylinder_id: str,
    payload: CylinderTransitionRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinder | None:
    cylinder = get_cylinder(db, tenant_id=tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        return None

    transition = ensure_transition_allowed(db, cylinder=cylinder, to_state=payload.to_state)
    previous_state = cylinder.current_state
    cylinder.current_state = transition.to_state
    db.add(cylinder)
    db.flush()

    db.add(
        LogisticsCylinderStateLog(
            tenant_id=tenant_id,
            cylinder_id=cylinder.id,
            from_state=previous_state,
            to_state=transition.to_state,
            changed_by=action_context.actor_user_id,
            movement_id=payload.movement_id,
            origin=payload.origin,
            reason_code=payload.reason_code,
            notes=payload.notes,
            metadata_json=dict(payload.metadata_json),
        )
    )

    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.transition",
        entity_type="cylinder",
        entity_id=cylinder.id,
        details={
            "serial": cylinder.serial,
            "from_state": previous_state,
            "to_state": transition.to_state,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.state_changed",
        entity_type="cylinder",
        entity_id=cylinder.id,
        payload={
            "serial": cylinder.serial,
            "from_state": previous_state,
            "to_state": transition.to_state,
            "origin": payload.origin,
            "reason_code": payload.reason_code,
        },
    )
    return cylinder


def _apply_cylinder_payload(
    cylinder: LogisticsCylinder,
    payload: CylinderCreateRequest | CylinderUpdateRequest,
    *,
    partial: bool = False,
) -> None:
    field_set = payload.model_fields_set

    def should_apply(field_name: str) -> bool:
        return not partial or field_name in field_set

    serial = getattr(payload, "serial", None)
    if serial and should_apply("serial"):
        cylinder.serial = serial.strip().upper()

    text_fields = {
        "description": payload.description.strip() if payload.description else None,
        "barcode1": payload.barcode1.strip().upper() if payload.barcode1 else None,
        "barcode2": payload.barcode2.strip().upper() if payload.barcode2 else None,
        "condition": payload.condition.strip().upper() if payload.condition else None,
        "country_code": payload.country_code.strip().upper() if payload.country_code else None,
        "box_number": payload.box_number.strip().upper() if payload.box_number else None,
        "manufacturer_code": payload.manufacturer_code.strip().upper()
        if payload.manufacturer_code
        else None,
        "adr_category": payload.adr_category.strip().upper() if payload.adr_category else None,
        "adr_un_number": payload.adr_un_number.strip().upper() if payload.adr_un_number else None,
        "adr_label": payload.adr_label.strip().upper() if payload.adr_label else None,
        "adr_package_type": payload.adr_package_type.strip().upper()
        if payload.adr_package_type
        else None,
        "adr_merchandise": payload.adr_merchandise.strip() if payload.adr_merchandise else None,
        "adr_tunnel": payload.adr_tunnel.strip().upper() if payload.adr_tunnel else None,
        "adr_subline": payload.adr_subline.strip().upper() if payload.adr_subline else None,
        "adr_unit_measure": payload.adr_unit_measure.strip().upper()
        if payload.adr_unit_measure
        else None,
        "location": payload.location.strip() if payload.location else None,
    }
    for field_name, value in text_fields.items():
        if should_apply(field_name):
            setattr(cylinder, field_name, value)

    for field_name in [
        "branch_id",
        "gas_group_id",
        "content_kg",
        "volume_m3",
        "brand_id",
        "cost",
        "price",
        "manufacturer_date",
        "manufacture_year",
        "weight_origin",
        "weight_current",
        "last_hydrotest_date",
        "next_hydrotest_date",
        "adr_weight_kg",
        "adr_factor",
        "adr_points",
    ]:
        if should_apply(field_name):
            setattr(cylinder, field_name, getattr(payload, field_name))

    if should_apply("is_service") and payload.is_service is not None:
        cylinder.is_service = payload.is_service
    is_active = getattr(payload, "is_active", None)
    if should_apply("is_active") and is_active is not None:
        cylinder.is_active = is_active
