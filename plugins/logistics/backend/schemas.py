from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CylinderStateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    is_final: bool
    description: str | None


class CylinderTransitionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_state: str
    to_state: str
    requires_adr: bool
    requires_hydrotest: bool
    description: str | None


class CylinderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str | None
    serial: str
    description: str | None
    barcode1: str | None
    barcode2: str | None
    current_state: str
    gas_group_id: str | None
    content_kg: float | None
    volume_m3: float | None
    condition: str | None
    brand_id: str | None
    cost: float | None
    price: float | None
    country_code: str | None
    box_number: str | None
    is_service: bool
    manufacturer_date: date | None
    manufacturer_code: str | None
    manufacture_year: int | None
    weight_origin: float | None
    weight_current: float | None
    last_hydrotest_date: date | None
    next_hydrotest_date: date | None
    adr_category: str | None
    adr_un_number: str | None
    adr_label: str | None
    adr_package_type: str | None
    adr_weight_kg: float | None
    adr_merchandise: str | None
    adr_tunnel: str | None
    adr_subline: str | None
    adr_factor: float | None
    adr_points: int | None
    adr_unit_measure: str | None
    location: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CylinderCreateRequest(BaseModel):
    serial: str = Field(min_length=1, max_length=50)
    branch_id: str | None = None
    description: str | None = Field(default=None, max_length=200)
    barcode1: str | None = Field(default=None, max_length=150)
    barcode2: str | None = Field(default=None, max_length=50)
    gas_group_id: str | None = None
    content_kg: float | None = None
    volume_m3: float | None = None
    condition: str | None = Field(default=None, max_length=50)
    brand_id: str | None = None
    cost: float | None = None
    price: float | None = None
    country_code: str | None = Field(default=None, max_length=100)
    box_number: str | None = Field(default=None, max_length=50)
    is_service: bool = False
    manufacturer_date: date | None = None
    manufacturer_code: str | None = Field(default=None, max_length=50)
    manufacture_year: int | None = None
    weight_origin: float | None = None
    weight_current: float | None = None
    last_hydrotest_date: date | None = None
    next_hydrotest_date: date | None = None
    adr_category: str | None = Field(default=None, max_length=50)
    adr_un_number: str | None = Field(default=None, max_length=10)
    adr_label: str | None = Field(default=None, max_length=50)
    adr_package_type: str | None = Field(default=None, max_length=50)
    adr_weight_kg: float | None = None
    adr_merchandise: str | None = Field(default=None, max_length=200)
    adr_tunnel: str | None = Field(default=None, max_length=10)
    adr_subline: str | None = Field(default=None, max_length=50)
    adr_factor: float | None = None
    adr_points: int | None = None
    adr_unit_measure: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=100)


class CylinderUpdateRequest(BaseModel):
    serial: str | None = Field(default=None, min_length=1, max_length=50)
    branch_id: str | None = None
    description: str | None = Field(default=None, max_length=200)
    barcode1: str | None = Field(default=None, max_length=150)
    barcode2: str | None = Field(default=None, max_length=50)
    gas_group_id: str | None = None
    content_kg: float | None = None
    volume_m3: float | None = None
    condition: str | None = Field(default=None, max_length=50)
    brand_id: str | None = None
    cost: float | None = None
    price: float | None = None
    country_code: str | None = Field(default=None, max_length=100)
    box_number: str | None = Field(default=None, max_length=50)
    is_service: bool | None = None
    manufacturer_date: date | None = None
    manufacturer_code: str | None = Field(default=None, max_length=50)
    manufacture_year: int | None = None
    weight_origin: float | None = None
    weight_current: float | None = None
    last_hydrotest_date: date | None = None
    next_hydrotest_date: date | None = None
    adr_category: str | None = Field(default=None, max_length=50)
    adr_un_number: str | None = Field(default=None, max_length=10)
    adr_label: str | None = Field(default=None, max_length=50)
    adr_package_type: str | None = Field(default=None, max_length=50)
    adr_weight_kg: float | None = None
    adr_merchandise: str | None = Field(default=None, max_length=200)
    adr_tunnel: str | None = Field(default=None, max_length=10)
    adr_subline: str | None = Field(default=None, max_length=50)
    adr_factor: float | None = None
    adr_points: int | None = None
    adr_unit_measure: str | None = Field(default=None, max_length=20)
    location: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class CylinderStateLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: str
    cylinder_id: str
    from_state: str | None
    to_state: str
    changed_by: str
    movement_id: str | None
    origin: str | None
    reason_code: str | None
    notes: str | None
    metadata_json: dict[str, object]
    created_at: datetime


