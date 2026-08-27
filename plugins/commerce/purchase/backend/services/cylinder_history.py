"""Historial técnico del envase por serial (COMPRAS-016).

Consulta consolidada de SOLO LECTURA en dominio compras: despachos con
custodia (005/007/008), recepciones con su diferencia comercial (009) y
servicios con datos legales PH/retimbrado (014/015). La resolución del
serial lee lg_cylinders sin escribir en modelos lg_* (patrón de familia
de services/receipts.py, §32). Ninguna mutación ocurre como efecto de
esta consulta.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import (
    ComDispatch,
    ComDispatchCylinder,
    ComPurchaseOrder,
    ComPurchaseReceipt,
    ComReceiptServiceLine,
)
from plugins.logistics.backend.models.cylinder import LogisticsCylinder


class SerialNotFoundError(ValueError):
    """Serial inexistente en lg_cylinders del tenant → 404 en HTTP."""


def get_cylinder_history(db: Session, *, tenant_id: str, serial: str) -> dict:
    """Historial consolidado del serial, cada lista en orden cronológico."""
    cylinder = db.scalar(
        select(LogisticsCylinder).where(
            LogisticsCylinder.tenant_id == tenant_id,
            LogisticsCylinder.serial == serial,
        )
    )
    if cylinder is None:
        raise SerialNotFoundError(f"Serial {serial} no encontrado en el tenant")

    dispatch_rows = db.execute(
        select(ComDispatchCylinder, ComDispatch)
        .join(ComDispatch, ComDispatch.id == ComDispatchCylinder.dispatch_id)
        .where(
            ComDispatchCylinder.tenant_id == tenant_id,
            ComDispatchCylinder.cylinder_id == cylinder.id,
        )
        .order_by(ComDispatch.dispatch_date.asc(), ComDispatch.created_at.asc())
    ).all()

    dispatch_ids = [item.dispatch_id for item, _ in dispatch_rows]

    receipts: list[ComPurchaseReceipt] = []
    if dispatch_ids:
        receipts = list(
            db.scalars(
                select(ComPurchaseReceipt)
                .join(ComPurchaseOrder, ComPurchaseOrder.id == ComPurchaseReceipt.order_id)
                .where(
                    ComPurchaseReceipt.dispatch_id.in_(dispatch_ids),
                    ComPurchaseOrder.tenant_id == tenant_id,
                )
                .order_by(
                    ComPurchaseReceipt.receipt_date.asc(),
                    ComPurchaseReceipt.created_at.asc(),
                )
            ).all()
        )

    services = list(
        db.scalars(
            select(ComReceiptServiceLine).where(
                ComReceiptServiceLine.tenant_id == tenant_id,
                ComReceiptServiceLine.cylinder_id == cylinder.id,
            )
            .order_by(
                ComReceiptServiceLine.created_at.asc(),
                ComReceiptServiceLine.id.asc(),
            )
        ).all()
    )

    return {
        "cylinder_id": cylinder.id,
        "serial": serial,
        "dispatches": [
            {
                "dispatch_id": dispatch.id,
                "order_id": dispatch.order_id,
                "supplier_id": dispatch.supplier_id,
                "dispatch_date": dispatch.dispatch_date,
                "service_type": item.service_type,
                "status": item.status,
                "returned_at": item.returned_at,
            }
            for item, dispatch in dispatch_rows
        ],
        "receipts": [
            {
                "receipt_id": receipt.id,
                "order_id": receipt.order_id,
                "receipt_date": receipt.receipt_date,
                "qty_accepted": receipt.qty_accepted,
                "qty_rejected": receipt.qty_rejected,
                "difference_type": receipt.difference_type,
            }
            for receipt in receipts
        ],
        "services": [
            {
                "receipt_id": line.receipt_id,
                "service_type": line.service_type,
                "cost": line.cost,
                "notes": line.notes,
                "test_date": line.test_date,
                "next_test_date": line.next_test_date,
                "result": line.result,
                "document_ref": line.document_ref,
                "created_at": line.created_at,
            }
            for line in services
        ],
    }
