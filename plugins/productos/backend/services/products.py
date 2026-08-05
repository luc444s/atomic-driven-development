from __future__ import annotations

from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from plugins.productos.backend.common import (
    ProductosActionContext,
    audit_productos_action,
    emit_productos_event,
)
from plugins.productos.backend.models import (
    Product,
    ProductBarcode,
    ProductBrand,
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
    ProductCreateRequest,
    ProductListItemRead,
    ProductRead,
    ProductSearchItemRead,
    ProductUpdateRequest,
)
from plugins.productos.backend.services.catalog import require_condition, require_status


def get_product(db: Session, *, tenant_id: str, product_id: str) -> Product | None:
    return db.scalar(
        select(Product)
        .options(
            selectinload(Product.barcodes),
            selectinload(Product.prices),
            selectinload(Product.costs),
            selectinload(Product.taxes),
            selectinload(Product.adr_configs),
            selectinload(Product.media_items),
            selectinload(Product.promotions),
        )
        .where(Product.id == product_id, Product.tenant_id == tenant_id)
    )


def require_product(db: Session, *, tenant_id: str, product_id: str) -> Product:
    product = get_product(db, tenant_id=tenant_id, product_id=product_id)
    if product is None:
        raise ValueError("Producto no encontrado")
    return product


def create_product(
    db: Session,
    *,
    tenant_id: str,
    actor_user_id: str,
    payload: ProductCreateRequest,
    action_context: ProductosActionContext,
) -> Product:
    _validate_product_payload(db, tenant_id=tenant_id, payload=payload)
    product = Product(
        tenant_id=tenant_id,
        legacy_id=payload.legacy_id,
        sku=payload.sku.strip(),
        name=payload.name.strip(),
        description=payload.description,
        short_description=payload.short_description,
        line_id=payload.line_id,
        subline_id=payload.subline_id,
        brand_id=payload.brand_id,
        insumo_type_id=payload.insumo_type_id,
        unit_id=payload.unit_id,
        box_unit_id=payload.box_unit_id,
        qty_per_box=payload.qty_per_box,
        subcategory_id=payload.subcategory_id,
        group_id=payload.group_id,
        status_code=payload.status_code,
        condition_code=payload.condition_code,
        weight_kg=payload.weight_kg,
        default_weight_kg=payload.default_weight_kg,
        content_m3=payload.content_m3,
        country_code=payload.country_code,
        is_service=payload.is_service,
        is_active=payload.is_active,
        created_by=actor_user_id,
    )
    db.add(product)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.create",
        entity_type="product",
        entity_id=product.id,
        details={"sku": product.sku, "name": product.name},
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.product.created",
        entity_type="product",
        entity_id=product.id,
        payload={"product_id": product.id, "sku": product.sku, "name": product.name},
    )
    return require_product(db, tenant_id=tenant_id, product_id=product.id)


def update_product(
    db: Session,
    *,
    product: Product,
    payload: ProductUpdateRequest,
    action_context: ProductosActionContext,
) -> Product:
    effective = ProductCreateRequest(
        legacy_id=payload.legacy_id if payload.legacy_id is not None else product.legacy_id,
        sku=payload.sku if payload.sku is not None else product.sku,
        name=payload.name if payload.name is not None else product.name,
        description=payload.description if payload.description is not None else product.description,
        short_description=(
            payload.short_description
            if payload.short_description is not None
            else product.short_description
        ),
        line_id=payload.line_id if payload.line_id is not None else product.line_id,
        subline_id=payload.subline_id if payload.subline_id is not None else product.subline_id,
        brand_id=payload.brand_id if payload.brand_id is not None else product.brand_id,
        insumo_type_id=(
            payload.insumo_type_id if payload.insumo_type_id is not None else product.insumo_type_id
        ),
        unit_id=payload.unit_id if payload.unit_id is not None else product.unit_id,
        box_unit_id=payload.box_unit_id if payload.box_unit_id is not None else product.box_unit_id,
        qty_per_box=payload.qty_per_box if payload.qty_per_box is not None else product.qty_per_box,
        subcategory_id=(
            payload.subcategory_id if payload.subcategory_id is not None else product.subcategory_id
        ),
        group_id=payload.group_id if payload.group_id is not None else product.group_id,
        status_code=payload.status_code if payload.status_code is not None else product.status_code,
        condition_code=(
            payload.condition_code if payload.condition_code is not None else product.condition_code
        ),
        weight_kg=payload.weight_kg if payload.weight_kg is not None else product.weight_kg,
        default_weight_kg=(
            payload.default_weight_kg
            if payload.default_weight_kg is not None
            else product.default_weight_kg
        ),
        content_m3=payload.content_m3 if payload.content_m3 is not None else product.content_m3,
        country_code=payload.country_code
        if payload.country_code is not None
        else product.country_code,
        is_service=payload.is_service if payload.is_service is not None else product.is_service,
        is_active=payload.is_active if payload.is_active is not None else product.is_active,
    )
    _validate_product_payload(
        db,
        tenant_id=product.tenant_id,
        payload=effective,
        exclude_product_id=product.id,
    )
    changed_fields: list[str] = []
    for field in [
        "legacy_id",
        "sku",
        "name",
        "description",
        "short_description",
        "line_id",
        "subline_id",
        "brand_id",
        "insumo_type_id",
        "unit_id",
        "box_unit_id",
        "qty_per_box",
        "subcategory_id",
        "group_id",
        "status_code",
        "condition_code",
        "weight_kg",
        "content_m3",
        "country_code",
        "is_service",
        "is_active",
    ]:
        value = getattr(payload, field)
        if value is None:
            continue
        new_value = value.strip() if isinstance(value, str) else value
        if getattr(product, field) != new_value:
            setattr(product, field, new_value)
            changed_fields.append(field)
    db.add(product)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.update",
        entity_type="product",
        entity_id=product.id,
        details={"changed_fields": changed_fields},
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.product.updated",
        entity_type="product",
        entity_id=product.id,
        payload={"product_id": product.id, "changed_fields": changed_fields},
    )
    return require_product(db, tenant_id=product.tenant_id, product_id=product.id)


