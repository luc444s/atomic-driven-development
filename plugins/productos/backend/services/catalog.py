from __future__ import annotations

from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from plugins.productos.backend.common import (
    ProductosActionContext,
    audit_productos_action,
    emit_productos_event,
)
from plugins.productos.backend.models import (
    Product,
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
    NamedCatalogUpdateRequest,
    ProductGroupCreateRequest,
    ProductGroupUpdateRequest,
    ProductLineCreateRequest,
    ProductLineUpdateRequest,
    ProductSublineCreateRequest,
    ProductSublineUpdateRequest,
    ProductUnitCreateRequest,
    ProductUnitUpdateRequest,
)

CONDITION_SEEDS: tuple[dict[str, str | bool | None], ...] = (
    {
        "code": "PRODUCTO",
        "name": "Producto",
        "description": "Producto general",
        "is_active": True,
    },
    {"code": "GAS", "name": "Gas", "description": "Producto de gas", "is_active": True},
    {
        "code": "CILPRO",
        "name": "Cilindro propio",
        "description": "Envase propio",
        "is_active": True,
    },
    {
        "code": "CILCLI",
        "name": "Cilindro cliente",
        "description": "Envase del cliente",
        "is_active": True,
    },
    {
        "code": "CILPROV",
        "name": "Cilindro proveedor",
        "description": "Envase del proveedor",
        "is_active": True,
    },
    {
        "code": "CILGAR",
        "name": "Cilindro garantia",
        "description": "Envase en garantia",
        "is_active": True,
    },
    {
        "code": "SERVICIO",
        "name": "Servicio",
        "description": "Producto tipo servicio",
        "is_active": True,
    },
)

STATUS_SEEDS: tuple[dict[str, str | bool], ...] = (
    {"code": "ACTIVO", "name": "Activo", "is_active": True},
    {"code": "INACTIVO", "name": "Inactivo", "is_active": True},
    {"code": "OBSOLETO", "name": "Obsoleto", "is_active": True},
)


def ensure_static_catalogs_seeded(db: Session) -> None:
    has_conditions = db.scalar(select(ProductCondition.code).limit(1))
    if has_conditions is None:
        for seed in CONDITION_SEEDS:
            db.add(ProductCondition(**seed))

    has_status = db.scalar(select(ProductStatus.code).limit(1))
    if has_status is None:
        for seed in STATUS_SEEDS:
            db.add(ProductStatus(**seed))
    db.flush()


def list_conditions(db: Session) -> list[ProductCondition]:
    ensure_static_catalogs_seeded(db)
    return list(
        db.scalars(
            select(ProductCondition)
            .where(ProductCondition.is_active.is_(True))
            .order_by(ProductCondition.code.asc())
        ).all()
    )


def list_gas_products(db: Session, *, tenant_id: str) -> list[Product]:
    return list(
        db.scalars(
            select(Product)
            .where(
                Product.tenant_id == tenant_id,
                Product.is_active.is_(True),
            )
            .order_by(Product.name.asc())
        ).all()
    )


def list_status(db: Session) -> list[ProductStatus]:
    ensure_static_catalogs_seeded(db)
    return list(
        db.scalars(
            select(ProductStatus)
            .where(ProductStatus.is_active.is_(True))
            .order_by(ProductStatus.code.asc())
        ).all()
    )


def list_categories(db: Session, *, tenant_id: str) -> list[ProductCategory]:
    return _list_named_catalog(db, ProductCategory, tenant_id=tenant_id)


def list_lines(db: Session, *, tenant_id: str) -> list[ProductLine]:
    return _list_named_catalog(db, ProductLine, tenant_id=tenant_id)


def list_brands(db: Session, *, tenant_id: str) -> list[ProductBrand]:
    return _list_named_catalog(db, ProductBrand, tenant_id=tenant_id)


def list_insumo_types(db: Session, *, tenant_id: str) -> list[ProductInsumoType]:
    return _list_named_catalog(db, ProductInsumoType, tenant_id=tenant_id)


def list_subcategories(db: Session, *, tenant_id: str) -> list[ProductSubcategory]:
    return _list_named_catalog(db, ProductSubcategory, tenant_id=tenant_id)


