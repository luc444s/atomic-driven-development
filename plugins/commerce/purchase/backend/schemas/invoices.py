from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class SupplierInvoiceLineCreate(BaseModel):
    order_item_id: str | None = None
    product_id: str | None = None
    qty: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    notes: str | None = None


class SupplierInvoiceCreate(BaseModel):
    invoice_number: str = Field(min_length=1, max_length=60)
    invoice_date: date
    currency: str = "PEN"
    tax: float = 0
    lines: list[SupplierInvoiceLineCreate] = Field(min_length=1)


class SupplierInvoiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    invoice_id: str
    order_item_id: str | None
    product_id: str | None
    qty: float
    unit_price: float
    line_total: float
    notes: str | None


class SupplierInvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    supplier_id: str
    order_id: str
    invoice_number: str
    invoice_date: date
    currency: str
    subtotal: float
    tax: float
    total: float
    status: str
    lines: list[SupplierInvoiceLineRead] = []


class ReconciliationItemRead(BaseModel):
    order_item_id: str | None
    ordered_qty: float
    accepted_qty: float
    invoiced_qty: float
    ordered_cost: float
    real_cost: float
    invoiced_cost: float
    status: str
    reason: str | None = None


class ReconciliationTotalsRead(BaseModel):
    ordered: float
    real: float
    invoiced: float
    status: str
    reasons: list[str] = []


class ReconciliationRead(BaseModel):
    by_item: list[ReconciliationItemRead] = []
    totals: ReconciliationTotalsRead
    invoice_status: str | None = None
