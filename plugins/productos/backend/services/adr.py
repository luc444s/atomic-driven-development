from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.productos.backend.common import (
    ProductosActionContext,
    audit_productos_action,
    emit_productos_event,
)
from plugins.productos.backend.models import Product, ProductAdr, ProductSubline
from plugins.productos.backend.schemas import ProductAdrCreateRequest, ProductAdrUpdateRequest
from plugins.productos.backend.services.catalog import require_tenant_entity

CRYOGENIC_RECIPE_REQUIRED_MESSAGE = (
    "La receta criogenica requiere source_product_id, source_quantity_liters, "
    "net_weight_kg y net_volume_m3"
)


def list_adr_configs(db: Session, *, product_id: str) -> list[ProductAdr]:
    return list(
        db.scalars(
            select(ProductAdr)
            .where(ProductAdr.product_id == product_id)
            .order_by(ProductAdr.valid_from.desc())
        ).all()
    )


def create_adr_config(
    db: Session,
    *,
    product: Product,
    actor_user_id: str,
    payload: ProductAdrCreateRequest,
    action_context: ProductosActionContext,
) -> ProductAdr:
    _validate_adr_payload(
        db,
        tenant_id=product.tenant_id,
        result_product_id=product.id,
        values={
            "source_product_id": payload.source_product_id,
            "source_quantity_liters": payload.source_quantity_liters,
            "net_weight_kg": payload.net_weight_kg,
            "net_volume_m3": payload.net_volume_m3,
            "subline_id": payload.subline_id,
        },
    )
    _close_active_adr(db, product_id=product.id, valid_from=payload.valid_from)
    item = ProductAdr(
        tenant_id=product.tenant_id,
        product_id=product.id,
        source_product_id=payload.source_product_id,
        source_quantity_liters=payload.source_quantity_liters,
        category=payload.category,
        packaging_type=payload.packaging_type,
        net_weight_kg=payload.net_weight_kg,
        net_volume_m3=payload.net_volume_m3,
        un_number=payload.un_number,
        cargo_description=payload.cargo_description,
        label=payload.label,
        tunnel_restriction=payload.tunnel_restriction,
        subline_id=payload.subline_id,
        factor=payload.factor,
        points=payload.points,
        unit_measure=payload.unit_measure,
        valid_from=payload.valid_from,
        created_by=actor_user_id,
    )
    db.add(item)
    db.flush()
    _audit_emit_adr(db, product=product, adr=item, action_context=action_context, action="create")
    return item


