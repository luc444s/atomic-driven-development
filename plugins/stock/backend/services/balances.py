from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import LogisticsWarehouse
from plugins.productos.backend.models import Product
from plugins.stock.backend.models import StockBalance, StockConfig, StockLedger
from plugins.stock.backend.schemas import (
    StockBalancePageRead,
    StockBalanceRead,
    StockConfigRead,
    StockLedgerRead,
)
from plugins.stock.backend.services.catalog import require_product, require_warehouse


def _as_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _build_balance_read(*, balance, product, warehouse, config) -> StockBalanceRead:
    quantity = _as_float(getattr(balance, "quantity", 0)) or 0.0
    min_quantity = _as_float(getattr(config, "min_quantity", None))
    max_quantity = _as_float(getattr(config, "max_quantity", None))
    return StockBalanceRead(
        id=getattr(balance, "id", None),
        tenant_id=product.tenant_id,
        product_id=product.id,
        product_sku=product.sku,
        product_name=product.name,
        warehouse_id=warehouse.id,
        warehouse_code=warehouse.code,
        warehouse_name=warehouse.name,
        quantity=quantity,
        min_quantity=min_quantity,
        max_quantity=max_quantity,
        is_below_min=min_quantity is not None and quantity < min_quantity,
        updated_by=getattr(balance, "updated_by", None),
        updated_at=getattr(balance, "updated_at", None),
    )


def list_balances(
    db: Session,
    *,
    tenant_id: str,
    q: str | None,
    product_id: str | None,
    warehouse_id: str | None,
    below_min_only: bool,
    allowed_warehouse_ids: tuple[str, ...] | None,
    limit: int,
    offset: int,
) -> StockBalancePageRead:
    stmt = (
        select(StockBalance, Product, LogisticsWarehouse, StockConfig)
        .join(Product, Product.id == StockBalance.product_id)
        .join(LogisticsWarehouse, LogisticsWarehouse.id == StockBalance.warehouse_id)
        .outerjoin(
            StockConfig,
            (StockConfig.tenant_id == StockBalance.tenant_id)
            & (StockConfig.product_id == StockBalance.product_id)
            & (StockConfig.warehouse_id == StockBalance.warehouse_id),
        )
        .where(StockBalance.tenant_id == tenant_id)
    )
    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Product.sku.ilike(term),
                Product.name.ilike(term),
                LogisticsWarehouse.name.ilike(term),
                LogisticsWarehouse.code.ilike(term),
            )
        )
    if product_id:
        stmt = stmt.where(StockBalance.product_id == product_id)
    if warehouse_id:
        stmt = stmt.where(StockBalance.warehouse_id == warehouse_id)
    if allowed_warehouse_ids is not None:
        stmt = stmt.where(StockBalance.warehouse_id.in_(allowed_warehouse_ids))
    if below_min_only:
        stmt = stmt.where(
            StockConfig.is_active.is_(True),
            StockConfig.min_quantity.is_not(None),
            StockBalance.quantity < StockConfig.min_quantity,
        )

    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(
        stmt.order_by(Product.name.asc(), LogisticsWarehouse.name.asc()).offset(offset).limit(limit)
    ).all()
    return StockBalancePageRead(
        items=[
            _build_balance_read(
                balance=balance, product=product, warehouse=warehouse, config=config
            )
            for balance, product, warehouse, config in rows
        ],
        total=int(total),
        limit=limit,
        offset=offset,
    )


def list_product_balances(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    allowed_warehouse_ids: tuple[str, ...] | None,
) -> list[StockBalanceRead]:
    product = require_product(db, tenant_id=tenant_id, product_id=product_id)
    stmt = (
        select(StockBalance, LogisticsWarehouse, StockConfig)
        .join(LogisticsWarehouse, LogisticsWarehouse.id == StockBalance.warehouse_id)
        .outerjoin(
            StockConfig,
            (StockConfig.tenant_id == StockBalance.tenant_id)
            & (StockConfig.product_id == StockBalance.product_id)
            & (StockConfig.warehouse_id == StockBalance.warehouse_id),
        )
        .where(
            StockBalance.tenant_id == tenant_id,
            StockBalance.product_id == product_id,
        )
        .order_by(LogisticsWarehouse.name.asc())
    )
    if allowed_warehouse_ids is not None:
        stmt = stmt.where(StockBalance.warehouse_id.in_(allowed_warehouse_ids))
    rows = db.execute(stmt).all()
    return [
        _build_balance_read(balance=balance, product=product, warehouse=warehouse, config=config)
        for balance, warehouse, config in rows
    ]


