from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import (
    ComDispatch,
    ComDispatchCylinder,
    ComMerchandiseReturn,
    ComMerchandiseReturnEvent,
    ComMerchandiseReturnLine,
    ComPurchaseOrder,
    ComPurchaseReceipt,
    ComSupplierClaim,
)
from plugins.logistics.backend.models.cylinder import LogisticsCylinder

STATUS_REGISTRADA = "REGISTRADA"
STATUS_CONCRETADA = "CONCRETADA"
STATUS_ANULADA = "ANULADA"

_TERMINAL_STATUSES = {STATUS_CONCRETADA, STATUS_ANULADA}
_ALLOWED_TRANSITIONS = {
    STATUS_REGISTRADA: {STATUS_CONCRETADA, STATUS_ANULADA},
}


class MerchandiseReturnTransitionError(ValueError):
    """Transición inválida del ciclo de devolución (→ 409)."""


class MerchandiseReturnReferenceNotFoundError(ValueError):
    """Referencia inexistente o ajena al tenant actual (→ 404)."""


def _stamp_event(
    db: Session,
    *,
    return_record: ComMerchandiseReturn,
    from_status: str | None,
    to_status: str,
    reason: str | None = None,
    user_id: str | None = None,
) -> None:
    db.add(
        ComMerchandiseReturnEvent(
            tenant_id=return_record.tenant_id,
            return_id=return_record.id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            user_id=user_id,
        )
    )
    db.flush()


def _get_receipt(
    db: Session, *, tenant_id: str, receipt_id: str
) -> ComPurchaseReceipt | None:
    receipt = db.scalar(
        select(ComPurchaseReceipt).where(ComPurchaseReceipt.id == receipt_id)
    )
    if receipt is None:
        return None
    order = db.scalar(
        select(ComPurchaseOrder.id).where(
            ComPurchaseOrder.id == receipt.order_id,
            ComPurchaseOrder.tenant_id == tenant_id,
        )
    )
    return receipt if order is not None else None


def _get_claim(db: Session, *, tenant_id: str, claim_id: str) -> ComSupplierClaim | None:
    return db.scalar(
        select(ComSupplierClaim).where(
            ComSupplierClaim.id == claim_id,
            ComSupplierClaim.tenant_id == tenant_id,
        )
    )


def _resolve_cylinder_for_order(
    db: Session, *, tenant_id: str, order_id: str, cylinder_id: str
) -> tuple[str | None, str | None]:
    rows = db.execute(
        select(
            ComDispatch.order_id,
            ComDispatchCylinder.product_id,
            LogisticsCylinder.serial,
        )
        .join(ComDispatch, ComDispatch.id == ComDispatchCylinder.dispatch_id)
        .join(LogisticsCylinder, LogisticsCylinder.id == ComDispatchCylinder.cylinder_id)
        .where(
            ComDispatchCylinder.tenant_id == tenant_id,
            LogisticsCylinder.tenant_id == tenant_id,
            ComDispatchCylinder.cylinder_id == cylinder_id,
        )
    ).all()
    if not rows:
        raise MerchandiseReturnReferenceNotFoundError("Serial no encontrado")
    for dispatch_order_id, product_id, serial in rows:
        if dispatch_order_id == order_id:
            return serial, product_id
    raise ValueError("El serial no pertenece a esta orden")


