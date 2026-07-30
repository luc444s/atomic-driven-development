from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.config import get_settings
from plugins.logistics.backend.common import LogisticsActionContext
from plugins.logistics.backend.models import (
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsStockBridgeLog,
)
from plugins.productos.backend.models import ProductCost
from plugins.stock.backend.common import StockActionContext
from plugins.stock.backend.models import StockConfig, StockLedger
from plugins.stock.backend.services.operations import adjust_stock

_logger = logging.getLogger(__name__)


def _settings():
    return get_settings()


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


def _log_bridge_operation(
    db: Session,
    *,
    tenant_id: str,
    movement_id: str,
    operation: str,
    product_id: str | None,
    quantity: float | None,
    unit_cost: float | None,
    status: str,
    error_msg: str | None = None,
    payload: dict | None = None,
) -> None:
    entry = LogisticsStockBridgeLog(
        tenant_id=tenant_id,
        movement_id=movement_id,
        operation=operation,
        product_id=product_id,
        quantity=quantity,
        unit_cost=unit_cost,
        status=status,
        error_msg=error_msg,
        payload=payload or {},
    )
    db.add(entry)


def _resolve_product_id(
    db: Session,
    *,
    item: LogisticsMovementItem,
    movement: LogisticsMovement,
) -> str | None:
    if item.product_id is not None:
        return item.product_id
    stg = _settings()
    if stg.allow_cylinder_product_fallback and item.cylinder_id is not None:
        from plugins.logistics.backend.services.cylinders import get_cylinder

        cylinder = get_cylinder(db, tenant_id=movement.tenant_id, cylinder_id=item.cylinder_id)
        if cylinder is not None and cylinder.product_id is not None:
            _log_bridge_operation(
                db,
                tenant_id=movement.tenant_id,
                movement_id=movement.id,
                operation="product_resolution",
                product_id=cylinder.product_id,
                quantity=None,
                unit_cost=None,
                status="fallback",
                payload={
                    "tag": "deprecated:cylinder_product_fallback",
                    "cylinder_id": item.cylinder_id,
                },
            )
            return cylinder.product_id
    return None


def _resolve_purchase_unit_cost(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
) -> float | None:
    now = datetime.now(UTC).date()
    cost = db.scalar(
        select(ProductCost).where(
            ProductCost.tenant_id == tenant_id,
            ProductCost.product_id == product_id,
            ProductCost.cost_type == "BASE",
            ProductCost.valid_from <= now,
            (ProductCost.valid_to.is_(None)) | (ProductCost.valid_to >= now),
        ).order_by(ProductCost.valid_from.desc()).limit(1)
    )
    if cost is not None:
        return float(cost.amount)
    return None


def _handle_sale_out(
    db: Session,
    *,
    movement: LogisticsMovement,
    item: LogisticsMovementItem,
    action_context: LogisticsActionContext,
) -> None:
    from plugins.stock.backend.services.movements import sale_out_stock

    product_id = _resolve_product_id(db, item=item, movement=movement)
    if product_id is None:
        _log_bridge_operation(
            db, tenant_id=movement.tenant_id,
            movement_id=movement.id, operation="sale_out",
            product_id=None, quantity=None, unit_cost=None,
            status="error", error_msg="No product_id to execute sale_out",
        )
        raise ValueError(f"Movement {movement.id}: cannot execute sale_out without product_id")

    quantity = float(item.quantity_out or 0)
    if quantity <= 0:
        return

    warehouse_id = movement.warehouse_id
    assert warehouse_id is not None

    stock_ctx = build_stock_action_context(action_context)
    result = sale_out_stock(
        db,
        tenant_id=movement.tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        source="direct",
        allocation_id=None,
        reference_type="movement",
        reference_id=movement.id,
        idempotency_key=f"{movement.id}:sale_out:{item.id}",
        action_context=stock_ctx,
    )
    _log_bridge_operation(
        db, tenant_id=movement.tenant_id,
        movement_id=movement.id, operation="sale_out",
        product_id=product_id, quantity=quantity, unit_cost=None,
        status="success",
        payload={"ledger_entry_id": result.ledger_entry_id, "source": "direct"},
    )


