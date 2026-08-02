from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.core.pagination import OffsetPageRead


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
    reserved_quantity: float = 0.0
    available_quantity: float = 0.0
    total_cost: float | None = None
    unit_cost: float | None = None
    allow_negative_stock: bool = False
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
    is_primary: bool = False
    is_active: bool
    created_at: datetime
    updated_at: datetime


class StockBalancePageRead(OffsetPageRead[StockBalanceRead]):
    pass


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
    unit_cost: float | None = None
    total_cost: float | None = None
    cost_after: float | None = None
    source: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    notes: str | None = None
    created_by: str
    created_at: datetime


class StockAdjustRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float
    unit_cost: float | None = None
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
    allow_negative_stock: bool = False
    is_active: bool
    updated_at: datetime
    updated_by: str


class StockConfigUpsertRequest(BaseModel):
    product_id: str
    warehouse_id: str
    min_quantity: float = 0
    max_quantity: float | None = None
    allow_negative_stock: bool | None = None
    is_active: bool = True


# --- Allocation schemas ---

class StockAllocateRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float = Field(gt=0)
    reference_type: str
    reference_id: str
    allocation_group_id: str | None = None
    expires_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)


class StockAllocationReleaseRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class StockAllocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    allocation_group_id: str | None
    product_id: str
    product_sku: str = ""
    product_name: str = ""
    warehouse_id: str
    warehouse_code: str = ""
    warehouse_name: str = ""
    quantity: float
    remaining_quantity: float
    reference_type: str
    reference_id: str
    status: str
    created_by: str
    created_at: datetime
    expires_at: datetime | None
    released_at: datetime | None
    released_by: str | None
    release_reason: str | None


# --- Movement schemas ---

class StockSaleOutRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float = Field(gt=0)
    source: str = Field(pattern=r"^(allocation|direct)$")
    allocation_id: str | None = None
    reference_type: str
    reference_id: str
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)


class StockPurchaseInRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float = Field(gt=0)
    unit_cost: float = Field(gt=0)
    reference_type: str
    reference_id: str
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)


class StockReturnInRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float = Field(gt=0)
    original_sale_ledger_id: str
    reference_type: str
    reference_id: str
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)


class StockDamageOutRequest(BaseModel):
    product_id: str
    warehouse_id: str
    quantity: float = Field(gt=0)
    reason: str | None = Field(default=None, max_length=500)
    reference_type: str
    reference_id: str
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=100)


class StockMovementResultRead(BaseModel):
    operation: str
    balance: StockBalanceRead
    ledger_entry_id: str
