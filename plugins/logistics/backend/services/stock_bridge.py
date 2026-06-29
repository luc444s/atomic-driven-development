from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext
from plugins.stock.backend.common import StockActionContext
from plugins.stock.backend.models import StockConfig
from plugins.stock.backend.services.operations import adjust_stock


def build_stock_action_context(context: LogisticsActionContext) -> StockActionContext:
    return StockActionContext(
        tenant_id=context.tenant_id,
        branch_id=context.branch_id,
        actor_user_id=context.actor_user_id,
        correlation_id=context.correlation_id,
        request_id=context.request_id,
    )


def is_stock_controlled(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str,
    product_id: str | None,
) -> bool:
    if product_id is None:
        return False
    config = db.scalar(
        select(StockConfig).where(
            StockConfig.tenant_id == tenant_id,
            StockConfig.warehouse_id == warehouse_id,
            StockConfig.product_id == product_id,
            StockConfig.is_active.is_(True),
        )
    )
    return config is not None


def adjust_products_stock(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str,
    deltas: Iterable[tuple[str | None, float, str | None]],
    reason: str,
    idempotency_prefix: str,
    action_context: LogisticsActionContext,
) -> None:
    stock_context = build_stock_action_context(action_context)
    for index, (product_id, quantity, product_name) in enumerate(deltas, start=1):
        if product_id is None:
            continue
        if quantity == 0:
            continue
        if not is_stock_controlled(
            db,
            tenant_id=tenant_id,
            warehouse_id=warehouse_id,
            product_id=product_id,
        ):
            continue
        adjust_stock(
            db,
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            reason=f"{reason}: {product_name or product_id}",
            idempotency_key=f"{idempotency_prefix}:{index}:{product_id}",
            action_context=stock_context,
        )
