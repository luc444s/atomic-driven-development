# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)



# ── LogisticsEquipment ────────────────────────────────────────

class LogisticsEquipment(Base):
    __tablename__ = "lg_equipment"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_lg_equipment_tenant_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    equipment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )



# ── LogisticsMovementEquipment ────────────────────────────────────────

class LogisticsMovementEquipment(Base):
    __tablename__ = "lg_movement_equipment"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    movement_id: Mapped[str] = mapped_column(
        ForeignKey("lg_movements.id"), nullable=False, index=True
    )
    equipment_id: Mapped[str] = mapped_column(
        ForeignKey("lg_equipment.id"), nullable=False, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)



# ── LogisticsVehicleRouteRestriction ────────────────────────────────────────

class LogisticsVehicleRouteRestriction(Base):
    __tablename__ = "lg_vehicle_route_restrictions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "vehicle_id",
            "route_id",
            name="uq_lg_vehicle_route_restriction",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    vehicle_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicles.id"), nullable=False, index=True
    )
    route_id: Mapped[str] = mapped_column(ForeignKey("lg_routes.id"), nullable=False, index=True)
    restriction_type: Mapped[str] = mapped_column(String(10), nullable=False, default="ALLOW")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)



# ── LogisticsDriverParameter ────────────────────────────────────────

class LogisticsDriverParameter(Base):
    __tablename__ = "lg_driver_parameters"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "driver_id",
            "param_key",
            name="uq_lg_driver_parameter_key",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    driver_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    param_key: Mapped[str] = mapped_column(String(100), nullable=False)
    param_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