def get_balance_detail(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
) -> StockBalanceRead:
    product = require_product(db, tenant_id=tenant_id, product_id=product_id)
    warehouse = require_warehouse(db, tenant_id=tenant_id, warehouse_id=warehouse_id)
    row = db.execute(
        select(StockBalance, StockConfig)
        .outerjoin(
            StockConfig,
            (StockConfig.tenant_id == tenant_id)
            & (StockConfig.product_id == product_id)
            & (StockConfig.warehouse_id == warehouse_id),
        )
        .where(
            StockBalance.tenant_id == tenant_id,
            StockBalance.product_id == product_id,
            StockBalance.warehouse_id == warehouse_id,
        )
    ).first()
    if row is None:
        config = db.scalar(
            select(StockConfig).where(
                StockConfig.tenant_id == tenant_id,
                StockConfig.product_id == product_id,
                StockConfig.warehouse_id == warehouse_id,
            )
        )
        return _build_balance_read(
            balance=None, product=product, warehouse=warehouse, config=config
        )
    balance, config = row
    return _build_balance_read(
        balance=balance,
        product=product,
        warehouse=warehouse,
        config=config,
    )


def list_ledger_entries(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str | None,
    operation: str | None,
    allowed_warehouse_ids: tuple[str, ...] | None,
    limit: int,
    offset: int,
) -> list[StockLedgerRead]:
    product = require_product(db, tenant_id=tenant_id, product_id=product_id)
    stmt = (
        select(StockLedger, LogisticsWarehouse)
        .join(LogisticsWarehouse, LogisticsWarehouse.id == StockLedger.warehouse_id)
        .where(
            StockLedger.tenant_id == tenant_id,
            StockLedger.product_id == product_id,
        )
    )
    if warehouse_id is not None:
        require_warehouse(db, tenant_id=tenant_id, warehouse_id=warehouse_id)
        stmt = stmt.where(StockLedger.warehouse_id == warehouse_id)
    if allowed_warehouse_ids is not None:
        stmt = stmt.where(StockLedger.warehouse_id.in_(allowed_warehouse_ids))
    if operation is not None:
        stmt = stmt.where(StockLedger.operation == operation)
    rows = db.execute(
        stmt.order_by(StockLedger.created_at.desc(), StockLedger.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return [
        StockLedgerRead(
            id=ledger.id,
            tenant_id=ledger.tenant_id,
            product_id=ledger.product_id,
            product_sku=product.sku,
            product_name=product.name,
            warehouse_id=ledger.warehouse_id,
            warehouse_code=warehouse.code,
            warehouse_name=warehouse.name,
            operation=ledger.operation,
            quantity=_as_float(ledger.quantity) or 0.0,
            balance_after=_as_float(ledger.balance_after) or 0.0,
            reference_type=ledger.reference_type,
            reference_id=ledger.reference_id,
            notes=ledger.notes,
            created_by=ledger.created_by,
            created_at=ledger.created_at,
        )
        for ledger, warehouse in rows
    ]


def list_configs(
    db: Session,
    *,
    tenant_id: str,
    product_id: str | None,
    warehouse_id: str | None,
    allowed_warehouse_ids: tuple[str, ...] | None,
) -> list[StockConfigRead]:
    stmt = (
        select(StockConfig, Product, LogisticsWarehouse)
        .join(Product, Product.id == StockConfig.product_id)
        .join(LogisticsWarehouse, LogisticsWarehouse.id == StockConfig.warehouse_id)
        .where(StockConfig.tenant_id == tenant_id)
        .order_by(Product.name.asc(), LogisticsWarehouse.name.asc())
    )
    if product_id:
        stmt = stmt.where(StockConfig.product_id == product_id)
    if warehouse_id:
        stmt = stmt.where(StockConfig.warehouse_id == warehouse_id)
    if allowed_warehouse_ids is not None:
        stmt = stmt.where(StockConfig.warehouse_id.in_(allowed_warehouse_ids))
    rows = db.execute(stmt).all()
    return [
        StockConfigRead(
            id=config.id,
            tenant_id=config.tenant_id,
            product_id=config.product_id,
            product_sku=product.sku,
            product_name=product.name,
            warehouse_id=config.warehouse_id,
            warehouse_code=warehouse.code,
            warehouse_name=warehouse.name,
            min_quantity=_as_float(config.min_quantity) or 0.0,
            max_quantity=_as_float(config.max_quantity),
            is_active=config.is_active,
            updated_at=config.updated_at,
            updated_by=config.updated_by,
        )
        for config, product, warehouse in rows
    ]
