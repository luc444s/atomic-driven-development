from __future__ import annotations

from datetime import UTC, date, datetime
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


class ProductCondition(Base):
    __tablename__ = "prod_conditions"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ProductStatus(Base):
    __tablename__ = "prod_status"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ProductCategory(Base):
    __tablename__ = "prod_categories"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_prod_category_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ProductLine(Base):
    __tablename__ = "prod_lines"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_prod_line_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_categories.id"), nullable=True, index=True
    )
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ProductSubline(Base):
    __tablename__ = "prod_subline"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", "line_id", name="uq_prod_subline_tenant_code_line"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    line_id: Mapped[str] = mapped_column(ForeignKey("prod_lines.id"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ProductBrand(Base):
    __tablename__ = "prod_brands"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_prod_brand_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ProductInsumoType(Base):
    __tablename__ = "prod_insumo_types"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_prod_insumo_type_tenant_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ProductUnit(Base):
    __tablename__ = "prod_units"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_prod_unit_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    equivalencia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    m3_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    liter_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    kg_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ProductSubcategory(Base):
    __tablename__ = "prod_subcategories"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_prod_subcategory_tenant_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class ProductGroup(Base):
    __tablename__ = "prod_groups"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_prod_group_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gas_product_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_products.id", use_alter=True, name="fk_prod_group_gas_product"),
        nullable=True,
        index=True,
    )
    line_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_lines.id"), nullable=True, index=True
    )
    subline_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_subline.id"), nullable=True, index=True
    )
    unit_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_units.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class Product(Base):
    __tablename__ = "prod_products"
    __table_args__ = (UniqueConstraint("tenant_id", "sku", name="uq_prod_product_tenant_sku"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    legacy_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sku: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    line_id: Mapped[str] = mapped_column(ForeignKey("prod_lines.id"), nullable=False, index=True)
    subline_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_subline.id"), nullable=True, index=True
    )
    brand_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_brands.id"), nullable=True, index=True
    )
    insumo_type_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_insumo_types.id"), nullable=True, index=True
    )
    unit_id: Mapped[str] = mapped_column(ForeignKey("prod_units.id"), nullable=False, index=True)
    box_unit_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_units.id"), nullable=True, index=True
    )
    qty_per_box: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    subcategory_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_subcategories.id"), nullable=True, index=True
    )
    group_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_groups.id"), nullable=True, index=True
    )
    status_code: Mapped[str] = mapped_column(
        ForeignKey("prod_status.code"), nullable=False, index=True
    )
    condition_code: Mapped[str] = mapped_column(
        ForeignKey("prod_conditions.code"), nullable=False, index=True
    )
    weight_kg: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    default_weight_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    content_m3: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    is_service: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    barcodes: Mapped[list[ProductBarcode]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    prices: Mapped[list[ProductPrice]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    costs: Mapped[list[ProductCost]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    taxes: Mapped[list[ProductTaxConfig]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    adr_configs: Mapped[list[ProductAdr]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    media_items: Mapped[list[ProductMedia]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    promotions: Mapped[list[ProductPromotion]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class ProductBarcode(Base):
    __tablename__ = "prod_barcodes"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "barcode_type", "barcode", name="uq_prod_barcode_tenant_type_value"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    barcode_type: Mapped[str] = mapped_column(String(20), nullable=False)
    barcode: Mapped[str] = mapped_column(String(150), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    product: Mapped[Product] = relationship(back_populates="barcodes")


class ProductPrice(Base):
    __tablename__ = "prod_prices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    price_list: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    product: Mapped[Product] = relationship(back_populates="prices")


class ProductCost(Base):
    __tablename__ = "prod_costs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    cost_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    product: Mapped[Product] = relationship(back_populates="costs")


class ProductTaxConfig(Base):
    __tablename__ = "prod_tax_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    value: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    is_exempt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    product: Mapped[Product] = relationship(back_populates="taxes")


class ProductAdr(Base):
    __tablename__ = "prod_adr"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    source_product_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    source_product_id_2: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_product_id_3: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_quantity_liters: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    packaging_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    net_weight_kg: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    net_volume_m3: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    un_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cargo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tunnel_restriction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    subline_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_subline.id"), nullable=True, index=True
    )
    factor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit_measure: Mapped[str | None] = mapped_column(String(20), nullable=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    product: Mapped[Product] = relationship(back_populates="adr_configs")


class ProductMedia(Base):
    __tablename__ = "prod_media"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    product: Mapped[Product] = relationship(back_populates="media_items")


class ProductPromotion(Base):
    __tablename__ = "prod_promotions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    condition: Mapped[str] = mapped_column(String(20), nullable=False)
    qty_required: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discount_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    unit_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    box_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    product: Mapped[Product] = relationship(back_populates="promotions")