def _handle_return_in(
    db: Session,
    *,
    movement: LogisticsMovement,
    item: LogisticsMovementItem,
    action_context: LogisticsActionContext,
) -> None:
    from plugins.stock.backend.services.movements import return_in_stock

    product_id = _resolve_product_id(db, item=item, movement=movement)
    if product_id is None:
        raise ValueError(f"Movement {movement.id}: cannot execute return_in without product_id")

    quantity = float(item.quantity_in or 0)
    if quantity <= 0:
        return

    warehouse_id = movement.warehouse_id
    assert warehouse_id is not None

    if movement.origin_movement_id is None:
        stg = _settings()
        if not stg.allow_legacy_stock_fallback:
            _log_bridge_operation(
                db, tenant_id=movement.tenant_id,
                movement_id=movement.id, operation="return_in",
                product_id=product_id, quantity=quantity, unit_cost=None,
                status="error",
                error_msg="IC movement without origin_movement_id and legacy fallback disabled",
            )
            raise ValueError(
                f"Movement {movement.id}: IC movement requires origin_movement_id "
                "to reference the original sale_out ledger entry"
            )
        _log_bridge_operation(
            db, tenant_id=movement.tenant_id,
            movement_id=movement.id, operation="return_in",
            product_id=product_id, quantity=quantity, unit_cost=None,
            status="fallback",
            error_msg="Using adjust_stock because origin_movement_id is NULL",
        )
        adjust_stock(
            db,
            tenant_id=movement.tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            reason=f"IC fallback: movement {movement.id} without origin",
            unit_cost=None,
            idempotency_key=f"{movement.id}:return_in_fallback:{item.id}",
            action_context=build_stock_action_context(action_context),
        )
        return

    origin = db.scalar(
        select(LogisticsMovement).where(
            LogisticsMovement.id == movement.origin_movement_id
        )
    )
    if origin is not None and origin.movement_type != "SC":
        _log_bridge_operation(
            db, tenant_id=movement.tenant_id,
            movement_id=movement.id, operation="return_in",
            product_id=product_id, quantity=quantity, unit_cost=None,
            status="error",
            error_msg="origin_movement_id must reference an SC movement",
        )
        raise ValueError(
            f"Movement {movement.id}: origin_movement_id must reference an SC movement, "
            f"got {origin.movement_type}"
        )

    original_ledger = db.scalar(
        select(StockLedger).where(
            StockLedger.tenant_id == movement.tenant_id,
            StockLedger.reference_type == "movement",
            StockLedger.reference_id.like(
                f"{movement.origin_movement_id}:sale_out:%"
            ),
            StockLedger.operation == "sale_out",
        )
    )
    if original_ledger is None:
        stg = _settings()
        if not stg.allow_legacy_stock_fallback:
            _log_bridge_operation(
                db, tenant_id=movement.tenant_id,
                movement_id=movement.id, operation="return_in",
                product_id=product_id, quantity=quantity, unit_cost=None,
                status="error",
                error_msg=(
                    "No sale_out ledger found for origin_movement_id "
                    "and legacy fallback disabled"
                ),
            )
            raise ValueError(
                f"Movement {movement.id}: cannot find original sale_out ledger "
                f"for origin_movement_id {movement.origin_movement_id}"
            )
        _log_bridge_operation(
            db, tenant_id=movement.tenant_id,
            movement_id=movement.id, operation="return_in",
            product_id=product_id, quantity=quantity, unit_cost=None,
            status="fallback",
            error_msg="Using adjust_stock because original sale_out ledger not found",
        )
        adjust_stock(
            db,
            tenant_id=movement.tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            reason=f"IC fallback: no sale_out for origin {movement.origin_movement_id}",
            unit_cost=None,
            idempotency_key=f"{movement.id}:return_in_fallback:{item.id}",
            action_context=build_stock_action_context(action_context),
        )
        return

    stock_ctx = build_stock_action_context(action_context)
    result = return_in_stock(
        db,
        tenant_id=movement.tenant_id,
        product_id=original_ledger.product_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        original_sale_ledger_id=original_ledger.id,
        reference_type="movement",
        reference_id=movement.id,
        idempotency_key=f"{movement.id}:return_in:{item.id}",
        action_context=stock_ctx,
    )
    _log_bridge_operation(
        db, tenant_id=movement.tenant_id,
        movement_id=movement.id, operation="return_in",
        product_id=product_id, quantity=quantity,
        unit_cost=original_ledger.unit_cost,
        status="success",
        payload={
            "ledger_entry_id": result.ledger_entry_id,
            "original_sale_ledger_id": original_ledger.id,
            "historical_unit_cost": (
                float(original_ledger.unit_cost)
                if original_ledger.unit_cost is not None
                else None
            ),
        },
    )


