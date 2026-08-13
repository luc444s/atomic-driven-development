from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

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


class VehicleSessionCreateWithRouteRequest(BaseModel):
    vehicle_id: str
    driver_id: str
    origin_warehouse_id: str | None = None
    route_id: str | None = None
    customer_ids: list[str] = Field(default_factory=list)
    address_ids: list[str] = Field(default_factory=list)
    route_date: date | None = None


class SessionActionRequest(BaseModel):
    notes: str | None = Field(default=None, max_length=500)


class SessionStockSummaryRead(BaseModel):
    warehouse_id: str
    warehouse_code: str
    warehouse_name: str
    total_products: int = 0
    total_units: float = 0
    total_adr_points: float = 0


class SessionHistoryEntryRead(BaseModel):
    occurred_at: datetime
    category: str
    label: str


class VehicleSessionPageRead(BaseModel):
    items: list[VehicleSessionRead]
    total: int
    page: int
    per_page: int
    total_pages: int


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
    route_date: date | None = None
    route_origin_label: str | None = None
    route_destination_label: str | None = None
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


class WaybillIssuerRead(BaseModel):
    legal_name: str
    address_line: str
    postal_city_line: str


class WaybillConsigneeRead(BaseModel):
    mode: Literal["SINGLE_DESTINATION", "ROUTE_DISTRIBUTION"]
    legal_name: str | None = None
    address_line: str | None = None
    note: str | None = None


class WaybillRegulatoryLineRead(BaseModel):
    adr_goods_description: str
    product_name: str
    adr_category: str | None = None
    package_type_label: str | None = None
    package_count: int | None = None
    net_quantity: float | None = None
    net_unit_label: str | None = None
    adr_total_quantity: float | None = None
    adr_total_unit_label: str | None = None


class WaybillOfficialSnapshotRead(BaseModel):
    issue_date: date
    vehicle_plate: str
    trailer_plate: str | None = None
    driver_name: str
    issuer: WaybillIssuerRead
    consignee: WaybillConsigneeRead
    regulatory_lines: list[WaybillRegulatoryLineRead] = Field(default_factory=list)
    totals: SessionWaybillTotalsRead


class SessionWaybillVersionBaseRead(BaseModel):
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
    document_kind: Literal["PREVIEW", "OFFICIAL"]


class SessionWaybillPreviewVersionRead(SessionWaybillVersionBaseRead):
    document_kind: Literal["PREVIEW"] = "PREVIEW"
    snapshot: SessionWaybillSnapshotRead


class SessionWaybillOfficialVersionRead(SessionWaybillVersionBaseRead):
    document_kind: Literal["OFFICIAL"] = "OFFICIAL"
    snapshot: WaybillOfficialSnapshotRead


class SessionWaybillHistoryVersionRead(SessionWaybillVersionBaseRead):
    snapshot: dict[str, Any]


class SessionWaybillStateRead(BaseModel):
    active: SessionWaybillPreviewVersionRead | None = None
    issued: SessionWaybillOfficialVersionRead | None = None
    sync_status: str | None = None
    can_regenerate: bool = False
    can_emit: bool = False
    can_reissue: bool = False
    emit_block_reason: str | None = None


class AssignRouteRequest(BaseModel):
    route_id: str = Field(min_length=1, max_length=36)


class SessionWaybillRegenerateRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    event: str = Field(min_length=1, max_length=40)
    idempotency_key: str | None = Field(default=None, max_length=120)


class SessionWaybillEmitRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=120)
