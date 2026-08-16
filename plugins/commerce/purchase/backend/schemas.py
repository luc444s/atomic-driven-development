from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

# ── Supplier ──

class SupplierCreateRequest(BaseModel):
    name: str
    commercial_name: str | None = None
    document_type_code: str | None = None
    document_number: str | None = None
    country_code: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    payment_term_code: str | None = None
    billing_type: str | None = None
    accounting_code: str | None = None
    fiscal_operation_key: str | None = None
    tax_regime_code: str | None = None
    notes: str | None = None


class SupplierUpdateRequest(BaseModel):
    name: str | None = None
    commercial_name: str | None = None
    document_type_code: str | None = None
    document_number: str | None = None
    country_code: str | None = None
    email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    payment_term_code: str | None = None
    billing_type: str | None = None
    accounting_code: str | None = None
    fiscal_operation_key: str | None = None
    tax_regime_code: str | None = None
    notes: str | None = None


class SupplierAddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str | None
    line1: str
    district: str | None
    city: str | None
    country_code: str
    latitude: float | None
    longitude: float | None
    is_active: bool


class SupplierContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str | None
    role: str | None
    phone: str | None
    email: str | None
    is_primary: bool


class SupplierBankAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bank_name: str
    account_holder: str
    iban: str
    bic_swift: str | None
    is_primary: bool


class SupplierPaymentTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    payment_term_code: str
    notes: str | None


class SupplierRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    commercial_name: str | None
    document_type_code: str | None
    document_number: str | None
    country_code: str | None
    email: str | None
    phone: str | None
    mobile: str | None
    payment_term_code: str | None
    billing_type: str | None
    accounting_code: str | None
    fiscal_operation_key: str | None
    tax_regime_code: str | None
    notes: str | None
    is_active: bool
    addresses: list[SupplierAddressRead]
    contacts: list[SupplierContactRead]
    bank_accounts: list[SupplierBankAccountRead]
    payment_terms: list[SupplierPaymentTermRead]
    created_at: datetime
    updated_at: datetime


# ── Purchase Order ──

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


class PurchaseOrderPageRead(BaseModel):
    items: list[PurchaseOrderRead]
    total: int
    limit: int
    offset: int


# ── Receive ──

class ReceiveItemRequest(BaseModel):
    purchase_item_id: str
    quantity: float = Field(gt=0)


class ReceiveOrderRequest(BaseModel):
    warehouse_id: str
    items: list[ReceiveItemRequest] = Field(min_length=1)
    notes: str | None = None
    tank_id: str | None = None


class CancelOrderRequest(BaseModel):
    reason: str | None = None


class SupplierAddressCreateRequest(BaseModel):
    line1: str
    label: str | None = None
    district: str | None = None
    city: str | None = None
    country_code: str = "PE"
    latitude: float | None = None
    longitude: float | None = None


class SupplierContactCreateRequest(BaseModel):
    full_name: str | None = None
    role: str | None = None
    phone: str | None = None
    email: str | None = None


class SupplierBankAccountCreateRequest(BaseModel):
    bank_name: str
    account_holder: str
    iban: str
    bic_swift: str | None = None
