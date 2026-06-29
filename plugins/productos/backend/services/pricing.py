from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.productos.backend.common import (
    ProductosActionContext,
    audit_productos_action,
    emit_productos_event,
)
from plugins.productos.backend.models import Product, ProductCost, ProductPrice, ProductTaxConfig
from plugins.productos.backend.schemas import (
    ProductCostCreateRequest,
    ProductCostSupersedeRequest,
    ProductPriceBulkUpdateRequest,
    ProductPriceCreateRequest,
    ProductPriceSupersedeRequest,
    ProductTaxConfigUpdateRequest,
)


def list_prices(db: Session, *, product_id: str) -> list[ProductPrice]:
    return list(
        db.scalars(
            select(ProductPrice)
            .where(ProductPrice.product_id == product_id)
            .order_by(ProductPrice.price_list.asc(), ProductPrice.valid_from.desc())
        ).all()
    )


def create_price(
    db: Session,
    *,
    product: Product,
    actor_user_id: str,
    payload: ProductPriceCreateRequest,
    action_context: ProductosActionContext,
) -> ProductPrice:
    _close_open_price(
        db, product_id=product.id, price_list=payload.price_list, valid_from=payload.valid_from
    )
    item = ProductPrice(
        tenant_id=product.tenant_id,
        product_id=product.id,
        price_list=payload.price_list.strip().upper(),
        amount=payload.amount,
        currency=payload.currency.strip().upper(),
        valid_from=payload.valid_from,
        created_by=actor_user_id,
    )
    db.add(item)
    db.flush()
    _audit_emit_price_change(
        db, product=product, price=item, action_context=action_context, action="create"
    )
    return item


def supersede_price(
    db: Session,
    *,
    price: ProductPrice,
    actor_user_id: str,
    payload: ProductPriceSupersedeRequest,
    action_context: ProductosActionContext,
) -> ProductPrice:
    if price.valid_to is not None:
        raise ValueError("Only active prices can be superseded")
    _close_open_price(
        db,
        product_id=price.product_id,
        price_list=price.price_list,
        valid_from=payload.valid_from,
    )
    item = ProductPrice(
        tenant_id=price.tenant_id,
        product_id=price.product_id,
        price_list=price.price_list,
        amount=payload.amount,
        currency=payload.currency.strip().upper(),
        valid_from=payload.valid_from,
        created_by=actor_user_id,
    )
    db.add(item)
    db.flush()
    product = db.get(Product, price.product_id)
    if product is None:
        raise ValueError("Product not found")
    _audit_emit_price_change(
        db, product=product, price=item, action_context=action_context, action="supersede"
    )
    return item


def update_all_prices(
    db: Session,
    *,
    product: Product,
    actor_user_id: str,
    payload: ProductPriceBulkUpdateRequest,
    action_context: ProductosActionContext,
) -> list[ProductPrice]:
    created: list[ProductPrice] = []
    for item in payload.items:
        created.append(
            create_price(
                db,
                product=product,
                actor_user_id=actor_user_id,
                payload=item,
                action_context=action_context,
            )
        )
    return created


def list_costs(db: Session, *, product_id: str) -> list[ProductCost]:
    return list(
        db.scalars(
            select(ProductCost)
            .where(ProductCost.product_id == product_id)
            .order_by(ProductCost.cost_type.asc(), ProductCost.valid_from.desc())
        ).all()
    )


def create_cost(
    db: Session,
    *,
    product: Product,
    actor_user_id: str,
    payload: ProductCostCreateRequest,
    action_context: ProductosActionContext,
) -> ProductCost:
    _close_open_cost(
        db, product_id=product.id, cost_type=payload.cost_type, valid_from=payload.valid_from
    )
    item = ProductCost(
        tenant_id=product.tenant_id,
        product_id=product.id,
        cost_type=payload.cost_type.strip().upper(),
        amount=payload.amount,
        currency=payload.currency.strip().upper(),
        valid_from=payload.valid_from,
        created_by=actor_user_id,
    )
    db.add(item)
    db.flush()
    _audit_emit_cost_change(
        db, product=product, cost=item, action_context=action_context, action="create"
    )
    return item


def supersede_cost(
    db: Session,
    *,
    cost: ProductCost,
    actor_user_id: str,
    payload: ProductCostSupersedeRequest,
    action_context: ProductosActionContext,
) -> ProductCost:
    if cost.valid_to is not None:
        raise ValueError("Only active costs can be superseded")
    _close_open_cost(
        db,
        product_id=cost.product_id,
        cost_type=cost.cost_type,
        valid_from=payload.valid_from,
    )
    item = ProductCost(
        tenant_id=cost.tenant_id,
        product_id=cost.product_id,
        cost_type=cost.cost_type,
        amount=payload.amount,
        currency=payload.currency.strip().upper(),
        valid_from=payload.valid_from,
        created_by=actor_user_id,
    )
    db.add(item)
    db.flush()
    product = db.get(Product, cost.product_id)
    if product is None:
        raise ValueError("Product not found")
    _audit_emit_cost_change(
        db, product=product, cost=item, action_context=action_context, action="supersede"
    )
    return item