class CylinderTransitionRequest(BaseModel):
    to_state: str = Field(min_length=1, max_length=50)
    movement_id: str | None = None
    origin: str | None = Field(default=None, max_length=100)
    reason_code: str | None = Field(default=None, max_length=30)
    notes: str | None = None
    metadata_json: dict[str, object] = Field(default_factory=dict)


class CylinderSummaryItem(BaseModel):
    state: str
    count: int


class WarehouseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str | None
    name: str
    code: str
    address: str | None
    phone: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WarehouseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=20)
    branch_id: str | None = None
    address: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=50)


class WarehouseUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=1, max_length=20)
    branch_id: str | None = None
    address: str | None = Field(default=None, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    code: str
    is_active: bool
    created_at: datetime


class ZoneCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=20)


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    plate: str
    vehicle_type: str | None
    brand: str | None
    model: str | None
    capacity_weight: float | None
    capacity_volume: float | None
    useful_load: float | None
    adr_class: str | None
    status: str
    warehouse_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VehicleCreateRequest(BaseModel):
    plate: str = Field(min_length=1, max_length=20)
    vehicle_type: str | None = Field(default=None, max_length=50)
    brand: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    capacity_weight: float | None = None
    capacity_volume: float | None = None
    useful_load: float | None = None
    adr_class: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=20)
    warehouse_id: str | None = None


class VehicleUpdateRequest(BaseModel):
    vehicle_type: str | None = Field(default=None, max_length=50)
    brand: str | None = Field(default=None, max_length=50)
    model: str | None = Field(default=None, max_length=50)
    capacity_weight: float | None = None
    capacity_volume: float | None = None
    useful_load: float | None = None
    adr_class: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=20)
    warehouse_id: str | None = None
    is_active: bool | None = None


class DeliveryPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    customer_id: str
    contact_name: str | None
    contact_email: str | None
    address: str
    phone: str | None
    zone_id: str | None
    warehouse_id: str | None
    address_id: str | None
    is_primary: bool
    delivery_day: str | None
    visit_day: str | None
    time_window: str | None
    instructions: str | None
    service_time_min: int | None
    demand_units: int | None
    demand_weight_kg: float | None
    agent_user_id: str | None
    fiscal_operation_document: str | None
    fiscal_operation_type: str | None
    gps_link: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DeliveryPointCreateRequest(BaseModel):
    customer_id: str
    contact_name: str | None = Field(default=None, max_length=100)
    contact_email: str | None = Field(default=None, max_length=100)
    address: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    zone_id: str | None = None
    warehouse_id: str | None = None
    address_id: str | None = None
    is_primary: bool = False
    delivery_day: str | None = Field(default=None, max_length=50)
    visit_day: str | None = Field(default=None, max_length=50)
    time_window: str | None = Field(default=None, max_length=50)
    instructions: str | None = Field(default=None, max_length=200)
    service_time_min: int | None = None
    demand_units: int | None = None
    demand_weight_kg: float | None = None
    agent_user_id: str | None = None
    fiscal_operation_document: str | None = Field(default=None, max_length=50)
    fiscal_operation_type: str | None = Field(default=None, max_length=30)
    gps_link: str | None = Field(default=None, max_length=200)


