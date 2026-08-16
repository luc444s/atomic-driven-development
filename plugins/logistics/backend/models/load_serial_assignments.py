from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LogisticsLoadSerialAssignment(Base):
    __tablename__ = "lg_load_serial_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    cylinder_serial: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    assignment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="SELECTED", index=True
    )
    selected_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    selected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    confirmed_by_operation_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_logistics_operations.id"), nullable=True, index=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    release_reason: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
