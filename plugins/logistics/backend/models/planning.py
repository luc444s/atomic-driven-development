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
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)



# ── LogisticsPlanningReservation ────────────────────────────────────────

class LogisticsPlanningReservation(Base):
    __tablename__ = "lg_planning_reservations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id"), nullable=True, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(ForeignKey("lg_vehicles.id"), nullable=False, index=True)
    origin_warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=False, index=True
    )
    planned_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    planned_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_load_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    expected_weight_total: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    expected_volume_total: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    service_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    route_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_routes.id"), nullable=True, index=True
    )
    driver_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    adr_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    quote_id: Mapped[str | None] = mapped_column(
        ForeignKey("ventas_quote_drafts.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PLANNED", index=True)
    conflict_reason: Mapped[str | None] = mapped_column(String(40), nullable=True)
    permit_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    customer_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    address_ids_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    linked_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=True, index=True
    )
    actual_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_load_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    updated_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )



# ── LogisticsPlanPreload ────────────────────────────────────────

class LogisticsPlanPreload(Base):
    __tablename__ = "lg_plan_preloads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=False, index=True
    )
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id"), nullable=True, index=True
    )
    preload_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE", index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )



# ── LogisticsPlanPreloadItem ────────────────────────────────────────

class LogisticsPlanPreloadItem(Base):
    __tablename__ = "lg_plan_preload_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    preload_id: Mapped[str] = mapped_column(
        ForeignKey("lg_plan_preloads.id"), nullable=False, index=True
    )
    order_item_id: Mapped[str] = mapped_column(
        ForeignKey("lg_order_items.id"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    product_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quantity_planned: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    quantity_loaded: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)



# ── LogisticsReceptionIncident ────────────────────────────────────────

class LogisticsReceptionIncident(Base):
    __tablename__ = "lg_reception_incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    movement_id: Mapped[str] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=False, index=True
    )
    cylinder_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=True, index=True
    )
    reason_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

