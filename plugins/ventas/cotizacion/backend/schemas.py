from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExecuteCommandRequest(BaseModel):
    command: str = Field(..., min_length=1, max_length=2000, description="Comando DSL a ejecutar (ej: 'cotizar cliente Juan 400 cilindros mañana 14h')")


class QuoteItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    product_name: str | None = None
    quantity: int
    unit_weight_kg: Decimal | None = None


class CustomerSummary(BaseModel):
    id: str
    name: str


class ProductSummary(BaseModel):
    id: str
    name: str
    sku: str | None = None


class VehicleSummary(BaseModel):
    id: str
    plate: str


class QuoteDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    customer: CustomerSummary
    items: list[QuoteItemResponse] = []
    delivery_date: date
    delivery_time: time | None = None
    vehicle: VehicleSummary | None = None
    conditions: str | None = None
    created_at: datetime


class QuoteDraftListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    customer_name: str | None = None
    delivery_date: date
    created_at: datetime


class ValidationError(BaseModel):
    error: str = "validation_error"
    message: str
    details: dict | None = None


class AmbiguityError(BaseModel):
    error: str = "ambiguity_error"
    message: str
    entity: str
    options: list[dict]