def _handle_purchase_in(
    db: Session,
    *,
    movement: LogisticsMovement,
    item: LogisticsMovementItem,
    action_context: LogisticsActionContext,
) -> None:
    from plugins.stock.backend.services.movements import purchase_in_stock

    product_id = _resolve_product_id(db, item=item, movement=movement)
    if product_id is None:
        raise ValueError(f"Movement {movement.id}: cannot execute purchase_in without product_id")

    quantity = float(item.quantity_in or 0)
    if quantity <= 0:
        return

    warehouse_id = movement.warehouse_id
    assert warehouse_id is not None

    unit_cost = _resolve_purchase_unit_cost(
        db, tenant_id=movement.tenant_id, product_id=product_id,
    )
    if unit_cost is None:
        stg = _settings()
        if not stg.allow_legacy_stock_fallback:
            _log_bridge_operation(
                db, tenant_id=movement.tenant_id,
                movement_id=movement.id, operation="purchase_in",
                product_id=product_id, quantity=quantity, unit_cost=None,
                status="error",
                error_msg="Cannot resolve unit_cost for purchase_in",
            )
            raise ValueError(
                f"Movement {movement.id}: cannot execute purchase_in without unit_cost "
                f"for product {product_id}"
            )
        _log_bridge_operation(
            db, tenant_id=movement.tenant_id,
            movement_id=movement.id, operation="purchase_in",
            product_id=product_id, quantity=quantity, unit_cost=None,
            status="fallback",
            error_msg="Using adjust_stock because unit_cost could not be resolved",
        )
        adjust_stock(
            db,
            tenant_id=movement.tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            reason=f"IP fallback: no unit_cost for product {product_id}",
            unit_cost=None,
            idempotency_key=f"{movement.id}:purchase_in_fallback:{item.id}",
            action_context=build_stock_action_context(action_context),
        )
        return

    stock_ctx = build_stock_action_context(action_context)
    result = purchase_in_stock(
        db,
        tenant_id=movement.tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        unit_cost=unit_cost,
        reference_type="movement",
        reference_id=movement.id,
        idempotency_key=f"{movement.id}:purchase_in:{item.id}",
        action_context=stock_ctx,
    )
    _log_bridge_operation(
        db, tenant_id=movement.tenant_id,
        movement_id=movement.id, operation="purchase_in",
        product_id=product_id, quantity=quantity, unit_cost=unit_cost,
        status="success",
        payload={"ledger_entry_id": result.ledger_entry_id, "unit_cost": unit_cost},
    )


def _handle_damage_out(
    db: Session,
    *,
    movement: LogisticsMovement,
    item: LogisticsMovementItem,
    action_context: LogisticsActionContext,
) -> None:
    from plugins.stock.backend.services.movements import damage_out_stock

    product_id = _resolve_product_id(db, item=item, movement=movement)
    if product_id is None:
        raise ValueError(f"Movement {movement.id}: cannot execute damage_out without product_id")

    quantity = float(item.quantity_out or 0)
    if quantity <= 0:
        return

    warehouse_id = movement.warehouse_id
    assert warehouse_id is not None

    stock_ctx = build_stock_action_context(action_context)
    result = damage_out_stock(
        db,
        tenant_id=movement.tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        reason=movement.notes,
        reference_type="movement",
        reference_id=movement.id,
        idempotency_key=f"{movement.id}:damage_out:{item.id}",
        action_context=stock_ctx,
    )
    _log_bridge_operation(
        db, tenant_id=movement.tenant_id,
        movement_id=movement.id, operation="damage_out",
        product_id=product_id, quantity=quantity, unit_cost=None,
        status="success",
        payload={"ledger_entry_id": result.ledger_entry_id},
    )


