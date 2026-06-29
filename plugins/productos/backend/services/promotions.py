from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.productos.backend.common import (
    ProductosActionContext,
    audit_productos_action,
    emit_productos_event,
)
from plugins.productos.backend.models import Product, ProductPromotion
from plugins.productos.backend.schemas import (
    ProductPromotionCreateRequest,
    ProductPromotionUpdateRequest,
)


def list_promotions(db: Session, *, product_id: str) -> list[ProductPromotion]:
    return list(
        db.scalars(
            select(ProductPromotion)
            .where(ProductPromotion.product_id == product_id)
            .order_by(ProductPromotion.valid_from.desc(), ProductPromotion.created_at.desc())
        ).all()
    )


def create_promotion(
    db: Session,
    *,
    product: Product,
    actor_user_id: str,
    payload: ProductPromotionCreateRequest,
    action_context: ProductosActionContext,
) -> ProductPromotion:
    item = ProductPromotion(
        tenant_id=product.tenant_id,
        product_id=product.id,
        name=payload.name,
        condition=payload.condition.strip().upper(),
        qty_required=payload.qty_required,
        discount_percent=payload.discount_percent,
        unit_price=payload.unit_price,
        box_price=payload.box_price,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        is_active=payload.is_active,
        created_by=actor_user_id,
    )
    db.add(item)
    db.flush()
    _audit_emit_promotion(
        db, product=product, promotion=item, action_context=action_context, action="create"
    )
    return item


def update_promotion(
    db: Session,
    *,
    promotion: ProductPromotion,
    payload: ProductPromotionUpdateRequest,
    action_context: ProductosActionContext,
) -> ProductPromotion:
    changed_fields: list[str] = []
    for field in [
        "name",
        "qty_required",
        "discount_percent",
        "unit_price",
        "box_price",
        "valid_from",
        "valid_to",
        "is_active",
    ]:
        value = getattr(payload, field)
        if value is None:
            continue
        if getattr(promotion, field) != value:
            setattr(promotion, field, value)
            changed_fields.append(field)
    if payload.condition is not None:
        condition = payload.condition.strip().upper()
        if promotion.condition != condition:
            promotion.condition = condition
            changed_fields.append("condition")
    db.add(promotion)
    db.flush()
    product = db.get(Product, promotion.product_id)
    if product is None:
        raise ValueError("Product not found")
    _audit_emit_promotion(
        db,
        product=product,
        promotion=promotion,
        action_context=action_context,
        action="update",
        changed_fields=changed_fields,
    )
    return promotion


def delete_promotion(
    db: Session,
    *,
    promotion: ProductPromotion,
    action_context: ProductosActionContext,
) -> None:
    product = db.get(Product, promotion.product_id)
    db.delete(promotion)
    db.flush()
    if product is not None:
        audit_productos_action(
            db,
            context=action_context,
            action="product.promotion.delete",
            entity_type="product_promotion",
            entity_id=promotion.id,
            details={"product_id": product.id},
        )


def require_promotion(db: Session, *, promotion_id: str) -> ProductPromotion:
    promotion = db.get(ProductPromotion, promotion_id)
    if promotion is None:
        raise ValueError("ProductPromotion not found")
    return promotion


def expire_due_promotions(db: Session, *, today: date | None = None) -> int:
    current_day = today or date.today()
    expired = list(
        db.scalars(
            select(ProductPromotion).where(
                ProductPromotion.is_active.is_(True),
                ProductPromotion.valid_to.is_not(None),
                ProductPromotion.valid_to < current_day,
            )
        ).all()
    )
    for item in expired:
        item.is_active = False
        db.add(item)
    db.flush()
    return len(expired)


def _audit_emit_promotion(
    db: Session,
    *,
    product: Product,
    promotion: ProductPromotion,
    action_context: ProductosActionContext,
    action: str,
    changed_fields: list[str] | None = None,
) -> None:
    audit_productos_action(
        db,
        context=action_context,
        action=f"product.promotion.{action}",
        entity_type="product_promotion",
        entity_id=promotion.id,
        details={"product_id": product.id, "changed_fields": changed_fields or []},
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name=(
            "productos.promotion.created" if action == "create" else "productos.promotion.updated"
        ),
        entity_type="product",
        entity_id=product.id,
        payload={"product_id": product.id, "promotion_id": promotion.id, "action": action},
    )
