from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RouteOperationItemRequest(BaseModel):
    product_id: str
    product_name: str | None = Field(default=None, max_length=200)
    quantity: float = Field(gt=0)
    direction: str = Field(min_length=1, max_length=10)


class RouteOperationCreateRequest(BaseModel):
    route_stop_id: str | None = None
    operation_type: str = Field(min_length=1, max_length=30)
    notes: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=120)
    items: list[RouteOperationItemRequest] = Field(default_factory=list)


class ExchangeOperationLineRequest(BaseModel):
    product_id: str
    product_name: str | None = Field(default=None, max_length=200)
    quantity: float = Field(gt=0)


class ExchangeRouteOperationCreateRequest(BaseModel):
    route_stop_id: str | None = None
    notes: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=120)
    delivered_lines: list[ExchangeOperationLineRequest] = Field(default_factory=list)
    picked_up_lines: list[ExchangeOperationLineRequest] = Field(default_factory=list)


class RouteOperationItemRead(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: float
    direction: str
    created_at: datetime


class RouteOperationRead(BaseModel):
    id: str
    session_id: str
    route_stop_id: str | None = None
    operation_type: str
    status: str
    movement_ids: list[str] = Field(default_factory=list)
    idempotency_key: str
    notes: str | None = None
    performed_by: str | None = None
    performed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    items: list[RouteOperationItemRead] = Field(default_factory=list)


class CompositionLineRead(BaseModel):
    product_id: str
    product_name: str
    quantity: float
    weight_kg: float | None = None
    adr_points: float | None = None


class CompositionTotalsRead(BaseModel):
    total_packages: float
    total_weight_kg: float
    total_adr_points: float


class CurrentCompositionRead(BaseModel):
    session_id: str
    composition_version: int | None = None
    product_lines: list[CompositionLineRead] = Field(default_factory=list)
    totals: CompositionTotalsRead


class RouteIncidentCreateRequest(BaseModel):
    route_stop_id: str | None = None
    related_operation_id: str | None = None
    type: str = Field(min_length=1, max_length=40)
    notes: str | None = Field(default=None, max_length=500)


class RouteIncidentResolveRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)


class RouteIncidentCorrectRequest(BaseModel):
    route_stop_id: str | None = None
    operation_type: str = Field(min_length=1, max_length=30)
    notes: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=120)
    items: list[RouteOperationItemRequest] = Field(default_factory=list)


class RouteIncidentRead(BaseModel):
    id: str
    session_id: str
    route_stop_id: str | None = None
    related_operation_id: str | None = None
    type: str
    status: str
    corrective_operation_id: str | None = None
    notes: str | None = None
    created_by: str
    closed_by: str | None = None
    created_at: datetime
    closed_at: datetime | None = None
    updated_at: datetime


class RouteStopProgressRead(BaseModel):
    route_stop_id: str
    progress_status: str
    last_operation_at: datetime | None = None
    open_incidents: int = 0
