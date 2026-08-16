from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
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


class LogisticsStockBridgeLog(Base):
    __tablename__ = "lg_stock_bridge_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    movement_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(20), nullable=False)
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    quantity: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
