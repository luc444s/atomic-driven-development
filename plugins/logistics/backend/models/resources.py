# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


# ── LogisticsWarehouse ────────────────────────────────────────


class LogisticsWarehouse(Base):
    __tablename__ = "lg_warehouses"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_lg_warehouse_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    warehouse_type: Mapped[str] = mapped_column(String(20), nullable=False, default="FIXED")
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    formatted_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    place_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geocode_source: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


# ── LogisticsZone ────────────────────────────────────────


class LogisticsZone(Base):
    __tablename__ = "lg_zones"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_lg_zone_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ── LogisticsVehicle ────────────────────────────────────────


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
    mobile_warehouse_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


# ── LogisticsDeliveryPoint ────────────────────────────────────────


class LogisticsDeliveryPoint(Base):
    __tablename__ = "lg_delivery_points"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
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
    agent_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    fiscal_operation_document: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fiscal_operation_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    gps_link: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gps_coordinates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


# ── LogisticsVehicleDeliveryPoint ────────────────────────────────────────


class LogisticsVehicleDeliveryPoint(Base):
    __tablename__ = "lg_vehicle_delivery_points"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "vehicle_id",
            "delivery_point_id",
            name="uq_lg_vehicle_delivery_point",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicles.id"), nullable=False, index=True
    )
    delivery_point_id: Mapped[str] = mapped_column(
        ForeignKey("lg_delivery_points.id"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
