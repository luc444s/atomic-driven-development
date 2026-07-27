from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.stock.backend.common import (
    StockActionContext,
    audit_stock_action,
    emit_stock_event,
)
from plugins.stock.backend.models import StockAllocation, StockBalance, StockConfig, StockLedger
from plugins.stock.backend.schemas import StockBalanceRead, StockMovementResultRead
from plugins.stock.backend.services.allocation import _lock_balance
from plugins.stock.backend.services.catalog import require_product, require_warehouse

FOUR_DECIMALS = Decimal("0.0001")
THREE_DECIMALS = Decimal("0.001")


def _to_dec(value: float, precision: Decimal = THREE_DECIMALS) -> Decimal:
    return Decimal(str(value)).quantize(precision, rounding=ROUND_HALF_UP)


def _avg_cost(total_cost: float, quantity: float) -> Decimal:
    if quantity == 0:
        return Decimal("0.0000")
    return _to_dec(
        float(Decimal(str(total_cost)) / Decimal(str(quantity))), FOUR_DECIMALS
    )


def _idempotent_check(
    db: Session,
    *,
    tenant_id: str,
    operation: str,
    product_id: str,
    warehouse_id: str,
    reference_type: str,
    reference_id: str,
    idempotency_key: str | None,
) -> StockBalanceRead | None:
    if not idempotency_key:
        return None
    ref_id = idempotency_key
    existing = db.scalar(
        select(StockLedger.id).where(
            StockLedger.tenant_id == tenant_id,
            StockLedger.product_id == product_id,
            StockLedger.warehouse_id == warehouse_id,
            StockLedger.operation == operation,
            StockLedger.reference_type == reference_type,
            StockLedger.reference_id == ref_id,
        )
    )
    if existing is None:
        return None
    return _get_balance_read(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id,
    )


def _get_balance_read(
    db: Session, *, tenant_id: str, product_id: str, warehouse_id: str
) -> StockBalanceRead:
    from plugins.stock.backend.services.balances import get_balance_detail
    return get_balance_detail(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id,
    )


def _allow_negative_stock(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    balance: StockBalance | None = None,
) -> bool:
    if balance is not None and balance.allow_negative_stock:
        return True
    config = db.scalar(
        select(StockConfig.allow_negative_stock).where(
            StockConfig.tenant_id == tenant_id,
            StockConfig.product_id == product_id,
            StockConfig.warehouse_id == warehouse_id,
            StockConfig.is_active.is_(True),
        )
    )
    return bool(config)


