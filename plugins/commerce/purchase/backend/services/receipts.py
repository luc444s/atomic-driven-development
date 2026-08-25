from __future__ import annotations

from datetime import date

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from plugins.commerce._shared.stock_connector import DuplicateReceiptError, StockConnector
from plugins.commerce.purchase.backend.models import (
    ComDispatch,
    ComPurchaseItem,
    ComPurchaseOrder,
    ComPurchaseReceipt,
)
from plugins.commerce.purchase.backend.services import orders
from plugins.logistics.backend.models.cylinder import LogisticsCylinder


def receive_order(
    db: Session,
    *,
    order: ComPurchaseOrder,
    warehouse_id: str,
    items_payload: list[dict],
    notes: str | None,
    created_by: str,
    stock_connector: StockConnector,
    tank_id: str | None = None,
    dispatch_id: str | None = None,
) -> ComPurchaseOrder:
    if order.status not in ("ORDERED", "PARTIAL"):
        raise ValueError(f"No se puede recepcionar una orden en estado {order.status}")

    if dispatch_id is not None:
        dispatch = db.scalar(
            select(ComDispatch).where(
                ComDispatch.id == dispatch_id,
                ComDispatch.tenant_id == order.tenant_id,
            )
        )
        if dispatch is None:
            raise ValueError("Despacho no encontrado")
        if dispatch.order_id != order.id:
            raise ValueError("El despacho no pertenece a esta orden")

    item_map: dict[str, ComPurchaseItem] = {item.id: item for item in order.items}
    errors: list[str] = []

    # Get the cryogenic tank if specified
    tank = None
    if tank_id:
        tank = db.scalar(
            select(LogisticsCylinder).where(
                LogisticsCylinder.id == tank_id,
                LogisticsCylinder.tenant_id == order.tenant_id,
                LogisticsCylinder.container_type == "CRYOGENIC_TANK",
            )
        )
        if tank is None:
            errors.append(f"Tanque {tank_id} no encontrado o no es criogenico")

    total_kg_added = 0.0
    for entry in items_payload:
        purchase_item_id = entry["purchase_item_id"]
        qty = entry["quantity"]

        item = item_map.get(purchase_item_id)
        if item is None:
            errors.append(f"Item {purchase_item_id} no pertenece a la orden {order.id}")
            continue

        if float(item.received_qty) + qty > float(item.quantity):
            errors.append(
                f"Cantidad {qty} excede pendiente "
                f"({float(item.quantity) - float(item.received_qty)}) de {item.product_id}"
            )
            continue

        if qty <= 0:
            errors.append(f"Cantidad debe ser > 0 para {item.product_id}")
            continue

        try:
            stock_connector.purchase_in(
                product_id=item.product_id,
                warehouse_id=warehouse_id,
                quantity=qty,
                unit_cost=float(item.unit_cost),
                reference_type="purchase_order",
                reference_id=order.id,
                idempotency_key=f"compras-{order.id}-{item.id}",
            )
        except DuplicateReceiptError:
            errors.append(f"Item {item.product_id} ya fue recepcionado (duplicado)")
            continue

        item.received_qty = float(item.received_qty) + qty
        db.add(item)

        if tank and item.product_id == tank.product_id:
            total_kg_added += qty

    if errors:
        raise ValueError("; ".join(errors))

    if tank and total_kg_added > 0:
        current = float(tank.content_kg or 0)
        db.execute(
            update(LogisticsCylinder)
            .where(LogisticsCylinder.id == tank.id)
            .values(content_kg=current + total_kg_added)
        )

    receipt = ComPurchaseReceipt(
        order_id=order.id,
        warehouse_id=warehouse_id,
        receipt_date=date.today(),
        dispatch_id=dispatch_id,
        notes=notes,
        created_by=created_by,
    )
    db.add(receipt)

    all_received = all(float(item.received_qty) >= float(item.quantity) for item in order.items)
    target = "RECEIVED" if all_received else "PARTIAL"
    orders.transition(
        db,
        order=order,
        target=target,
        user_id=created_by,
        reason="AUTO_RECEIPT",
    )

    return order
