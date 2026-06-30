from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.productos.backend.common import (
    ProductosActionContext,
    audit_productos_action,
    emit_productos_event,
)
from plugins.productos.backend.models import Product, ProductBarcode
from plugins.productos.backend.schemas import (
    ProductBarcodeCreateRequest,
    ProductBarcodeUpdateRequest,
)


def list_barcodes(db: Session, *, product_id: str) -> list[ProductBarcode]:
    return list(
        db.scalars(
            select(ProductBarcode)
            .where(ProductBarcode.product_id == product_id)
            .order_by(ProductBarcode.is_primary.desc(), ProductBarcode.created_at.asc())
        ).all()
    )


def get_barcode(db: Session, *, product_id: str, barcode_id: str) -> ProductBarcode | None:
    return db.scalar(
        select(ProductBarcode).where(
            ProductBarcode.product_id == product_id, ProductBarcode.id == barcode_id
        )
    )


def require_barcode(db: Session, *, product_id: str, barcode_id: str) -> ProductBarcode:
    barcode = get_barcode(db, product_id=product_id, barcode_id=barcode_id)
    if barcode is None:
        raise ValueError("Código de barras no encontrado")
    return barcode


def create_barcode(
    db: Session,
    *,
    product: Product,
    payload: ProductBarcodeCreateRequest,
    action_context: ProductosActionContext,
) -> ProductBarcode:
    _ensure_unique_barcode(
        db,
        tenant_id=product.tenant_id,
        barcode_type=payload.barcode_type,
        barcode=payload.barcode,
    )
    item = ProductBarcode(
        tenant_id=product.tenant_id,
        product_id=product.id,
        barcode_type=payload.barcode_type.strip().upper(),
        barcode=payload.barcode.strip(),
        is_primary=payload.is_primary,
        is_active=payload.is_active,
    )
    if item.is_primary:
        _clear_primary_barcode(db, product_id=product.id)
    db.add(item)
    db.flush()
    if not _has_primary_barcode(db, product_id=product.id):
        item.is_primary = True
        db.add(item)
        db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.barcode.create",
        entity_type="product_barcode",
        entity_id=item.id,
        details={"product_id": product.id, "barcode_type": item.barcode_type},
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.product.barcode_added",
        entity_type="product",
        entity_id=product.id,
        payload={
            "product_id": product.id,
            "barcode_id": item.id,
            "barcode_type": item.barcode_type,
        },
    )
    return item


def update_barcode(
    db: Session,
    *,
    barcode: ProductBarcode,
    payload: ProductBarcodeUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductBarcode:
    new_type = (
        payload.barcode_type.strip().upper()
        if payload.barcode_type is not None
        else barcode.barcode_type
    )
    new_value = payload.barcode.strip() if payload.barcode is not None else barcode.barcode
    _ensure_unique_barcode(
        db,
        tenant_id=barcode.tenant_id,
        barcode_type=new_type,
        barcode=new_value,
        exclude_id=barcode.id,
    )
    changed_fields: list[str] = []
    if new_type != barcode.barcode_type:
        barcode.barcode_type = new_type
        changed_fields.append("barcode_type")
    if new_value != barcode.barcode:
        barcode.barcode = new_value
        changed_fields.append("barcode")
    if payload.is_active is not None and payload.is_active != barcode.is_active:
        barcode.is_active = payload.is_active
        changed_fields.append("is_active")
    if payload.is_primary is not None and payload.is_primary != barcode.is_primary:
        if payload.is_primary:
            _clear_primary_barcode(db, product_id=barcode.product_id)
        barcode.is_primary = payload.is_primary
        changed_fields.append("is_primary")
    if not _has_primary_barcode(db, product_id=barcode.product_id):
        barcode.is_primary = True
    db.add(barcode)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.barcode.update",
        entity_type="product_barcode",
        entity_id=barcode.id,
        details={"changed_fields": changed_fields},
    )
    return barcode


def delete_barcode(
    db: Session,
    *,
    barcode: ProductBarcode,
    action_context: ProductosActionContext,
) -> None:
    product_id = barcode.product_id
    was_primary = barcode.is_primary
    db.delete(barcode)
    db.flush()
    replacement = db.scalar(
        select(ProductBarcode)
        .where(ProductBarcode.product_id == product_id)
        .order_by(ProductBarcode.created_at.asc())
        .limit(1)
    )
    if was_primary and replacement is not None:
        replacement.is_primary = True
        db.add(replacement)
        db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.barcode.delete",
        entity_type="product_barcode",
        entity_id=barcode.id,
        details={"product_id": product_id},
    )


def set_primary_barcode(
    db: Session,
    *,
    barcode: ProductBarcode,
    action_context: ProductosActionContext,
) -> ProductBarcode:
    _clear_primary_barcode(db, product_id=barcode.product_id)
    barcode.is_primary = True
    db.add(barcode)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.barcode.set_primary",
        entity_type="product_barcode",
        entity_id=barcode.id,
        details={"product_id": barcode.product_id},
    )
    return barcode


def _clear_primary_barcode(db: Session, *, product_id: str) -> None:
    current = list(
        db.scalars(
            select(ProductBarcode).where(
                ProductBarcode.product_id == product_id,
                ProductBarcode.is_primary.is_(True),
            )
        ).all()
    )
    for item in current:
        item.is_primary = False
        db.add(item)
    db.flush()


def _has_primary_barcode(db: Session, *, product_id: str) -> bool:
    return (
        db.scalar(
            select(ProductBarcode.id).where(
                ProductBarcode.product_id == product_id,
                ProductBarcode.is_primary.is_(True),
            )
        )
        is not None
    )


def _ensure_unique_barcode(
    db: Session,
    *,
    tenant_id: str,
    barcode_type: str,
    barcode: str,
    exclude_id: str | None = None,
) -> None:
    existing = db.scalar(
        select(ProductBarcode).where(
            ProductBarcode.tenant_id == tenant_id,
            ProductBarcode.barcode_type == barcode_type.strip().upper(),
            ProductBarcode.barcode == barcode.strip(),
        )
    )
    if existing is not None and existing.id != exclude_id:
        raise ValueError("El código de barras del producto ya existe")
