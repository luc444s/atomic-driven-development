# ruff: noqa: E501
from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsMovementType,
    LogisticsScanLog,
    LogisticsStateTransition,
)
from plugins.logistics.backend.schemas import CylinderTransitionRequest, ScanRequest
from plugins.logistics.backend.services.cylinders import get_cylinder_by_serial, transition_cylinder
from plugins.logistics.backend.services.envase import register_ownership_change
from plugins.logistics.backend.services.state_machine import (
    StateTransitionError,
    has_valid_adr,
    has_valid_hydrotest,
)


def list_scan_logs(
    db: Session,
    *,
    tenant_id: str,
    movement_id: str | None = None,
) -> list[LogisticsScanLog]:
    stmt = select(LogisticsScanLog).where(LogisticsScanLog.tenant_id == tenant_id)
    if movement_id is not None:
        stmt = stmt.where(LogisticsScanLog.movement_id == movement_id)
    stmt = stmt.order_by(LogisticsScanLog.scanned_at.desc(), LogisticsScanLog.created_at.desc())
    return list(db.scalars(stmt).all())


def process_scan(
    db: Session,
    *,
    tenant_id: str,
    payload: ScanRequest,
    action_context: LogisticsActionContext,
) -> LogisticsScanLog:
    normalized_service_type = payload.service_type.strip().upper()

    movement: LogisticsMovement | None = None
    if payload.movement_id:
        movement = db.scalar(
            select(LogisticsMovement).where(
                LogisticsMovement.id == payload.movement_id,
                LogisticsMovement.tenant_id == tenant_id,
            )
        )
    cylinder = get_cylinder_by_serial(
        db, tenant_id=tenant_id, serial_or_barcode=payload.barcode_serial
    )
    if movement is None and cylinder is not None:
        last_item = db.scalar(
            select(LogisticsMovementItem)
            .where(
                LogisticsMovementItem.cylinder_id == cylinder.id,
            )
            .order_by(desc(LogisticsMovementItem.created_at))
            .limit(1)
        )
        if last_item is not None:
            movement = db.scalar(
                select(LogisticsMovement).where(
                    LogisticsMovement.id == last_item.movement_id,
                    LogisticsMovement.tenant_id == tenant_id,
                )
            )
    if cylinder is None:
        log = _record_scan(
            db,
            tenant_id=tenant_id,
            movement_id=movement.id if movement else None,
            cylinder_id=None,
            barcode_scanned=payload.barcode_serial,
            service_type=normalized_service_type,
            result="ERROR",
            error_reason="Envase no encontrado para el serial/código proporcionado",
            adr_validated=False,
            hydrotest_validated=False,
            gps_lat=payload.gps_lat,
            gps_lng=payload.gps_lng,
            action_context=action_context,
        )
        raise ValueError(log.error_reason or "Envase no encontrado")

    if movement is None:
        log = _record_scan(
            db,
            tenant_id=tenant_id,
            movement_id=None,
            cylinder_id=cylinder.id,
            barcode_scanned=payload.barcode_serial,
            service_type=normalized_service_type,
            result="OK",
            error_reason=None,
            adr_validated=False,
            hydrotest_validated=False,
            gps_lat=payload.gps_lat,
            gps_lng=payload.gps_lng,
            action_context=action_context,
        )
        db.flush()
        return log

    duplicate = db.scalar(
        select(LogisticsScanLog).where(
            LogisticsScanLog.tenant_id == tenant_id,
            LogisticsScanLog.movement_id == movement.id,
            LogisticsScanLog.cylinder_id == cylinder.id,
            LogisticsScanLog.service_type == normalized_service_type,
            LogisticsScanLog.result == "OK",
        )
    )
    if movement is not None and duplicate is not None:
        raise ValueError("El envase ya fue escaneado para este movimiento y servicio")

    target_state = _resolve_target_state(
        db, movement=movement, service_type=normalized_service_type
    )
    transition = db.scalar(
        select(LogisticsStateTransition).where(
            LogisticsStateTransition.from_state == cylinder.current_state,
            LogisticsStateTransition.to_state == target_state,
        )
    )
    if transition is None:
        log = _record_scan(
            db,
            tenant_id=tenant_id,
            movement_id=movement.id if movement else None,
            cylinder_id=cylinder.id,
            barcode_scanned=payload.barcode_serial,
            service_type=normalized_service_type,
            result="ERROR",
            error_reason=f"Transición no permitida: {cylinder.current_state} → {target_state}",
            adr_validated=False,
            hydrotest_validated=False,
            gps_lat=payload.gps_lat,
            gps_lng=payload.gps_lng,
            action_context=action_context,
        )
        raise ValueError(log.error_reason or "Transición inválida")

    adr_validated = not transition.requires_adr or has_valid_adr(db, cylinder)
    hydrotest_validated = not transition.requires_hydrotest or has_valid_hydrotest(cylinder)
    if not adr_validated or not hydrotest_validated:
        reason = "Transition requires valid ADR and hydrotest data"
        log = _record_scan(
            db,
            tenant_id=tenant_id,
            movement_id=movement.id if movement else None,
            cylinder_id=cylinder.id,
            barcode_scanned=payload.barcode_serial,
            service_type=normalized_service_type,
            result="ERROR",
            error_reason=reason,
            adr_validated=adr_validated,
            hydrotest_validated=hydrotest_validated,
            gps_lat=payload.gps_lat,
            gps_lng=payload.gps_lng,
            action_context=action_context,
        )
        raise ValueError(log.error_reason or reason)

    try:
        transition_cylinder(
            db,
            tenant_id=tenant_id,
            cylinder_id=cylinder.id,
            payload=CylinderTransitionRequest(
                to_state=target_state,
                movement_id=movement.id,
                origin="SCAN_SERVICE",
                reason_code=normalized_service_type,
                notes=f"Scan service {normalized_service_type}",
                metadata_json={"barcode_scanned": payload.barcode_serial},
            ),
            action_context=action_context,
        )
    except StateTransitionError as exc:
        log = _record_scan(
            db,
            tenant_id=tenant_id,
            movement_id=movement.id,
            cylinder_id=cylinder.id,
            barcode_scanned=payload.barcode_serial,
            service_type=normalized_service_type,
            result="ERROR",
            error_reason=str(exc),
            adr_validated=adr_validated,
            hydrotest_validated=hydrotest_validated,
            gps_lat=payload.gps_lat,
            gps_lng=payload.gps_lng,
            action_context=action_context,
        )
        raise ValueError(log.error_reason or str(exc)) from exc

    item = db.scalar(
        select(LogisticsMovementItem).where(
            LogisticsMovementItem.movement_id == movement.id,
            LogisticsMovementItem.cylinder_id == cylinder.id,
        )
    )
    if item is not None:
        item.state_after = target_state
        db.add(item)

    if target_state in {"EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO"}:
        register_ownership_change(
            db,
            cylinder=cylinder,
            movement_id=movement.id,
            customer_id=movement.customer_id,
            customer_name=movement.customer_name,
            notes=movement.notes,
            action_context=action_context,
        )
    elif target_state in {"EN_ALMACEN_VACIO", "VACIO_EN_ALMACEN"}:
        register_ownership_change(
            db,
            cylinder=cylinder,
            movement_id=movement.id,
            customer_id=None,
            customer_name="ALMACEN",
            notes=movement.notes,
            action_context=action_context,
        )

    log = _record_scan(
        db,
        tenant_id=tenant_id,
        movement_id=movement.id,
        cylinder_id=cylinder.id,
        barcode_scanned=payload.barcode_serial,
        service_type=normalized_service_type,
        result="OK",
        error_reason=None,
        adr_validated=adr_validated,
        hydrotest_validated=hydrotest_validated,
        gps_lat=payload.gps_lat,
        gps_lng=payload.gps_lng,
        action_context=action_context,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="scan.execute",
        entity_type="scan",
        entity_id=log.id,
        details={
            "movement_id": movement.id,
            "cylinder_id": cylinder.id,
            "service_type": normalized_service_type,
            "target_state": target_state,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.scanned",
        entity_type="scan",
        entity_id=log.id,
        payload={
            "movement_id": movement.id,
            "cylinder_id": cylinder.id,
            "service_type": normalized_service_type,
            "target_state": target_state,
        },
    )
    return log


def _resolve_target_state(
    db: Session,
    *,
    movement: LogisticsMovement,
    service_type: str,
) -> str:
    normalized = service_type.strip().upper()
    if normalized == "CANJE_RECOJO":
        return "VACIO_EN_ALMACEN"
    if normalized == "DEVOLUCION":
        return "EN_ALMACEN_VACIO"
    if normalized == "RECHAZO":
        return "OBSERVADO"

    movement_type = db.scalar(
        select(LogisticsMovementType).where(LogisticsMovementType.code == movement.movement_type)
    )
    if movement_type is None or not movement_type.target_state:
        raise ValueError("El tipo de movimiento no define un estado destino")
    return movement_type.target_state


def _record_scan(
    db: Session,
    *,
    tenant_id: str,
    movement_id: str | None,
    cylinder_id: str | None,
    barcode_scanned: str,
    service_type: str,
    result: str,
    error_reason: str | None,
    adr_validated: bool,
    hydrotest_validated: bool,
    gps_lat: float | None,
    gps_lng: float | None,
    action_context: LogisticsActionContext,
) -> LogisticsScanLog:
    log = LogisticsScanLog(
        tenant_id=tenant_id,
        movement_id=movement_id,
        cylinder_id=cylinder_id,
        barcode_scanned=barcode_scanned.strip().upper(),
        service_type=service_type.strip().upper(),
        user_id=action_context.actor_user_id,
        gps_lat=gps_lat,
        gps_lng=gps_lng,
        result=result,
        error_reason=error_reason,
        adr_validated=adr_validated,
        hydrotest_validated=hydrotest_validated,
    )
    db.add(log)
    db.flush()
    return log
