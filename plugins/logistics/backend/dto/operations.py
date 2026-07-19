from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LogisticsOperationItemRead(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: float
    weight_kg: float | None = None
    notes: str | None = None
    created_at: datetime


class LogisticsOperationRead(BaseModel):
    id: str
    session_id: str
    movement_type: str
    status: str
    external_movement_id: str | None = None
    idempotency_key: str
    performed_by: str | None = None
    performed_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[LogisticsOperationItemRead] = Field(default_factory=list)
