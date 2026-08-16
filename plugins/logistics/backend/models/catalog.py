# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)



# ── Marcas y productos gas → migrados a productos plugin (prod_brands, prod_products)
# ── BRIDGE: usar product_bridge.py para resolver nombres



# ── LogisticsMovementType ────────────────────────────────────────

class LogisticsMovementType(Base):
    __tablename__ = "lg_movement_types"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    moves_cylinders: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    origin_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_state: Mapped[str | None] = mapped_column(String(50), nullable=True)



# ── LogisticsAgendaTaskType ────────────────────────────────────────

class LogisticsAgendaTaskType(Base):
    __tablename__ = "lg_agenda_task_types"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)



# ── LogisticsServiceType ────────────────────────────────────────

class LogisticsServiceType(Base):
    __tablename__ = "lg_service_types"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_lg_service_type_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


