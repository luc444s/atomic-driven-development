from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.core.pagination import OffsetPageRead


class NamedCatalogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NamedCatalogCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=200)


class NamedCatalogUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=200)
    is_active: bool | None = None


class ProductLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    name: str
    category_id: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductLineCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    category_id: str | None = None
    description: str | None = Field(default=None, max_length=200)


class ProductLineUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    category_id: str | None = None
    description: str | None = Field(default=None, max_length=200)
    is_active: bool | None = None


class ProductSublineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    name: str
    line_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductSublineCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    line_id: str


class ProductSublineUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    line_id: str | None = None
    is_active: bool | None = None


class ProductUnitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    name: str
    equivalencia: int | None
    m3_factor: float | None
    liter_factor: float | None
    kg_factor: float | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductUnitCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=50)
    equivalencia: int | None = None
    m3_factor: float | None = None
    liter_factor: float | None = None
    kg_factor: float | None = None


class ProductUnitUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=50)
    equivalencia: int | None = None
    m3_factor: float | None = None
    liter_factor: float | None = None
    kg_factor: float | None = None
    is_active: bool | None = None


class ProductGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    name: str
    gas_product_id: str | None
    line_id: str | None
    subline_id: str | None
    unit_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductGroupCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=50)
    gas_product_id: str | None = None
    line_id: str | None = None
    subline_id: str | None = None
    unit_id: str | None = None


class ProductGroupUpdateRequest(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=50)
    gas_product_id: str | None = None
    line_id: str | None = None
    subline_id: str | None = None
    unit_id: str | None = None
    is_active: bool | None = None


class GasProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    code: str
    content_kg: float | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductConditionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    description: str | None
    is_active: bool


class ProductStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    is_active: bool


class ProductBarcodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    barcode_type: str
    barcode: str
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductBarcodeCreateRequest(BaseModel):
    barcode_type: str = Field(min_length=1, max_length=20)
    barcode: str = Field(min_length=1, max_length=150)
    is_primary: bool = False
    is_active: bool = True


class ProductBarcodeUpdateRequest(BaseModel):
    barcode_type: str | None = Field(default=None, min_length=1, max_length=20)
    barcode: str | None = Field(default=None, min_length=1, max_length=150)
    is_primary: bool | None = None
    is_active: bool | None = None


class ProductPriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    price_list: str
    amount: float
    currency: str
    valid_from: date
    valid_to: date | None
    created_by: str
    created_at: datetime


class ProductPriceCreateRequest(BaseModel):
    price_list: str = Field(min_length=1, max_length=20)
    amount: float
    currency: str = Field(min_length=3, max_length=3)
    valid_from: date = Field(default_factory=date.today)


class ProductPriceSupersedeRequest(BaseModel):
    amount: float
    currency: str = Field(min_length=3, max_length=3)
    valid_from: date = Field(default_factory=date.today)


class ProductPriceBulkUpdateRequest(BaseModel):
    items: list[ProductPriceCreateRequest] = Field(default_factory=list)


class ProductCostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    cost_type: str
    amount: float
    currency: str
    valid_from: date
    valid_to: date | None
    created_by: str
    created_at: datetime


class ProductCostCreateRequest(BaseModel):
    cost_type: str = Field(min_length=1, max_length=20)
    amount: float
    currency: str = Field(min_length=3, max_length=3)
    valid_from: date = Field(default_factory=date.today)


class ProductCostSupersedeRequest(BaseModel):
    amount: float
    currency: str = Field(min_length=3, max_length=3)
    valid_from: date = Field(default_factory=date.today)


class ProductTaxConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    tax_type: str
    value: float | None
    is_exempt: bool
    valid_from: date
    valid_to: date | None
    created_at: datetime


class ProductTaxConfigWrite(BaseModel):
    tax_type: str = Field(min_length=1, max_length=20)
    value: float | None = None
    is_exempt: bool = False
    valid_from: date = Field(default_factory=date.today)


class ProductTaxConfigUpdateRequest(BaseModel):
    configs: list[ProductTaxConfigWrite] = Field(default_factory=list)


class ProductAdrRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    source_product_id: str | None
    source_product_id_2: str | None
    source_product_id_3: str | None
    source_quantity_liters: float | None
    category: str | None
    packaging_type: str | None
    net_weight_kg: float | None
    net_volume_m3: float | None
    un_number: str | None
    cargo_description: str | None
    label: str | None
    tunnel_restriction: str | None
    subline_id: str | None
    factor: int | None
    points: int | None
    unit_measure: str | None
    valid_from: date
    valid_to: date | None
    created_by: str
    created_at: datetime


class ProductAdrCreateRequest(BaseModel):
    source_product_id: str | None = None
    source_product_id_2: str | None = None
    source_product_id_3: str | None = None
    source_quantity_liters: float | None = None
    category: str | None = Field(default=None, max_length=50)
    packaging_type: str | None = Field(default=None, max_length=50)
    net_weight_kg: float | None = None
    net_volume_m3: float | None = None
    un_number: str | None = Field(default=None, max_length=10)
    cargo_description: str | None = None
    label: str | None = Field(default=None, max_length=50)
    tunnel_restriction: str | None = Field(default=None, max_length=10)
    subline_id: str | None = None
    factor: int | None = None
    points: int | None = None
    unit_measure: str | None = Field(default=None, max_length=20)
    valid_from: date = Field(default_factory=date.today)


