from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from systutor.core.database import Base


def _new_uuid() -> str:
    return str(uuid4())


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ComSupplier(Base):
    __tablename__ = "com_suppliers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    commercial_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    document_type_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(5), nullable=True, default="PE")
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_term_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    billing_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    accounting_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fiscal_operation_key: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tax_regime_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )

    orders: Mapped[list[ComPurchaseOrder]] = relationship(back_populates="supplier")
    addresses: Mapped[list[ComSupplierAddress]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    contacts: Mapped[list[ComSupplierContact]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    bank_accounts: Mapped[list[ComSupplierBankAccount]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    payment_terms: Mapped[list[ComSupplierPaymentTerm]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )


class ComSupplierAddress(Base):
    __tablename__ = "com_supplier_addresses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    line1: Mapped[str] = mapped_column(String(200), nullable=False)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, default="PE")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    supplier: Mapped[ComSupplier] = relationship(back_populates="addresses")


class ComSupplierContact(Base):
    __tablename__ = "com_supplier_contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )

    supplier: Mapped[ComSupplier] = relationship(back_populates="contacts")


class ComSupplierBankAccount(Base):
    __tablename__ = "com_supplier_bank_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_holder: Mapped[str] = mapped_column(String(200), nullable=False)
    iban: Mapped[str] = mapped_column(String(34), nullable=False)
    bic_swift: Mapped[str | None] = mapped_column(String(11), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    supplier: Mapped[ComSupplier] = relationship(back_populates="bank_accounts")


class ComSupplierPaymentTerm(Base):
    __tablename__ = "com_supplier_payment_terms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    payment_term_code: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(250), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    supplier: Mapped[ComSupplier] = relationship(back_populates="payment_terms")


class ComPurchaseOrder(Base):
    __tablename__ = "com_purchase_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )

    items: Mapped[list[ComPurchaseItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    receipts: Mapped[list[ComPurchaseReceipt]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    supplier: Mapped[ComSupplier] = relationship(back_populates="orders")


class ComPurchaseItem(Base):
    __tablename__ = "com_purchase_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    received_qty: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    order: Mapped[ComPurchaseOrder] = relationship(back_populates="items")


class ComPurchaseReceipt(Base):
    __tablename__ = "com_purchase_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_orders.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    order: Mapped[ComPurchaseOrder] = relationship(back_populates="receipts")
