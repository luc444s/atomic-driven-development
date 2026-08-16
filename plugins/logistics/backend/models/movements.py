# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
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



# ── LogisticsMovement ────────────────────────────────────────

class LogisticsMovement(Base):
    __tablename__ = "lg_movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id"), nullable=True, index=True
    )
    movement_type: Mapped[str] = mapped_column(
        ForeignKey("lg_movement_types.code"), nullable=False, index=True
    )
    document_series: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    full_document: Mapped[str | None] = mapped_column(String(27), nullable=True)
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_orders.id"), nullable=True, index=True
    )
    route_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_routes.id"), nullable=True, index=True
    )
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=True, index=True
    )
    customer_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    warehouse_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=True, index=True
    )
    driver_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    vehicle_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicles.id"), nullable=True, index=True
    )
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
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_movement_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=True, index=True
    )
    origin_movement_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=True, index=True
    )
    last_stock_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )



# ── LogisticsMovementItem ────────────────────────────────────────

class LogisticsMovementItem(Base):
    __tablename__ = "lg_movement_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    movement_id: Mapped[str] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=False, index=True
    )
    cylinder_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=True, index=True
    )
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    product_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
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



# ── LogisticsMovementStatusHistory ────────────────────────────────────────

class LogisticsMovementStatusHistory(Base):
    __tablename__ = "lg_movement_status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    movement_id: Mapped[str] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    from_value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    to_value: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