def list_products(
    db: Session,
    *,
    tenant_id: str,
    sku: str | None = None,
    name: str | None = None,
    line_id: str | None = None,
    brand_id: str | None = None,
    condition_code: str | None = None,
    is_active: bool | None = None,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[ProductListItemRead], int]:
    line_alias = ProductLine
    brand_alias = ProductBrand
    unit_alias = ProductUnit
    subcategory_alias = ProductSubcategory
    status_alias = ProductStatus
    condition_alias = ProductCondition
    stmt = (
        select(
            Product.id,
            Product.sku,
            Product.name,
            Product.line_id,
            line_alias.name.label("line_name"),
            Product.brand_id,
            brand_alias.name.label("brand_name"),
            Product.unit_id,
            unit_alias.name.label("unit_name"),
            Product.subcategory_id,
            subcategory_alias.name.label("subcategory_name"),
            Product.status_code,
            status_alias.name.label("status_name"),
            Product.condition_code,
            condition_alias.name.label("condition_name"),
            Product.is_service,
            Product.is_active,
            Product.created_at,
            Product.updated_at,
        )
        .join(line_alias, line_alias.id == Product.line_id)
        .join(unit_alias, unit_alias.id == Product.unit_id)
        .join(status_alias, status_alias.code == Product.status_code)
        .join(condition_alias, condition_alias.code == Product.condition_code)
        .outerjoin(brand_alias, brand_alias.id == Product.brand_id)
        .outerjoin(subcategory_alias, subcategory_alias.id == Product.subcategory_id)
        .where(Product.tenant_id == tenant_id)
    )
    count_stmt: Select[Any] = (
        select(func.count()).select_from(Product).where(Product.tenant_id == tenant_id)
    )
    if sku or name:
        search_conditions = []
        if sku:
            sku_pattern = f"%{sku.strip()}%"
            search_conditions.append(Product.sku.ilike(sku_pattern))
        if name:
            name_pattern = f"%{name.strip()}%"
            search_conditions.append(Product.name.ilike(name_pattern))
        search_filter = or_(*search_conditions)
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)
    if line_id:
        stmt = stmt.where(Product.line_id == line_id)
        count_stmt = count_stmt.where(Product.line_id == line_id)
    if brand_id:
        stmt = stmt.where(Product.brand_id == brand_id)
        count_stmt = count_stmt.where(Product.brand_id == brand_id)
    if condition_code:
        stmt = stmt.where(Product.condition_code == condition_code)
        count_stmt = count_stmt.where(Product.condition_code == condition_code)
    if is_active is not None:
        stmt = stmt.where(Product.is_active.is_(is_active))
        count_stmt = count_stmt.where(Product.is_active.is_(is_active))
    stmt = stmt.order_by(Product.name.asc()).limit(limit).offset(offset)
    rows = db.execute(stmt).all()
    total = db.scalar(count_stmt) or 0
    return (
        [
            ProductListItemRead(
                id=row.id,
                sku=row.sku,
                name=row.name,
                line_id=row.line_id,
                line_name=row.line_name,
                brand_id=row.brand_id,
                brand_name=row.brand_name,
                unit_id=row.unit_id,
                unit_name=row.unit_name,
                subcategory_id=row.subcategory_id,
                subcategory_name=row.subcategory_name,
                status_code=row.status_code,
                status_name=row.status_name,
                condition_code=row.condition_code,
                condition_name=row.condition_name,
                is_service=row.is_service,
                is_active=row.is_active,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ],
        total,
    )


def search_products(
    db: Session, *, tenant_id: str, query: str, limit: int = 10
) -> list[ProductSearchItemRead]:
    term = f"%{query.strip()}%"
    stmt = (
        select(Product, ProductBrand.name.label("brand_name"))
        .outerjoin(ProductBrand, ProductBrand.id == Product.brand_id)
        .outerjoin(ProductBarcode, ProductBarcode.product_id == Product.id)
        .where(
            Product.tenant_id == tenant_id,
            Product.is_active.is_(True),
            or_(
                Product.sku.ilike(term),
                Product.name.ilike(term),
                ProductBarcode.barcode.ilike(term),
            ),
        )
        .order_by(Product.name.asc())
        .distinct()
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [
        ProductSearchItemRead(
            id=product.id,
            sku=product.sku,
            name=product.name,
            brand_name=brand_name,
            condition_code=product.condition_code,
            is_active=product.is_active,
        )
        for product, brand_name in rows
    ]


def toggle_product_active(
    db: Session,
    *,
    product: Product,
    is_active: bool,
    reason: str | None,
    action_context: ProductosActionContext,
) -> Product:
    if product.is_active == is_active:
        return product
    previous = product.is_active
    product.is_active = is_active
    if not is_active and product.status_code == "ACTIVO":
        require_status(db, "INACTIVO")
        product.status_code = "INACTIVO"
    elif is_active and product.status_code == "INACTIVO":
        require_status(db, "ACTIVO")
        product.status_code = "ACTIVO"
    db.add(product)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.status_change",
        entity_type="product",
        entity_id=product.id,
        details={"previous": previous, "is_active": is_active, "reason": reason},
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.product.status_changed",
        entity_type="product",
        entity_id=product.id,
        payload={"product_id": product.id, "previous": previous, "is_active": is_active},
    )
    return require_product(db, tenant_id=product.tenant_id, product_id=product.id)


def serialize_product(product: Product) -> ProductRead:
    return ProductRead.model_validate(product)


def _validate_product_payload(
    db: Session,
    *,
    tenant_id: str,
    payload: ProductCreateRequest,
    exclude_product_id: str | None = None,
) -> None:
    _require_tenant_entity(db, ProductLine, tenant_id=tenant_id, entity_id=payload.line_id)
    if payload.subline_id is not None:
        subline = _require_tenant_entity(
            db, ProductSubline, tenant_id=tenant_id, entity_id=payload.subline_id
        )
        if subline.line_id != payload.line_id:
            raise ValueError("La sublínea no pertenece a la línea de producto")
    if payload.brand_id is not None:
        _require_tenant_entity(db, ProductBrand, tenant_id=tenant_id, entity_id=payload.brand_id)
    if payload.insumo_type_id is not None:
        _require_tenant_entity(
            db, ProductInsumoType, tenant_id=tenant_id, entity_id=payload.insumo_type_id
        )
    _require_tenant_entity(db, ProductUnit, tenant_id=tenant_id, entity_id=payload.unit_id)
    if payload.box_unit_id is not None:
        _require_tenant_entity(db, ProductUnit, tenant_id=tenant_id, entity_id=payload.box_unit_id)
    if payload.subcategory_id is not None:
        _require_tenant_entity(
            db, ProductSubcategory, tenant_id=tenant_id, entity_id=payload.subcategory_id
        )
    if payload.group_id is not None:
        _require_tenant_entity(db, ProductGroup, tenant_id=tenant_id, entity_id=payload.group_id)
    require_status(db, payload.status_code)
    require_condition(db, payload.condition_code)

    existing = db.scalar(
        select(Product).where(Product.tenant_id == tenant_id, Product.sku == payload.sku.strip())
    )
    if existing is not None and existing.id != exclude_product_id:
        raise ValueError("El SKU del producto ya existe")


def _require_tenant_entity(db: Session, model: type[Any], *, tenant_id: str, entity_id: str):
    entity = db.scalar(select(model).where(model.id == entity_id, model.tenant_id == tenant_id))
    if entity is None:
        raise ValueError(f"{model.__name__} not found")
    return entity
