# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)



# ── LogisticsAdrProductConfig ────────────────────────────────────────

class LogisticsAdrProductConfig(Base):
    __tablename__ = "lg_adr_product_config"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "product_id",
            "valid_from",
            name="uq_lg_adr_product_config_from",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    adr_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    adr_points: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    adr_tunnel: Mapped[str | None] = mapped_column(String(10), nullable=True)
    max_quantity: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )



# ── LogisticsAdrIncompatibility ────────────────────────────────────────

class LogisticsAdrIncompatibility(Base):
    __tablename__ = "lg_adr_incompatibilities"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "product_id_1",
            "product_id_2",
            name="uq_lg_adr_incompatibility_pair",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id_1: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    product_id_2: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


