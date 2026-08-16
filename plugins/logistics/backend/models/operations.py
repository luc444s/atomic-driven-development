# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import uuid4

from sqlalchemy import (
    JSON,
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
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)



# ── LogisticsOrder ────────────────────────────────────────

class LogisticsOrder(Base):
    __tablename__ = "lg_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id"), nullable=True, index=True
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
    customer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    document_series: Mapped[str | None] = mapped_column(String(50), nullable=True)
    document_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warehouse_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=True, index=True
    )
    carrier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commitment_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_window_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    time_window_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )



# ── LogisticsOrderItem ────────────────────────────────────────

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



# ── LogisticsRoute ────────────────────────────────────────

class LogisticsRoute(Base):
    __tablename__ = "lg_routes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id"), nullable=True, index=True
    )
    route_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    driver_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicles.id"), nullable=True, index=True
    )
    origin_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    destination_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PLANIFICADO")
    gps_start_coordinates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )



# ── LogisticsRouteStop ────────────────────────────────────────

class LogisticsRouteStop(Base):
    __tablename__ = "lg_route_stops"
    __table_args__ = (UniqueConstraint("route_id", "stop_order", name="uq_lg_route_stop_order"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    route_id: Mapped[str] = mapped_column(ForeignKey("lg_routes.id"), nullable=False, index=True)
    delivery_point_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_delivery_points.id"), nullable=True, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=True, index=True
    )
    customer_name_snapshot: Mapped[str | None] = mapped_column(String(120), nullable=True)
    stop_order: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    arrival_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    departure_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    gps_coordinates: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class LogisticsCylinderEvent(Base):
    __tablename__ = "lg_cylinder_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    location_type: Mapped[str] = mapped_column(String(20), nullable=False)
    location_id: Mapped[str] = mapped_column(String(36), nullable=False)
    warehouse_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=True, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=True, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=True, index=True
    )
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)


# ── LogisticsLoad ────────────────────────────────────────

class LogisticsLoad(Base):
    __tablename__ = "lg_loads"
    __table_args__ = (
        UniqueConstraint("route_id", "cylinder_id", name="uq_lg_load_route_cylinder"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    route_id: Mapped[str] = mapped_column(ForeignKey("lg_routes.id"), nullable=False, index=True)
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    stop_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_route_stops.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ASIGNADO")
    loaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

