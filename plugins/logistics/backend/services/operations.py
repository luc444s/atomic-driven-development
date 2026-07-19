from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.integrations.stock import transfer
from plugins.logistics.backend.models import (
    LogisticsLoadPlanItem,
    LogisticsOperation,
    LogisticsOperationItem,
    LogisticsVehicleSession,
)
from plugins.productos.backend.models import Product


def _require_product(db: Session, *, product_id: str) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise LookupError("Producto no encontrado")
    return product


def _create_operation(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    movement_type: str,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsOperation:
    operation = LogisticsOperation(
        tenant_id=session.tenant_id,
        session_id=session.id,
        movement_type=movement_type,
        status="PENDING_STOCK",
        idempotency_key=f"{session.id}:{movement_type}:{datetime.now(UTC).timestamp()}",
        notes=notes,
    )
    db.add(operation)
    db.flush()
    operation.idempotency_key = f"{session.id}:{operation.id}"
    operation.performed_by = action_context.actor_user_id
    db.add(operation)
    db.flush()
    return operation


def confirm_transfer_out(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    load_plan_items: list[LogisticsLoadPlanItem],
    notes: str | None,
    action_context: LogisticsActionContext,
) -> float:
    operation = _create_operation(
        db,
        session=session,
        movement_type="TRANSFER_OUT",
        notes=notes,
        action_context=action_context,
    )
    total_weight = 0.0
    try:
        for item in load_plan_items:
            product = _require_product(db, product_id=item.product_id)
            unit_weight = float(product.weight_kg or 0)
            weight_kg = (
                float(item.planned_weight_kg)
                if item.planned_weight_kg is not None
                else unit_weight * float(item.planned_quantity)
            )
            result = transfer(
                db,
                tenant_id=session.tenant_id,
                from_warehouse_id=item.source_warehouse_id,
                to_warehouse_id=session.mobile_warehouse_id,
                product_id=item.product_id,
                quantity=float(item.planned_quantity),
                notes=notes,
                idempotency_key=f"{session.id}:{operation.id}:{item.id}",
                action_context=action_context,
            )
            operation_item = LogisticsOperationItem(
                operation_id=operation.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=float(item.planned_quantity),
                weight_kg=weight_kg,
                notes=item.notes,
            )
            db.add(operation_item)
            total_weight += weight_kg
            operation.external_movement_id = result.reference_id
        operation.status = "CONFIRMED"
        operation.performed_at = datetime.now(UTC)
        db.add(operation)
        audit_logistics_action(
            db,
            context=action_context,
            action="vehicle_session.transfer_out.confirmed",
            entity_type="vehicle_session",
            entity_id=session.id,
            details={"operation_id": operation.id, "items": len(load_plan_items)},
        )
        return total_weight
    except Exception:
        operation.status = "FAILED"
        db.add(operation)
        raise


def confirm_transfer_in(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    destination_warehouse_id: str,
    balances,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> float:
    operation = _create_operation(
        db,
        session=session,
        movement_type="TRANSFER_IN",
        notes=notes,
        action_context=action_context,
    )
    total_weight = 0.0
    try:
        for index, balance in enumerate(balances):
            quantity = float(balance.quantity)
            if quantity <= 0:
                continue
            product = _require_product(db, product_id=balance.product_id)
            unit_weight = float(product.weight_kg or 0)
            weight_kg = unit_weight * quantity
            result = transfer(
                db,
                tenant_id=session.tenant_id,
                from_warehouse_id=session.mobile_warehouse_id,
                to_warehouse_id=destination_warehouse_id,
                product_id=balance.product_id,
                quantity=quantity,
                notes=notes,
                idempotency_key=f"{session.id}:{operation.id}:{index}",
                action_context=action_context,
            )
            operation_item = LogisticsOperationItem(
                operation_id=operation.id,
                product_id=balance.product_id,
                product_name=balance.product_name,
                quantity=quantity,
                weight_kg=weight_kg,
                notes=notes,
            )
            db.add(operation_item)
            total_weight += weight_kg
            operation.external_movement_id = result.reference_id
        operation.status = "CONFIRMED"
        operation.performed_at = datetime.now(UTC)
        db.add(operation)
        audit_logistics_action(
            db,
            context=action_context,
            action="vehicle_session.transfer_in.confirmed",
            entity_type="vehicle_session",
            entity_id=session.id,
            details={"operation_id": operation.id},
        )
        return total_weight
    except Exception:
        operation.status = "FAILED"
        db.add(operation)
        raise


def list_session_operations(db: Session, *, session_id: str) -> list[LogisticsOperation]:
    return list(
        db.scalars(
            select(LogisticsOperation)
            .where(LogisticsOperation.session_id == session_id)
            .order_by(LogisticsOperation.created_at.asc())
        ).all()
    )


def list_operation_items(db: Session, *, operation_id: str) -> list[LogisticsOperationItem]:
    return list(
        db.scalars(
            select(LogisticsOperationItem)
            .where(LogisticsOperationItem.operation_id == operation_id)
            .order_by(LogisticsOperationItem.created_at.asc())
        ).all()
    )
