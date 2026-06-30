from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    contact_type: str
    value: str
    label: str | None
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CustomerContactCreateRequest(BaseModel):
    contact_type: str = Field(min_length=1, max_length=20)
    value: str = Field(min_length=1, max_length=200)
    label: str | None = Field(default=None, max_length=100)
    is_primary: bool = False

    @field_validator("contact_type")
    @classmethod
    def normalize_contact_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"PHONE", "EMAIL", "OTHER"}:
            raise ValueError("contact_type debe ser PHONE, EMAIL o OTHER")
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
    notes: str | None
    is_active: bool
    captured_by: str | None
    captured_at: datetime | None
    ubigeo_code: str | None
    created_at: datetime
    updated_at: datetime


class CustomerAddressCreateRequest(BaseModel):
    address_type: str = Field(default="DELIVERY", min_length=1, max_length=30)
    label: str | None = Field(default=None, max_length=100)
    geography_id: str | None = None
    line1: str = Field(min_length=1, max_length=200)
    line2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=12)
    country_code: str = Field(default="PER", min_length=2, max_length=5)
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
    notes: str | None = Field(default=None, max_length=250)
    ubigeo_code: str | None = Field(default=None, max_length=6)

    @field_validator("address_type")
    @classmethod
    def normalize_address_type(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in {"FISCAL", "DELIVERY", "BILLING", "OTHER"}:
            raise ValueError("address_type debe ser FISCAL, DELIVERY, BILLING o OTHER")
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
    notes: str | None = Field(default=None, max_length=250)
    ubigeo_code: str | None = Field(default=None, max_length=6)
    is_active: bool | None = None

    @field_validator("address_type")
    @classmethod
    def normalize_address_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if normalized not in {"FISCAL", "DELIVERY", "BILLING", "OTHER"}:
            raise ValueError("address_type debe ser FISCAL, DELIVERY, BILLING o OTHER")
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
    is_active: bool
    fiscal_address_id: str | None
    created_at: datetime
    updated_at: datetime


class CustomerSearchItemRead(BaseModel):
    id: str
    legal_name: str
    document_type_code: str
    document_number: str
    email: str | None
    phone: str | None
    country_code: str
    fiscal_address_summary: str | None


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


class CustomerCreateRequest(BaseModel):
    external_code: str | None = Field(default=None, max_length=50)
    legal_name: str = Field(min_length=1, max_length=200)
    commercial_name: str | None = Field(default=None, max_length=100)
    document_type_code: str = Field(min_length=1, max_length=20)
    document_number: str = Field(min_length=1, max_length=30)
    country_code: str = Field(default="PER", min_length=2, max_length=5)
    email: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    mobile: str | None = Field(default=None, max_length=50)
    economic_activity_code: str | None = Field(default=None, max_length=20)
    economic_activity_description: str | None = Field(default=None, max_length=300)
    payment_term_code: str | None = Field(default=None, max_length=20)
    billing_type: str | None = Field(default=None, max_length=20)
    is_exempt: bool = False
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
        return value.strip().lower() if value else value


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
        return value.strip().lower() if value else value


class CustomerToggleActiveRequest(BaseModel):
    is_active: bool
    reason: str | None = None


class CustomerPageRead(BaseModel):
    items: list[CustomerListItemRead]
    total: int
    limit: int
    offset: int


class FiscalAddressSetResponse(BaseModel):
    customer_id: str
    fiscal_address_id: str
