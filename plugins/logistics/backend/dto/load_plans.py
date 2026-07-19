from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoadPlanItemUpsert(BaseModel):
    product_id: str
    planned_quantity: float = Field(gt=0)
    source_warehouse_id: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class LoadPlanUpsertRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)
    items: list[LoadPlanItemUpsert]


class ConfirmLoadRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)


class ReturnRemainingRequest(BaseModel):
    destination_warehouse_id: str | None = None
    notes: str | None = Field(default=None, max_length=500)


class LoadPlanItemRead(BaseModel):
    id: str
    product_id: str
    product_name: str
    planned_quantity: float
    planned_weight_kg: float | None = None
    source_warehouse_id: str
    notes: str | None = None
    created_at: datetime


class LoadPlanRead(BaseModel):
    id: str | None = None
    session_id: str
    status: str
    notes: str | None = None
    planned_weight_kg: float = 0
    items: list[LoadPlanItemRead] = Field(default_factory=list)
