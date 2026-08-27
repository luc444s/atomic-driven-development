from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from plugins.commerce.purchase.backend.schemas.suppliers import SupplierRead


class PurchaseItemCreateRequest(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)
    unit_cost: float = Field(gt=0)


class PurchaseOrderCreateRequest(BaseModel):
    supplier_id: str
    expected_date: date | None = None
    notes: str | None = None
    items: list[PurchaseItemCreateRequest] = Field(min_length=1)


class PurchaseOrderUpdateRequest(BaseModel):
    supplier_id: str | None = None
    expected_date: date | None = None
    notes: str | None = None
    items: list[PurchaseItemCreateRequest] | None = None


class PurchaseItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    quantity: float
    unit_cost: float
    received_qty: float


class PurchaseReceiptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    warehouse_id: str
    receipt_date: date
    dispatch_id: str | None
    notes: str | None
    created_at: datetime
    # COMPRAS-009
    qty_accepted: int | None
    qty_rejected: int | None
    difference_type: str | None
    incidence_notes: str | None
    commercial_closed_at: datetime | None
    commercial_closed_by: str | None
    # COMPRAS-010
    extra_total: float | None
    real_total: float | None
    unit_cost_real: float | None
    cost_lines: list[ReceiptCostLineRead] = []


class ReceiptCostLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cost_type: str
    amount: float
    currency: str
    notes: str | None


class PurchaseOrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    supplier: SupplierRead | None
    status: str
    order_date: date
    expected_date: date | None
    notes: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class PurchaseOrderDetailRead(PurchaseOrderRead):
    items: list[PurchaseItemRead]
    receipts: list[PurchaseReceiptRead]
    events: list[PurchaseOrderEventRead] = []


class PurchaseOrderEventRead(BaseModel):
    id: str
    from_status: str | None
    to_status: str
    reason: str | None
    user_id: str | None
    created_at: datetime


class PurchaseOrderPageRead(BaseModel):
    items: list[PurchaseOrderRead]
    total: int
    limit: int
    offset: int


class ReceiveItemRequest(BaseModel):
    purchase_item_id: str
    quantity: float = Field(gt=0)
    # COMPRAS-009: distinción comercial (opcional, retrocompatible)
    qty_accepted: int | None = None
    qty_rejected: int | None = None


class ReceiveCostLine(BaseModel):
    cost_type: str
    amount: float = Field(ge=0)
    currency: str = "PEN"
    notes: str | None = None


class ReceiveOrderRequest(BaseModel):
    warehouse_id: str
    items: list[ReceiveItemRequest] = Field(min_length=1)
    notes: str | None = None
    tank_id: str | None = None
    dispatch_id: str | None = None
    # COMPRAS-010: costos adicionales de la recepción
    cost_lines: list[ReceiveCostLine] | None = None


class CommercialCloseLineRequest(BaseModel):
    purchase_item_id: str
    qty_accepted: int
    qty_rejected: int = 0


class CommercialCloseRequest(BaseModel):
    """COMPRAS-009: cierre comercial de una recepción ya creada."""

    lines: list[CommercialCloseLineRequest] | None = None
    # COMPRAS-010: costos adicionales al cerrar
    cost_lines: list[ReceiveCostLine] | None = None
    incidence_notes: str | None = None


class CancelOrderRequest(BaseModel):
    reason: str | None = None


class CloseOrderRequest(BaseModel):
    reason: str = Field(min_length=1)