def sale_out_stock(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    quantity: float,
    source: str,
    allocation_id: str | None,
    reference_type: str,
    reference_id: str,
    idempotency_key: str | None,
    action_context: StockActionContext,
) -> StockMovementResultRead:
    existing = _idempotent_check(
        db, tenant_id=tenant_id, operation="sale_out",
        product_id=product_id, warehouse_id=warehouse_id,
        reference_type=reference_type,
        reference_id=idempotency_key or reference_id,
        idempotency_key=idempotency_key,
    )
    if existing is not None:
        return StockMovementResultRead(
            operation="sale_out", balance=existing,
            ledger_entry_id="idempotent",
        )

    if source not in ("allocation", "direct"):
        raise ValueError("source must be 'allocation' or 'direct'")

    _product = require_product(
        db, tenant_id=tenant_id, product_id=product_id,
    )
    warehouse = require_warehouse(
        db, tenant_id=tenant_id, warehouse_id=warehouse_id,
    )
    qty = _to_dec(quantity)

    allocation = None
    if source == "allocation":
        if not allocation_id:
            raise ValueError("allocation_id required when source=allocation")
        allocation = db.execute(
            select(StockAllocation).where(
                StockAllocation.id == allocation_id,
                StockAllocation.tenant_id == tenant_id,
            ).with_for_update()
        ).scalar_one_or_none()
        if allocation is None:
            raise LookupError("Allocation not found")
        if allocation.status not in ("active", "partially_consumed"):
            raise ValueError(
                f"Allocation status '{allocation.status}' cannot be consumed"
            )
        remaining = Decimal(str(allocation.remaining_quantity))
        if qty > remaining:
            raise ValueError(
                f"Allocation remaining={float(remaining)}"
                f" < requested={quantity}"
            )

    balance = _lock_balance(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id, actor_user_id=action_context.actor_user_id,
    )
    current_qty = Decimal(str(balance.quantity))
    current_reserved = Decimal(str(balance.reserved_quantity))
    current_total_cost = Decimal(str(balance.total_cost))

    new_qty = current_qty - qty
    if new_qty < 0 and not _allow_negative_stock(  # noqa: F841
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id, balance=balance,
    ):
        raise ValueError(
            f"Stock insuficiente: disponible={float(current_qty)},"
            f" solicitado={quantity}"
        )

    _unit_cost = (
        _avg_cost(float(current_total_cost), float(current_qty))
        if current_qty > 0
        else Decimal("0.0000")
    )
    total_cost_out = _unit_cost * qty
    new_total_cost = current_total_cost - total_cost_out
    if new_qty <= 0:
        new_total_cost = Decimal("0.0000")

    balance.quantity = float(new_qty)

    if source == "allocation" and allocation is not None:
        new_reserved = current_reserved - qty
        if new_reserved < 0:
            new_reserved = Decimal("0.0000")
        balance.reserved_quantity = float(new_reserved)

        allocation.remaining_quantity = float(remaining - qty)
        if allocation.remaining_quantity <= 0:
            allocation.status = "consumed"
        else:
            allocation.status = "partially_consumed"
        db.add(allocation)

    balance.total_cost = float(new_total_cost)
    db.add(balance)
    db.flush()

    ref_id = idempotency_key or str(uuid4())
    ledger = StockLedger(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        operation="sale_out",
        quantity=float(-qty),
        balance_after=float(new_qty),
        unit_cost=float(_unit_cost),
        total_cost=float(total_cost_out),
        cost_after=float(new_total_cost),
        source=source,
        reference_type=reference_type,
        reference_id=ref_id,
        created_by=action_context.actor_user_id,
    )
    db.add(ledger)

    audit_stock_action(
        db, context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        action="movement.sale_out",
        entity_type="movement",
        entity_id=ledger.id,
        details={
            "product_id": product_id, "warehouse_id": warehouse_id,
            "quantity": float(qty), "source": source,
            "allocation_id": allocation_id,
            "unit_cost": float(_unit_cost),
            "reference_type": reference_type,
        },
    )
    emit_stock_event(
        db, context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        event_name="stock.movement.sale_out",
        entity_type="movement",
        entity_id=ledger.id,
        payload={
            "product_id": product_id, "warehouse_id": warehouse_id,
            "quantity": float(qty), "source": source,
            "unit_cost": float(_unit_cost),
            "reference_type": reference_type, "reference_id": ref_id,
        },
    )

    balance_read = _get_balance_read(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id,
    )
    return StockMovementResultRead(
        operation="sale_out", balance=balance_read,
        ledger_entry_id=ledger.id,
    )


