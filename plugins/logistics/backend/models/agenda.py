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
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)



# ── LogisticsRouteWeekday ────────────────────────────────────────

class LogisticsRouteWeekday(Base):
    __tablename__ = "lg_route_weekdays"
    __table_args__ = (UniqueConstraint("route_id", "weekday", name="uq_lg_route_weekday"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    route_id: Mapped[str] = mapped_column(ForeignKey("lg_routes.id"), nullable=False, index=True)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)



# ── LogisticsAgendaTask ────────────────────────────────────────

class LogisticsAgendaTask(Base):
    __tablename__ = "lg_agenda_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    route_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_routes.id"), nullable=True, index=True
    )
    driver_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
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
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_orders.id"), nullable=True, index=True
    )
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


