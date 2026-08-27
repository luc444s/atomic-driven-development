from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from systutor.kernel.tenants.context import TenantContext

from plugins.commerce.purchase.backend.models import (
    ComPurchaseOrder,
    ComSupplierInvoice,
)
from plugins.commerce.purchase.backend.routers.common import (
    DB_SESSION,
    REQUIRE_ORDER_MANAGE,
    REQUIRE_ORDER_READ,
    TENANT_CONTEXT,
)
from plugins.commerce.purchase.backend.schemas import (
    SupplierInvoiceCreate,
    SupplierInvoiceRead,
)
from plugins.commerce.purchase.backend.services import invoices as invoices_service
from plugins.commerce.purchase.backend.services import orders as orders_service

router = APIRouter()


def _get_order(db: Session, tenant_id: str, order_id: str) -> ComPurchaseOrder:
    order = orders_service.get_order(db, tenant_id=tenant_id, order_id=order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order


@router.post(
    "/orders/{order_id}/invoices",
    response_model=SupplierInvoiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def create_invoice(
    order_id: str,
    payload: SupplierInvoiceCreate,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierInvoiceRead:
    order = _get_order(db, tenant_context.current_tenant_id, order_id)
    try:
        invoice = invoices_service.create_supplier_invoice(
            db,
            order=order,
            invoice_number=payload.invoice_number,
            invoice_date=payload.invoice_date,
            currency=payload.currency,
            tax=payload.tax,
            lines=[ln.model_dump() for ln in payload.lines],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return SupplierInvoiceRead.model_validate(invoice)


@router.get(
    "/orders/{order_id}/invoices",
    response_model=list[SupplierInvoiceRead],
    dependencies=[REQUIRE_ORDER_READ],
)
def list_invoices(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> list[SupplierInvoiceRead]:
    order = _get_order(db, tenant_context.current_tenant_id, order_id)
    rows = invoices_service.list_supplier_invoices(db, order=order)
    return [SupplierInvoiceRead.model_validate(r) for r in rows]


@router.get(
    "/orders/{order_id}/reconciliation",
    dependencies=[REQUIRE_ORDER_READ],
)
def reconciliation(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
):
    order = _get_order(db, tenant_context.current_tenant_id, order_id)
    return invoices_service.reconcile_order(db, order=order)


@router.post(
    "/invoices/{invoice_id}/cancel",
    response_model=SupplierInvoiceRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def cancel_invoice(
    invoice_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierInvoiceRead:
    invoice = db.scalar(
        select(ComSupplierInvoice).where(
            ComSupplierInvoice.id == invoice_id,
            ComSupplierInvoice.tenant_id == tenant_context.current_tenant_id,
        )
    )
    if invoice is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    invoice = invoices_service.cancel_invoice(db, invoice=invoice)
    db.commit()
    return SupplierInvoiceRead.model_validate(invoice)