def list_subline(db: Session, *, tenant_id: str) -> list[ProductSubline]:
    return list(
        db.scalars(
            select(ProductSubline)
            .where(ProductSubline.tenant_id == tenant_id)
            .order_by(ProductSubline.name.asc())
        ).all()
    )


def list_units(db: Session, *, tenant_id: str) -> list[ProductUnit]:
    return list(
        db.scalars(
            select(ProductUnit)
            .where(ProductUnit.tenant_id == tenant_id)
            .order_by(ProductUnit.name.asc())
        ).all()
    )


def list_groups(db: Session, *, tenant_id: str) -> list[ProductGroup]:
    return list(
        db.scalars(
            select(ProductGroup)
            .where(ProductGroup.tenant_id == tenant_id)
            .order_by(ProductGroup.name.asc())
        ).all()
    )


def create_category(
    db: Session,
    *,
    tenant_id: str,
    payload: NamedCatalogCreateRequest,
    action_context: ProductosActionContext,
) -> ProductCategory:
    return _create_named_catalog(
        db,
        ProductCategory,
        tenant_id=tenant_id,
        payload=payload,
        action_context=action_context,
        entity_type="category",
    )


def update_category(
    db: Session,
    *,
    category: ProductCategory,
    payload: NamedCatalogUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductCategory:
    return _update_named_catalog(
        db,
        category,
        payload=payload,
        action_context=action_context,
        entity_type="category",
    )


def create_line(
    db: Session,
    *,
    tenant_id: str,
    payload: ProductLineCreateRequest,
    action_context: ProductosActionContext,
) -> ProductLine:
    _validate_category_reference(db, tenant_id=tenant_id, category_id=payload.category_id)
    item = ProductLine(
        tenant_id=tenant_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        description=payload.description,
        category_id=payload.category_id,
    )
    _ensure_unique_catalog_code(db, ProductLine, tenant_id=tenant_id, code=item.code)
    db.add(item)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="catalog.line.create",
        entity_type="line",
        entity_id=item.id,
        details={"code": item.code, "name": item.name},
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.line.created",
        entity_type="line",
        entity_id=item.id,
        payload={"line_id": item.id, "code": item.code, "name": item.name},
    )
    return item


def update_line(
    db: Session,
    *,
    line: ProductLine,
    payload: ProductLineUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductLine:
    _validate_category_reference(db, tenant_id=line.tenant_id, category_id=payload.category_id)
    changed_fields = _apply_named_catalog_updates(line, payload)
    if payload.category_id != line.category_id:
        line.category_id = payload.category_id
        changed_fields.append("category_id")
    if payload.code is not None:
        _ensure_unique_catalog_code(
            db, ProductLine, tenant_id=line.tenant_id, code=line.code, exclude_id=line.id
        )
    db.add(line)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="catalog.line.update",
        entity_type="line",
        entity_id=line.id,
        details={"changed_fields": changed_fields},
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.line.updated",
        entity_type="line",
        entity_id=line.id,
        payload={"line_id": line.id, "changed_fields": changed_fields},
    )
    return line


def create_brand(
    db: Session,
    *,
    tenant_id: str,
    payload: NamedCatalogCreateRequest,
    action_context: ProductosActionContext,
) -> ProductBrand:
    item = _create_named_catalog(
        db,
        ProductBrand,
        tenant_id=tenant_id,
        payload=payload,
        action_context=action_context,
        entity_type="brand",
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.brand.created",
        entity_type="brand",
        entity_id=item.id,
        payload={"brand_id": item.id, "code": item.code, "name": item.name},
    )
    return item


