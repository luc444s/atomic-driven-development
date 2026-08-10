from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class CrmDocumentType(Base):
    __tablename__ = "crm_document_types"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_person: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_company: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validation_pattern: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CrmPaymentTerm(Base):
    __tablename__ = "crm_payment_terms"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    operation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="CONTADO")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CrmGeography(Base):
    __tablename__ = "crm_geography"
    __table_args__ = (
        UniqueConstraint(
            "country_code", "level", "code", name="uq_crm_geography_country_level_code"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("crm_geography.id"), nullable=True, index=True
    )
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, index=True)
    ubigeo_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CrmCustomer(Base):
    __tablename__ = "crm_customers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "document_type_code",
            "document_number",
            name="uq_crm_customer_tenant_document",
        ),
        UniqueConstraint("tenant_id", "external_code", name="uq_crm_customer_tenant_external_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    external_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    legal_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    commercial_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_type_code: Mapped[str] = mapped_column(
        ForeignKey("crm_document_types.code"), nullable=False, index=True
    )
    document_number: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, default="PE")
    email: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fiscal_address_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    economic_activity_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    economic_activity_description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    activity_validated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activity_validation_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activity_validation_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_term_code: Mapped[str | None] = mapped_column(
        ForeignKey("crm_payment_terms.code"), nullable=True, index=True
    )
    billing_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_exempt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    accounting_code: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    is_intracommunity: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fiscal_operation_key: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tax_regime_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    equivalence_surcharge_applicable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    cash_criterion_applicable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    addresses: Mapped[list[CrmCustomerAddress]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    contacts: Mapped[list[CrmCustomerContact]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    commercial_assignments: Mapped[list[CrmCustomerCommercialAssignment]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    bank_accounts: Mapped[list[CrmCustomerBankAccount]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    pricing_terms: Mapped[list[CrmCustomerPricingTerm]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )


class CrmCustomerAddress(Base):
    __tablename__ = "crm_customer_addresses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
    address_type: Mapped[str] = mapped_column(String(30), nullable=False, default="DELIVERY")
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    geography_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    line1: Mapped[str] = mapped_column(String(200), nullable=False)
    line2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(12), nullable=True)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, default="PE")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    place_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    formatted_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    street_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    street_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    geocode_source: Mapped[str | None] = mapped_column(String(20), nullable=True)
    precision_meters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gps_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_operational_site: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str | None] = mapped_column(String(250), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    captured_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ubigeo_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped[CrmCustomer] = relationship(back_populates="addresses")


class CrmCustomerContact(Base):
    __tablename__ = "crm_customer_contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address_id: Mapped[str | None] = mapped_column(
        ForeignKey("crm_customer_addresses.id"), nullable=True, index=True
    )
    contact_purpose: Mapped[str] = mapped_column(String(30), nullable=False, default="GENERAL")
    contact_type: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(250), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped[CrmCustomer] = relationship(back_populates="contacts")


class CrmCustomerCommercialAssignment(Base):
    __tablename__ = "crm_customer_commercial_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
    address_id: Mapped[str | None] = mapped_column(
        ForeignKey("crm_customer_addresses.id"), nullable=True, index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    assignment_role: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(250), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped[CrmCustomer] = relationship(back_populates="commercial_assignments")


class CrmCustomerBankAccount(Base):
    __tablename__ = "crm_customer_bank_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_holder: Mapped[str] = mapped_column(String(200), nullable=False)
    iban: Mapped[str] = mapped_column(String(34), nullable=False)
    bic_swift: Mapped[str | None] = mapped_column(String(11), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped[CrmCustomer] = relationship(back_populates="bank_accounts")


class CrmCustomerPricingTerm(Base):
    __tablename__ = "crm_customer_pricing_terms"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "customer_id",
            "product_id",
            "scope_type",
            name="uq_crm_customer_pricing_tenant_customer_product_scope",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("crm_customers.id"), nullable=False, index=True
    )
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    pricing_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    fixed_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    discount_percent: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(5), nullable=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_quote_ref: Mapped[str | None] = mapped_column(String(50), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    customer: Mapped[CrmCustomer] = relationship(back_populates="pricing_terms")
