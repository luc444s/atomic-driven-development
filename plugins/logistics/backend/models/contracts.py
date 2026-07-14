# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LogisticsCylinderContract(Base):
    __tablename__ = "lg_cylinder_contracts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(ForeignKey("branches.id"), nullable=True)
    warehouse_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_warehouses.id"), nullable=True, index=True
    )

    contract_number: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )
    document_type_code: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    document_prefix: Mapped[str] = mapped_column(String(5), nullable=False, default="CT")
    series: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    contract_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")

    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
    customer_snapshot: Mapped[dict[str, str | None] | None] = mapped_column(JSON, nullable=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    cylinder_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_products.id"), nullable=True
    )
    cylinder_condition: Mapped[str | None] = mapped_column(
        ForeignKey("prod_conditions.code"), nullable=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)

    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    signed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    signature_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    signed_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    contract_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    termination_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class LogisticsCylinderContractHistory(Base):
    __tablename__ = "lg_cylinder_contract_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    contract_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinder_contracts.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True)


class LogisticsContractType(Base):
    __tablename__ = "lg_contract_types"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    duration_unit: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_value: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