def update_brand(
    db: Session,
    *,
    brand: ProductBrand,
    payload: NamedCatalogUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductBrand:
    item = _update_named_catalog(
        db,
        brand,
        payload=payload,
        action_context=action_context,
        entity_type="brand",
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.brand.updated",
        entity_type="brand",
        entity_id=item.id,
        payload={"brand_id": item.id, "code": item.code, "name": item.name},
    )
    return item


def create_insumo_type(
    db: Session,
    *,
    tenant_id: str,
    payload: NamedCatalogCreateRequest,
    action_context: ProductosActionContext,
) -> ProductInsumoType:
    return _create_named_catalog(
        db,
        ProductInsumoType,
        tenant_id=tenant_id,
        payload=payload,
        action_context=action_context,
        entity_type="insumo_type",
    )


def update_insumo_type(
    db: Session,
    *,
    insumo_type: ProductInsumoType,
    payload: NamedCatalogUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductInsumoType:
    return _update_named_catalog(
        db,
        insumo_type,
        payload=payload,
        action_context=action_context,
        entity_type="insumo_type",
    )


def create_subcategory(
    db: Session,
    *,
    tenant_id: str,
    payload: NamedCatalogCreateRequest,
    action_context: ProductosActionContext,
) -> ProductSubcategory:
    return _create_named_catalog(
        db,
        ProductSubcategory,
        tenant_id=tenant_id,
        payload=payload,
        action_context=action_context,
        entity_type="subcategory",
    )


def update_subcategory(
    db: Session,
    *,
    subcategory: ProductSubcategory,
    payload: NamedCatalogUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductSubcategory:
    return _update_named_catalog(
        db,
        subcategory,
        payload=payload,
        action_context=action_context,
        entity_type="subcategory",
    )


def create_subline(
    db: Session,
    *,
    tenant_id: str,
    payload: ProductSublineCreateRequest,
    action_context: ProductosActionContext,
) -> ProductSubline:
    _require_tenant_entity(db, ProductLine, tenant_id=tenant_id, entity_id=payload.line_id)
    _ensure_unique_subline_code(db, tenant_id=tenant_id, line_id=payload.line_id, code=payload.code)
    item = ProductSubline(
        tenant_id=tenant_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        line_id=payload.line_id,
    )
    db.add(item)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="catalog.subline.create",
        entity_type="subline",
        entity_id=item.id,
        details={"code": item.code, "line_id": item.line_id},
    )
    return item


def update_subline(
    db: Session,
    *,
    subline: ProductSubline,
    payload: ProductSublineUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductSubline:
    line_id = payload.line_id if payload.line_id is not None else subline.line_id
    _require_tenant_entity(db, ProductLine, tenant_id=subline.tenant_id, entity_id=line_id)
    changed_fields: list[str] = []
    if payload.code is not None and payload.code.strip() != subline.code:
        subline.code = payload.code.strip()
        changed_fields.append("code")
    if payload.name is not None and payload.name.strip() != subline.name:
        subline.name = payload.name.strip()
        changed_fields.append("name")
    if line_id != subline.line_id:
        subline.line_id = line_id
        changed_fields.append("line_id")
    if payload.is_active is not None and payload.is_active != subline.is_active:
        subline.is_active = payload.is_active
        changed_fields.append("is_active")
    _ensure_unique_subline_code(
        db,
        tenant_id=subline.tenant_id,
        line_id=subline.line_id,
        code=subline.code,
        exclude_id=subline.id,
    )
    db.add(subline)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="catalog.subline.update",
        entity_type="subline",
        entity_id=subline.id,
        details={"changed_fields": changed_fields},
    )
    return subline


def create_unit(
    db: Session,
    *,
    tenant_id: str,
    payload: ProductUnitCreateRequest,
    action_context: ProductosActionContext,
) -> ProductUnit:
    _ensure_unique_catalog_code(db, ProductUnit, tenant_id=tenant_id, code=payload.code)
    item = ProductUnit(
        tenant_id=tenant_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        equivalencia=payload.equivalencia,
        m3_factor=payload.m3_factor,
        liter_factor=payload.liter_factor,
        kg_factor=payload.kg_factor,
    )
    db.add(item)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="catalog.unit.create",
        entity_type="unit",
        entity_id=item.id,
        details={"code": item.code, "name": item.name},
    )
    return item


def update_unit(
    db: Session,
    *,
    unit: ProductUnit,
    payload: ProductUnitUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductUnit:
    changed_fields: list[str] = []
    for field in ["code", "name", "equivalencia", "m3_factor", "liter_factor", "kg_factor"]:
        value = getattr(payload, field)
        if value is None:
            continue
        current = getattr(unit, field)
        new_value = value.strip() if isinstance(value, str) else value
        if current != new_value:
            setattr(unit, field, new_value)
            changed_fields.append(field)
    if payload.is_active is not None and payload.is_active != unit.is_active:
        unit.is_active = payload.is_active
        changed_fields.append("is_active")
    _ensure_unique_catalog_code(
        db, ProductUnit, tenant_id=unit.tenant_id, code=unit.code, exclude_id=unit.id
    )
    db.add(unit)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="catalog.unit.update",
        entity_type="unit",
        entity_id=unit.id,
        details={"changed_fields": changed_fields},
    )
    return unit


def create_group(
    db: Session,
    *,
    tenant_id: str,
    payload: ProductGroupCreateRequest,
    action_context: ProductosActionContext,
) -> ProductGroup:
    _validate_group_references(
        db,
        tenant_id=tenant_id,
        gas_product_id=payload.gas_product_id,
        line_id=payload.line_id,
        subline_id=payload.subline_id,
        unit_id=payload.unit_id,
    )
    _ensure_unique_catalog_code(db, ProductGroup, tenant_id=tenant_id, code=payload.code)
    item = ProductGroup(
        tenant_id=tenant_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        gas_product_id=payload.gas_product_id,
        line_id=payload.line_id,
        subline_id=payload.subline_id,
        unit_id=payload.unit_id,
    )
    db.add(item)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="catalog.group.create",
        entity_type="group",
        entity_id=item.id,
        details={"code": item.code, "name": item.name},
    )
    return item


