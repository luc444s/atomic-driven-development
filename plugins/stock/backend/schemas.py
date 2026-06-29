from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StockBalanceRead(BaseModel):
    id: str | None = None
    tenant_id: str
    product_id: str
    product_sku: str
    product_name: str
    warehouse_id: str
    warehouse_code: str
    warehouse_name: str
    quantity: float
    min_quantity: float | None = None
    max_quantity: float | None = None
    is_below_min: bool
    updated_by: str | None = None
    updated_at: datetime | None = None


class StockWarehouseRead(BaseModel):
    id: str
    tenant_id: str
    branch_id: str | None
    name: str
    code: str
    address: str | None = None
    phone: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StockBalancePageRead(BaseModel):
    items: list[StockBalanceRead]
    total: int
    limit: int
    offset: int


class StockLedgerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    product_id: str
    product_sku: str
    product_name: str
    warehouse_id: str
    warehouse_code: str
    warehouse_name: str
    operation: str
    quantity: float
    balance_after: float
    reference_type: str | None = None
    reference_id: str | None = None
    notes: str | None = None
    created_by: str
    created_at: datetime


class StockAdjustRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float
    reason: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)


class StockTransferRequest(BaseModel):
    product_id: str
    from_warehouse_id: str
    to_warehouse_id: str
    quantity: float = Field(gt=0)
    notes: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)


class StockTransferResultRead(BaseModel):
    reference_id: str
    from_balance: StockBalanceRead
    to_balance: StockBalanceRead


class StockConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    product_id: str
    product_sku: str
    product_name: str
    warehouse_id: str
    warehouse_code: str
    warehouse_name: str
    min_quantity: float
    max_quantity: float | None = None
    is_active: bool
    updated_at: datetime
    updated_by: str


class StockConfigUpsertRequest(BaseModel):
    product_id: str
    warehouse_id: str
    min_quantity: float = 0
    max_quantity: float | None = None
    is_active: bool = True
