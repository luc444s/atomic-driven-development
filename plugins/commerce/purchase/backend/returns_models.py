from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from systutor.core.database import Base


def _new_uuid() -> str:
    return str(uuid4())


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ComMerchandiseReturn(Base):
    __tablename__ = "com_merchandise_returns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_orders.id"), nullable=False, index=True
    )
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    receipt_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_receipts.id"), nullable=False, index=True
    )
    claim_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_supplier_claims.id"), nullable=True, index=True
    )
    return_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="REGISTRADA")
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    resolved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    lines: Mapped[list[ComMerchandiseReturnLine]] = relationship(
        back_populates="return_record", cascade="all, delete-orphan"
    )
    events: Mapped[list[ComMerchandiseReturnEvent]] = relationship(
        back_populates="return_record", cascade="all, delete-orphan"
    )


class ComMerchandiseReturnLine(Base):
    __tablename__ = "com_merchandise_return_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    return_id: Mapped[str] = mapped_column(
        ForeignKey("com_merchandise_returns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_item_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_purchase_items.id"), nullable=True, index=True
    )
    product_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_products.id"), nullable=True, index=True
    )
    cylinder_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=True, index=True
    )
    serial: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qty: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    return_record: Mapped[ComMerchandiseReturn] = relationship(back_populates="lines")


class ComMerchandiseReturnEvent(Base):
    __tablename__ = "com_merchandise_return_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    return_id: Mapped[str] = mapped_column(
        ForeignKey("com_merchandise_returns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    return_record: Mapped[ComMerchandiseReturn] = relationship(back_populates="events")