def update_group(
    db: Session,
    *,
    group: ProductGroup,
    payload: ProductGroupUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductGroup:
    gas_product_id = (
        payload.gas_product_id if payload.gas_product_id is not None else group.gas_product_id
    )
    line_id = payload.line_id if payload.line_id is not None else group.line_id
    subline_id = payload.subline_id if payload.subline_id is not None else group.subline_id
    unit_id = payload.unit_id if payload.unit_id is not None else group.unit_id
    _validate_group_references(
        db,
        tenant_id=group.tenant_id,
        gas_product_id=gas_product_id,
        line_id=line_id,
        subline_id=subline_id,
        unit_id=unit_id,
    )
    changed_fields: list[str] = []
    for field in ["code", "name", "gas_product_id", "line_id", "subline_id", "unit_id"]:
        value = getattr(payload, field)
        if value is None:
            continue
        current = getattr(group, field)
        new_value = value.strip() if isinstance(value, str) else value
        if current != new_value:
            setattr(group, field, new_value)
            changed_fields.append(field)
    if payload.is_active is not None and payload.is_active != group.is_active:
        group.is_active = payload.is_active
        changed_fields.append("is_active")
    _ensure_unique_catalog_code(
        db, ProductGroup, tenant_id=group.tenant_id, code=group.code, exclude_id=group.id
    )
    db.add(group)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="catalog.group.update",
        entity_type="group",
        entity_id=group.id,
        details={"changed_fields": changed_fields},
    )
    return group


def get_tenant_entity_or_none(db: Session, model: type[Any], *, tenant_id: str, entity_id: str):
    return db.scalar(select(model).where(model.id == entity_id, model.tenant_id == tenant_id))


def require_tenant_entity(db: Session, model: type[Any], *, tenant_id: str, entity_id: str):
    entity = get_tenant_entity_or_none(db, model, tenant_id=tenant_id, entity_id=entity_id)
    if entity is None:
        raise ValueError(f"{model.__name__} not found")
    return entity


def require_status(db: Session, code: str) -> ProductStatus:
    ensure_static_catalogs_seeded(db)
    status = db.get(ProductStatus, code)
    if status is None or not status.is_active:
        raise ValueError("Estado de producto no encontrado")
    return status


def require_condition(db: Session, code: str) -> ProductCondition:
    ensure_static_catalogs_seeded(db)
    condition = db.get(ProductCondition, code)
    if condition is None or not condition.is_active:
        raise ValueError("Condición de producto no encontrada")
    return condition


def _list_named_catalog(db: Session, model: type[Any], *, tenant_id: str):
    stmt: Select[Any] = select(model).where(model.tenant_id == tenant_id).order_by(model.name.asc())
    return list(db.scalars(stmt).all())