def create_return(
    db: Session,
    *,
    order: ComPurchaseOrder,
    receipt_id: str,
    claim_id: str | None,
    return_date,
    notes: str | None,
    lines_payload: list[dict],
    created_by: str,
) -> ComMerchandiseReturn:
    receipt = _get_receipt(db, tenant_id=order.tenant_id, receipt_id=receipt_id)
    if receipt is None:
        raise MerchandiseReturnReferenceNotFoundError("Recepción no encontrada")
    if receipt.order_id != order.id:
        raise ValueError("La recepción no pertenece a esta orden")

    claim = None
    if claim_id is not None:
        claim = _get_claim(db, tenant_id=order.tenant_id, claim_id=claim_id)
        if claim is None:
            raise MerchandiseReturnReferenceNotFoundError("Reclamación no encontrada")
        if claim.order_id != order.id:
            raise ValueError("La reclamación no pertenece a esta orden")

    item_map = {item.id: item for item in order.items}

    return_record = ComMerchandiseReturn(
        tenant_id=order.tenant_id,
        order_id=order.id,
        supplier_id=order.supplier_id,
        receipt_id=receipt.id,
        claim_id=claim.id if claim is not None else None,
        return_date=return_date,
        notes=notes,
        status=STATUS_REGISTRADA,
        created_by=created_by,
    )
    db.add(return_record)
    db.flush()

    for line in lines_payload:
        order_item = None
        if line.get("order_item_id"):
            order_item = item_map.get(line["order_item_id"])
            if order_item is None:
                raise ValueError(f"Item {line['order_item_id']} ajeno a la orden")

        product_id = line.get("product_id") or (
            order_item.product_id if order_item is not None else None
        )
        serial = None
        if line.get("cylinder_id"):
            serial, cylinder_product_id = _resolve_cylinder_for_order(
                db,
                tenant_id=order.tenant_id,
                order_id=order.id,
                cylinder_id=line["cylinder_id"],
            )
            if product_id is None:
                product_id = cylinder_product_id
            elif cylinder_product_id and product_id != cylinder_product_id:
                raise ValueError("El serial no coincide con el producto de la línea")

        if line.get("product_id") and order_item is not None and product_id != order_item.product_id:
            raise ValueError("El producto no coincide con el item de la orden")

        db.add(
            ComMerchandiseReturnLine(
                tenant_id=order.tenant_id,
                return_id=return_record.id,
                order_item_id=order_item.id if order_item is not None else line.get("order_item_id"),
                product_id=product_id,
                cylinder_id=line.get("cylinder_id"),
                serial=serial,
                qty=float(line["qty"]),
                unit_cost=(
                    line.get("unit_cost")
                    if line.get("unit_cost") is not None
                    else (float(order_item.unit_cost) if order_item is not None else None)
                ),
                notes=line.get("notes"),
            )
        )
    db.flush()
    _stamp_event(
        db,
        return_record=return_record,
        from_status=None,
        to_status=STATUS_REGISTRADA,
        user_id=created_by,
    )
    return return_record


def list_returns(db: Session, *, order: ComPurchaseOrder) -> list[ComMerchandiseReturn]:
    stmt = (
        select(ComMerchandiseReturn)
        .where(
            ComMerchandiseReturn.tenant_id == order.tenant_id,
            ComMerchandiseReturn.order_id == order.id,
        )
        .order_by(ComMerchandiseReturn.created_at.desc(), ComMerchandiseReturn.id.desc())
    )
    return list(db.scalars(stmt).all())


def get_return(
    db: Session, *, tenant_id: str, order_id: str, return_id: str
) -> ComMerchandiseReturn | None:
    stmt = select(ComMerchandiseReturn).where(
        ComMerchandiseReturn.id == return_id,
        ComMerchandiseReturn.tenant_id == tenant_id,
        ComMerchandiseReturn.order_id == order_id,
    )
    return db.scalar(stmt)


def list_return_lines(
    db: Session, *, return_record: ComMerchandiseReturn
) -> list[ComMerchandiseReturnLine]:
    stmt = (
        select(ComMerchandiseReturnLine)
        .where(ComMerchandiseReturnLine.return_id == return_record.id)
        .order_by(ComMerchandiseReturnLine.id.asc())
    )
    return list(db.scalars(stmt).all())


def list_events(
    db: Session, *, return_record: ComMerchandiseReturn
) -> list[ComMerchandiseReturnEvent]:
    stmt = (
        select(ComMerchandiseReturnEvent)
        .where(ComMerchandiseReturnEvent.return_id == return_record.id)
        .order_by(ComMerchandiseReturnEvent.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def _transition(
    db: Session,
    *,
    return_record: ComMerchandiseReturn,
    target: str,
    user_id: str,
    event_reason: str | None = None,
    resolution_notes: str | None = None,
) -> bool:
    if return_record.status == target:
        return False
    if return_record.status in _TERMINAL_STATUSES:
        raise MerchandiseReturnTransitionError(
            f"La devolución está en estado terminal {return_record.status}"
        )
    if target not in _ALLOWED_TRANSITIONS.get(return_record.status, set()):
        raise MerchandiseReturnTransitionError(
            f"No se puede pasar de {return_record.status} a {target}"
        )

    from_status = return_record.status
    return_record.status = target
    return_record.resolved_by = user_id
    return_record.resolved_at = datetime.now(UTC)
    if resolution_notes is not None:
        return_record.resolution_notes = resolution_notes
    db.add(return_record)
    _stamp_event(
        db,
        return_record=return_record,
        from_status=from_status,
        to_status=target,
        reason=event_reason,
        user_id=user_id,
    )
    db.flush()
    return True


def complete_return(
    db: Session, *, return_record: ComMerchandiseReturn, resolution_notes: str, user_id: str
) -> ComMerchandiseReturn:
    _transition(
        db,
        return_record=return_record,
        target=STATUS_CONCRETADA,
        user_id=user_id,
        resolution_notes=resolution_notes,
    )
    return return_record


def annul_return(
    db: Session, *, return_record: ComMerchandiseReturn, reason: str, user_id: str
) -> ComMerchandiseReturn:
    _transition(
        db,
        return_record=return_record,
        target=STATUS_ANULADA,
        user_id=user_id,
        event_reason=reason,
    )
    return return_record
