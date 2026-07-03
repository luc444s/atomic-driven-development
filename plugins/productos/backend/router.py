from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.productos.backend.common import build_action_context
from plugins.productos.backend.models import (
    ProductBrand,
    ProductCategory,
    ProductCondition,
    ProductGroup,
    ProductInsumoType,
    ProductLine,
    ProductStatus,
    ProductSubcategory,
    ProductSubline,
    ProductUnit,
)
from plugins.productos.backend.schemas import (
    NamedCatalogCreateRequest,
    NamedCatalogRead,
    NamedCatalogUpdateRequest,
    ProductAdrCreateRequest,
    ProductAdrRead,
    ProductAdrUpdateRequest,
    ProductBarcodeCreateRequest,
    ProductBarcodeRead,
    ProductBarcodeUpdateRequest,
    ProductConditionRead,
    ProductCostCreateRequest,
    ProductCostRead,
    ProductCostSupersedeRequest,
    ProductCreateRequest,
    ProductGroupCreateRequest,
    ProductGroupRead,
    ProductGroupUpdateRequest,
    ProductLineCreateRequest,
    ProductLineRead,
    ProductLineUpdateRequest,
    ProductMediaRead,
    ProductPageRead,
    ProductPriceBulkUpdateRequest,
    ProductPriceCreateRequest,
    ProductPriceRead,
    ProductPriceSupersedeRequest,
    ProductPromotionCreateRequest,
    ProductPromotionRead,
    ProductPromotionUpdateRequest,
    ProductRead,
    ProductSearchItemRead,
    ProductStatusRead,
    ProductSublineCreateRequest,
    ProductSublineRead,
    ProductSublineUpdateRequest,
    ProductTaxConfigRead,
    ProductTaxConfigUpdateRequest,
    ProductToggleActiveRequest,
    ProductUnitCreateRequest,
    ProductUnitRead,
    ProductUnitUpdateRequest,
    ProductUpdateRequest,
)
from plugins.productos.backend.services.adr import (
    create_adr_config,
    expire_adr_config,
    list_adr_configs,
    require_adr_config,
    update_adr_config,
)
from plugins.productos.backend.services.barcode import (
    create_barcode,
    delete_barcode,
    list_barcodes,
    require_barcode,
    set_primary_barcode,
    update_barcode,
)
from plugins.productos.backend.services.catalog import (
    create_brand,
    create_category,
    create_group,
    create_insumo_type,
    create_line,
    create_subcategory,
    create_subline,
    create_unit,
    get_tenant_entity_or_none,
    list_brands,
    list_categories,
    list_conditions,
    list_groups,
    list_insumo_types,
    list_lines,
    list_status,
    list_subcategories,
    list_subline,
    list_units,
    update_brand,
    update_category,
    update_group,
    update_insumo_type,
    update_line,
    update_subcategory,
    update_subline,
    update_unit,
)
from plugins.productos.backend.services.media import (
    create_media,
    delete_media,
    list_media,
    require_media,
    resolve_media_path,
    set_primary_media,
)
from plugins.productos.backend.services.pricing import (
    create_cost,
    create_price,
    list_costs,
    list_prices,
    list_tax_configs,
    replace_tax_configs,
    require_cost,
    require_price,
    supersede_cost,
    supersede_price,
    update_all_prices,
)
from plugins.productos.backend.services.products import (
    create_product,
    get_product,
    list_products,
    require_product,
    search_products,
    serialize_product,
    toggle_product_active,
    update_product,
)
from plugins.productos.backend.services.promotions import (
    create_promotion,
    delete_promotion,
    list_promotions,
    require_promotion,
    update_promotion,
)

router = APIRouter(tags=["productos"])
DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
UPLOAD_FILE = File(...)

