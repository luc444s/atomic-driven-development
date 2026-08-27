from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MerchandiseReturnLineCreate(BaseModel):
    order_item_id: str | None = None
    product_id: str | None = None
    cylinder_id: str | None = None
    qty: float = Field(gt=0)
    unit_cost: float | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_reference(self) -> "MerchandiseReturnLineCreate":
        if self.order_item_id or self.product_id or self.cylinder_id:
            return self
        raise ValueError("Cada línea requiere item, producto o serial")


class MerchandiseReturnCreate(BaseModel):
    receipt_id: str
    claim_id: str | None = None
    return_date: date
    notes: str | None = None
    lines: list[MerchandiseReturnLineCreate] = Field(min_length=1)


class MerchandiseReturnCompleteRequest(BaseModel):
    resolution_notes: str = Field(min_length=1, max_length=4000)


class MerchandiseReturnAnnulRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=4000)


class MerchandiseReturnEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_status: str | None
    to_status: str
    reason: str | None
    user_id: str | None
    created_at: datetime


class MerchandiseReturnLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    return_id: str
    order_item_id: str | None
    product_id: str | None
    cylinder_id: str | None
    serial: str | None
    qty: float
    unit_cost: float | None
    notes: str | None


class MerchandiseReturnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    order_id: str
    supplier_id: str
    receipt_id: str
    claim_id: str | None
    return_date: date
    notes: str | None
    status: str
    created_by: str
    created_at: datetime
    resolved_by: str | None
    resolved_at: datetime | None
    resolution_notes: str | None


class MerchandiseReturnDetailRead(MerchandiseReturnRead):
    lines: list[MerchandiseReturnLineRead] = []
    events: list[MerchandiseReturnEventRead] = []
