# ═══════════════════════════════════════════════════════════════════
# MODULO DESHABILITADO — Ver plugin.py para contexto completo.
# ═══════════════════════════════════════════════════════════════════
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


def _new_uuid() -> str:
    return str(uuid4())


def _utc_now() -> datetime:
    return datetime.now(UTC)


class QuoteDraft(Base):
    __tablename__ = "ventas_quote_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("crm_customers.id"), nullable=False, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT", index=True)
    delivery_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    delivery_time: Mapped[datetime | None] = mapped_column(Time, nullable=True)
    vehicle_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicles.id"), nullable=True, index=True
    )
    vehicle_plate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    updated_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now
    )


class QuoteItem(Base):
    __tablename__ = "ventas_quote_items"
    __table_args__ = (
        UniqueConstraint("quote_draft_id", "product_id", name="uq_quote_item_draft_product"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    quote_draft_id: Mapped[str] = mapped_column(
        ForeignKey("ventas_quote_drafts.id"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(ForeignKey("prod_products.id"), nullable=False, index=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