def _create_named_catalog(
    db: Session,
    model: type[Any],
    *,
    tenant_id: str,
    payload: NamedCatalogCreateRequest,
    action_context: ProductosActionContext,
    entity_type: str,
):
    _ensure_unique_catalog_code(db, model, tenant_id=tenant_id, code=payload.code)
    item = model(
        tenant_id=tenant_id,
        code=payload.code.strip(),
        name=payload.name.strip(),
        description=payload.description,
    )
    db.add(item)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action=f"catalog.{entity_type}.create",
        entity_type=entity_type,
        entity_id=item.id,
        details={"code": item.code, "name": item.name},
    )
    return item


def _update_named_catalog(
    db: Session,
    item: Any,
    *,
    payload: NamedCatalogUpdateRequest,
    action_context: ProductosActionContext,
    entity_type: str,
):
    changed_fields = _apply_named_catalog_updates(item, payload)
    if payload.code is not None:
        _ensure_unique_catalog_code(
            db,
            type(item),
            tenant_id=item.tenant_id,
            code=item.code,
            exclude_id=item.id,
        )
    db.add(item)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action=f"catalog.{entity_type}.update",
        entity_type=entity_type,
        entity_id=item.id,
        details={"changed_fields": changed_fields},
    )
    return item


def _apply_named_catalog_updates(item: Any, payload: Any) -> list[str]:
    changed_fields: list[str] = []
    for field in ["code", "name", "description"]:
        value = getattr(payload, field)
        if value is None:
            continue
        new_value = value.strip() if isinstance(value, str) else value
        if getattr(item, field) != new_value:
            setattr(item, field, new_value)
            changed_fields.append(field)
    if payload.is_active is not None and payload.is_active != item.is_active:
        item.is_active = payload.is_active
        changed_fields.append("is_active")
    return changed_fields


def _ensure_unique_catalog_code(
    db: Session,
    model: type[Any],
    *,
    tenant_id: str,
    code: str,
    exclude_id: str | None = None,
) -> None:
    stmt = select(model).where(model.tenant_id == tenant_id, model.code == code.strip())
    existing = db.scalar(stmt)
    if existing is not None and getattr(existing, "id", None) != exclude_id:
        raise ValueError(f"{model.__name__} code already exists")


def _ensure_unique_subline_code(
    db: Session,
    *,
    tenant_id: str,
    line_id: str,
    code: str,
    exclude_id: str | None = None,
) -> None:
    stmt = select(ProductSubline).where(
        ProductSubline.tenant_id == tenant_id,
        ProductSubline.line_id == line_id,
        ProductSubline.code == code.strip(),
    )
    existing = db.scalar(stmt)
    if existing is not None and existing.id != exclude_id:
        raise ValueError("El código de sublínea ya existe")


def _validate_category_reference(db: Session, *, tenant_id: str, category_id: str | None) -> None:
    if category_id is None:
        return
    _require_tenant_entity(db, ProductCategory, tenant_id=tenant_id, entity_id=category_id)


def _validate_group_references(
    db: Session,
    *,
    tenant_id: str,
    gas_product_id: str | None,
    line_id: str | None,
    subline_id: str | None,
    unit_id: str | None,
) -> None:
    from plugins.productos.backend.models import Product

    if gas_product_id is not None:
        _require_tenant_entity(db, Product, tenant_id=tenant_id, entity_id=gas_product_id)
    if line_id is not None:
        _require_tenant_entity(db, ProductLine, tenant_id=tenant_id, entity_id=line_id)
    if subline_id is not None:
        _require_tenant_entity(db, ProductSubline, tenant_id=tenant_id, entity_id=subline_id)
    if unit_id is not None:
        _require_tenant_entity(db, ProductUnit, tenant_id=tenant_id, entity_id=unit_id)


def _require_tenant_entity(db: Session, model: type[Any], *, tenant_id: str, entity_id: str):
    entity = get_tenant_entity_or_none(db, model, tenant_id=tenant_id, entity_id=entity_id)
    if entity is None:
        raise ValueError(f"{model.__name__} not found")
    return entity