def _handle_transfer(
    db: Session,
    *,
    movement: LogisticsMovement,
    item: LogisticsMovementItem,
    action_context: LogisticsActionContext,
) -> None:
    product_id = _resolve_product_id(db, item=item, movement=movement)
    if product_id is None:
        return

    quantity_in = float(item.quantity_in or 0)
    quantity_out = float(item.quantity_out or 0)
    quantity = 0.0
    if quantity_in > 0:
        quantity = quantity_in
    elif quantity_out > 0:
        quantity = -quantity_out
    if quantity == 0:
        return

    warehouse_id = movement.warehouse_id
    assert warehouse_id is not None

    adjust_stock(
        db,
        tenant_id=movement.tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        reason=f"Movement {movement.id} confirmed: {item.product_name or product_id}",
        unit_cost=None,
        idempotency_key=f"{movement.id}:transfer:{item.id}",
        action_context=build_stock_action_context(action_context),
    )
    _log_bridge_operation(
        db, tenant_id=movement.tenant_id,
        movement_id=movement.id, operation="transfer",
        product_id=product_id, quantity=quantity, unit_cost=None,
        status="success",
    )


_HANDLERS = {
    "SC": _handle_sale_out,
    "IC": _handle_return_in,
    "IP": _handle_purchase_in,
    "IFP": _handle_purchase_in,
    "SP": _handle_sale_out,
    "MV": _handle_damage_out,
    "TR": _handle_transfer,
}


def apply_stock_for_movement(
    db: Session,
    *,
    movement: LogisticsMovement,
    items: list[LogisticsMovementItem],
    action_context: LogisticsActionContext,
) -> None:
    if movement.warehouse_id is None:
        return
    if not items:
        return

    stg = _settings()
    if not stg.use_transactional_stock_bridge:
        _apply_legacy_adjust_stock(db, movement=movement, items=items,
                                   action_context=action_context)
        return

    handler = _HANDLERS.get(movement.movement_type)
    if handler is None:
        return

    for item in items:
        handler(db, movement=movement, item=item, action_context=action_context)


def _apply_legacy_adjust_stock(
    db: Session,
    *,
    movement: LogisticsMovement,
    items: list[LogisticsMovementItem],
    action_context: LogisticsActionContext,
) -> None:
    warehouse_id = movement.warehouse_id
    assert warehouse_id is not None
    stock_ctx = build_stock_action_context(action_context)
    for index, item in enumerate(items, start=1):
        if item.product_id is None:
            continue
        delta = 0.0
        if movement.movement_type == "SC" or movement.movement_type == "SP":
            delta = -float(item.quantity_out or 0)
        elif movement.movement_type == "IC":
            delta = float(item.quantity_in or 0)
        elif movement.movement_type == "IP" or movement.movement_type == "IFP":
            delta = float(item.quantity_in or 0)
        elif movement.movement_type == "MV":
            delta = -float(item.quantity_out or 0)
        else:
            qin = float(item.quantity_in or 0)
            qout = float(item.quantity_out or 0)
            delta = qin - qout
        if delta == 0:
            continue
        adjust_stock(
            db,
            tenant_id=movement.tenant_id,
            product_id=item.product_id,
            warehouse_id=warehouse_id,
            quantity=delta,
            reason=f"Movement {movement.id} confirmed: {item.product_name or item.product_id}",
            unit_cost=None,
            idempotency_key=f"{movement.id}:legacy:{index}:{item.product_id}",
            action_context=stock_ctx,
        )
        _log_bridge_operation(
            db, tenant_id=movement.tenant_id,
            movement_id=movement.id, operation="adjust_stock_legacy",
            product_id=item.product_id, quantity=delta, unit_cost=None,
            status="success",
            payload={"mode": "legacy"},
        )


def adjust_required_product_stock(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str,
    product_id: str,
    quantity: float,
    reason: str,
    idempotency_key: str,
    action_context: LogisticsActionContext,
) -> None:
    adjust_stock(
        db,
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        reason=reason,
        unit_cost=None,
        idempotency_key=idempotency_key,
        action_context=build_stock_action_context(action_context),
    )


def adjust_products_stock(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str,
    deltas: tuple[tuple[str | None, float, str | None], ...],
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
            unit_cost=None,
            idempotency_key=f"{idempotency_prefix}:{index}:{product_id}",
            action_context=stock_context,
        )
