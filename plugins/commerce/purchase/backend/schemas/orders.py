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
    events: list["PurchaseOrderEventRead"] = []


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


class ReceiveOrderRequest(BaseModel):
    warehouse_id: str
    items: list[ReceiveItemRequest] = Field(min_length=1)
    notes: str | None = None
    tank_id: str | None = None
    dispatch_id: str | None = None


class CancelOrderRequest(BaseModel):
    reason: str | None = None


class CloseOrderRequest(BaseModel):
    reason: str = Field(min_length=1)
