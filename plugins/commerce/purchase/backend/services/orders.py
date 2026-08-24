from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import (
    ComPurchaseItem,
    ComPurchaseOrder,
    ComPurchaseOrderEvent,
)

VALID_STATUSES = ("DRAFT", "ORDERED", "PARTIAL", "RECEIVED", "CLOSED", "CANCELLED")

# Matriz de transiciones válidas (COMPRAS-002). PARTIAL/RECEIVED solo se
# alcanzan vía recepción (services/receipts.py pasa por transition()).
TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"ORDERED", "CANCELLED"},
    "ORDERED": {"PARTIAL", "RECEIVED", "CANCELLED", "CLOSED"},
    "PARTIAL": {"RECEIVED", "CANCELLED", "CLOSED"},
    "RECEIVED": {"CLOSED"},
    "CLOSED": set(),
    "CANCELLED": set(),
}


def _validate_status_transition(current: str, target: str) -> None:
    allowed = TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(f"No se puede pasar de {current} a {target}")


def transition(
    db: Session,
    *,
    order: ComPurchaseOrder,
    target: str,
    user_id: str | None = None,
    reason: str | None = None,
) -> ComPurchaseOrder:
    """Única puerta de mutación de status (COMPRAS-002).

    Valida la matriz de transiciones, aplica reglas de negocio por destino y
    registra un evento de auditoría. Ningún otro código debe asignar
    order.status directamente.
    """
    if target not in VALID_STATUSES:
        raise ValueError(f"Estado desconocido: {target}")
    _validate_status_transition(order.status, target)

    if target == "ORDERED":
        if not order.items:
            raise ValueError("No se puede confirmar una orden sin items")
    if target == "CANCELLED":
        received = any(float(item.received_qty) > 0 for item in order.items)
        if received:
            raise ValueError(
                "No se puede cancelar una orden con cantidades ya recepcionadas"
            )
    if target == "CLOSED" and not (reason and reason.strip()):
        raise ValueError("El cierre administrativo requiere un motivo")

    event = ComPurchaseOrderEvent(
        order_id=order.id,
        from_status=order.status,
        to_status=target,
        reason=reason,
        user_id=user_id,
    )
    db.add(event)
    order.status = target
    db.add(order)
    db.flush()
    return order


def _base_query(tenant_id: str, status: str | None = None, supplier_id: str | None = None):
    stmt = select(ComPurchaseOrder).where(ComPurchaseOrder.tenant_id == tenant_id)
    if status:
        stmt = stmt.where(ComPurchaseOrder.status == status)
    if supplier_id:
        stmt = stmt.where(ComPurchaseOrder.supplier_id == supplier_id)
    return stmt


def list_orders(
    db: Session,
    *,
    tenant_id: str,
    status: str | None = None,
    supplier_id: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[ComPurchaseOrder], int]:
    stmt = _base_query(tenant_id, status, supplier_id)

    count_stmt = select(func.count()).select_from(ComPurchaseOrder).where(
        ComPurchaseOrder.tenant_id == tenant_id
    )
    if status:
        count_stmt = count_stmt.where(ComPurchaseOrder.status == status)
    if supplier_id:
        count_stmt = count_stmt.where(ComPurchaseOrder.supplier_id == supplier_id)
    total = db.scalar(count_stmt) or 0

    stmt = stmt.order_by(ComPurchaseOrder.order_date.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all()), total


def get_order(db: Session, *, tenant_id: str, order_id: str) -> ComPurchaseOrder | None:
    return db.scalar(
        select(ComPurchaseOrder).where(
            ComPurchaseOrder.id == order_id, ComPurchaseOrder.tenant_id == tenant_id
        )
    )


def create_order(
    db: Session,
    *,
    tenant_id: str,
    branch_id: str | None,
    supplier_id: str,
    items_payload: list[dict],
    expected_date: date | None,
    notes: str | None,
    created_by: str,
) -> ComPurchaseOrder:
    order = ComPurchaseOrder(
        tenant_id=tenant_id,
        branch_id=branch_id,
        supplier_id=supplier_id,
        status="DRAFT",
        order_date=date.today(),
        expected_date=expected_date,
        notes=notes,
        created_by=created_by,
    )
    db.add(order)
    db.flush()

    for item in items_payload:
        db.add(ComPurchaseItem(
            order_id=order.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_cost=item["unit_cost"],
            received_qty=0,
        ))
    db.flush()
    return order


def update_order(
    db: Session,
    *,
    order: ComPurchaseOrder,
    payload: dict,
) -> ComPurchaseOrder:
    if order.status != "DRAFT":
        raise ValueError("Solo se puede editar una orden en estado DRAFT")

    if "supplier_id" in payload and payload["supplier_id"] is not None:
        order.supplier_id = payload["supplier_id"]
    for field in ("expected_date", "notes"):
        if field in payload:
            setattr(order, field, payload[field])

    if "items" in payload and payload["items"] is not None:
        for item in list(order.items):
            db.delete(item)
        db.flush()
        for item in payload["items"]:
            db.add(ComPurchaseItem(
                order_id=order.id,
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_cost=item["unit_cost"],
                received_qty=0,
            ))

    db.add(order)
    db.flush()
    return order


def confirm_order(
    db: Session, *, order: ComPurchaseOrder, user_id: str | None = None
) -> ComPurchaseOrder:
    return transition(db, order=order, target="ORDERED", user_id=user_id)


def cancel_order(
    db: Session,
    *,
    order: ComPurchaseOrder,
    user_id: str | None = None,
    reason: str | None = None,
) -> ComPurchaseOrder:
    return transition(db, order=order, target="CANCELLED", user_id=user_id, reason=reason)


def close_order(
    db: Session,
    *,
    order: ComPurchaseOrder,
    user_id: str | None = None,
    reason: str,
) -> ComPurchaseOrder:
    return transition(db, order=order, target="CLOSED", user_id=user_id, reason=reason)
