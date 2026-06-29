# ruff: noqa: E501
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.crm.backend.services.customers import require_customer
from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsMovementStatusHistory,
    LogisticsMovementType,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import (
    CylinderTransitionRequest,
    MovementCancelRequest,
    MovementCreateRequest,
    MovementItemCreateRequest,
    MovementUpdateRequest,
)
from plugins.logistics.backend.services.cylinders import get_cylinder, transition_cylinder
from plugins.logistics.backend.services.envase import register_ownership_change


def list_movements(
    db: Session,
    *,
    tenant_id: str,
    movement_type: str | None = None,
    status: str | None = None,
    customer: str | None = None,
) -> list[LogisticsMovement]:
    stmt = select(LogisticsMovement).where(LogisticsMovement.tenant_id == tenant_id)
    if movement_type:
        stmt = stmt.where(LogisticsMovement.movement_type == movement_type)
    if status:
        stmt = stmt.where(LogisticsMovement.status == status)
    if customer:
        stmt = stmt.where(LogisticsMovement.customer_name.ilike(f"%{customer.strip()}%"))
    stmt = stmt.order_by(LogisticsMovement.created_at.desc())
    return list(db.scalars(stmt).all())


def get_movement(db: Session, *, tenant_id: str, movement_id: str) -> LogisticsMovement | None:
    return db.scalar(
        select(LogisticsMovement).where(
            LogisticsMovement.id == movement_id,
            LogisticsMovement.tenant_id == tenant_id,
        )
    )


def get_movement_type(db: Session, *, code: str) -> LogisticsMovementType | None:
    return db.scalar(select(LogisticsMovementType).where(LogisticsMovementType.code == code))


def list_movement_items(db: Session, *, movement_id: str) -> list[LogisticsMovementItem]:
    return list(
        db.scalars(
            select(LogisticsMovementItem)
            .where(LogisticsMovementItem.movement_id == movement_id)
            .order_by(LogisticsMovementItem.created_at.asc())
        ).all()
    )


def list_movement_history(db: Session, *, movement_id: str) -> list[LogisticsMovementStatusHistory]:
    return list(
        db.scalars(
            select(LogisticsMovementStatusHistory)
            .where(LogisticsMovementStatusHistory.movement_id == movement_id)
            .order_by(LogisticsMovementStatusHistory.created_at.desc())
        ).all()
    )


def create_movement(
    db: Session,
    *,
    tenant_id: str,
    created_by: str,
    payload: MovementCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsMovement:
    customer_name = None
    customer_id = payload.customer_id
    if customer_id is not None:
        customer = require_customer(db, tenant_id=tenant_id, customer_id=customer_id)
        customer_name = customer.legal_name
    warehouse_branch_id = None
    if payload.warehouse_id is not None:
        warehouse = db.scalar(
            select(LogisticsWarehouse).where(
                LogisticsWarehouse.id == payload.warehouse_id,
                LogisticsWarehouse.tenant_id == tenant_id,
            )
        )
        warehouse_branch_id = warehouse.branch_id if warehouse is not None else None
    movement = LogisticsMovement(
        tenant_id=tenant_id,
        branch_id=payload.branch_id or warehouse_branch_id,
        movement_type=payload.movement_type,
        document_series=payload.document_series,
        document_number=payload.document_number,
        full_document=(
            f"{payload.document_series}-{payload.document_number}"
            if payload.document_series and payload.document_number
            else None
        ),
        order_id=payload.order_id,
        route_id=payload.route_id,
        customer_id=customer_id,
        customer_name=customer_name,
        warehouse_id=payload.warehouse_id,
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
        total=payload.total,
        tax=payload.tax,
        discount=payload.discount,
        currency=payload.currency,
        exchange_rate=payload.exchange_rate,
        payment_status=payload.payment_status,
        carrier=payload.carrier,
        plate=payload.plate,
        destination_place=payload.destination_place,
        destination_address=payload.destination_address,
        notes=payload.notes,
        created_by=created_by,
    )
    db.add(movement)
    db.flush()
    for raw_item in payload.items:
        item_payload = MovementItemCreateRequest.model_validate(raw_item)
        create_movement_item(db, movement=movement, payload=item_payload)
    audit_logistics_action(
        db,
        context=action_context,
        action="movement.create",
        entity_type="movement",
        entity_id=movement.id,
        details={"type": movement.movement_type, "status": movement.status},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.movement.created",
        entity_type="movement",
        entity_id=movement.id,
        payload={"type": movement.movement_type, "status": movement.status},
    )
    return movement


def create_movement_item(
    db: Session,
    *,
    movement: LogisticsMovement,
    payload: MovementItemCreateRequest,
) -> LogisticsMovementItem:
    cylinder = None
    if payload.cylinder_id is not None:
        cylinder = get_cylinder(db, tenant_id=movement.tenant_id, cylinder_id=payload.cylinder_id)
    item = LogisticsMovementItem(
        movement_id=movement.id,
        cylinder_id=payload.cylinder_id,
        product_id=payload.product_id,
        product_name=payload.product_name,
        quantity_in=payload.quantity_in,
        quantity_out=payload.quantity_out,
        quantity=payload.quantity,
        quantity_planned=payload.quantity_planned,
        unit_price=payload.unit_price,
        total_item=payload.total_item,
        discount=payload.discount,
        item_status=payload.item_status or "R",
        notes=payload.notes,
        state_before=cylinder.current_state if cylinder is not None else None,
    )
    db.add(item)
    db.flush()
    return item


def update_movement(
    db: Session,
    *,
    movement: LogisticsMovement,
    payload: MovementUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsMovement:
    previous_status = movement.status
    for field in [
        "status",
        "payment_status",
        "notes",
        "carrier",
        "plate",
        "destination_place",
        "destination_address",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(movement, field, value)
    db.add(movement)
    db.flush()
    if previous_status != movement.status:
        record_movement_status_change(
            db,
            movement=movement,
            field_name="status",
            from_value=previous_status,
            to_value=movement.status,
            changed_by=action_context.actor_user_id,
        )
    audit_logistics_action(
        db,
        context=action_context,
        action="movement.update",
        entity_type="movement",
        entity_id=movement.id,
        details={"type": movement.movement_type, "status": movement.status},
    )
    return movement


def record_movement_status_change(
    db: Session,
    *,
    movement: LogisticsMovement,
    field_name: str,
    from_value: str | None,
    to_value: str,
    changed_by: str,
    notes: str | None = None,
) -> LogisticsMovementStatusHistory:
    history = LogisticsMovementStatusHistory(
        movement_id=movement.id,
        field_name=field_name,
        from_value=from_value,
        to_value=to_value,
        changed_by=changed_by,
        notes=notes,
    )
    db.add(history)
    db.flush()
    return history


def confirm_movement(
    db: Session,
    *,
    tenant_id: str,
    movement: LogisticsMovement,
    action_context: LogisticsActionContext,
) -> LogisticsMovement:
    previous_status = movement.status
    movement.status = "COMPLETADO"
    db.add(movement)
    movement_type = get_movement_type(db, code=movement.movement_type)
    if movement_type is not None and movement_type.moves_cylinders and movement_type.target_state:
        for item in list_movement_items(db, movement_id=movement.id):
            if item.cylinder_id is None:
                continue
            cylinder = get_cylinder(db, tenant_id=tenant_id, cylinder_id=item.cylinder_id)
            if cylinder is None:
                continue
            if cylinder.current_state != movement_type.target_state:
                transitioned = transition_cylinder(
                    db,
                    tenant_id=tenant_id,
                    cylinder_id=cylinder.id,
                    payload=CylinderTransitionRequest(
                        to_state=movement_type.target_state,
                        movement_id=movement.id,
                        origin="MOVEMENT_CONFIRM",
                        notes=movement.notes,
                    ),
                    action_context=action_context,
                )
                if transitioned is not None:
                    item.state_after = transitioned.current_state
                    db.add(item)
                    if movement_type.target_state in {"EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO"}:
                        register_ownership_change(
                            db,
                            cylinder=transitioned,
                            movement_id=movement.id,
                            customer_id=movement.customer_id,
                            customer_name=movement.customer_name,
                            notes=movement.notes,
                            action_context=action_context,
                        )
                    elif movement_type.target_state in {"EN_ALMACEN_VACIO", "VACIO_EN_ALMACEN"}:
                        register_ownership_change(
                            db,
                            cylinder=transitioned,
                            movement_id=movement.id,
                            customer_id=None,
                            customer_name="ALMACEN",
                            notes=movement.notes,
                            action_context=action_context,
                        )
            elif movement_type.target_state in {"EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO"}:
                register_ownership_change(
                    db,
                    cylinder=cylinder,
                    movement_id=movement.id,
                    customer_id=movement.customer_id,
                    customer_name=movement.customer_name,
                    notes=movement.notes,
                    action_context=action_context,
                )
            elif movement_type.target_state in {"EN_ALMACEN_VACIO", "VACIO_EN_ALMACEN"}:
                register_ownership_change(
                    db,
                    cylinder=cylinder,
                    movement_id=movement.id,
                    customer_id=None,
                    customer_name="ALMACEN",
                    notes=movement.notes,
                    action_context=action_context,
                )
    record_movement_status_change(
        db,
        movement=movement,
        field_name="status",
        from_value=previous_status,
        to_value=movement.status,
        changed_by=action_context.actor_user_id,
    )
    db.flush()
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.movement.completed",
        entity_type="movement",
        entity_id=movement.id,
        payload={"type": movement.movement_type, "status": movement.status},
    )
    return movement


def cancel_movement(
    db: Session,
    *,
    movement: LogisticsMovement,
    payload: MovementCancelRequest,
    action_context: LogisticsActionContext,
) -> LogisticsMovement:
    previous_status = movement.status
    movement.status = "CANCELADO"
    if movement.notes:
        movement.notes = f"{movement.notes}\nMotivo cancelacion: {payload.reason}"
    else:
        movement.notes = f"Motivo cancelacion: {payload.reason}"
    db.add(movement)
    record_movement_status_change(
        db,
        movement=movement,
        field_name="status",
        from_value=previous_status,
        to_value=movement.status,
        changed_by=action_context.actor_user_id,
        notes=payload.reason,
    )
    db.flush()
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.movement.cancelled",
        entity_type="movement",
        entity_id=movement.id,
        payload={
            "type": movement.movement_type,
            "status": movement.status,
            "reason": payload.reason,
        },
    )
    return movement
