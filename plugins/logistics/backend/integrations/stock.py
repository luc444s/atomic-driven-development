from __future__ import annotations

from plugins.logistics.backend.common import LogisticsActionContext
from plugins.stock.backend.common import StockActionContext
from plugins.stock.backend.schemas import StockBalancePageRead, StockTransferResultRead
from plugins.stock.backend.services.balances import list_balances
from plugins.stock.backend.services.operations import transfer_stock as stock_transfer_stock


def _build_stock_context(context: LogisticsActionContext) -> StockActionContext:
    return StockActionContext(
        tenant_id=context.tenant_id,
        branch_id=context.branch_id,
        actor_user_id=context.actor_user_id,
        correlation_id=context.correlation_id,
        request_id=context.request_id,
    )


def get_warehouse_balances(
    db,
    *,
    tenant_id: str,
    warehouse_id: str,
    limit: int = 200,
) -> StockBalancePageRead:
    return list_balances(
        db,
        tenant_id=tenant_id,
        q=None,
        product_id=None,
        warehouse_id=warehouse_id,
        below_min_only=False,
        allowed_warehouse_ids=None,
        limit=limit,
        offset=0,
    )


def transfer(
    db,
    *,
    tenant_id: str,
    from_warehouse_id: str,
    to_warehouse_id: str,
    product_id: str,
    quantity: float,
    notes: str | None,
    idempotency_key: str,
    action_context: LogisticsActionContext,
) -> StockTransferResultRead:
    return stock_transfer_stock(
        db,
        tenant_id=tenant_id,
        product_id=product_id,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        quantity=quantity,
        notes=notes,
        idempotency_key=idempotency_key,
        action_context=_build_stock_context(action_context),
    )
