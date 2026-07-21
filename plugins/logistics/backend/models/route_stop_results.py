from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LogisticsRouteStopResult(Base):
    __tablename__ = "lg_route_stop_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=False, index=True
    )
    route_stop_id: Mapped[str] = mapped_column(
        ForeignKey("lg_route_stops.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    completion_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    outcome_type: Mapped[str] = mapped_column(String(40), nullable=False, default="NORMAL")
    driver_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    updated_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