class DeliveryPointUpdateRequest(BaseModel):
    customer_id: str | None = None
    contact_name: str | None = Field(default=None, max_length=100)
    contact_email: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    zone_id: str | None = None
    warehouse_id: str | None = None
    address_id: str | None = None
    is_primary: bool | None = None
    delivery_day: str | None = Field(default=None, max_length=50)
    visit_day: str | None = Field(default=None, max_length=50)
    time_window: str | None = Field(default=None, max_length=50)
    instructions: str | None = Field(default=None, max_length=200)
    service_time_min: int | None = None
    demand_units: int | None = None
    demand_weight_kg: float | None = None
    agent_user_id: str | None = None
    fiscal_operation_document: str | None = Field(default=None, max_length=50)
    fiscal_operation_type: str | None = Field(default=None, max_length=30)
    gps_link: str | None = Field(default=None, max_length=200)
    is_active: bool | None = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str | None
    order_date: datetime
    customer_id: str | None
    customer_name: str
    movement_type: str
    document_series: str | None
    document_number: int | None
    warehouse_id: str | None
    carrier: str | None
    commitment_date: datetime | None
    time_window_start: datetime | None
    time_window_end: datetime | None
    status: str
    notes: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    product_id: str | None
    product_name: str
    reason: str | None
    condition: str | None
    quantity_requested: float
    quantity_planned: float
    status: int
    location: str | None
    description: str | None
    created_at: datetime


class OrderCreateRequest(BaseModel):
    branch_id: str | None = None
    customer_id: str
    movement_type: str = Field(min_length=1, max_length=50)
    document_series: str | None = Field(default=None, max_length=50)
    document_number: int | None = None
    warehouse_id: str | None = None
    carrier: str | None = Field(default=None, max_length=100)
    commitment_date: datetime | None = None
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    status: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class OrderUpdateRequest(BaseModel):
    customer_id: str | None = None
    warehouse_id: str | None = None
    carrier: str | None = Field(default=None, max_length=100)
    commitment_date: datetime | None = None
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    status: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class OrderItemCreateRequest(BaseModel):
    product_id: str | None = None
    product_name: str = Field(min_length=1, max_length=120)
    reason: str | None = Field(default=None, max_length=50)
    condition: str | None = Field(default=None, max_length=50)
    quantity_requested: float = 0
    quantity_planned: float = 0
    status: int = 0
    location: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)


class OrderItemUpdateRequest(BaseModel):
    product_name: str | None = Field(default=None, min_length=1, max_length=120)
    reason: str | None = Field(default=None, max_length=50)
    condition: str | None = Field(default=None, max_length=50)
    quantity_requested: float | None = None
    quantity_planned: float | None = None
    status: int | None = None
    location: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)


class RouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str | None
    route_date: date
    driver_id: str
    vehicle_id: str | None
    status: str
    gps_start_coordinates: dict[str, object] | None
    notes: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class RouteCreateRequest(BaseModel):
    branch_id: str | None = None
    route_date: date
    driver_id: str | None = None
    vehicle_id: str | None = None
    notes: str | None = None


class RouteUpdateRequest(BaseModel):
    route_date: date | None = None
    driver_id: str | None = None
    vehicle_id: str | None = None
    status: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class RouteStopRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    route_id: str
    delivery_point_id: str
    stop_order: int
    scheduled_time: time | None
    status: str
    arrival_time: datetime | None
    departure_time: datetime | None
    gps_coordinates: dict[str, object] | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class RouteStopCreateRequest(BaseModel):
    delivery_point_id: str
    stop_order: int
    scheduled_time: time | None = None
    notes: str | None = None


class RouteStopUpdateRequest(BaseModel):
    stop_order: int | None = None
    scheduled_time: time | None = None
    status: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class LoadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    route_id: str
    cylinder_id: str
    stop_id: str | None
    status: str
    loaded_at: datetime | None
    unloaded_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class LoadCreateRequest(BaseModel):
    route_id: str
    cylinder_id: str
    stop_id: str | None = None
    notes: str | None = None


class LoadBulkCreateRequest(BaseModel):
    route_id: str
    cylinder_ids: list[str]
    stop_id: str | None = None
    notes: str | None = None


class LoadConfirmRequest(BaseModel):
    route_id: str


class MovementTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    category: str
    moves_cylinders: bool
    origin_state: str | None
    target_state: str | None


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str | None
    movement_type: str
    document_series: str | None
    document_number: str | None
    full_document: str | None
    order_id: str | None
    route_id: str | None
    customer_id: str | None
    customer_name: str | None
    warehouse_id: str | None
    driver_id: str | None
    vehicle_id: str | None
    total: float | None
    tax: float | None
    discount: float | None
    currency: str
    exchange_rate: float
    status: str
    payment_status: str | None
    carrier: str | None
    plate: str | None
    destination_place: str | None
    destination_address: str | None
    dispatched_at: datetime | None
    notes: str | None
    parent_movement_id: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class MovementItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    movement_id: str
    cylinder_id: str | None
    product_id: str | None
    product_name: str | None
    quantity_in: float
    quantity_out: float
    quantity: int
    quantity_planned: float
    unit_price: float | None
    total_item: float | None
    discount: float
    item_status: str
    state_before: str | None
    state_after: str | None
    notes: str | None
    created_at: datetime


class MovementStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    movement_id: str
    field_name: str
    from_value: str | None
    to_value: str
    changed_by: str
    notes: str | None
    created_at: datetime


class MovementCreateRequest(BaseModel):
    branch_id: str | None = None
    movement_type: str = Field(min_length=1, max_length=50)
    document_series: str | None = Field(default=None, max_length=20)
    document_number: str | None = Field(default=None, max_length=50)
    order_id: str | None = None
    route_id: str | None = None
    customer_id: str | None = None
    warehouse_id: str | None = None
    driver_id: str | None = None
    vehicle_id: str | None = None
    total: float | None = None
    tax: float | None = None
    discount: float | None = None
    currency: str = Field(default="PEN", max_length=10)
    exchange_rate: float = 1
    payment_status: str | None = Field(default=None, max_length=50)
    carrier: str | None = Field(default=None, max_length=100)
    plate: str | None = Field(default=None, max_length=20)
    destination_place: str | None = Field(default=None, max_length=200)
    destination_address: str | None = Field(default=None, max_length=500)
    notes: str | None = None
    items: list[dict[str, object]] = Field(default_factory=list)


class MovementUpdateRequest(BaseModel):
    status: str | None = Field(default=None, max_length=50)
    payment_status: str | None = Field(default=None, max_length=50)
    notes: str | None = None
    carrier: str | None = Field(default=None, max_length=100)
    plate: str | None = Field(default=None, max_length=20)
    destination_place: str | None = Field(default=None, max_length=200)
    destination_address: str | None = Field(default=None, max_length=500)


class MovementItemCreateRequest(BaseModel):
    cylinder_id: str | None = None
    product_id: str | None = None
    product_name: str | None = Field(default=None, max_length=200)
    quantity_in: float = 0
    quantity_out: float = 0
    quantity: int = 1
    quantity_planned: float = 0
    unit_price: float | None = None
    total_item: float | None = None
    discount: float = 0
    item_status: str | None = Field(default=None, max_length=20)
    notes: str | None = None

    @field_validator("cylinder_id", mode="before")
    @classmethod
    def coerce_empty_string_to_none(cls, v: object) -> str | None:
        if v == "":
            return None
        return v


class MovementCancelRequest(BaseModel):
    reason: str = Field(min_length=1)


class AgendaTaskTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    description: str


class AgendaTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    route_id: str | None
    driver_id: str
    customer_id: str | None
    customer_name: str | None
    delivery_point_id: str | None
    task_type: str
    description: str | None
    scheduled_date: date
    scheduled_time: time | None
    status: str
    priority: int
    order_id: str | None
    quantity_requested: int | None
    quantity_served: int | None
    cylinder_serial: str | None
    customer_confirmed: bool
    requires_signature: bool
    evidence_url: str | None
    delivery_location: str | None
    gps_coordinates: dict[str, object]
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AgendaTaskCreateRequest(BaseModel):
    route_id: str | None = None
    driver_id: str | None = None
    customer_id: str
    delivery_point_id: str | None = None
    task_type: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    scheduled_date: date
    scheduled_time: time | None = None
    priority: int = 0
    order_id: str | None = None
    quantity_requested: int | None = None
    quantity_served: int | None = None
    cylinder_serial: str | None = Field(default=None, max_length=50)
    customer_confirmed: bool = False
    requires_signature: bool = False
    evidence_url: str | None = Field(default=None, max_length=300)
    delivery_location: str | None = Field(default=None, max_length=200)
    gps_coordinates: dict[str, object] = Field(default_factory=dict)


class AgendaTaskUpdateRequest(BaseModel):
    status: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    scheduled_time: time | None = None
    priority: int | None = None
    quantity_served: int | None = None
    customer_confirmed: bool | None = None
    evidence_url: str | None = Field(default=None, max_length=300)
    delivery_location: str | None = Field(default=None, max_length=200)
    gps_coordinates: dict[str, object] | None = None


class AgendaTaskBulkFromRouteRequest(BaseModel):
    route_id: str


class HydrostaticTestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cylinder_id: str
    test_date: date
    previous_test_date: date | None
    status: str | None
    movement_id: str | None
    modified_by: str | None
    notes: str | None
    created_at: datetime


class HydrostaticTestCreateRequest(BaseModel):
    test_date: date
    previous_test_date: date | None = None
    status: str | None = Field(default=None, max_length=50)
    movement_id: str | None = None
    modified_by: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class WarrantyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    cylinder_id: str
    customer_id: str | None
    customer_name: str
    warranty_type: str
    status: str
    description: str | None
    return_date: datetime | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class WarrantyCreateRequest(BaseModel):
    customer_id: str
    warranty_type: str = Field(min_length=1, max_length=50)
    status: str | None = Field(default=None, max_length=50)
    description: str | None = None
    return_date: datetime | None = None


class GasProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    code: str
    content_kg: float | None
    unit: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ServiceTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CylinderConditionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    is_active: bool
    created_at: datetime


class CylinderRetimbradoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cylinder_id: str
    retimbrado_date: date
    manufacture_code: str | None
    manufacture_year: int | None
    serial_number: str | None
    weight_origin: float | None
    weight_current: float | None
    service_pressure: float | None
    test_pressure: float | None
    approval_number: str | None
    danger_class: str | None
    marking1: str | None
    marking2: str | None
    package_format: str | None
    transport_code: int | None
    adr_label: str | None
    adr_tunnel: str | None
    un_number: str | None
    food_registry: str | None
    movement_id: str | None
    notes: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class CylinderRetimbradoCreateRequest(BaseModel):
    retimbrado_date: date
    manufacture_code: str | None = Field(default=None, max_length=50)
    manufacture_year: int | None = None
    serial_number: str | None = Field(default=None, max_length=50)
    weight_origin: float | None = None
    weight_current: float | None = None
    service_pressure: float | None = None
    test_pressure: float | None = None
    approval_number: str | None = Field(default=None, max_length=50)
    danger_class: str | None = Field(default=None, max_length=50)
    marking1: str | None = Field(default=None, max_length=50)
    marking2: str | None = Field(default=None, max_length=50)
    package_format: str | None = Field(default=None, max_length=50)
    transport_code: int | None = None
    adr_label: str | None = Field(default=None, max_length=50)
    adr_tunnel: str | None = Field(default=None, max_length=10)
    un_number: str | None = Field(default=None, max_length=10)
    food_registry: str | None = Field(default=None, max_length=50)
    movement_id: str | None = None
    notes: str | None = None


class CylinderOwnershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cylinder_id: str
    customer_id: str | None
    customer_name: str | None
    movement_id: str | None
    change_date: datetime
    condition: str | None
    notes: str | None
    created_by: str
    created_at: datetime


class CylinderLabelHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cylinder_id: str
    origin: str
    reason: str | None
    printer_name: str | None
    copies: int
    printed_by: str
    printed_at: datetime
    created_at: datetime


class PrintLabelRequest(BaseModel):
    origin: str = Field(min_length=1, max_length=50)
    reason: str | None = Field(default=None, max_length=200)
    printer_name: str | None = Field(default=None, max_length=150)
    copies: int = Field(default=1, ge=1, le=20)


class CylinderLabelDataRead(BaseModel):
    cylinder_id: str
    serial: str
    barcode2: str | None
    description: str | None
    brand_name: str | None
    gas_product_name: str | None
    manufacturer_code: str | None
    manufacture_year: int | None
    approval_number: str | None
    danger_class: str | None
    un_number: str | None
    last_hydrotest_date: date | None
    next_hydrotest_date: date | None
    adr_label: str | None
    adr_un_number: str | None
    label_origin: str | None


class ScanRequest(BaseModel):
    movement_id: str
    barcode_serial: str = Field(min_length=1, max_length=150)
    service_type: str = Field(min_length=1, max_length=20)
    gps_lat: float | None = None
    gps_lng: float | None = None


class ScanLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    movement_id: str
    cylinder_id: str | None
    barcode_scanned: str
    service_type: str
    user_id: str
    gps_lat: float | None
    gps_lng: float | None
    result: str
    error_reason: str | None
    adr_validated: bool
    hydrotest_validated: bool
    scanned_at: datetime
    created_at: datetime


class CylinderServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cylinder_id: str
    order_id: str | None
    order_item_id: str | None
    movement_id: str | None
    service_type_id: str
    status: str
    start_date: datetime | None
    end_date: datetime | None
    notes: str | None
    purchase_price: float | None
    sale_price: float | None
    stock_in: float | None
    stock_out: float | None
    group_code: str | None
    discount_pct: float | None
    discount_amount: float | None
    total_amount: float | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class CylinderServiceCreateRequest(BaseModel):
    order_id: str | None = None
    order_item_id: str | None = None
    movement_id: str | None = None
    service_type_id: str
    status: str | None = Field(default=None, max_length=50)
    start_date: datetime | None = None
    end_date: datetime | None = None
    notes: str | None = None
    purchase_price: float | None = None
    sale_price: float | None = None
    stock_in: float | None = None
    stock_out: float | None = None
    group_code: str | None = Field(default=None, max_length=50)
    discount_pct: float | None = None
    discount_amount: float | None = None
    total_amount: float | None = None


class CylinderServiceUpdateRequest(BaseModel):
    service_type_id: str | None = None
    status: str | None = Field(default=None, max_length=50)
    start_date: datetime | None = None
    end_date: datetime | None = None
    notes: str | None = None
    purchase_price: float | None = None
    sale_price: float | None = None
    stock_in: float | None = None
    stock_out: float | None = None
    group_code: str | None = Field(default=None, max_length=50)
    discount_pct: float | None = None
    discount_amount: float | None = None
    total_amount: float | None = None


class PlanningStockSummaryItem(BaseModel):
    product_id: str
    product_name: str
    warehouse_id: str
    stock_actual: float
    stock_comprometido: float
    stock_planificado: float
    stock_disponible: float
    coverage_status: str


class PlanningPendingOrderItemRead(BaseModel):
    order_item_id: str
    product_id: str | None
    product_name: str
    quantity_requested: float
    quantity_planned: float
    quantity_pending: float
    stock_disponible: float
    coverage_status: str


class PlanningPendingOrderRead(BaseModel):
    order_id: str
    customer_id: str | None
    customer_name: str
    warehouse_id: str | None
    status: str
    coverage_status: str
    items: list[PlanningPendingOrderItemRead]


class PlanningPlanOrderRequest(BaseModel):
    mode: str = Field(default="partial", pattern="^(all|full|partial)$")
    permit_without_stock: bool = False


class PlanningPlanOrderResult(BaseModel):
    order_id: str
    mode: str
    updated_items: list[OrderItemRead]


class PlanningStockSummaryRequest(BaseModel):
    warehouse_id: str
    product_ids: list[str] = Field(default_factory=list)


class PlanningGeneratePreloadRequest(BaseModel):
    warehouse_id: str
    preload_date: date
    order_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class PlanningPreloadItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    preload_id: str
    order_item_id: str
    product_id: str
    product_name: str | None
    quantity_planned: float
    quantity_loaded: float
    created_at: datetime


class PlanningPreloadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    warehouse_id: str
    branch_id: str | None
    preload_date: date
    status: str
    notes: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    items: list[PlanningPreloadItemRead] = Field(default_factory=list)


class PlanningPreloadActionResult(BaseModel):
    preload: PlanningPreloadRead
    movement: MovementRead | None = None


class ReceptionIncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    movement_id: str
    cylinder_id: str | None
    reason_code: str
    description: str | None
    created_by: str
    created_at: datetime


class ReceptionIncidentCreateRequest(BaseModel):
    cylinder_id: str | None = None
    reason_code: str = Field(min_length=1, max_length=50)
    description: str | None = None

    @field_validator("cylinder_id", mode="before")
    @classmethod
    def coerce_empty_string_to_none(cls, v: object) -> str | None:
        if v == "":
            return None
        return v


class ReceptionItemReceiveRequest(BaseModel):
    movement_item_id: str
    quantity_received: float = Field(ge=0)


class ReceptionReceiveRequest(BaseModel):
    items: list[ReceptionItemReceiveRequest] = Field(default_factory=list)
    notes: str | None = None


class ReceptionReceiveResult(BaseModel):
    movement: MovementRead
    incidents: list[ReceptionIncidentRead] = Field(default_factory=list)
    shortage_items: list[MovementItemRead] = Field(default_factory=list)


class IncidentReasonRead(BaseModel):
    code: str
    description: str
    target_state: str | None


class WaybillDetailItemRead(BaseModel):
    product_id: str | None
    product_name: str | None
    quantity: float
    unit_weight_kg: float | None
    total_weight_kg: float | None
    adr_points: float | None


class WaybillRead(BaseModel):
    movement_id: str
    movement_type: str
    document: str | None
    warehouse_id: str | None
    warehouse_name: str | None
    customer_id: str | None
    customer_name: str | None
    vehicle_id: str | None
    vehicle_plate: str | None
    driver_id: str | None
    destination_place: str | None
    destination_address: str | None
    items: list[WaybillDetailItemRead]
    total_packages: float
    total_weight_kg: float
    total_adr_points: float


class WaybillSummaryRead(BaseModel):
    movement_id: str
    total_packages: float
    total_weight_kg: float
    total_adr_points: float


class DispatchGuideAssignRequest(BaseModel):
    document_series: str = Field(min_length=1, max_length=20)


class DispatchVehicleReturnRequest(BaseModel):
    cylinder_ids: list[str] = Field(default_factory=list)
    notes: str | None = None


class EquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    equipment_type: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EquipmentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    equipment_type: str | None = Field(default=None, max_length=50)
    is_active: bool = True


class MovementEquipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    movement_id: str
    equipment_id: str
    assigned_at: datetime
    returned_at: datetime | None
    notes: str | None


class MovementEquipmentAssignRequest(BaseModel):
    equipment_id: str
    notes: str | None = None


class MovementEquipmentReturnRequest(BaseModel):
    notes: str | None = None


class VehicleRouteRestrictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    vehicle_id: str
    route_id: str
    restriction_type: str
    created_at: datetime


class VehicleRouteRestrictionUpsertRequest(BaseModel):
    restrictions: list[dict[str, str]] = Field(default_factory=list)


class DriverParameterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    driver_id: str
    param_key: str
    param_value: str | None
    updated_at: datetime


class DriverParametersUpsertRequest(BaseModel):
    parameters: dict[str, str | None] = Field(default_factory=dict)


class VehicleDeliveryPointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    vehicle_id: str
    delivery_point_id: str
    created_at: datetime


class VehicleDeliveryPointCreateRequest(BaseModel):
    delivery_point_id: str


class AgendaDailySummaryBucket(BaseModel):
    driver_id: str
    status: str
    total: int


class RouteWeekdayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    route_id: str
    weekday: int
    created_at: datetime


class RouteWeekdayUpdateRequest(BaseModel):
    weekdays: list[int] = Field(default_factory=list)


class LoadWeightSummaryRead(BaseModel):
    route_id: str
    weight_limit_kg: float
    total_weight_kg: float
    exceeds_limit: bool


class AdrProductConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    product_id: str
    adr_class: str | None
    adr_points: float | None
    adr_tunnel: str | None
    max_quantity: float | None
    valid_from: date
    valid_to: date | None
    created_at: datetime
    updated_at: datetime


class AdrProductConfigUpsertRequest(BaseModel):
    adr_class: str | None = Field(default=None, max_length=50)
    adr_points: float | None = None
    adr_tunnel: str | None = Field(default=None, max_length=10)
    max_quantity: float | None = None
    valid_from: date
    valid_to: date | None = None


class AdrIncompatibilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    product_id_1: str
    product_id_2: str
    created_at: datetime


class AdrIncompatibilityCreateRequest(BaseModel):
    product_id_1: str
    product_id_2: str


class AdrPointsItemRead(BaseModel):
    product_id: str | None
    product_name: str | None
    quantity: float
    adr_points_per_unit: float
    total_adr_points: float


class AdrPointsSummaryRead(BaseModel):
    movement_id: str
    total_adr_points: float
    items: list[AdrPointsItemRead]


class VehicleEligibilityRead(BaseModel):
    vehicle_id: str
    plate: str
    adr_class: str | None
    capacity_weight: float | None
    eligible: bool
    reason: str | None


class RouteGpsStartRequest(BaseModel):
    gps_coordinates: dict[str, object]


class RouteStopGpsRequest(BaseModel):
    gps_coordinates: dict[str, object]


class AgendaTaskGpsRequest(BaseModel):
    gps_coordinates: dict[str, object]


class CylinderWeightRead(BaseModel):
    cylinder_id: str
    serial: str
    product_id: str | None
    product_name: str | None
    tara_weight_kg: float | None
    current_weight_kg: float | None
    content_kg: float | None
    total_weight_kg: float | None


class ProductContentRead(BaseModel):
    product_id: str
    product_name: str
    content_kg: float | None


class RouteAgendaReportStopRead(BaseModel):
    stop_id: str
    stop_order: int
    customer_name: str | None
    address: str | None
    scheduled_time: time | None
    status: str


class RouteAgendaReportRead(BaseModel):
    route_id: str
    route_date: date
    driver_id: str
    vehicle_id: str | None
    stops: list[RouteAgendaReportStopRead]


class DispatchTicketRead(WaybillRead):
    pass


class TransferAlbaranRead(WaybillRead):
    pass


class LoadSummaryItemRead(BaseModel):
    cylinder_id: str
    serial: str | None
    state: str | None
    weight_kg: float | None


class LoadSummaryReportRead(BaseModel):
    route_id: str
    driver_id: str
    vehicle_id: str | None
    total_weight_kg: float
    items: list[LoadSummaryItemRead]
