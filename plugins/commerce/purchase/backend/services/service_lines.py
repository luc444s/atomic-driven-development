from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import (
    ComPurchaseOrder,
    ComPurchaseReceipt,
    ComReceiptServiceLine,
)
from plugins.logistics.backend.models.cylinder import LogisticsCylinder


class ReceiptCommerciallyClosedError(ValueError):
    """Receipt con cierre comercial estampado (009) → 409 en HTTP."""


class SerialNotFoundError(ValueError):
    """Serial inexistente en lg_cylinders del tenant → 422 en HTTP."""


def get_receipt(
    db: Session, *, tenant_id: str, receipt_id: str
) -> ComPurchaseReceipt | None:
    """Receipt del tenant resuelto vía su orden; cross-tenant → None (404)."""
    receipt = db.scalar(
        select(ComPurchaseReceipt).where(ComPurchaseReceipt.id == receipt_id)
    )
    if receipt is None:
        return None
    order = db.scalar(
        select(ComPurchaseOrder).where(
            ComPurchaseOrder.id == receipt.order_id,
            ComPurchaseOrder.tenant_id == tenant_id,
        )
    )
    if order is None:
        return None
    return receipt


def _resolve_serial(db: Session, *, tenant_id: str, serial: str) -> LogisticsCylinder:
    cylinder = db.scalar(
        select(LogisticsCylinder).where(
            LogisticsCylinder.tenant_id == tenant_id,
            LogisticsCylinder.serial == serial,
        )
    )
    if cylinder is None:
        raise SerialNotFoundError(f"Serial {serial} no encontrado en el tenant")
    return cylinder


def _ensure_commercial_open(receipt: ComPurchaseReceipt) -> None:
    if receipt.commercial_closed_at is not None:
        raise ReceiptCommerciallyClosedError(
            "La recepción tiene cierre comercial: no admite líneas de servicio"
        )


def create_service_line(
    db: Session,
    *,
    receipt: ComPurchaseReceipt,
    tenant_id: str,
    serial: str,
    service_type: str,
    cost: float | None,
    notes: str | None,
    created_by: str,
) -> ComReceiptServiceLine:
    _ensure_commercial_open(receipt)
    cylinder = _resolve_serial(db, tenant_id=tenant_id, serial=serial)
    line = ComReceiptServiceLine(
        tenant_id=tenant_id,
        receipt_id=receipt.id,
        cylinder_id=cylinder.id,
        serial=serial,
        service_type=service_type,
        cost=cost,
        notes=notes,
        created_by=created_by,
    )
    db.add(line)
    db.flush()
    return line


def list_service_lines(
    db: Session, *, tenant_id: str, receipt: ComPurchaseReceipt
) -> list[ComReceiptServiceLine]:
    stmt = (
        select(ComReceiptServiceLine)
        .where(
            ComReceiptServiceLine.tenant_id == tenant_id,
            ComReceiptServiceLine.receipt_id == receipt.id,
        )
        .order_by(ComReceiptServiceLine.created_at, ComReceiptServiceLine.id)
    )
    return list(db.scalars(stmt).all())


def delete_service_line(
    db: Session, *, receipt: ComPurchaseReceipt, line_id: str
) -> bool:
    """Borra una línea del receipt; False si no existe (→ 404)."""
    _ensure_commercial_open(receipt)
    line = db.scalar(
        select(ComReceiptServiceLine).where(
            ComReceiptServiceLine.id == line_id,
            ComReceiptServiceLine.receipt_id == receipt.id,
        )
    )
    if line is None:
        return False
    db.delete(line)
    db.flush()
    return True
