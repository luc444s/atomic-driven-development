from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DriverOptionRead(BaseModel):
    id: str
    full_name: str
    email: str


class VehicleSessionCreateRequest(BaseModel):
    vehicle_id: str
    driver_id: str
    origin_warehouse_id: str | None = None
    route_id: str | None = None


class SessionActionRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)


class SessionStockSummaryRead(BaseModel):
    warehouse_id: str
    warehouse_code: str
    warehouse_name: str
    total_products: int = 0
    total_units: float = 0


class SessionHistoryEntryRead(BaseModel):
    occurred_at: datetime
    category: str
    label: str


class VehicleSessionRead(BaseModel):
    id: str
    vehicle_id: str
    vehicle_plate: str
    driver_id: str
    driver_name: str
    origin_warehouse_id: str
    origin_warehouse_name: str
    mobile_warehouse_id: str
    mobile_warehouse_code: str
    mobile_warehouse_name: str
    route_id: str | None = None
    status: str
    opened_at: datetime
    ready_at: datetime | None = None
    departed_at: datetime | None = None
    returned_at: datetime | None = None
    closed_at: datetime | None = None
    planned_weight_kg: float | None = None
    loaded_weight_kg: float | None = None
    occupancy_percent: float | None = None
    last_activity: str | None = None
    can_depart: bool = False
    can_close: bool = False
    next_transition_allowed: bool = False
    next_transition_blocker: str | None = None
    current_stock: SessionStockSummaryRead


class VehicleSessionDetailRead(VehicleSessionRead):
    history: list[SessionHistoryEntryRead] = Field(default_factory=list)
