from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LogisticsRouteCalculation(Base):
    __tablename__ = "lg_route_calculations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    route_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_routes.id"), nullable=True, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=True, index=True
    )
    planning_reservation_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_planning_reservations.id"), nullable=True, index=True
    )
    provider_stack: Mapped[str] = mapped_column(String(50), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ordered_stop_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    totals_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    violations_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    polyline: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