REQUIRE_CATALOG_READ = Depends(require_permission("productos.catalog.read"))
REQUIRE_CATALOG_MANAGE = Depends(require_permission("productos.catalog.manage"))
REQUIRE_PRODUCT_READ = Depends(require_permission("productos.product.read"))
REQUIRE_PRODUCT_CREATE = Depends(require_permission("productos.product.create"))
REQUIRE_PRODUCT_UPDATE = Depends(require_permission("productos.product.update"))
REQUIRE_PRODUCT_DELETE = Depends(require_permission("productos.product.delete"))
REQUIRE_PRICE_READ = Depends(require_permission("productos.price.read"))
REQUIRE_PRICE_MANAGE = Depends(require_permission("productos.price.manage"))
REQUIRE_COST_READ = Depends(require_permission("productos.cost.read"))
REQUIRE_COST_MANAGE = Depends(require_permission("productos.cost.manage"))
REQUIRE_ADR_READ = Depends(require_permission("productos.adr.read"))
REQUIRE_ADR_MANAGE = Depends(require_permission("productos.adr.manage"))
REQUIRE_MEDIA_MANAGE = Depends(require_permission("productos.media.manage"))
REQUIRE_PROMOTION_READ = Depends(require_permission("productos.promotion.read"))
REQUIRE_PROMOTION_MANAGE = Depends(require_permission("productos.promotion.manage"))


