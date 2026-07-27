from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class StockLedger(Base):
    __tablename__ = "stk_ledger"
    __table_args__ = (
        CheckConstraint(
            "operation IN ('initial','adjust','transfer_in','transfer_out',"
            "'reserve','release','sale_out','purchase_in','return_in','damage_out',"
            "'production_in','production_out')",
            name="ck_stk_ledger_operation",
        ),
        UniqueConstraint(
            "tenant_id",
            "reference_type",
            "reference_id",
            "operation",
            "warehouse_id",
            name="uq_stk_ledger_idempotency",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=False, index=True
    )
    operation: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    total_cost: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    cost_after: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)
    source: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )


class StockBalance(Base):
    __tablename__ = "stk_balance"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "product_id",
            "warehouse_id",
            name="uq_stk_balance_tenant_product_warehouse",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    reserved_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    total_cost: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    allow_negative_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    updated_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)


class StockConfig(Base):
    __tablename__ = "stk_config"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "product_id",
            "warehouse_id",
            name="uq_stk_config_tenant_product_warehouse",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=False, index=True
    )
    min_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    max_quantity: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    allow_negative_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    updated_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)


class StockAllocation(Base):
    __tablename__ = "stk_allocation"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_stk_allocation_quantity_positive"),
        CheckConstraint(
            "remaining_quantity >= 0 AND remaining_quantity <= quantity",
            name="ck_stk_allocation_remaining_range",
        ),
        CheckConstraint(
            "status IN ('active','partially_consumed','consumed','released','expired')",
            name="ck_stk_allocation_status",
        ),
        UniqueConstraint(
            "tenant_id",
            "reference_type",
            "reference_id",
            "product_id",
            "warehouse_id",
            name="uq_stk_allocation_ref",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    allocation_group_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    remaining_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    release_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
