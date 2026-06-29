# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LogisticsCylinderState(Base):
    __tablename__ = "lg_cylinder_states"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class LogisticsStateTransition(Base):
    __tablename__ = "lg_state_transitions"
    __table_args__ = (
        UniqueConstraint("from_state", "to_state", name="uq_lg_state_transition_from_to"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    from_state: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinder_states.code"), nullable=False, index=True
    )
    to_state: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinder_states.code"), nullable=False, index=True
    )
    requires_adr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_hydrotest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class LogisticsCylinder(Base):
    __tablename__ = "lg_cylinders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "serial", name="uq_lg_cylinder_tenant_serial"),
        UniqueConstraint("tenant_id", "barcode1", name="uq_lg_cylinder_tenant_barcode1"),
        UniqueConstraint("tenant_id", "barcode2", name="uq_lg_cylinder_tenant_barcode2"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), nullable=True, index=True)
    serial: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    barcode1: Mapped[str | None] = mapped_column(String(150), nullable=True)
    barcode2: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_state: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinder_states.code"), nullable=False, default="CREADO_VACIO", index=True
    )
    gas_group_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_gas_products.id"), nullable=True, index=True
    )
    content_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    volume_m3: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    condition: Mapped[str | None] = mapped_column(
        ForeignKey("lg_cylinder_conditions.code"), nullable=True, index=True
    )
    brand_id: Mapped[str | None] = mapped_column(ForeignKey("lg_brands.id"), nullable=True, index=True)
    cost: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    box_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_service: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manufacturer_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    manufacturer_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    manufacture_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_origin: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    weight_current: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    last_hydrotest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_hydrotest_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    adr_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adr_un_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    adr_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adr_package_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adr_weight_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    adr_merchandise: Mapped[str | None] = mapped_column(String(200), nullable=True)
    adr_tunnel: Mapped[str | None] = mapped_column(String(10), nullable=True)
    adr_subline: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adr_factor: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    adr_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adr_unit_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsCylinderStateLog(Base):
    __tablename__ = "lg_cylinder_state_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    from_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_state: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    movement_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)


class LogisticsGasProduct(Base):
    __tablename__ = "lg_gas_products"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_lg_gas_product_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    content_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsBrand(Base):
    __tablename__ = "lg_brands"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_lg_brand_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsCylinderCondition(Base):
    __tablename__ = "lg_cylinder_conditions"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogisticsWarehouse(Base):
    __tablename__ = "lg_warehouses"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_lg_warehouse_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsZone(Base):
    __tablename__ = "lg_zones"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_lg_zone_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogisticsVehicle(Base):
    __tablename__ = "lg_vehicles"
    __table_args__ = (UniqueConstraint("tenant_id", "plate", name="uq_lg_vehicle_tenant_plate"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    plate: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    capacity_weight: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    capacity_volume: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    useful_load: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    adr_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DISPONIBLE")
    warehouse_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsDeliveryPoint(Base):
    __tablename__ = "lg_delivery_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("crm_customers.id"), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    zone_id: Mapped[str | None] = mapped_column(ForeignKey("lg_zones.id"), nullable=True, index=True)
    warehouse_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=True, index=True
    )
    address_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    delivery_day: Mapped[str | None] = mapped_column(String(50), nullable=True)
    visit_day: Mapped[str | None] = mapped_column(String(50), nullable=True)
    time_window: Mapped[str | None] = mapped_column(String(50), nullable=True)
    instructions: Mapped[str | None] = mapped_column(String(200), nullable=True)
    service_time_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    demand_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    demand_weight_kg: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    agent_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    fiscal_operation_document: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fiscal_operation_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    gps_link: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsOrder(Base):
    __tablename__ = "lg_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), nullable=True, index=True)
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    customer_id: Mapped[str] = mapped_column(ForeignKey("crm_customers.id"), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_series: Mapped[str | None] = mapped_column(String(50), nullable=True)
    document_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warehouse_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=True, index=True
    )
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commitment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_window_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsOrderItem(Base):
    __tablename__ = "lg_order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    order_id: Mapped[str] = mapped_column(ForeignKey("lg_orders.id"), nullable=False, index=True)
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    product_name: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quantity_requested: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    quantity_planned: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    location: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogisticsRoute(Base):
    __tablename__ = "lg_routes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), nullable=True, index=True)
    route_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    driver_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("lg_vehicles.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PLANIFICADO")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsRouteStop(Base):
    __tablename__ = "lg_route_stops"
    __table_args__ = (UniqueConstraint("route_id", "stop_order", name="uq_lg_route_stop_order"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    route_id: Mapped[str] = mapped_column(ForeignKey("lg_routes.id"), nullable=False, index=True)
    delivery_point_id: Mapped[str] = mapped_column(
        ForeignKey("lg_delivery_points.id"), nullable=False, index=True
    )
    stop_order: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    arrival_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    departure_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsLoad(Base):
    __tablename__ = "lg_loads"
    __table_args__ = (UniqueConstraint("route_id", "cylinder_id", name="uq_lg_load_route_cylinder"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    route_id: Mapped[str] = mapped_column(ForeignKey("lg_routes.id"), nullable=False, index=True)
    cylinder_id: Mapped[str] = mapped_column(ForeignKey("lg_cylinders.id"), nullable=False, index=True)
    stop_id: Mapped[str | None] = mapped_column(ForeignKey("lg_route_stops.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ASIGNADO")
    loaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsMovementType(Base):
    __tablename__ = "lg_movement_types"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    moves_cylinders: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    origin_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_state: Mapped[str | None] = mapped_column(String(50), nullable=True)


class LogisticsMovement(Base):
    __tablename__ = "lg_movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), nullable=True, index=True)
    movement_type: Mapped[str] = mapped_column(
        ForeignKey("lg_movement_types.code"), nullable=False, index=True
    )
    document_series: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    full_document: Mapped[str | None] = mapped_column(String(27), nullable=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("lg_orders.id"), nullable=True, index=True)
    route_id: Mapped[str | None] = mapped_column(ForeignKey("lg_routes.id"), nullable=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("crm_customers.id"), nullable=True, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    warehouse_id: Mapped[str | None] = mapped_column(ForeignKey("lg_warehouses.id"), nullable=True, index=True)
    driver_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    vehicle_id: Mapped[str | None] = mapped_column(ForeignKey("lg_vehicles.id"), nullable=True, index=True)
    total: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    tax: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    discount: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PEN")
    exchange_rate: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    payment_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    plate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    destination_place: Mapped[str | None] = mapped_column(String(200), nullable=True)
    destination_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_movement_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=True, index=True
    )
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsMovementItem(Base):
    __tablename__ = "lg_movement_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    movement_id: Mapped[str] = mapped_column(ForeignKey("lg_movements.id"), nullable=False, index=True)
    cylinder_id: Mapped[str] = mapped_column(ForeignKey("lg_cylinders.id"), nullable=False, index=True)
    quantity_in: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    quantity_out: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_planned: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    unit_price: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    total_item: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    discount: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    item_status: Mapped[str] = mapped_column(String(20), nullable=False, default="R")
    state_before: Mapped[str | None] = mapped_column(String(50), nullable=True)
    state_after: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogisticsMovementStatusHistory(Base):
    __tablename__ = "lg_movement_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    movement_id: Mapped[str] = mapped_column(ForeignKey("lg_movements.id"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    from_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_value: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogisticsAgendaTaskType(Base):
    __tablename__ = "lg_agenda_task_types"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)


class LogisticsAgendaTask(Base):
    __tablename__ = "lg_agenda_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    route_id: Mapped[str | None] = mapped_column(ForeignKey("lg_routes.id"), nullable=True, index=True)
    driver_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("crm_customers.id"), nullable=False, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    delivery_point_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_delivery_points.id"), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(ForeignKey("lg_agenda_task_types.code"), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    scheduled_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PROGRAMADO")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("lg_orders.id"), nullable=True, index=True)
    quantity_requested: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity_served: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cylinder_serial: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_signature: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    evidence_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    delivery_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gps_coordinates: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsHydrostaticTest(Base):
    __tablename__ = "lg_hydrostatic_tests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(ForeignKey("lg_cylinders.id"), nullable=False, index=True)
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    previous_test_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    movement_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    modified_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogisticsCylinderWarranty(Base):
    __tablename__ = "lg_cylinder_warranties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    cylinder_id: Mapped[str] = mapped_column(ForeignKey("lg_cylinders.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("crm_customers.id"), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    warranty_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="INGRESO")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    return_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsCylinderRetimbrado(Base):
    __tablename__ = "lg_cylinder_retimbrados"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(ForeignKey("lg_cylinders.id"), nullable=False, index=True)
    retimbrado_date: Mapped[date] = mapped_column(Date, nullable=False)
    manufacture_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    manufacture_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    weight_origin: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    weight_current: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    service_pressure: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    test_pressure: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    approval_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    danger_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    marking1: Mapped[str | None] = mapped_column(String(50), nullable=True)
    marking2: Mapped[str | None] = mapped_column(String(50), nullable=True)
    package_format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transport_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adr_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adr_tunnel: Mapped[str | None] = mapped_column(String(10), nullable=True)
    un_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    food_registry: Mapped[str | None] = mapped_column(String(50), nullable=True)
    movement_id: Mapped[str | None] = mapped_column(ForeignKey("lg_movements.id"), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsCylinderOwnership(Base):
    __tablename__ = "lg_cylinder_ownership"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(ForeignKey("lg_cylinders.id"), nullable=False, index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("crm_customers.id"), nullable=True, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    movement_id: Mapped[str | None] = mapped_column(ForeignKey("lg_movements.id"), nullable=True, index=True)
    change_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogisticsCylinderLabelHistory(Base):
    __tablename__ = "lg_cylinder_label_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(ForeignKey("lg_cylinders.id"), nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    printer_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    copies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    printed_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    printed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogisticsScanLog(Base):
    __tablename__ = "lg_scan_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    movement_id: Mapped[str] = mapped_column(ForeignKey("lg_movements.id"), nullable=False, index=True)
    cylinder_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=True, index=True
    )
    barcode_scanned: Mapped[str] = mapped_column(String(150), nullable=False)
    service_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    gps_lat: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    gps_lng: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    adr_validated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hydrotest_validated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    scanned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class LogisticsServiceType(Base):
    __tablename__ = "lg_service_types"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_lg_service_type_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsCylinderService(Base):
    __tablename__ = "lg_cylinder_services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(ForeignKey("lg_cylinders.id"), nullable=False, index=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("lg_orders.id"), nullable=True, index=True)
    order_item_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_order_items.id"), nullable=True, index=True
    )
    movement_id: Mapped[str | None] = mapped_column(ForeignKey("lg_movements.id"), nullable=True, index=True)
    service_type_id: Mapped[str] = mapped_column(ForeignKey("lg_service_types.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchase_price: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    sale_price: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    stock_in: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    stock_out: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    group_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    discount_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    discount_amount: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    total_amount: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