class ProductAdrUpdateRequest(BaseModel):
    source_product_id: str | None = None
    source_product_id_2: str | None = None
    source_product_id_3: str | None = None
    source_quantity_liters: float | None = None
    category: str | None = Field(default=None, max_length=50)
    packaging_type: str | None = Field(default=None, max_length=50)
    net_weight_kg: float | None = None
    net_volume_m3: float | None = None
    un_number: str | None = Field(default=None, max_length=10)
    cargo_description: str | None = None
    label: str | None = Field(default=None, max_length=50)
    tunnel_restriction: str | None = Field(default=None, max_length=10)
    subline_id: str | None = None
    factor: int | None = None
    points: int | None = None
    unit_measure: str | None = Field(default=None, max_length=20)
    valid_from: date | None = None
    valid_to: date | None = None


class ProductMediaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    media_type: str
    url: str
    is_primary: bool
    created_at: datetime


class ProductPromotionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    name: str | None
    condition: str
    qty_required: int | None
    discount_percent: float | None
    unit_price: float | None
    box_price: float | None
    valid_from: date
    valid_to: date | None
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime


class ProductPromotionCreateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    condition: str = Field(min_length=1, max_length=20)
    qty_required: int | None = None
    discount_percent: float | None = None
    unit_price: float | None = None
    box_price: float | None = None
    valid_from: date = Field(default_factory=date.today)
    valid_to: date | None = None
    is_active: bool = True


class ProductPromotionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    condition: str | None = Field(default=None, min_length=1, max_length=20)
    qty_required: int | None = None
    discount_percent: float | None = None
    unit_price: float | None = None
    box_price: float | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_active: bool | None = None


class ProductListItemRead(BaseModel):
    id: str
    sku: str
    name: str
    line_id: str
    line_name: str | None
    brand_id: str | None
    brand_name: str | None
    unit_id: str
    unit_name: str | None
    subcategory_id: str | None
    subcategory_name: str | None
    status_code: str
    status_name: str | None
    condition_code: str
    condition_name: str | None
    is_service: bool
    is_active: bool
    default_weight_kg: float | None
    created_at: datetime
    updated_at: datetime


class ProductSearchItemRead(BaseModel):
    id: str
    sku: str
    name: str
    brand_name: str | None
    condition_code: str
    is_active: bool


class ProductPageRead(OffsetPageRead[ProductListItemRead]):
    pass


class ProductCreateRequest(BaseModel):
    legacy_id: int | None = None
    sku: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    line_id: str
    subline_id: str | None = None
    brand_id: str | None = None
    insumo_type_id: str | None = None
    unit_id: str
    box_unit_id: str | None = None
    qty_per_box: float | None = None
    subcategory_id: str | None = None
    group_id: str | None = None
    status_code: str = Field(default="ACTIVO", min_length=1, max_length=20)
    condition_code: str = Field(default="PRODUCTO", min_length=1, max_length=20)
    weight_kg: float | None = None
    default_weight_kg: float | None = None
    content_m3: float | None = None
    country_code: str | None = Field(default=None, max_length=5)
    is_service: bool = False
    is_active: bool = True


class ProductUpdateRequest(BaseModel):
    legacy_id: int | None = None
    sku: str | None = Field(default=None, min_length=1, max_length=30)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    short_description: str | None = Field(default=None, max_length=500)
    line_id: str | None = None
    subline_id: str | None = None
    brand_id: str | None = None
    insumo_type_id: str | None = None
    unit_id: str | None = None
    box_unit_id: str | None = None
    qty_per_box: float | None = None
    subcategory_id: str | None = None
    group_id: str | None = None
    status_code: str | None = Field(default=None, min_length=1, max_length=20)
    condition_code: str | None = Field(default=None, min_length=1, max_length=20)
    weight_kg: float | None = None
    default_weight_kg: float | None = None
    content_m3: float | None = None
    country_code: str | None = Field(default=None, max_length=5)
    is_service: bool | None = None
    is_active: bool | None = None


class ProductToggleActiveRequest(BaseModel):
    is_active: bool
    reason: str | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    legacy_id: int | None
    sku: str
    name: str
    description: str | None
    short_description: str | None
    line_id: str
    subline_id: str | None
    brand_id: str | None
    insumo_type_id: str | None
    unit_id: str
    box_unit_id: str | None
    qty_per_box: float | None
    subcategory_id: str | None
    group_id: str | None
    status_code: str
    condition_code: str
    weight_kg: float | None
    default_weight_kg: float | None = None
    content_m3: float | None
    country_code: str | None
    is_service: bool
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime
    line_name: str | None = None
    subline_name: str | None = None
    brand_name: str | None = None
    unit_name: str | None = None
    insumo_type_name: str | None = None
    subcategory_name: str | None = None
    group_name: str | None = None
    condition_name: str | None = None
    status_name: str | None = None
    barcodes: list[ProductBarcodeRead]
    prices: list[ProductPriceRead]
    costs: list[ProductCostRead]
    taxes: list[ProductTaxConfigRead]
    adr_configs: list[ProductAdrRead]
    media_items: list[ProductMediaRead]
    promotions: list[ProductPromotionRead]
