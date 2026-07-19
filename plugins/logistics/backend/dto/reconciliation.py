from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReconciliationCountItemRequest(BaseModel):
    product_id: str
    counted_quantity: float


class ReconciliationCountRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)
    items: list[ReconciliationCountItemRequest]


class CloseSessionRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)


class ReconciliationLineRead(BaseModel):
    product_id: str
    product_name: str
    expected_quantity: float
    counted_quantity: float | None = None
    difference_quantity: float | None = None


class InventoryDiscrepancyRead(BaseModel):
    id: str
    product_id: str
    product_name: str
    expected_quantity: float
    counted_quantity: float
    difference_quantity: float
    status: str
    resolution_notes: str | None = None


class SessionReconciliationRead(BaseModel):
    id: str | None = None
    session_id: str
    status: str
    counted_by: str | None = None
    counted_at: datetime | None = None
    notes: str | None = None
    can_close: bool = False
    lines: list[ReconciliationLineRead] = Field(default_factory=list)
    discrepancies: list[InventoryDiscrepancyRead] = Field(default_factory=list)