def purchase_in_stock(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    quantity: float,
    unit_cost: float,
    reference_type: str,
    reference_id: str,
    idempotency_key: str | None,
    action_context: StockActionContext,
) -> StockMovementResultRead:
    existing = _idempotent_check(
        db, tenant_id=tenant_id, operation="purchase_in",
        product_id=product_id, warehouse_id=warehouse_id,
        reference_type=reference_type,
        reference_id=idempotency_key or reference_id,
        idempotency_key=idempotency_key,
    )
    if existing is not None:
        return StockMovementResultRead(
            operation="purchase_in", balance=existing,
            ledger_entry_id="idempotent",
        )

    _product = require_product(
        db, tenant_id=tenant_id, product_id=product_id,
    )
    warehouse = require_warehouse(
        db, tenant_id=tenant_id, warehouse_id=warehouse_id,
    )
    qty = _to_dec(quantity)
    uc = _to_dec(unit_cost, FOUR_DECIMALS)

    balance = _lock_balance(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id, actor_user_id=action_context.actor_user_id,
    )
    current_qty = Decimal(str(balance.quantity))
    current_total_cost = Decimal(str(balance.total_cost))

    new_qty = current_qty + qty
    total_cost_in = uc * qty
    new_total_cost = current_total_cost + total_cost_in

    balance.quantity = float(new_qty)
    balance.total_cost = float(new_total_cost)
    db.add(balance)
    db.flush()

    ref_id = idempotency_key or str(uuid4())
    ledger = StockLedger(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        operation="purchase_in",
        quantity=float(qty),
        balance_after=float(new_qty),
        unit_cost=float(uc),
        total_cost=float(total_cost_in),
        cost_after=float(new_total_cost),
        reference_type=reference_type,
        reference_id=ref_id,
        created_by=action_context.actor_user_id,
    )
    db.add(ledger)

    audit_stock_action(
        db, context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        action="movement.purchase_in",
        entity_type="movement",
        entity_id=ledger.id,
        details={
            "product_id": product_id, "warehouse_id": warehouse_id,
            "quantity": float(qty), "unit_cost": float(uc),
            "reference_type": reference_type,
        },
    )
    emit_stock_event(
        db, context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        event_name="stock.movement.purchase_in",
        entity_type="movement",
        entity_id=ledger.id,
        payload={
            "product_id": product_id, "warehouse_id": warehouse_id,
            "quantity": float(qty), "unit_cost": float(uc),
            "reference_type": reference_type, "reference_id": ref_id,
        },
    )

    balance_read = _get_balance_read(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id,
    )
    return StockMovementResultRead(
        operation="purchase_in", balance=balance_read,
        ledger_entry_id=ledger.id,
    )


def return_in_stock(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    quantity: float,
    original_sale_ledger_id: str,
    reference_type: str,
    reference_id: str,
    idempotency_key: str | None,
    action_context: StockActionContext,
) -> StockMovementResultRead:
    existing = _idempotent_check(
        db, tenant_id=tenant_id, operation="return_in",
        product_id=product_id, warehouse_id=warehouse_id,
        reference_type=reference_type,
        reference_id=idempotency_key or reference_id,
        idempotency_key=idempotency_key,
    )
    if existing is not None:
        return StockMovementResultRead(
            operation="return_in", balance=existing,
            ledger_entry_id="idempotent",
        )

    original = db.execute(
        select(StockLedger).where(
            StockLedger.id == original_sale_ledger_id,
            StockLedger.tenant_id == tenant_id,
            StockLedger.operation == "sale_out",
        )
    ).scalar_one_or_none()

    if original is None:
        raise ValueError(
            "original_sale_ledger_id must reference a valid sale_out entry"
        )

    _product = require_product(
        db, tenant_id=tenant_id, product_id=product_id,
    )
    warehouse = require_warehouse(
        db, tenant_id=tenant_id, warehouse_id=warehouse_id,
    )
    qty = _to_dec(quantity)

    historical_unit_cost = _to_dec(original.unit_cost or 0, FOUR_DECIMALS)

    balance = _lock_balance(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id, actor_user_id=action_context.actor_user_id,
    )
    current_qty = Decimal(str(balance.quantity))
    current_total_cost = Decimal(str(balance.total_cost))

    new_qty = current_qty + qty
    total_cost_in = historical_unit_cost * qty
    new_total_cost = current_total_cost + total_cost_in

    balance.quantity = float(new_qty)
    balance.total_cost = float(new_total_cost)
    db.add(balance)
    db.flush()

    ref_id = idempotency_key or str(uuid4())
    ledger = StockLedger(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        operation="return_in",
        quantity=float(qty),
        balance_after=float(new_qty),
        unit_cost=float(historical_unit_cost),
        total_cost=float(total_cost_in),
        cost_after=float(new_total_cost),
        reference_type=reference_type,
        reference_id=ref_id,
        notes=f"Return from sale ledger {original_sale_ledger_id}",
        created_by=action_context.actor_user_id,
    )
    db.add(ledger)

    audit_stock_action(
        db, context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        action="movement.return_in",
        entity_type="movement",
        entity_id=ledger.id,
        details={
            "product_id": product_id, "warehouse_id": warehouse_id,
            "quantity": float(qty),
            "historical_unit_cost": float(historical_unit_cost),
            "original_sale_ledger_id": original_sale_ledger_id,
            "reference_type": reference_type,
        },
    )
    emit_stock_event(
        db, context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        event_name="stock.movement.return_in",
        entity_type="movement",
        entity_id=ledger.id,
        payload={
            "product_id": product_id, "warehouse_id": warehouse_id,
            "quantity": float(qty),
            "unit_cost": float(historical_unit_cost),
            "original_sale_ledger_id": original_sale_ledger_id,
            "reference_type": reference_type, "reference_id": ref_id,
        },
    )

    balance_read = _get_balance_read(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id,
    )
    return StockMovementResultRead(
        operation="return_in", balance=balance_read,
        ledger_entry_id=ledger.id,
    )


