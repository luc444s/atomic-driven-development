from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

VALID_SERVICE_TYPES = (
    "LLENADO",
    "PH",
    "RETIMBRADO",
    "INSPECCION",
    "REPARACION",
    "CAMBIO_VALVULA",
    "ACONDICIONAMIENTO",
    "CERTIFICACION",
    "MIXTO",
)


class DispatchCylinderInput(BaseModel):
    cylinder_id: str
    product_id: str | None = None
    service_type: str = Field(default="LLENADO")
    notes: str | None = None


class DispatchCreateRequest(BaseModel):
    supplier_id: str
    order_id: str | None = None
    warehouse_id: str | None = None
    dispatch_date: date | None = None
    carrier: str | None = None
    vehicle_plate: str | None = None
    driver_name: str | None = None
    notes: str | None = None
    cylinders: list[DispatchCylinderInput] = Field(min_length=1)


class DispatchCylinderRead(BaseModel):
    id: str
    cylinder_id: str
    serial: str | None = None
    product_id: str | None = None
    service_type: str
    status: str
    returned_at: datetime | None = None
    notes: str | None = None


class DispatchRead(BaseModel):
    id: str
    supplier_id: str
    supplier_name: str | None = None
    order_id: str | None = None
    warehouse_id: str | None = None
    dispatch_date: date
    carrier: str | None = None
    vehicle_plate: str | None = None
    driver_name: str | None = None
    status: str
    notes: str | None = None
    created_by: str
    created_at: datetime
    cylinders: list[DispatchCylinderRead] = []


class CustodyEntryRead(BaseModel):
    dispatch_id: str
    dispatch_date: date
    cylinder_id: str
    serial: str | None = None
    product_id: str | None = None
    service_type: str
    days_out: int
    order_id: str | None = None


class CustodySummaryRow(BaseModel):
    supplier_id: str
    supplier_name: str | None = None
    total_cylinders: int
    oldest_days_out: int


class DispatchPageRead(BaseModel):
    items: list[DispatchRead]
    total: int
    limit: int
    offset: int


class DispatchReturnItem(BaseModel):
    cylinder_id: str


class DispatchReturnRequest(BaseModel):
    cylinders: list[DispatchReturnItem] = Field(min_length=1)
    notes: str | None = None


class DispatchSessionLinkRequest(BaseModel):
    kind: str = Field(pattern="^(outbound|return)$")
    session_id: str | None = None
