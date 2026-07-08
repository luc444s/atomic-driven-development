# BRIDGE: Acceso a catálogos de productos
# Phase 1: import directo (aislado en este archivo)
# Phase 2: reemplazar por httpx a productos API
from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.productos.backend.models import (
    Product,
    ProductAdr,
    ProductBrand,
    ProductCondition,
    ProductSubline,
)
from plugins.productos.backend.schemas import GasProductRead


def resolve_brand(db: Session, brand_id: str) -> ProductBrand | None:
    return db.get(ProductBrand, brand_id)


def resolve_brand_name(db: Session, brand_id: str) -> str | None:
    brand = resolve_brand(db, brand_id)
    return brand.name if brand else None


def resolve_gas_product(db: Session, gas_product_id: str, tenant_id: str) -> Product | None:
    return db.scalar(
        select(Product).where(
            Product.id == gas_product_id,
            Product.tenant_id == tenant_id,
            Product.condition_code == "GAS",
        )
    )


def resolve_gas_product_name(db: Session, gas_product_id: str, tenant_id: str) -> str | None:
    product = resolve_gas_product(db, gas_product_id, tenant_id)
    return product.name if product else None


def resolve_condition(condition_code: str, db: Session) -> ProductCondition | None:
    return db.get(ProductCondition, condition_code)


def resolve_product_adr(db: Session, product_id: str) -> ProductAdr | None:
    today = date.today()
    return db.scalar(
        select(ProductAdr)
        .where(
            ProductAdr.product_id == product_id,
            ProductAdr.valid_from <= today,
            (ProductAdr.valid_to.is_(None) | (ProductAdr.valid_to >= today)),
        )
        .order_by(ProductAdr.valid_from.desc())
        .limit(1)
    )


def resolve_product_adr_subline_name(db: Session, subline_id: str | None) -> str | None:
    if not subline_id:
        return None
    subline = db.get(ProductSubline, subline_id)
    return subline.name if subline else None


def _gas_product_to_read(product: Product) -> GasProductRead:
    return GasProductRead(
        id=product.id,
        name=product.name,
        code=product.sku,
        content_kg=float(product.weight_kg) if product.weight_kg is not None else None,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )
