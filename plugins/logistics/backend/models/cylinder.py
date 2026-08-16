# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, date, datetime
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)



# ── LogisticsCylinderState ────────────────────────────────────────

class LogisticsCylinderState(Base):
    __tablename__ = "lg_cylinder_states"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)



# ── LogisticsStateTransition ────────────────────────────────────────

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



# ── LogisticsCylinder ────────────────────────────────────────

class LogisticsCylinder(Base):
    __tablename__ = "lg_cylinders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "serial", name="uq_lg_cylinder_tenant_serial"),
        UniqueConstraint("tenant_id", "barcode1", name="uq_lg_cylinder_tenant_barcode1"),
        UniqueConstraint("tenant_id", "barcode2", name="uq_lg_cylinder_tenant_barcode2"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id"), nullable=True, index=True
    )
    serial: Mapped[str] = mapped_column(String(50), nullable=False)
    container_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CYLINDER", index=True
    )
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    barcode1: Mapped[str | None] = mapped_column(String(150), nullable=True)
    barcode2: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_state: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinder_states.code"), nullable=False, default="CREADO_VACIO", index=True
    )
    gas_group_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_products.id"), nullable=True, index=True
    )
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    content_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    volume_m3: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    condition: Mapped[str | None] = mapped_column(
        ForeignKey("prod_conditions.code"), nullable=True, index=True
    )
    brand_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_brands.id"), nullable=True, index=True
    )
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
    is_medical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    medical_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )



# ── LogisticsCylinderStateLog ────────────────────────────────────────

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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )



# ── Condiciones de cilindro → migradas a productos (prod_conditions)
# ── BRIDGE: usar product_bridge.resolve_condition()

# ── LogisticsHydrostaticTest ────────────────────────────────────────

class LogisticsHydrostaticTest(Base):
    __tablename__ = "lg_hydrostatic_tests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    test_date: Mapped[date] = mapped_column(Date, nullable=False)
    previous_test_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    movement_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    modified_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)



# ── LogisticsCylinderWarranty ────────────────────────────────────────

class LogisticsCylinderWarranty(Base):
    __tablename__ = "lg_cylinder_warranties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
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



# ── LogisticsCylinderRetimbrado ────────────────────────────────────────

class LogisticsCylinderRetimbrado(Base):
    __tablename__ = "lg_cylinder_retimbrados"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
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
    movement_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )



# ── LogisticsCylinderOwnership ────────────────────────────────────────

class LogisticsCylinderOwnership(Base):
    __tablename__ = "lg_cylinder_ownership"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=True, index=True
    )
    customer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    movement_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=True, index=True
    )
    change_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)



# ── LogisticsCylinderLabelHistory ────────────────────────────────────────

class LogisticsCylinderLabelHistory(Base):
    __tablename__ = "lg_cylinder_label_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    origin: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    printer_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    copies: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    printed_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    printed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)



# ── LogisticsScanLog ────────────────────────────────────────

class LogisticsScanLog(Base):
    __tablename__ = "lg_scan_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    movement_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=True, index=True
    )
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
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)



# ── LogisticsCylinderService ────────────────────────────────────────

class LogisticsCylinderService(Base):
    __tablename__ = "lg_cylinder_services"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_orders.id"), nullable=True, index=True
    )
    order_item_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_order_items.id"), nullable=True, index=True
    )
    movement_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=True, index=True
    )
    service_type_id: Mapped[str] = mapped_column(
        ForeignKey("lg_service_types.id"), nullable=False, index=True
    )
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
