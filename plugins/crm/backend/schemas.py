from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from apps.api.app.core.pagination import OffsetPageRead


class DocumentTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    country_code: str
    description: str | None
    is_person: bool
    is_company: bool
    validation_pattern: str | None
    is_active: bool


class PaymentTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str | None
    days: int
    operation_type: str
    payment_mode: str
    is_active: bool


class GeographyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parent_id: str | None
    code: str | None
    name: str
    level: int
    country_code: str
    ubigeo_code: str | None
    is_active: bool


class GeographySeedRequest(BaseModel):
    country_code: str = Field(min_length=2, max_length=5)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.strip().upper()


class GeographySeedResponse(BaseModel):
    country_code: str
    inserted: int


class CustomerContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str | None
    label: str | None
    role: str | None
    phone: str | None
    email: str | None
    address_id: str | None
    contact_purpose: str
    contact_type: str
    notes: str | None
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


CONTACT_PURPOSES = {
    "GENERAL",
    "FACTURACION",
    "COBRANZA",
    "COMPRAS",
    "OPERACIONES",
    "RECEPCION",
    "OTRO",
}


class CustomerContactCreateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    label: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    address_id: str | None = None
    contact_purpose: str = "GENERAL"
    contact_type: str = "PHONE"
    notes: str | None = Field(default=None, max_length=250)
    is_primary: bool = False

    @field_validator("contact_purpose")
    @classmethod
    def normalize_contact_purpose(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in CONTACT_PURPOSES:
            raise ValueError(
                "contact_purpose debe ser GENERAL, FACTURACION, COBRANZA, COMPRAS, "
                "OPERACIONES, RECEPCION u OTRO"
            )
        return normalized

    @field_validator("contact_type")
    @classmethod
    def normalize_contact_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"PHONE", "EMAIL", "OTHER"}:
            raise ValueError("contact_type debe ser PHONE, EMAIL o OTHER")
        return normalized


class CustomerContactUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    label: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=200)
    address_id: str | None = None
    contact_purpose: str | None = Field(default=None, max_length=30)
    contact_type: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=250)
    is_primary: bool | None = None
    is_active: bool | None = None

    @field_validator("contact_purpose")
    @classmethod
    def normalize_optional_contact_purpose(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in CONTACT_PURPOSES:
            raise ValueError(
                "contact_purpose debe ser GENERAL, FACTURACION, COBRANZA, COMPRAS, "
                "OPERACIONES, RECEPCION u OTRO"
            )
        return normalized

    @field_validator("contact_type")
    @classmethod
    def normalize_optional_contact_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in {"PHONE", "EMAIL", "OTHER"}:
            raise ValueError("contact_type debe ser PHONE, EMAIL o OTHER")
        return normalized


class CommercialUserOptionRead(BaseModel):
    id: str
    full_name: str
    email: str
    is_active: bool


class CustomerCommercialAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    address_id: str | None
    user_id: str
    user_display_name: str
    user_email: str
    assignment_role: str
    notes: str | None
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


ASSIGNMENT_ROLES = {"AGENT", "SUPERVISOR"}


class CustomerCommercialAssignmentCreateRequest(BaseModel):
    address_id: str | None = None
    user_id: str
    assignment_role: str = "AGENT"
    notes: str | None = Field(default=None, max_length=250)
    is_primary: bool = False

    @field_validator("assignment_role")
    @classmethod
    def normalize_assignment_role(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in ASSIGNMENT_ROLES:
            raise ValueError("assignment_role debe ser AGENT o SUPERVISOR")
        return normalized


class CustomerCommercialAssignmentUpdateRequest(BaseModel):
    address_id: str | None = None
    user_id: str | None = None
    assignment_role: str | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=250)
    is_primary: bool | None = None
    is_active: bool | None = None

    @field_validator("assignment_role")
    @classmethod
    def normalize_optional_assignment_role(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in ASSIGNMENT_ROLES:
            raise ValueError("assignment_role debe ser AGENT o SUPERVISOR")
        return normalized


class CustomerAddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    address_type: str
    label: str | None
    geography_id: str | None
    line1: str
    line2: str | None
    city: str | None
    state: str | None
    district: str | None
    postal_code: str | None
    country_code: str
    latitude: float | None
    longitude: float | None
    place_id: str | None
    formatted_address: str | None
    street_name: str | None
    street_number: str | None
    geocode_source: str | None
    precision_meters: int | None
    gps_link: str | None
    contact_name: str | None
    contact_phone: str | None
    contact_email: str | None
    is_operational_site: bool
    notes: str | None
    is_active: bool
    captured_by: str | None
    captured_at: datetime | None
    ubigeo_code: str | None
    created_at: datetime
    updated_at: datetime


ADDRESS_TYPES = {"FISCAL", "COMERCIAL", "ENTREGA", "OTRA"}


class CustomerAddressCreateRequest(BaseModel):
    address_type: str = Field(default="ENTREGA", min_length=1, max_length=30)
    label: str | None = Field(default=None, max_length=100)
    geography_id: str | None = None
    line1: str = Field(min_length=1, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=12)
    country_code: str = Field(default="PE", min_length=2, max_length=5)
    latitude: float | None = None
    longitude: float | None = None
    place_id: str | None = Field(default=None, max_length=64)
    formatted_address: str | None = Field(default=None, max_length=255)
    street_name: str | None = Field(default=None, max_length=160)
    street_number: str | None = Field(default=None, max_length=20)
    geocode_source: str | None = Field(default=None, max_length=20)
    precision_meters: int | None = None
    gps_link: str | None = Field(default=None, max_length=500)
    contact_name: str | None = Field(default=None, max_length=100)
    contact_phone: str | None = Field(default=None, max_length=50)
    contact_email: str | None = Field(default=None, max_length=100)
    is_operational_site: bool = False
    notes: str | None = Field(default=None, max_length=250)
    ubigeo_code: str | None = Field(default=None, max_length=6)

    @field_validator("address_type")
    @classmethod
    def normalize_address_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in ADDRESS_TYPES:
            raise ValueError("address_type debe ser FISCAL, COMERCIAL, ENTREGA u OTRA")
        return normalized

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("geocode_source")
    @classmethod
    def normalize_geocode_source(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value


class CustomerAddressUpdateRequest(BaseModel):
    address_type: str | None = Field(default=None, min_length=1, max_length=30)
    label: str | None = Field(default=None, max_length=100)
    geography_id: str | None = None
    line1: str | None = Field(default=None, min_length=1, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=12)
    country_code: str | None = Field(default=None, min_length=2, max_length=5)
    latitude: float | None = None
    longitude: float | None = None
    place_id: str | None = Field(default=None, max_length=64)
    formatted_address: str | None = Field(default=None, max_length=255)
    street_name: str | None = Field(default=None, max_length=160)
    street_number: str | None = Field(default=None, max_length=20)
    geocode_source: str | None = Field(default=None, max_length=20)
    precision_meters: int | None = None
    gps_link: str | None = Field(default=None, max_length=500)
    contact_name: str | None = Field(default=None, max_length=100)
    contact_phone: str | None = Field(default=None, max_length=50)
    contact_email: str | None = Field(default=None, max_length=100)
    is_operational_site: bool | None = None
    notes: str | None = Field(default=None, max_length=250)
    ubigeo_code: str | None = Field(default=None, max_length=6)
    is_active: bool | None = None

    @field_validator("address_type")
    @classmethod
    def normalize_address_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in ADDRESS_TYPES:
            raise ValueError("address_type debe ser FISCAL, COMERCIAL, ENTREGA u OTRA")
        return normalized

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value

    @field_validator("geocode_source")
    @classmethod
    def normalize_geocode_source(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value


class CustomerListItemRead(BaseModel):
    id: str
    legal_name: str
    commercial_name: str | None
    external_code: str | None
    document_type_code: str
    document_number: str
    country_code: str
    email: str | None
    phone: str | None
    mobile: str | None
    payment_term_code: str | None
    billing_type: str | None
    is_exempt: bool
    accounting_code: str | None
    is_intracommunity: bool
    fiscal_operation_key: str | None
    tax_regime_code: str | None
    equivalence_surcharge_applicable: bool
    cash_criterion_applicable: bool
    is_active: bool
    fiscal_address_id: str | None
    created_at: datetime
    updated_at: datetime


class CustomerSearchItemRead(BaseModel):
    id: str
    legal_name: str
    commercial_name: str | None
    display_name: str
    document_type_code: str
    document_number: str
    external_code: str | None
    email: str | None
    phone: str | None
    country_code: str
    fiscal_address_summary: str | None
    locality_summary: str | None


class CustomerRead(CustomerListItemRead):
    economic_activity_code: str | None
    economic_activity_description: str | None
    activity_validated: bool
    activity_validation_source: str | None
    activity_validation_date: datetime | None
    first_name: str | None
    last_name: str | None
    birth_date: date | None
    gender: str | None
    notes: str | None
    addresses: list[CustomerAddressRead]
    contacts: list[CustomerContactRead]


BILLING_TYPES = {"por_operacion", "mensual", "anticipada"}


class CustomerCreateRequest(BaseModel):
    external_code: str | None = Field(default=None, max_length=50)
    legal_name: str = Field(min_length=1, max_length=200)
    commercial_name: str | None = Field(default=None, max_length=100)
    document_type_code: str = Field(min_length=1, max_length=20)
    document_number: str = Field(min_length=1, max_length=30)
    country_code: str = Field(default="PE", min_length=2, max_length=5)
    email: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    mobile: str | None = Field(default=None, max_length=50)
    economic_activity_code: str | None = Field(default=None, max_length=20)
    economic_activity_description: str | None = Field(default=None, max_length=300)
    payment_term_code: str | None = Field(default=None, max_length=20)
    billing_type: str | None = Field(default=None, max_length=20)
    is_exempt: bool = False
    accounting_code: str | None = Field(default=None, max_length=20)
    is_intracommunity: bool = False
    fiscal_operation_key: str | None = Field(default=None, max_length=20)
    tax_regime_code: str | None = Field(default=None, max_length=20)
    equivalence_surcharge_applicable: bool = False
    cash_criterion_applicable: bool = False
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    birth_date: date | None = None
    gender: str | None = Field(default=None, max_length=10)
    notes: str | None = None

    @field_validator("document_type_code", "country_code")
    @classmethod
    def normalize_upper_codes(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("document_number")
    @classmethod
    def normalize_document_number(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("billing_type")
    @classmethod
    def normalize_billing_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in BILLING_TYPES:
            raise ValueError(
                "billing_type debe ser por_operacion, mensual o anticipada"
            )
        return normalized


class CustomerUpdateRequest(BaseModel):
    external_code: str | None = Field(default=None, max_length=50)
    legal_name: str | None = Field(default=None, min_length=1, max_length=200)
    commercial_name: str | None = Field(default=None, max_length=100)
    document_type_code: str | None = Field(default=None, min_length=1, max_length=20)
    document_number: str | None = Field(default=None, min_length=1, max_length=30)
    country_code: str | None = Field(default=None, min_length=2, max_length=5)
    email: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    mobile: str | None = Field(default=None, max_length=50)
    economic_activity_code: str | None = Field(default=None, max_length=20)
    economic_activity_description: str | None = Field(default=None, max_length=300)
    payment_term_code: str | None = Field(default=None, max_length=20)
    billing_type: str | None = Field(default=None, max_length=20)
    is_exempt: bool | None = None
    accounting_code: str | None = Field(default=None, max_length=20)
    is_intracommunity: bool | None = None
    fiscal_operation_key: str | None = Field(default=None, max_length=20)
    tax_regime_code: str | None = Field(default=None, max_length=20)
    equivalence_surcharge_applicable: bool | None = None
    cash_criterion_applicable: bool | None = None
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    birth_date: date | None = None
    gender: str | None = Field(default=None, max_length=10)
    notes: str | None = None

    @field_validator("document_type_code", "country_code")
    @classmethod
    def normalize_optional_upper_codes(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value

    @field_validator("document_number")
    @classmethod
    def normalize_optional_document_number(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else value

    @field_validator("billing_type")
    @classmethod
    def normalize_optional_billing_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in BILLING_TYPES:
            raise ValueError(
                "billing_type debe ser por_operacion, mensual o anticipada"
            )
        return normalized


class CustomerToggleActiveRequest(BaseModel):
    is_active: bool
    reason: str | None = None


class CustomerPageRead(OffsetPageRead[CustomerListItemRead]):
    pass


class FiscalAddressSetResponse(BaseModel):
    customer_id: str
    fiscal_address_id: str


# ── Bank Accounts ──────────────────────────────────────────────


class CustomerBankAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    bank_name: str
    account_holder: str
    iban: str
    bic_swift: str | None
    is_primary: bool
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CustomerBankAccountCreateRequest(BaseModel):
    bank_name: str = Field(min_length=1, max_length=100)
    account_holder: str = Field(min_length=1, max_length=200)
    iban: str = Field(min_length=1, max_length=34)
    bic_swift: str | None = Field(default=None, max_length=11)
    is_primary: bool = False
    notes: str | None = Field(default=None, max_length=250)

    @field_validator("iban")
    @classmethod
    def normalize_iban(cls, value: str) -> str:
        return value.strip().upper().replace(" ", "")


class CustomerBankAccountUpdateRequest(BaseModel):
    bank_name: str | None = Field(default=None, min_length=1, max_length=100)
    account_holder: str | None = Field(default=None, min_length=1, max_length=200)
    iban: str | None = Field(default=None, min_length=1, max_length=34)
    bic_swift: str | None = Field(default=None, max_length=11)
    is_primary: bool | None = None
    is_active: bool | None = None
    notes: str | None = Field(default=None, max_length=250)

    @field_validator("iban")
    @classmethod
    def normalize_optional_iban(cls, value: str | None) -> str | None:
        return value.strip().upper().replace(" ", "") if value else value


# ── Pricing Terms ───────────────────────────────────────────────

SCOPE_TYPES = {"PRODUCT", "GLOBAL"}
PRICING_MODES = {"FIXED_PRICE", "PERCENT_DISCOUNT"}


class CustomerPricingTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    product_id: str | None
    scope_type: str
    pricing_mode: str
    fixed_amount: Decimal | None
    discount_percent: Decimal | None
    currency: str | None
    valid_from: datetime
    valid_to: datetime | None
    source_quote_ref: str | None
    approved_by: str | None
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CustomerPricingTermCreateRequest(BaseModel):
    product_id: str | None = None
    scope_type: str = "GLOBAL"
    pricing_mode: str = "FIXED_PRICE"
    fixed_amount: Decimal | None = None
    discount_percent: Decimal | None = None
    currency: str | None = Field(default=None, max_length=5)
    valid_from: datetime
    valid_to: datetime | None = None
    source_quote_ref: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=250)

    @field_validator("scope_type")
    @classmethod
    def normalize_scope_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in SCOPE_TYPES:
            raise ValueError("scope_type debe ser PRODUCT o GLOBAL")
        return normalized

    @field_validator("pricing_mode")
    @classmethod
    def normalize_pricing_mode(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in PRICING_MODES:
            raise ValueError("pricing_mode debe ser FIXED_PRICE o PERCENT_DISCOUNT")
        return normalized


class CustomerPricingTermUpdateRequest(BaseModel):
    product_id: str | None = None
    scope_type: str | None = Field(default=None, max_length=20)
    pricing_mode: str | None = Field(default=None, max_length=20)
    fixed_amount: Decimal | None = None
    discount_percent: Decimal | None = None
    currency: str | None = Field(default=None, max_length=5)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    source_quote_ref: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None
    notes: str | None = Field(default=None, max_length=250)

    @field_validator("scope_type")
    @classmethod
    def normalize_optional_scope_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in SCOPE_TYPES:
            raise ValueError("scope_type debe ser PRODUCT o GLOBAL")
        return normalized

    @field_validator("pricing_mode")
    @classmethod
    def normalize_optional_pricing_mode(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in PRICING_MODES:
            raise ValueError("pricing_mode debe ser FIXED_PRICE o PERCENT_DISCOUNT")
        return normalized
