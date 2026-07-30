from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LogisticsVehicleLocationEvent(Base):
    __tablename__ = "lg_vehicle_location_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(
        ForeignKey("branches.id"), nullable=True, index=True
    )
    session_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=False, index=True
    )
    route_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_routes.id"), nullable=True, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicles.id"), nullable=False, index=True
    )
    driver_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    speed: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    heading: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    accuracy_meters: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )


class LogisticsRouteControlState(Base):
    __tablename__ = "lg_route_control_states"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), primary_key=True
    )
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    route_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_routes.id"), nullable=True, index=True
    )
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicles.id"), nullable=False, index=True
    )
    active_stop_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_route_stops.id"), nullable=True, index=True
    )
    active_stop_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    current_stop_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_route_stops.id"), nullable=True, index=True
    )
    current_stop_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    last_lat: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    last_lng: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    last_speed: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    last_heading: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    last_recorded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_stops: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_stops: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    progress_percent: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    off_route: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    next_stop_eta_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geofence_state: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
