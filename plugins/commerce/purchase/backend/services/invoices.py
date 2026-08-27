from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import (
    ComPurchaseOrder,
    ComPurchaseReceipt,
    ComReceiptCostLine,
    ComSupplierInvoice,
    ComSupplierInvoiceLine,
)


def _order_extra_total(db: Session, order: ComPurchaseOrder) -> float:
    stmt = (
        select(ComReceiptCostLine.amount)
        .join(
            ComPurchaseReceipt,
            ComPurchaseReceipt.id == ComReceiptCostLine.receipt_id,
        )
        .where(ComPurchaseReceipt.order_id == order.id)
    )
    return float(sum(float(a) for a in db.scalars(stmt).all()))


def create_supplier_invoice(
    db: Session,
    *,
    order: ComPurchaseOrder,
    invoice_number: str,
    invoice_date: date,
    currency: str,
    tax: float,
    lines: list[dict],
) -> ComSupplierInvoice:
    item_ids = {i.id for i in order.items}
    for line in lines:
        oi = line.get("order_item_id")
        if oi is not None and oi not in item_ids:
            raise ValueError(f"Linea de factura referencia item {oi} ajeno a la orden")

    invoice = ComSupplierInvoice(
        tenant_id=order.tenant_id,
        supplier_id=order.supplier_id,
        order_id=order.id,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        currency=currency,
        tax=float(tax),
        subtotal=0,
        total=0,
        status="REGISTRADA",
    )
    db.add(invoice)
    db.flush()

    subtotal = 0.0
    for line in lines:
        qty = float(line["qty"])
        unit_price = float(line["unit_price"])
        line_total = qty * unit_price
        subtotal += line_total
        db.add(
            ComSupplierInvoiceLine(
                invoice_id=invoice.id,
                order_item_id=line.get("order_item_id"),
                product_id=line.get("product_id"),
                qty=qty,
                unit_price=unit_price,
                line_total=line_total,
                notes=line.get("notes"),
            )
        )
    invoice.subtotal = subtotal
    invoice.total = subtotal + float(tax)
    db.add(invoice)
    db.flush()
    return invoice


def cancel_invoice(db: Session, *, invoice: ComSupplierInvoice) -> ComSupplierInvoice:
    if invoice.status == "ANULADA":
        return invoice
    invoice.status = "ANULADA"
    db.add(invoice)
    db.flush()
    return invoice


def _invoiced_qty_and_cost(
    db: Session, invoice: ComSupplierInvoice, order_item_id: str
) -> tuple[float, float]:
    stmt = select(ComSupplierInvoiceLine).where(
        ComSupplierInvoiceLine.invoice_id == invoice.id,
        ComSupplierInvoiceLine.order_item_id == order_item_id,
    )
    qty = 0.0
    cost = 0.0
    for line in db.scalars(stmt).all():
        qty += float(line.qty)
        cost += float(line.line_total)
    return qty, cost


def reconcile_order(db: Session, *, order: ComPurchaseOrder):
    from plugins.commerce.purchase.backend.schemas.invoices import (
        ReconciliationItemRead,
        ReconciliationRead,
        ReconciliationTotalsRead,
    )

    receipts = list(order.receipts)
    total_received = sum(float(i.received_qty) for i in order.items)
    total_accepted = sum(float(r.qty_accepted or 0) for r in receipts)
    ratio = (total_accepted / total_received) if total_received > 0 else 0.0
    extra_total = _order_extra_total(db, order)
    total_ordered_cost = sum(float(i.unit_cost) * float(i.quantity) for i in order.items) or 1.0

    invoices = [iv for iv in _invoices_for_order(db, order) if iv.status != "ANULADA"]
    has_invoice = len(invoices) > 0

    by_item: list[ReconciliationItemRead] = []
    all_match = True
    for item in order.items:
        ordered_qty = float(item.quantity)
        accepted_qty = round(float(item.received_qty) * ratio, 2)
        ordered_cost = float(item.unit_cost) * ordered_qty
        real_cost = (ordered_cost * ratio) + (
            extra_total * (ordered_cost / total_ordered_cost)
        )

        invoiced_qty = 0.0
        invoiced_cost = 0.0
        for invoice in invoices:
            q, c = _invoiced_qty_and_cost(db, invoice, item.id)
            invoiced_qty += q
            invoiced_cost += c

        if not has_invoice:
            status = "MISMATCH"
            reason = "sin factura"
            all_match = False
        else:
            qty_ok = abs(invoiced_qty - accepted_qty) < 1e-9
            tol = max(0.01, 0.01 * abs(real_cost))
            cost_ok = abs(invoiced_cost - real_cost) <= tol
            if qty_ok and cost_ok:
                status = "MATCH"
                reason = None
            else:
                status = "MISMATCH"
                reason = []
                if not qty_ok:
                    reason.append(
                        f"facturado {invoiced_qty} != aceptado {accepted_qty}"
                    )
                if not cost_ok:
                    reason.append(
                        f"costo facturado {invoiced_cost:.2f} != real {real_cost:.2f}"
                    )
                reason = "; ".join(reason)
                all_match = False

        by_item.append(
            ReconciliationItemRead(
                order_item_id=item.id,
                ordered_qty=ordered_qty,
                accepted_qty=accepted_qty,
                invoiced_qty=invoiced_qty,
                ordered_cost=ordered_cost,
                real_cost=real_cost,
                invoiced_cost=invoiced_cost,
                status=status,
                reason=reason,
            )
        )

    ordered_total = sum(float(i.unit_cost) * float(i.quantity) for i in order.items)
    real_total = sum(b.real_cost for b in by_item)
    invoiced_total = sum(b.invoiced_cost for b in by_item)

    if not has_invoice:
        totals_status = "MISMATCH"
        totals_reasons = ["sin factura"]
    else:
        tol = max(0.01, 0.01 * abs(real_total))
        totals_status = "MATCH" if (
            all_match and abs(invoiced_total - real_total) <= tol
        ) else "MISMATCH"
        totals_reasons = [] if totals_status == "MATCH" else [
            f"facturado {invoiced_total:.2f} vs real {real_total:.2f}"
        ]

    invoice_status = "CONCILIADA" if (has_invoice and all_match) else None

    return ReconciliationRead(
        by_item=by_item,
        totals=ReconciliationTotalsRead(
            ordered=ordered_total,
            real=real_total,
            invoiced=invoiced_total,
            status=totals_status,
            reasons=totals_reasons,
        ),
        invoice_status=invoice_status,
    )


def _invoices_for_order(db: Session, order: ComPurchaseOrder) -> list[ComSupplierInvoice]:
    return list(
        db.scalars(
            select(ComSupplierInvoice).where(ComSupplierInvoice.order_id == order.id)
        ).all()
    )


def list_supplier_invoices(db: Session, *, order: ComPurchaseOrder) -> list[ComSupplierInvoice]:
    return _invoices_for_order(db, order)
