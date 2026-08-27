from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from plugins.commerce._shared.stock_connector import DuplicateReceiptError, StockConnector
from plugins.commerce.purchase.backend.models import (
    ComDispatch,
    ComPurchaseItem,
    ComPurchaseOrder,
    ComPurchaseReceipt,
    ComReceiptCostLine,
)
from plugins.commerce.purchase.backend.services import orders
from plugins.logistics.backend.models.cylinder import LogisticsCylinder


def _derive_difference_type(
    *, qty_received: int, qty_ordered: float, qty_rejected: int
) -> str | None:
    if qty_rejected > 0:
        return "DANO"
    if qty_received < qty_ordered:
        return "FALTANTE"
    if qty_received > qty_ordered:
        return "SOBRANTE"
    return None


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
    cost_lines: list[dict] | None = None,
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
    total_accepted = 0
    total_rejected = 0
    for entry in items_payload:
        purchase_item_id = entry["purchase_item_id"]
        qty = float(entry["quantity"])

        item = item_map.get(purchase_item_id)
        if item is None:
            errors.append(f"Item {purchase_item_id} no pertenece a la orden {order.id}")
            continue

        qty_accepted = entry.get("qty_accepted")
        qty_rejected = entry.get("qty_rejected")
        if qty_accepted is None:
            qty_accepted = int(qty)
        if qty_rejected is None:
            qty_rejected = 0
        if int(qty_accepted) + int(qty_rejected) != int(qty):
            errors.append(
                f"Linea {purchase_item_id}: aceptadas+rechazadas ({qty_accepted}+{qty_rejected}) "
                f"debe igualar recibidas ({int(qty)})"
            )
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

        total_accepted += int(qty_accepted)
        total_rejected += int(qty_rejected)

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
        qty_accepted=total_accepted,
        qty_rejected=total_rejected,
        difference_type=_derive_difference_type(
            qty_received=total_accepted + total_rejected,
            qty_ordered=sum(float(i.quantity) for i in order.items),
            qty_rejected=total_rejected,
        ),
    )
    db.add(receipt)
    db.flush()

    if cost_lines:
        _persist_cost_lines(db, receipt=receipt, tenant_id=order.tenant_id, cost_lines=cost_lines)

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


def _persist_cost_lines(
    db: Session, *, receipt: ComPurchaseReceipt, tenant_id: str, cost_lines: list[dict]
) -> None:
    for line in cost_lines:
        db.add(
            ComReceiptCostLine(
                tenant_id=tenant_id,
                receipt_id=receipt.id,
                cost_type=line["cost_type"],
                amount=float(line["amount"]),
                currency=line.get("currency", "PEN"),
                notes=line.get("notes"),
            )
        )
    db.flush()


def recompute_receipt_real_cost(receipt: ComPurchaseReceipt) -> dict:
    """COMPRAS-010: devuelve extra_total, real_total, unit_cost_real del receipt."""
    extra_total = sum(float(c.amount) for c in receipt.cost_lines)
    item_cost_total = _receipt_item_cost_total_from_order(receipt)
    real_total = item_cost_total + extra_total
    accepted = receipt.qty_accepted or 0
    unit_cost_real = (real_total / accepted) if accepted > 0 else None
    return {
        "extra_total": extra_total,
        "real_total": real_total,
        "unit_cost_real": unit_cost_real,
    }


def _receipt_item_cost_total_from_order(receipt: ComPurchaseReceipt) -> float:
    order = receipt.order
    total_ordered = sum(float(i.quantity) for i in order.items) or 1.0
    accepted = receipt.qty_accepted or int(sum(float(i.received_qty) for i in order.items))
    ratio = min(accepted / total_ordered, 1.0) if total_ordered else 0.0
    return sum(float(i.unit_cost) * float(i.quantity) * ratio for i in order.items)


def commercial_close_receipt(
    db: Session,
    *,
    receipt: ComPurchaseReceipt,
    lines: list[dict] | None,
    cost_lines: list[dict] | None,
    incidence_notes: str | None,
    closed_by: str,
) -> ComPurchaseReceipt:
    """COMPRAS-009: cierre comercial idempotente de una recepción ya creada."""
    if lines:
        item_map: dict[str, ComPurchaseItem] = {i.id: i for i in receipt.order.items}
        total_accepted = 0
        total_rejected = 0
        for line in lines:
            item = item_map.get(line["purchase_item_id"])
            if item is None:
                raise ValueError(f"Item {line['purchase_item_id']} no pertenece a la orden")
            qa = int(line["qty_accepted"])
            qr = int(line.get("qty_rejected", 0))
            total_accepted += qa
            total_rejected += qr
        receipt.qty_accepted = total_accepted or None
        receipt.qty_rejected = total_rejected or None
        receipt.difference_type = _derive_difference_type(
            qty_received=total_accepted + total_rejected,
            qty_ordered=sum(float(i.quantity) for i in receipt.order.items),
            qty_rejected=total_rejected,
        )
    else:
        if receipt.qty_accepted is None and receipt.qty_rejected is None:
            received = int(sum(float(i.received_qty) for i in receipt.order.items))
            receipt.qty_accepted = received
            receipt.qty_rejected = 0

    if incidence_notes is not None:
        receipt.incidence_notes = incidence_notes

    if cost_lines is not None:
        for existing in list(receipt.cost_lines):
            db.delete(existing)
        db.flush()
        _persist_cost_lines(
            db, receipt=receipt, tenant_id=receipt.order.tenant_id, cost_lines=cost_lines
        )

    receipt.commercial_closed_at = datetime.now(UTC)
    receipt.commercial_closed_by = closed_by
    db.add(receipt)
    db.flush()
    return receipt
