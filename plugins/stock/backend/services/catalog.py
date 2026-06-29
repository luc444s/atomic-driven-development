from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import LogisticsWarehouse
from plugins.productos.backend.models import Product


def get_product(db: Session, *, tenant_id: str, product_id: str) -> Product | None:
    return db.scalar(
        select(Product).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id,
        )
    )


def require_product(db: Session, *, tenant_id: str, product_id: str) -> Product:
    product = get_product(db, tenant_id=tenant_id, product_id=product_id)
    if product is None:
        raise LookupError("Product not found")
    return product


def get_warehouse(db: Session, *, tenant_id: str, warehouse_id: str) -> LogisticsWarehouse | None:
    return db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == warehouse_id,
            LogisticsWarehouse.tenant_id == tenant_id,
        )
    )


def require_warehouse(db: Session, *, tenant_id: str, warehouse_id: str) -> LogisticsWarehouse:
    warehouse = get_warehouse(db, tenant_id=tenant_id, warehouse_id=warehouse_id)
    if warehouse is None:
        raise LookupError("Warehouse not found")
    return warehouse


def list_warehouses(
    db: Session,
    *,
    tenant_id: str,
    allowed_warehouse_ids: tuple[str, ...] | None,
) -> list[LogisticsWarehouse]:
    stmt = select(LogisticsWarehouse).where(
        LogisticsWarehouse.tenant_id == tenant_id,
        LogisticsWarehouse.is_active.is_(True),
    )
    if allowed_warehouse_ids is not None:
        stmt = stmt.where(LogisticsWarehouse.id.in_(allowed_warehouse_ids))
    stmt = stmt.order_by(LogisticsWarehouse.name.asc())
    return list(db.scalars(stmt))
