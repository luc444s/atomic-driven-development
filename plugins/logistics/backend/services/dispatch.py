from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import (
    CylinderTransitionRequest,
    DispatchGuideAssignRequest,
    DispatchVehicleReturnRequest,
)
from plugins.logistics.backend.services.cylinders import get_cylinder, transition_cylinder
from plugins.logistics.backend.services.movements import record_movement_status_change
from plugins.logistics.backend.services.stock_bridge import adjust_products_stock


def assign_dispatch_guide(
    db: Session,
    *,
    movement: LogisticsMovement,
    payload: DispatchGuideAssignRequest,
    action_context: LogisticsActionContext,
) -> LogisticsMovement:
    if movement.warehouse_id is None:
        raise ValueError("El movimiento debe tener almacén para asignar guía")
    year_prefix = movement.created_at.year
    numbers = []
    for row in db.scalars(
        select(LogisticsMovement.document_number).where(
            LogisticsMovement.tenant_id == movement.tenant_id,
            LogisticsMovement.warehouse_id == movement.warehouse_id,
            LogisticsMovement.document_series == payload.document_series,
        )
    ).all():
        if row is None:
            continue
        try:
            numbers.append(int(str(row)))
        except ValueError:
            continue
    next_number = max(numbers, default=0) + 1
    movement.document_series = payload.document_series
    movement.document_number = f"{next_number:08d}"
    movement.full_document = f"{payload.document_series}-{movement.document_number}"
    db.add(movement)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=movement.branch_id,
        action="dispatch.guide.assign",
        entity_type="movement",
        entity_id=movement.id,
        details={"document": movement.full_document, "year": year_prefix},
    )
    return movement


def close_dispatch(
    db: Session,
    *,
    movement: LogisticsMovement,
    action_context: LogisticsActionContext,
) -> LogisticsMovement:
    if movement.warehouse_id is None:
        raise ValueError("El movimiento debe definir el almacén")
    if movement.status == "CANCELADO":
        raise ValueError("Un movimiento cancelado no puede despacharse")
    if movement.dispatched_at is not None:
        return movement
    items = list(
        db.scalars(
            select(LogisticsMovementItem)
            .where(LogisticsMovementItem.movement_id == movement.id)
            .order_by(LogisticsMovementItem.created_at.asc())
        ).all()
    )
    deltas: dict[tuple[str | None, str | None], float] = {}
    for item in items:
        key = (item.product_id, item.product_name)
        deltas[key] = deltas.get(key, 0) - float(item.quantity_out or 0)
    adjust_products_stock(
        db,
        tenant_id=movement.tenant_id,
        warehouse_id=movement.warehouse_id,
        deltas=[
            (product_id, quantity, product_name)
            for (product_id, product_name), quantity in deltas.items()
        ],
        reason=f"Dispatch movement {movement.id}",
        idempotency_prefix=f"{movement.id}:dispatch",
        action_context=action_context,
    )
    previous_status = movement.status
    movement.status = "DESPACHADO"
    movement.dispatched_at = datetime.now(UTC)
    db.add(movement)
    record_movement_status_change(
        db,
        movement=movement,
        field_name="status",
        from_value=previous_status,
        to_value=movement.status,
        changed_by=action_context.actor_user_id,
    )
    db.flush()
    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == movement.warehouse_id,
            LogisticsWarehouse.tenant_id == movement.tenant_id,
        )
    )
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=warehouse.branch_id if warehouse is not None else movement.branch_id,
        action="dispatch.close",
        entity_type="movement",
        entity_id=movement.id,
        details={"warehouse_id": movement.warehouse_id, "document": movement.full_document},
    )
    emit_logistics_event(
        db,
        context=action_context,
        branch_id=warehouse.branch_id if warehouse is not None else movement.branch_id,
        event_name="logistics.dispatch.completed",
        entity_type="movement",
        entity_id=movement.id,
        payload={"warehouse_id": movement.warehouse_id, "document": movement.full_document},
    )
    return movement


def vehicle_return(
    db: Session,
    *,
    movement: LogisticsMovement,
    payload: DispatchVehicleReturnRequest,
    action_context: LogisticsActionContext,
) -> LogisticsMovement:
    items = list(
        db.scalars(
            select(LogisticsMovementItem).where(LogisticsMovementItem.movement_id == movement.id)
        ).all()
    )
    target_cylinders = set(payload.cylinder_ids)
    for item in items:
        if item.cylinder_id is None:
            continue
        if target_cylinders and item.cylinder_id not in target_cylinders:
            continue
        cylinder = get_cylinder(db, tenant_id=movement.tenant_id, cylinder_id=item.cylinder_id)
        if cylinder is None:
            continue
        transitioned = transition_cylinder(
            db,
            tenant_id=movement.tenant_id,
            cylinder_id=item.cylinder_id,
            payload=CylinderTransitionRequest(
                to_state="DESCARGADO_POR_RECEPCIONAR",
                movement_id=movement.id,
                origin="VEHICLE_RETURN",
                notes=payload.notes,
            ),
            action_context=action_context,
        )
        if transitioned is not None:
            item.state_after = transitioned.current_state
            db.add(item)
    previous_status = movement.status
    movement.status = "DESCARGADO_POR_RECEPCIONAR"
    if payload.notes:
        movement.notes = f"{movement.notes or ''}\nRetorno vehiculo: {payload.notes}".strip()
    db.add(movement)
    record_movement_status_change(
        db,
        movement=movement,
        field_name="status",
        from_value=previous_status,
        to_value=movement.status,
        changed_by=action_context.actor_user_id,
        notes=payload.notes,
    )
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=movement.branch_id,
        action="dispatch.vehicle_return",
        entity_type="movement",
        entity_id=movement.id,
        details={"movement_id": movement.id, "selected_cylinders": len(target_cylinders)},
    )
    emit_logistics_event(
        db,
        context=action_context,
        branch_id=movement.branch_id,
        event_name="logistics.dispatch.returned",
        entity_type="movement",
        entity_id=movement.id,
        payload={"movement_id": movement.id},
    )
    return movement
