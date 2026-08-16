from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LogisticsRouteOperation(Base):
    __tablename__ = "lg_route_operations"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "idempotency_key",
            name="uq_lg_route_operation_session_idempotency",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=False, index=True
    )
    route_stop_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_route_stops.id"), nullable=True, index=True
    )
    operation_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    context_type: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=True, index=True
    )
    customer_name_snapshot: Mapped[str | None] = mapped_column(String(120), nullable=True)
    warehouse_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=True, index=True
    )
    warehouse_name_snapshot: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT", index=True)
    movement_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    location_event_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicle_location_events.id"), nullable=True, index=True
    )
    location_lat: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    performed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )


class LogisticsRouteOperationItem(Base):
    __tablename__ = "lg_route_operation_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    route_operation_id: Mapped[str] = mapped_column(
        ForeignKey("lg_route_operations.id"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