def _bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def _not_found(entity_name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found")


def _serialize_named(items: Sequence[object]) -> list[NamedCatalogRead]:
    return [NamedCatalogRead.model_validate(item) for item in items]


def _require_product_or_404(db: Session, *, tenant_id: str, product_id: str):
    try:
        return require_product(db, tenant_id=tenant_id, product_id=product_id)
    except ValueError as exc:
        raise _not_found("Product") from exc


@router.get(
    "/catalog/categories",
    response_model=list[NamedCatalogRead],
    dependencies=[REQUIRE_CATALOG_READ],
)
def get_categories(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[NamedCatalogRead]:
    return _serialize_named(list_categories(db, tenant_id=tenant_context.current_tenant_id))


@router.post(
    "/catalog/categories",
    response_model=NamedCatalogRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def post_category(
    payload: NamedCatalogCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    item = create_category(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)


@router.put(
    "/catalog/categories/{category_id}",
    response_model=NamedCatalogRead,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def put_category(
    category_id: str,
    payload: NamedCatalogUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    category = get_tenant_entity_or_none(
        db,
        ProductCategory,
        tenant_id=tenant_context.current_tenant_id,
        entity_id=category_id,
    )
    if category is None:
        raise _not_found("Category")
    item = update_category(
        db,
        category=category,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)


@router.get(
    "/catalog/lines", response_model=list[ProductLineRead], dependencies=[REQUIRE_CATALOG_READ]
)
def get_lines(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductLineRead]:
    return [
        ProductLineRead.model_validate(item)
        for item in list_lines(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.post(
    "/catalog/lines",
    response_model=ProductLineRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def post_line(
    payload: ProductLineCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductLineRead:
    item = create_line(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return ProductLineRead.model_validate(item)


@router.put(
    "/catalog/lines/{line_id}",
    response_model=ProductLineRead,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def put_line(
    line_id: str,
    payload: ProductLineUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductLineRead:
    line = get_tenant_entity_or_none(
        db, ProductLine, tenant_id=tenant_context.current_tenant_id, entity_id=line_id
    )
    if line is None:
        raise _not_found("Line")
    item = update_line(
        db,
        line=line,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return ProductLineRead.model_validate(item)


@router.get(
    "/catalog/subline", response_model=list[ProductSublineRead], dependencies=[REQUIRE_CATALOG_READ]
)
def get_subline(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductSublineRead]:
    return [
        ProductSublineRead.model_validate(item)
        for item in list_subline(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.post(
    "/catalog/subline",
    response_model=ProductSublineRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def post_subline(
    payload: ProductSublineCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductSublineRead:
    item = create_subline(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return ProductSublineRead.model_validate(item)


@router.put(
    "/catalog/subline/{subline_id}",
    response_model=ProductSublineRead,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def put_subline(
    subline_id: str,
    payload: ProductSublineUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductSublineRead:
    subline = get_tenant_entity_or_none(
        db, ProductSubline, tenant_id=tenant_context.current_tenant_id, entity_id=subline_id
    )
    if subline is None:
        raise _not_found("Subline")
    item = update_subline(
        db,
        subline=subline,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return ProductSublineRead.model_validate(item)


@router.get(
    "/catalog/brands", response_model=list[NamedCatalogRead], dependencies=[REQUIRE_CATALOG_READ]
)
def get_brands(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[NamedCatalogRead]:
    return _serialize_named(list_brands(db, tenant_id=tenant_context.current_tenant_id))


@router.post(
    "/catalog/brands",
    response_model=NamedCatalogRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def post_brand(
    payload: NamedCatalogCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    item = create_brand(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)


@router.put(
    "/catalog/brands/{brand_id}",
    response_model=NamedCatalogRead,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def put_brand(
    brand_id: str,
    payload: NamedCatalogUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    brand = get_tenant_entity_or_none(
        db, ProductBrand, tenant_id=tenant_context.current_tenant_id, entity_id=brand_id
    )
    if brand is None:
        raise _not_found("Brand")
    item = update_brand(
        db,
        brand=brand,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)


@router.get(
    "/catalog/insumo-types",
    response_model=list[NamedCatalogRead],
    dependencies=[REQUIRE_CATALOG_READ],
)
def get_insumo_types(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[NamedCatalogRead]:
    return _serialize_named(list_insumo_types(db, tenant_id=tenant_context.current_tenant_id))


@router.post(
    "/catalog/insumo-types",
    response_model=NamedCatalogRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def post_insumo_type(
    payload: NamedCatalogCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    item = create_insumo_type(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)


@router.put(
    "/catalog/insumo-types/{insumo_type_id}",
    response_model=NamedCatalogRead,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def put_insumo_type(
    insumo_type_id: str,
    payload: NamedCatalogUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    insumo_type = get_tenant_entity_or_none(
        db,
        ProductInsumoType,
        tenant_id=tenant_context.current_tenant_id,
        entity_id=insumo_type_id,
    )
    if insumo_type is None:
        raise _not_found("Insumo type")
    item = update_insumo_type(
        db,
        insumo_type=insumo_type,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)


@router.get(
    "/catalog/units", response_model=list[ProductUnitRead], dependencies=[REQUIRE_CATALOG_READ]
)
def get_units(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductUnitRead]:
    return [
        ProductUnitRead.model_validate(item)
        for item in list_units(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.post(
    "/catalog/units",
    response_model=ProductUnitRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def post_unit(
    payload: ProductUnitCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductUnitRead:
    item = create_unit(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return ProductUnitRead.model_validate(item)


@router.put(
    "/catalog/units/{unit_id}",
    response_model=ProductUnitRead,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def put_unit(
    unit_id: str,
    payload: ProductUnitUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductUnitRead:
    unit = get_tenant_entity_or_none(
        db, ProductUnit, tenant_id=tenant_context.current_tenant_id, entity_id=unit_id
    )
    if unit is None:
        raise _not_found("Unit")
    item = update_unit(
        db,
        unit=unit,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return ProductUnitRead.model_validate(item)


@router.get(
    "/catalog/subcategories",
    response_model=list[NamedCatalogRead],
    dependencies=[REQUIRE_CATALOG_READ],
)
def get_subcategories(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[NamedCatalogRead]:
    return _serialize_named(list_subcategories(db, tenant_id=tenant_context.current_tenant_id))


@router.post(
    "/catalog/subcategories",
    response_model=NamedCatalogRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def post_subcategory(
    payload: NamedCatalogCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    item = create_subcategory(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)


@router.put(
    "/catalog/subcategories/{subcategory_id}",
    response_model=NamedCatalogRead,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def put_subcategory(
    subcategory_id: str,
    payload: NamedCatalogUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    subcategory = get_tenant_entity_or_none(
        db,
        ProductSubcategory,
        tenant_id=tenant_context.current_tenant_id,
        entity_id=subcategory_id,
    )
    if subcategory is None:
        raise _not_found("Subcategory")
    item = update_subcategory(
        db,
        subcategory=subcategory,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)


@router.get(
    "/catalog/groups", response_model=list[ProductGroupRead], dependencies=[REQUIRE_CATALOG_READ]
)
def get_groups(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductGroupRead]:
    return [
        ProductGroupRead.model_validate(item)
        for item in list_groups(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.post(
    "/catalog/groups",
    response_model=ProductGroupRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def post_group(
    payload: ProductGroupCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductGroupRead:
    item = create_group(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return ProductGroupRead.model_validate(item)


@router.put(
    "/catalog/groups/{group_id}",
    response_model=ProductGroupRead,
    dependencies=[REQUIRE_CATALOG_MANAGE],
)
def put_group(
    group_id: str,
    payload: ProductGroupUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductGroupRead:
    group = get_tenant_entity_or_none(
        db, ProductGroup, tenant_id=tenant_context.current_tenant_id, entity_id=group_id
    )
    if group is None:
        raise _not_found("Group")
    item = update_group(
        db,
        group=group,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return ProductGroupRead.model_validate(item)


@router.get(
    "/catalog/conditions",
    response_model=list[ProductConditionRead],
    dependencies=[REQUIRE_CATALOG_READ],
)
def get_conditions(db: Session = DB_SESSION) -> list[ProductConditionRead]:
    return [ProductConditionRead.model_validate(item) for item in list_conditions(db)]


@router.get(
    "/catalog/status",
    response_model=list[ProductStatusRead],
    dependencies=[REQUIRE_CATALOG_READ],
)
def get_status_catalog(db: Session = DB_SESSION) -> list[ProductStatusRead]:
    return [ProductStatusRead.model_validate(item) for item in list_status(db)]


@router.get("/products", response_model=ProductPageRead, dependencies=[REQUIRE_PRODUCT_READ])
def get_products(
    sku: str | None = Query(default=None),
    name: str | None = Query(default=None),
    line_id: str | None = Query(default=None),
    brand_id: str | None = Query(default=None),
    condition_code: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductPageRead:
    items, total = list_products(
        db,
        tenant_id=tenant_context.current_tenant_id,
        sku=sku,
        name=name,
        line_id=line_id,
        brand_id=brand_id,
        condition_code=condition_code,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return ProductPageRead(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/products/search",
    response_model=list[ProductSearchItemRead],
    dependencies=[REQUIRE_PRODUCT_READ],
)
def get_product_search(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductSearchItemRead]:
    return search_products(db, tenant_id=tenant_context.current_tenant_id, query=q, limit=limit)


@router.get(
    "/products/{product_id}", response_model=ProductRead, dependencies=[REQUIRE_PRODUCT_READ]
)
def get_product_detail(
    product_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductRead:
    product = get_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
    if product is None:
        raise _not_found("Product")
    result = serialize_product(product)

    def _name(model: type, pk: str | None) -> str | None:
        if pk is None:
            return None
        row = db.get(model, pk)
        return row.name if row else None

    result.line_name = _name(ProductLine, product.line_id)
    result.subline_name = _name(ProductSubline, product.subline_id)
    result.brand_name = _name(ProductBrand, product.brand_id)
    result.unit_name = _name(ProductUnit, product.unit_id)
    result.insumo_type_name = _name(ProductInsumoType, product.insumo_type_id)
    result.subcategory_name = _name(ProductSubcategory, product.subcategory_id)
    result.group_name = _name(ProductGroup, product.group_id)
    result.condition_name = _name(ProductCondition, product.condition_code)
    result.status_name = _name(ProductStatus, product.status_code)
    return result


@router.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_PRODUCT_CREATE],
)
def post_product(
    payload: ProductCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductRead:
    try:
        product = create_product(
            db,
            tenant_id=tenant_context.current_tenant_id,
            actor_user_id=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return serialize_product(product)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.put(
    "/products/{product_id}", response_model=ProductRead, dependencies=[REQUIRE_PRODUCT_UPDATE]
)
def put_product(
    product_id: str,
    payload: ProductUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductRead:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        updated = update_product(
            db,
            product=product,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return serialize_product(updated)
    except ValueError as exc:
        db.rollback()
        if str(exc) == "Product not found":
            raise _not_found("Product") from exc
        raise _bad_request(str(exc)) from exc


@router.patch(
    "/products/{product_id}/status",
    response_model=ProductRead,
    dependencies=[REQUIRE_PRODUCT_DELETE],
)
def patch_product_status(
    product_id: str,
    payload: ProductToggleActiveRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductRead:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        updated = toggle_product_active(
            db,
            product=product,
            is_active=payload.is_active,
            reason=payload.reason,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return serialize_product(updated)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.get(
    "/products/{product_id}/barcodes",
    response_model=list[ProductBarcodeRead],
    dependencies=[REQUIRE_PRODUCT_READ],
)
def get_product_barcodes(
    product_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductBarcodeRead]:
    _require_product_or_404(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
    return [
        ProductBarcodeRead.model_validate(item) for item in list_barcodes(db, product_id=product_id)
    ]


@router.post(
    "/products/{product_id}/barcodes",
    response_model=ProductBarcodeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_PRODUCT_UPDATE],
)
def post_product_barcode(
    product_id: str,
    payload: ProductBarcodeCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductBarcodeRead:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        item = create_barcode(
            db,
            product=product,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductBarcodeRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.put(
    "/products/{product_id}/barcodes/{barcode_id}",
    response_model=ProductBarcodeRead,
    dependencies=[REQUIRE_PRODUCT_UPDATE],
)
def put_product_barcode(
    product_id: str,
    barcode_id: str,
    payload: ProductBarcodeUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductBarcodeRead:
    try:
        require_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
        barcode = require_barcode(db, product_id=product_id, barcode_id=barcode_id)
        item = update_barcode(
            db,
            barcode=barcode,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductBarcodeRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.delete(
    "/products/{product_id}/barcodes/{barcode_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[REQUIRE_PRODUCT_UPDATE],
)
def delete_product_barcode(
    product_id: str,
    barcode_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> None:
    try:
        require_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
        barcode = require_barcode(db, product_id=product_id, barcode_id=barcode_id)
        delete_barcode(
            db, barcode=barcode, action_context=build_action_context(request, tenant_context)
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.post(
    "/products/{product_id}/barcodes/{barcode_id}/set-primary",
    response_model=ProductBarcodeRead,
    dependencies=[REQUIRE_PRODUCT_UPDATE],
)
def post_set_primary_barcode(
    product_id: str,
    barcode_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductBarcodeRead:
    try:
        require_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
        barcode = require_barcode(db, product_id=product_id, barcode_id=barcode_id)
        item = set_primary_barcode(
            db,
            barcode=barcode,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductBarcodeRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.get(
    "/products/{product_id}/prices",
    response_model=list[ProductPriceRead],
    dependencies=[REQUIRE_PRICE_READ],
)
def get_product_prices(
    product_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductPriceRead]:
    _require_product_or_404(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
    return [
        ProductPriceRead.model_validate(item) for item in list_prices(db, product_id=product_id)
    ]


@router.post(
    "/products/{product_id}/prices",
    response_model=ProductPriceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_PRICE_MANAGE],
)
def post_product_price(
    product_id: str,
    payload: ProductPriceCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductPriceRead:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        item = create_price(
            db,
            product=product,
            actor_user_id=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductPriceRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.post(
    "/products/{product_id}/prices/{price_id}/supersede",
    response_model=ProductPriceRead,
    dependencies=[REQUIRE_PRICE_MANAGE],
)
def post_supersede_price(
    product_id: str,
    price_id: str,
    payload: ProductPriceSupersedeRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductPriceRead:
    try:
        require_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
        price = require_price(db, product_id=product_id, price_id=price_id)
        item = supersede_price(
            db,
            price=price,
            actor_user_id=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductPriceRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.post(
    "/products/{product_id}/prices/update-all",
    response_model=list[ProductPriceRead],
    dependencies=[REQUIRE_PRICE_MANAGE],
)
def post_update_all_prices(
    product_id: str,
    payload: ProductPriceBulkUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductPriceRead]:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        items = update_all_prices(
            db,
            product=product,
            actor_user_id=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return [ProductPriceRead.model_validate(item) for item in items]
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.get(
    "/products/{product_id}/costs",
    response_model=list[ProductCostRead],
    dependencies=[REQUIRE_COST_READ],
)
def get_product_costs(
    product_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductCostRead]:
    _require_product_or_404(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
    return [ProductCostRead.model_validate(item) for item in list_costs(db, product_id=product_id)]


@router.post(
    "/products/{product_id}/costs",
    response_model=ProductCostRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_COST_MANAGE],
)
def post_product_cost(
    product_id: str,
    payload: ProductCostCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductCostRead:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        item = create_cost(
            db,
            product=product,
            actor_user_id=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductCostRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.post(
    "/products/{product_id}/costs/{cost_id}/supersede",
    response_model=ProductCostRead,
    dependencies=[REQUIRE_COST_MANAGE],
)
def post_supersede_cost(
    product_id: str,
    cost_id: str,
    payload: ProductCostSupersedeRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductCostRead:
    try:
        require_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
        cost = require_cost(db, product_id=product_id, cost_id=cost_id)
        item = supersede_cost(
            db,
            cost=cost,
            actor_user_id=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductCostRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.get(
    "/products/{product_id}/tax",
    response_model=list[ProductTaxConfigRead],
    dependencies=[REQUIRE_PRODUCT_READ],
)
def get_product_tax(
    product_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductTaxConfigRead]:
    _require_product_or_404(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
    return [
        ProductTaxConfigRead.model_validate(item)
        for item in list_tax_configs(db, product_id=product_id)
    ]


@router.put(
    "/products/{product_id}/tax",
    response_model=list[ProductTaxConfigRead],
    dependencies=[REQUIRE_PRODUCT_UPDATE],
)
def put_product_tax(
    product_id: str,
    payload: ProductTaxConfigUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductTaxConfigRead]:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        items = replace_tax_configs(
            db,
            product=product,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return [ProductTaxConfigRead.model_validate(item) for item in items]
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.get(
    "/products/{product_id}/adr",
    response_model=list[ProductAdrRead],
    dependencies=[REQUIRE_ADR_READ],
)
def get_product_adr(
    product_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductAdrRead]:
    _require_product_or_404(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
    return [
        ProductAdrRead.model_validate(item) for item in list_adr_configs(db, product_id=product_id)
    ]


@router.post(
    "/products/{product_id}/adr",
    response_model=ProductAdrRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_ADR_MANAGE],
)
def post_product_adr(
    product_id: str,
    payload: ProductAdrCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductAdrRead:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        item = create_adr_config(
            db,
            product=product,
            actor_user_id=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductAdrRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.put(
    "/products/{product_id}/adr/{adr_id}",
    response_model=ProductAdrRead,
    dependencies=[REQUIRE_ADR_MANAGE],
)
def put_product_adr(
    product_id: str,
    adr_id: str,
    payload: ProductAdrUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductAdrRead:
    try:
        require_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
        adr = require_adr_config(db, product_id=product_id, adr_id=adr_id)
        item = update_adr_config(
            db,
            adr=adr,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductAdrRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.post(
    "/products/{product_id}/adr/{adr_id}/expire",
    response_model=ProductAdrRead,
    dependencies=[REQUIRE_ADR_MANAGE],
)
def post_expire_adr(
    product_id: str,
    adr_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductAdrRead:
    try:
        require_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
        adr = require_adr_config(db, product_id=product_id, adr_id=adr_id)
        item = expire_adr_config(
            db,
            adr=adr,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductAdrRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.get(
    "/products/{product_id}/media",
    response_model=list[ProductMediaRead],
    dependencies=[REQUIRE_PRODUCT_READ],
)
def get_product_media(
    product_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductMediaRead]:
    _require_product_or_404(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
    return [ProductMediaRead.model_validate(item) for item in list_media(db, product_id=product_id)]


@router.post(
    "/products/{product_id}/media",
    response_model=ProductMediaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_MEDIA_MANAGE],
)
async def post_product_media(
    product_id: str,
    request: Request,
    media_type: str = Query(..., min_length=1, max_length=20),
    is_primary: bool = Query(default=False),
    file: UploadFile = UPLOAD_FILE,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductMediaRead:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        content = await file.read()
        item = create_media(
            db,
            product=product,
            media_type=media_type,
            is_primary=is_primary,
            filename=file.filename or "archivo",
            content=content,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductMediaRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.get(
    "/products/{product_id}/media/{media_id}/download/{stored_name}",
    dependencies=[REQUIRE_PRODUCT_READ],
)
def get_product_media_download(
    product_id: str,
    media_id: str,
    stored_name: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> FileResponse:
    _require_product_or_404(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
    media = require_media(db, product_id=product_id, media_id=media_id)
    path = resolve_media_path(media)
    if path.name != Path(stored_name).name or not path.exists():
        raise _not_found("Media file")
    return FileResponse(path)


@router.delete(
    "/products/{product_id}/media/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[REQUIRE_MEDIA_MANAGE],
)
def delete_product_media(
    product_id: str,
    media_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> None:
    try:
        require_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
        media = require_media(db, product_id=product_id, media_id=media_id)
        delete_media(db, media=media, action_context=build_action_context(request, tenant_context))
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.post(
    "/products/{product_id}/media/{media_id}/set-primary",
    response_model=ProductMediaRead,
    dependencies=[REQUIRE_MEDIA_MANAGE],
)
def post_set_primary_media(
    product_id: str,
    media_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductMediaRead:
    try:
        require_product(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
        media = require_media(db, product_id=product_id, media_id=media_id)
        item = set_primary_media(
            db,
            media=media,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductMediaRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.get(
    "/products/{product_id}/promotions",
    response_model=list[ProductPromotionRead],
    dependencies=[REQUIRE_PROMOTION_READ],
)
def get_product_promotions(
    product_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[ProductPromotionRead]:
    _require_product_or_404(db, tenant_id=tenant_context.current_tenant_id, product_id=product_id)
    return [
        ProductPromotionRead.model_validate(item)
        for item in list_promotions(db, product_id=product_id)
    ]


@router.post(
    "/products/{product_id}/promotions",
    response_model=ProductPromotionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_PROMOTION_MANAGE],
)
def post_product_promotion(
    product_id: str,
    payload: ProductPromotionCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductPromotionRead:
    try:
        product = require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
        )
        item = create_promotion(
            db,
            product=product,
            actor_user_id=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductPromotionRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.put(
    "/promotions/{promotion_id}",
    response_model=ProductPromotionRead,
    dependencies=[REQUIRE_PROMOTION_MANAGE],
)
def put_promotion(
    promotion_id: str,
    payload: ProductPromotionUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> ProductPromotionRead:
    try:
        promotion = require_promotion(db, promotion_id=promotion_id)
        require_product(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=promotion.product_id,
        )
        item = update_promotion(
            db,
            promotion=promotion,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ProductPromotionRead.model_validate(item)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.delete(
    "/promotions/{promotion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[REQUIRE_PROMOTION_MANAGE],
)
def delete_promotion_endpoint(
    promotion_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> None:
    try:
        promotion = require_promotion(db, promotion_id=promotion_id)
        require_product(
            db, tenant_id=tenant_context.current_tenant_id, product_id=promotion.product_id
        )
        delete_promotion(
            db,
            promotion=promotion,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc
