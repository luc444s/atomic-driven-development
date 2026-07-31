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


class SessionWaybillVehicleRead(BaseModel):
    id: str
    plate: str
    kind: str | None = None


class SessionWaybillDriverRead(BaseModel):
    id: str
    name: str
    license: str | None = None


class SessionWaybillDestinationRead(BaseModel):
    id: str | None = None
    name: str | None = None
    address: str | None = None


class SessionWaybillItemRead(BaseModel):
    product_id: str
    product_name: str
    quantity: float
    unit: str | None = None
    weight_kg: float | None = None
    adr_points: float | None = None


class SessionWaybillTotalsRead(BaseModel):
    total_packages: float | None = None
    total_weight_kg: float | None = None
    total_adr_points: float | None = None


class SessionWaybillSnapshotRead(BaseModel):
    vehicle: SessionWaybillVehicleRead
    driver: SessionWaybillDriverRead
    destination: SessionWaybillDestinationRead
    transported_items: list[SessionWaybillItemRead] = Field(default_factory=list)
    totals: SessionWaybillTotalsRead


class SessionWaybillVersionRead(BaseModel):
    id: str
    vehicle_session_id: str
    movement_ids: list[str] = Field(default_factory=list)
    version: int
    previous_version_id: str | None = None
    status: str
    regulatory_context: str
    generated_at: datetime
    generated_by: str | None = None
    snapshot_schema_version: int
    change_event: str
    change_reason: str
    snapshot: SessionWaybillSnapshotRead


class SessionWaybillStateRead(BaseModel):
    active: SessionWaybillVersionRead | None = None
    sync_status: str | None = None
    can_regenerate: bool = False


class AssignRouteRequest(BaseModel):
    route_id: str = Field(min_length=1, max_length=36)


class SessionWaybillRegenerateRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    event: str = Field(min_length=1, max_length=40)
    idempotency_key: str | None = Field(default=None, max_length=120)