def list_tax_configs(db: Session, *, product_id: str) -> list[ProductTaxConfig]:
    return list(
        db.scalars(
            select(ProductTaxConfig)
            .where(ProductTaxConfig.product_id == product_id)
            .order_by(ProductTaxConfig.tax_type.asc(), ProductTaxConfig.valid_from.desc())
        ).all()
    )


def replace_tax_configs(
    db: Session,
    *,
    product: Product,
    payload: ProductTaxConfigUpdateRequest,
    action_context: ProductosActionContext,
) -> list[ProductTaxConfig]:
    created: list[ProductTaxConfig] = []
    for config in payload.configs:
        _close_open_tax(
            db,
            product_id=product.id,
            tax_type=config.tax_type,
            valid_from=config.valid_from,
        )
        item = ProductTaxConfig(
            tenant_id=product.tenant_id,
            product_id=product.id,
            tax_type=config.tax_type.strip().upper(),
            value=config.value,
            is_exempt=config.is_exempt,
            valid_from=config.valid_from,
        )
        db.add(item)
        created.append(item)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.tax.replace",
        entity_type="product",
        entity_id=product.id,
        details={"tax_types": [item.tax_type for item in created]},
    )
    return created


def require_price(db: Session, *, product_id: str, price_id: str) -> ProductPrice:
    price = db.scalar(
        select(ProductPrice).where(
            ProductPrice.product_id == product_id, ProductPrice.id == price_id
        )
    )
    if price is None:
        raise ValueError("ProductPrice not found")
    return price


def require_cost(db: Session, *, product_id: str, cost_id: str) -> ProductCost:
    cost = db.scalar(
        select(ProductCost).where(ProductCost.product_id == product_id, ProductCost.id == cost_id)
    )
    if cost is None:
        raise ValueError("ProductCost not found")
    return cost


def _close_open_price(db: Session, *, product_id: str, price_list: str, valid_from: date) -> None:
    active = db.scalar(
        select(ProductPrice).where(
            ProductPrice.product_id == product_id,
            ProductPrice.price_list == price_list.strip().upper(),
            ProductPrice.valid_to.is_(None),
        )
    )
    if active is not None:
        active.valid_to = valid_from - timedelta(days=1)
        db.add(active)
        db.flush()


def _close_open_cost(db: Session, *, product_id: str, cost_type: str, valid_from: date) -> None:
    active = db.scalar(
        select(ProductCost).where(
            ProductCost.product_id == product_id,
            ProductCost.cost_type == cost_type.strip().upper(),
            ProductCost.valid_to.is_(None),
        )
    )
    if active is not None:
        active.valid_to = valid_from - timedelta(days=1)
        db.add(active)
        db.flush()


def _close_open_tax(db: Session, *, product_id: str, tax_type: str, valid_from: date) -> None:
    active = db.scalar(
        select(ProductTaxConfig).where(
            ProductTaxConfig.product_id == product_id,
            ProductTaxConfig.tax_type == tax_type.strip().upper(),
            ProductTaxConfig.valid_to.is_(None),
        )
    )
    if active is not None:
        active.valid_to = valid_from - timedelta(days=1)
        db.add(active)
        db.flush()


def _audit_emit_price_change(
    db: Session,
    *,
    product: Product,
    price: ProductPrice,
    action_context: ProductosActionContext,
    action: str,
) -> None:
    audit_productos_action(
        db,
        context=action_context,
        action=f"product.price.{action}",
        entity_type="product_price",
        entity_id=price.id,
        details={"product_id": product.id, "price_list": price.price_list, "amount": price.amount},
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.product.price_changed",
        entity_type="product",
        entity_id=product.id,
        payload={
            "product_id": product.id,
            "price_id": price.id,
            "price_list": price.price_list,
            "amount": float(price.amount),
            "currency": price.currency,
        },
    )


def _audit_emit_cost_change(
    db: Session,
    *,
    product: Product,
    cost: ProductCost,
    action_context: ProductosActionContext,
    action: str,
) -> None:
    audit_productos_action(
        db,
        context=action_context,
        action=f"product.cost.{action}",
        entity_type="product_cost",
        entity_id=cost.id,
        details={"product_id": product.id, "cost_type": cost.cost_type, "amount": cost.amount},
    )
    emit_productos_event(
        db,
        context=action_context,
        event_name="productos.product.cost_changed",
        entity_type="product",
        entity_id=product.id,
        payload={
            "product_id": product.id,
            "cost_id": cost.id,
            "cost_type": cost.cost_type,
            "amount": float(cost.amount),
            "currency": cost.currency,
        },
    )