def damage_out_stock(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    quantity: float,
    reason: str | None,
    reference_type: str,
    reference_id: str,
    idempotency_key: str | None,
    action_context: StockActionContext,
) -> StockMovementResultRead:
    existing = _idempotent_check(
        db, tenant_id=tenant_id, operation="damage_out",
        product_id=product_id, warehouse_id=warehouse_id,
        reference_type=reference_type,
        reference_id=idempotency_key or reference_id,
        idempotency_key=idempotency_key,
    )
    if existing is not None:
        return StockMovementResultRead(
            operation="damage_out", balance=existing,
            ledger_entry_id="idempotent",
        )

    _product = require_product(
        db, tenant_id=tenant_id, product_id=product_id,
    )
    warehouse = require_warehouse(
        db, tenant_id=tenant_id, warehouse_id=warehouse_id,
    )
    qty = _to_dec(quantity)

    balance = _lock_balance(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id, actor_user_id=action_context.actor_user_id,
    )
    current_qty = Decimal(str(balance.quantity))
    current_total_cost = Decimal(str(balance.total_cost))

    new_qty = current_qty - qty
    if new_qty < 0 and not _allow_negative_stock(  # noqa: F841
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id, balance=balance,
    ):
        raise ValueError(
            f"Stock insuficiente: disponible={float(current_qty)},"
            f" solicitado={quantity}"
        )

    _unit_cost = (
        _avg_cost(float(current_total_cost), float(current_qty))
        if current_qty > 0
        else Decimal("0.0000")
    )
    total_cost_out = _unit_cost * qty
    new_total_cost = current_total_cost - total_cost_out
    if new_qty <= 0:
        new_total_cost = Decimal("0.0000")

    balance.quantity = float(new_qty)
    balance.total_cost = float(new_total_cost)
    db.add(balance)
    db.flush()

    ref_id = idempotency_key or str(uuid4())
    ledger = StockLedger(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        operation="damage_out",
        quantity=float(-qty),
        balance_after=float(new_qty),
        unit_cost=float(_unit_cost),
        total_cost=float(total_cost_out),
        cost_after=float(new_total_cost),
        reference_type=reference_type,
        reference_id=ref_id,
        notes=reason,
        created_by=action_context.actor_user_id,
    )
    db.add(ledger)

    audit_stock_action(
        db, context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        action="movement.damage_out",
        entity_type="movement",
        entity_id=ledger.id,
        details={
            "product_id": product_id, "warehouse_id": warehouse_id,
            "quantity": float(qty), "reason": reason,
            "reference_type": reference_type,
        },
    )
    emit_stock_event(
        db, context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        event_name="stock.movement.damage_out",
        entity_type="movement",
        entity_id=ledger.id,
        payload={
            "product_id": product_id, "warehouse_id": warehouse_id,
            "quantity": float(qty), "reason": reason,
            "reference_type": reference_type, "reference_id": ref_id,
        },
    )

    if new_qty < 0:
        emit_stock_event(
            db, context=action_context,
            branch_id=warehouse.branch_id or action_context.branch_id,
            event_name="stock.balance.negative_warning",
            entity_type="balance",
            entity_id=balance.id,
            payload={
                "product_id": product_id, "warehouse_id": warehouse_id,
                "quantity": float(new_qty), "operation": "damage_out",
            },
        )

    balance_read = _get_balance_read(
        db, tenant_id=tenant_id, product_id=product_id,
        warehouse_id=warehouse_id,
    )
    return StockMovementResultRead(
        operation="damage_out", balance=balance_read,
        ledger_entry_id=ledger.id,
    )
