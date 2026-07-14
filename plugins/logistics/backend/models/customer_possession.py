from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LogisticsCustomerCylinderLedger(Base):
    __tablename__ = "lg_customer_cylinder_ledger"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_type",
            "source_id",
            "event_type",
            name="uq_lg_customer_cylinder_ledger_source_event",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
    contract_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_cylinder_contracts.id"), nullable=True, index=True
    )
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    product_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    condition: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False)
    cylinder_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=True, index=True
    )
    trace_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="AGGREGATE")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
