from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import LogisticsOrder, LogisticsOrderItem
from plugins.logistics.backend.schemas import (
    OrderCreateRequest,
    OrderItemCreateRequest,
    OrderItemUpdateRequest,
    OrderUpdateRequest,
)


def list_orders(
    db: Session,
    *,
    tenant_id: str,
    customer: str | None = None,
    status: str | None = None,
) -> list[LogisticsOrder]:
    stmt = select(LogisticsOrder).where(LogisticsOrder.tenant_id == tenant_id)
    if customer:
        stmt = stmt.where(LogisticsOrder.customer_name.ilike(f"%{customer.strip()}%"))
    if status:
        stmt = stmt.where(LogisticsOrder.status == status)
    stmt = stmt.order_by(LogisticsOrder.created_at.desc())
    return list(db.scalars(stmt).all())


def get_order(db: Session, *, tenant_id: str, order_id: str) -> LogisticsOrder | None:
    return db.scalar(
        select(LogisticsOrder).where(
            LogisticsOrder.id == order_id,
            LogisticsOrder.tenant_id == tenant_id,
        )
    )


def list_order_items(db: Session, *, order_id: str) -> list[LogisticsOrderItem]:
    return list(
        db.scalars(
            select(LogisticsOrderItem)
            .where(LogisticsOrderItem.order_id == order_id)
            .order_by(LogisticsOrderItem.created_at.asc())
        ).all()
    )


def create_order(
    db: Session,
    *,
    tenant_id: str,
    created_by: str,
    payload: OrderCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsOrder:
    order = LogisticsOrder(
        tenant_id=tenant_id,
        branch_id=payload.branch_id,
        customer_id=payload.customer_id,
        customer_name=payload.customer_name.strip(),
        movement_type=payload.movement_type,
        document_series=payload.document_series,
        document_number=payload.document_number,
        warehouse_id=payload.warehouse_id,
        carrier=payload.carrier,
        commitment_date=payload.commitment_date,
        time_window_start=payload.time_window_start,
        time_window_end=payload.time_window_end,
        status=payload.status or "PENDIENTE",
        notes=payload.notes,
        created_by=created_by,
    )
    db.add(order)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="order.create",
        entity_type="order",
        entity_id=order.id,
        details={"customer_name": order.customer_name, "status": order.status},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.order.created",
        entity_type="order",
        entity_id=order.id,
        payload={"customer_name": order.customer_name, "status": order.status},
    )
    return order


def update_order(
    db: Session,
    *,
    order: LogisticsOrder,
    payload: OrderUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsOrder:
    if payload.customer_name is not None:
        order.customer_name = payload.customer_name.strip()
    if payload.warehouse_id is not None:
        order.warehouse_id = payload.warehouse_id
    if payload.carrier is not None:
        order.carrier = payload.carrier
    if payload.commitment_date is not None:
        order.commitment_date = payload.commitment_date
    if payload.time_window_start is not None:
        order.time_window_start = payload.time_window_start
    if payload.time_window_end is not None:
        order.time_window_end = payload.time_window_end
    if payload.status is not None:
        order.status = payload.status
    if payload.notes is not None:
        order.notes = payload.notes
    db.add(order)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="order.update",
        entity_type="order",
        entity_id=order.id,
        details={"customer_name": order.customer_name, "status": order.status},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.order.updated",
        entity_type="order",
        entity_id=order.id,
        payload={"customer_name": order.customer_name, "status": order.status},
    )
    return order


def create_order_item(
    db: Session,
    *,
    order: LogisticsOrder,
    payload: OrderItemCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsOrderItem:
    item = LogisticsOrderItem(
        order_id=order.id,
        product_id=payload.product_id,
        product_name=payload.product_name.strip(),
        reason=payload.reason,
        condition=payload.condition,
        quantity_requested=payload.quantity_requested,
        quantity_planned=payload.quantity_planned,
        status=payload.status,
        location=payload.location,
        description=payload.description,
    )
    db.add(item)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="order_item.create",
        entity_type="order_item",
        entity_id=item.id,
        details={"order_id": order.id, "product_name": item.product_name},
    )
    return item


def get_order_item(db: Session, *, order_id: str, item_id: str) -> LogisticsOrderItem | None:
    return db.scalar(
        select(LogisticsOrderItem).where(
            LogisticsOrderItem.id == item_id,
            LogisticsOrderItem.order_id == order_id,
        )
    )


def update_order_item(
    db: Session,
    *,
    item: LogisticsOrderItem,
    payload: OrderItemUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsOrderItem:
    if payload.product_name is not None:
        item.product_name = payload.product_name.strip()
    if payload.reason is not None:
        item.reason = payload.reason
    if payload.condition is not None:
        item.condition = payload.condition
    if payload.quantity_requested is not None:
        item.quantity_requested = payload.quantity_requested
    if payload.quantity_planned is not None:
        item.quantity_planned = payload.quantity_planned
    if payload.status is not None:
        item.status = payload.status
    if payload.location is not None:
        item.location = payload.location
    if payload.description is not None:
        item.description = payload.description
    db.add(item)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="order_item.update",
        entity_type="order_item",
        entity_id=item.id,
        details={"order_id": item.order_id, "product_name": item.product_name},
    )
    return item


def delete_order_item(
    db: Session,
    *,
    item: LogisticsOrderItem,
    action_context: LogisticsActionContext,
) -> None:
    audit_logistics_action(
        db,
        context=action_context,
        action="order_item.delete",
        entity_type="order_item",
        entity_id=item.id,
        details={"order_id": item.order_id, "product_name": item.product_name},
    )
    db.delete(item)