def update_adr_config(
    db: Session,
    *,
    adr: ProductAdr,
    payload: ProductAdrUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductAdr:
    today = date.today()
    if adr.valid_to is None and adr.valid_from <= today:
        raise ValueError("Las configuraciones ADR activas no pueden editarse directamente")
    next_values = {
        "source_product_id": payload.source_product_id
        if payload.source_product_id is not None
        else adr.source_product_id,
        "source_quantity_liters": payload.source_quantity_liters
        if payload.source_quantity_liters is not None
        else adr.source_quantity_liters,
        "net_weight_kg": payload.net_weight_kg
        if payload.net_weight_kg is not None
        else adr.net_weight_kg,
        "net_volume_m3": payload.net_volume_m3
        if payload.net_volume_m3 is not None
        else adr.net_volume_m3,
        "subline_id": payload.subline_id if payload.subline_id is not None else adr.subline_id,
    }
    _validate_adr_payload(
        db,
        tenant_id=adr.tenant_id,
        result_product_id=adr.product_id,
        values=next_values,
    )
    changed_fields: list[str] = []
    for field in [
        "source_product_id",
        "source_quantity_liters",
        "category",
        "packaging_type",
        "net_weight_kg",
        "net_volume_m3",
        "un_number",
        "cargo_description",
        "label",
        "tunnel_restriction",
        "subline_id",
        "factor",
        "points",
        "unit_measure",
        "valid_from",
        "valid_to",
    ]:
        value = getattr(payload, field)
        if value is None:
            continue
        if getattr(adr, field) != value:
            setattr(adr, field, value)
            changed_fields.append(field)
    db.add(adr)
    db.flush()
    product = db.get(Product, adr.product_id)
    if product is None:
        raise ValueError("Producto no encontrado")
    _audit_emit_adr(
        db,
        product=product,
        adr=adr,
        action_context=action_context,
        action="update",
        changed_fields=changed_fields,
    )
    return adr


def expire_adr_config(
    db: Session,
    *,
    adr: ProductAdr,
    action_context: ProductosActionContext,
) -> ProductAdr:
    adr.valid_to = date.today()
    db.add(adr)
    db.flush()
    product = db.get(Product, adr.product_id)
    if product is None:
        raise ValueError("Producto no encontrado")
    _audit_emit_adr(db, product=product, adr=adr, action_context=action_context, action="expire")
    return adr


def require_adr_config(db: Session, *, product_id: str, adr_id: str) -> ProductAdr:
    adr = db.scalar(
        select(ProductAdr).where(ProductAdr.product_id == product_id, ProductAdr.id == adr_id)
    )
    if adr is None:
        raise ValueError("ADR de producto no encontrado")
    return adr


def _close_active_adr(db: Session, *, product_id: str, valid_from: date) -> None:
    active = db.scalar(
        select(ProductAdr).where(ProductAdr.product_id == product_id, ProductAdr.valid_to.is_(None))
    )
    if active is not None:
        active.valid_to = valid_from - timedelta(days=1)
        db.add(active)
        db.flush()


def _audit_emit_adr(
    db: Session,
    *,
    product: Product,
    adr: ProductAdr,
    action_context: ProductosActionContext,
    action: str,
    changed_fields: list[str] | None = None,
) -> None:
    audit_productos_action(
        db,
        context=action_context,
        action=f"product.adr.{action}",
        entity_type="product_adr",
        entity_id=adr.id,
        details={
            "product_id": product.id,
            "un_number": adr.un_number,
            "source_product_id": adr.source_product_id,
            "source_quantity_liters": float(adr.source_quantity_liters)
            if adr.source_quantity_liters is not None
            else None,
            "changed_fields": changed_fields or [],
        },
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.product.adr_updated",
        entity_type="product",
        entity_id=product.id,
        payload={"product_id": product.id, "adr_id": adr.id, "action": action},
    )


def _validate_adr_payload(
    db: Session,
    *,
    tenant_id: str,
    result_product_id: str,
    values: dict[str, object],
) -> None:
    subline_id = values.get("subline_id")
    if isinstance(subline_id, str):
        require_tenant_entity(db, ProductSubline, tenant_id=tenant_id, entity_id=subline_id)

    source_product_id = values.get("source_product_id")
    source_quantity_liters = values.get("source_quantity_liters")
    net_weight_kg = values.get("net_weight_kg")
    net_volume_m3 = values.get("net_volume_m3")
    has_cryogenic_recipe = source_product_id is not None or source_quantity_liters is not None
    if not has_cryogenic_recipe:
        return

    if not isinstance(source_product_id, str) or not source_product_id.strip():
        raise ValueError(CRYOGENIC_RECIPE_REQUIRED_MESSAGE)
    if source_product_id == result_product_id:
        raise ValueError("source_product_id debe ser distinto del producto resultado")
    require_tenant_entity(db, Product, tenant_id=tenant_id, entity_id=source_product_id)

    for field_name, value in {
        "source_quantity_liters": source_quantity_liters,
        "net_weight_kg": net_weight_kg,
        "net_volume_m3": net_volume_m3,
    }.items():
        if value is None:
            raise ValueError(CRYOGENIC_RECIPE_REQUIRED_MESSAGE)
        if not isinstance(value, (int, float, Decimal)) or float(value) <= 0:
            raise ValueError(f"{field_name} debe ser mayor que cero en la receta criogenica")
