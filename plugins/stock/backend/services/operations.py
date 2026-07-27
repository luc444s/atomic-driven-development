from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.stock.backend.common import StockActionContext, audit_stock_action, emit_stock_event
from plugins.stock.backend.models import StockBalance, StockConfig, StockLedger
from plugins.stock.backend.schemas import StockBalanceRead, StockConfigRead, StockTransferResultRead
from plugins.stock.backend.services.allocation import _lock_balance
from plugins.stock.backend.services.balances import (
    _as_float,
    _build_balance_read,
    get_balance_detail,
)
from plugins.stock.backend.services.catalog import require_product, require_warehouse

THREE_DECIMALS = Decimal("0.001")
FOUR_DECIMALS = Decimal("0.0001")


@dataclass(slots=True)
class _TransferPair:
    origin: StockBalance
    destination: StockBalance


def _to_decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(THREE_DECIMALS, rounding=ROUND_HALF_UP)


def _to_cost(value: float) -> Decimal:
    return Decimal(str(value)).quantize(FOUR_DECIMALS, rounding=ROUND_HALF_UP)


def _current_quantity(value: object | None) -> Decimal:
    if value is None:
        return Decimal("0.000")
    if isinstance(value, Decimal):
        return value.quantize(THREE_DECIMALS, rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(THREE_DECIMALS, rounding=ROUND_HALF_UP)


def _current_cost(value: object | None) -> Decimal:
    if value is None:
        return Decimal("0.0000")
    if isinstance(value, Decimal):
        return value.quantize(FOUR_DECIMALS, rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(FOUR_DECIMALS, rounding=ROUND_HALF_UP)


def _avg_cost(total_cost: Decimal, quantity: Decimal) -> Decimal:
    if quantity == Decimal("0.000"):
        return Decimal("0.0000")
    return (total_cost / quantity).quantize(FOUR_DECIMALS, rounding=ROUND_HALF_UP)


def _existing_adjustment_result(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    idempotency_key: str | None,
) -> StockBalanceRead | None:
    if not idempotency_key:
        return None
    existing = db.scalar(
        select(StockLedger.id).where(
            StockLedger.tenant_id == tenant_id,
            StockLedger.product_id == product_id,
            StockLedger.warehouse_id == warehouse_id,
            StockLedger.operation == "adjust",
            StockLedger.reference_type == "adjustment",
            StockLedger.reference_id == idempotency_key,
        )
    )
    if existing is None:
        return None
    return get_balance_detail(
        db,
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
    )


def _existing_transfer_result(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    from_warehouse_id: str,
    to_warehouse_id: str,
    idempotency_key: str | None,
) -> StockTransferResultRead | None:
    if not idempotency_key:
        return None
    rows = db.scalars(
        select(StockLedger).where(
            StockLedger.tenant_id == tenant_id,
            StockLedger.product_id == product_id,
            StockLedger.reference_type == "transfer",
            StockLedger.reference_id == idempotency_key,
        )
    ).all()
    if not rows:
        return None
    return StockTransferResultRead(
        reference_id=idempotency_key,
        from_balance=get_balance_detail(
            db,
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=from_warehouse_id,
        ),
        to_balance=get_balance_detail(
            db,
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=to_warehouse_id,
        ),
    )


def adjust_stock(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    quantity: float,
    reason: str | None,
    unit_cost: float | None,
    idempotency_key: str | None,
    action_context: StockActionContext,
) -> StockBalanceRead:
    existing = _existing_adjustment_result(
        db,
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        idempotency_key=idempotency_key,
    )
    if existing is not None:
        return existing

    product = require_product(db, tenant_id=tenant_id, product_id=product_id)
    warehouse = require_warehouse(db, tenant_id=tenant_id, warehouse_id=warehouse_id)
    quantity_decimal = _to_decimal(quantity)
    if quantity_decimal == Decimal("0.000"):
        raise ValueError("La cantidad debe ser diferente de cero")

    is_positive = quantity_decimal > Decimal("0.000")
    if is_positive and unit_cost is None:
        raise ValueError("unit_cost es obligatorio para ajustes positivos")

    balance = _lock_balance(
        db,
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        actor_user_id=action_context.actor_user_id,
    )
    current = _current_quantity(balance.quantity)
    current_total_cost = _current_cost(balance.total_cost)

    new_quantity = current + quantity_decimal
    if new_quantity < Decimal("0.000"):
        raise ValueError("Stock insuficiente para el ajuste")

    if is_positive:
        assert unit_cost is not None
        uc = _to_cost(unit_cost)
        total_cost_in = uc * quantity_decimal
        new_total_cost = current_total_cost + total_cost_in
    else:
        uc = (
            _avg_cost(current_total_cost, current)
            if current > Decimal("0.000")
            else Decimal("0.0000")
        )
        total_cost_out = uc * abs(quantity_decimal)
        new_total_cost = current_total_cost - total_cost_out
        if new_quantity <= Decimal("0.000"):
            new_total_cost = Decimal("0.0000")

    balance.quantity = float(new_quantity)
    balance.total_cost = float(new_total_cost)
    db.add(balance)
    db.flush()

    reference_id = idempotency_key or str(uuid4())
    ledger = StockLedger(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        operation="adjust",
        quantity=float(quantity_decimal),
        balance_after=float(new_quantity),
        unit_cost=float(uc),
        total_cost=float(uc * quantity_decimal),
        cost_after=float(new_total_cost),
        reference_type="adjustment",
        reference_id=reference_id,
        notes=reason,
        created_by=action_context.actor_user_id,
    )
    db.add(ledger)

    config = db.scalar(
        select(StockConfig).where(
            StockConfig.tenant_id == tenant_id,
            StockConfig.product_id == product_id,
            StockConfig.warehouse_id == warehouse_id,
        )
    )

    audit_stock_action(
        db,
        context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        action="balance.adjust",
        entity_type="balance",
        entity_id=balance.id,
        details={
            "product_id": product_id,
            "product_sku": product.sku,
            "warehouse_id": warehouse_id,
            "warehouse_code": warehouse.code,
            "branch_id": warehouse.branch_id,
            "quantity": float(quantity_decimal),
            "balance_after": float(new_quantity),
            "unit_cost": float(uc),
            "reference_id": reference_id,
            "reason": reason,
        },
    )
    emit_stock_event(
        db,
        context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        event_name="stock.balance.adjusted",
        entity_type="balance",
        entity_id=balance.id,
        payload={
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "branch_id": warehouse.branch_id,
            "quantity": float(quantity_decimal),
            "balance_after": float(new_quantity),
            "reference_type": "adjustment",
            "reference_id": reference_id,
            "notes": reason or "",
        },
    )

    if new_quantity < Decimal("0.000"):
        emit_stock_event(
            db,
            context=action_context,
            branch_id=warehouse.branch_id or action_context.branch_id,
            event_name="stock.balance.negative_warning",
            entity_type="balance",
            entity_id=balance.id,
            payload={
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": float(new_quantity),
                "operation": "adjust",
            },
        )

    return _build_balance_read(balance=balance, product=product, warehouse=warehouse, config=config)


def transfer_stock(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    from_warehouse_id: str,
    to_warehouse_id: str,
    quantity: float,
    notes: str | None,
    idempotency_key: str | None,
    action_context: StockActionContext,
) -> StockTransferResultRead:
    existing = _existing_transfer_result(
        db,
        tenant_id=tenant_id,
        product_id=product_id,
        from_warehouse_id=from_warehouse_id,
        to_warehouse_id=to_warehouse_id,
        idempotency_key=idempotency_key,
    )
    if existing is not None:
        return existing

    if from_warehouse_id == to_warehouse_id:
        raise ValueError("El almacén de origen y destino deben ser diferentes")

    product = require_product(db, tenant_id=tenant_id, product_id=product_id)
    from_warehouse = require_warehouse(db, tenant_id=tenant_id, warehouse_id=from_warehouse_id)
    to_warehouse = require_warehouse(db, tenant_id=tenant_id, warehouse_id=to_warehouse_id)
    quantity_decimal = _to_decimal(quantity)
    if quantity_decimal <= Decimal("0.000"):
        raise ValueError("La cantidad debe ser mayor que cero")

    first_warehouse_id, second_warehouse_id = sorted([from_warehouse_id, to_warehouse_id])
    first_balance = _lock_balance(
        db,
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=first_warehouse_id,
        actor_user_id=action_context.actor_user_id,
    )
    second_balance = _lock_balance(
        db,
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=second_warehouse_id,
        actor_user_id=action_context.actor_user_id,
    )
    pair = _TransferPair(
        origin=first_balance if first_warehouse_id == from_warehouse_id else second_balance,
        destination=second_balance if second_warehouse_id == to_warehouse_id else first_balance,
    )

    origin_current = _current_quantity(pair.origin.quantity)
    origin_reserved = _current_quantity(pair.origin.reserved_quantity)
    available = origin_current - origin_reserved
    if available < quantity_decimal:
        raise ValueError(
            f"Stock insuficiente para transferencia: disponible={float(available)}, "
            f"reservado={float(origin_reserved)}, solicitado={quantity}"
        )

    destination_current = _current_quantity(pair.destination.quantity)
    origin_total_cost = _current_cost(pair.origin.total_cost)
    destination_total_cost = _current_cost(pair.destination.total_cost)

    unit_cost = (
        _avg_cost(origin_total_cost, origin_current)
        if origin_current > Decimal("0.000")
        else Decimal("0.0000")
    )
    total_cost_out = unit_cost * quantity_decimal

    new_origin_cost = origin_total_cost - total_cost_out
    if origin_current - quantity_decimal <= Decimal("0.000"):
        new_origin_cost = Decimal("0.0000")
    new_dest_cost = destination_total_cost + total_cost_out

    pair.origin.quantity = float(origin_current - quantity_decimal)
    pair.origin.total_cost = float(new_origin_cost)
    pair.origin.updated_by = action_context.actor_user_id
    pair.destination.quantity = float(destination_current + quantity_decimal)
    pair.destination.total_cost = float(new_dest_cost)
    pair.destination.updated_by = action_context.actor_user_id

    reference_id = idempotency_key or str(uuid4())
    ledger_out = StockLedger(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=from_warehouse_id,
        operation="transfer_out",
        quantity=float(-quantity_decimal),
        balance_after=pair.origin.quantity,
        unit_cost=float(unit_cost),
        total_cost=float(total_cost_out),
        cost_after=float(new_origin_cost),
        reference_type="transfer",
        reference_id=reference_id,
        notes=notes,
        created_by=action_context.actor_user_id,
    )
    ledger_in = StockLedger(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=to_warehouse_id,
        operation="transfer_in",
        quantity=float(quantity_decimal),
        balance_after=pair.destination.quantity,
        unit_cost=float(unit_cost),
        total_cost=float(total_cost_out),
        cost_after=float(new_dest_cost),
        reference_type="transfer",
        reference_id=reference_id,
        notes=notes,
        created_by=action_context.actor_user_id,
    )
    db.add(ledger_out)
    db.add(ledger_in)
    db.add(pair.origin)
    db.add(pair.destination)
    db.flush()

    audit_stock_action(
        db,
        context=action_context,
        branch_id=from_warehouse.branch_id or to_warehouse.branch_id or action_context.branch_id,
        action="transfer.create",
        entity_type="transfer",
        entity_id=reference_id,
        details={
            "product_id": product_id,
            "product_sku": product.sku,
            "from_warehouse_id": from_warehouse_id,
            "from_warehouse_code": from_warehouse.code,
            "from_branch_id": from_warehouse.branch_id,
            "to_warehouse_id": to_warehouse_id,
            "to_warehouse_code": to_warehouse.code,
            "to_branch_id": to_warehouse.branch_id,
            "quantity": float(quantity_decimal),
            "unit_cost": float(unit_cost),
            "reference_id": reference_id,
            "notes": notes,
        },
    )
    emit_stock_event(
        db,
        context=action_context,
        branch_id=from_warehouse.branch_id or to_warehouse.branch_id or action_context.branch_id,
        event_name="stock.transfer.completed",
        entity_type="transfer",
        entity_id=reference_id,
        payload={
            "product_id": product_id,
            "from_warehouse_id": from_warehouse_id,
            "from_branch_id": from_warehouse.branch_id,
            "to_warehouse_id": to_warehouse_id,
            "to_branch_id": to_warehouse.branch_id,
            "quantity": float(quantity_decimal),
            "unit_cost": float(unit_cost),
            "reference_type": "transfer",
            "reference_id": reference_id,
            "notes": notes or "",
        },
    )
    return StockTransferResultRead(
        reference_id=reference_id,
        from_balance=get_balance_detail(
            db,
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=from_warehouse_id,
        ),
        to_balance=get_balance_detail(
            db,
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=to_warehouse_id,
        ),
    )


def upsert_stock_config(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    min_quantity: float,
    max_quantity: float | None,
    allow_negative_stock: bool | None,
    is_active: bool,
    action_context: StockActionContext,
) -> StockConfigRead:
    if min_quantity < 0:
        raise ValueError("La cantidad mínima no puede ser negativa")
    if max_quantity is not None and max_quantity < 0:
        raise ValueError("La cantidad máxima no puede ser negativa")
    if max_quantity is not None and max_quantity < min_quantity:
        raise ValueError("La cantidad máxima no puede ser menor que la cantidad mínima")

    product = require_product(db, tenant_id=tenant_id, product_id=product_id)
    warehouse = require_warehouse(db, tenant_id=tenant_id, warehouse_id=warehouse_id)
    config = db.scalar(
        select(StockConfig).where(
            StockConfig.tenant_id == tenant_id,
            StockConfig.product_id == product_id,
            StockConfig.warehouse_id == warehouse_id,
        )
    )
    if config is None:
        config = StockConfig(
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            min_quantity=float(_to_decimal(min_quantity)),
            max_quantity=float(_to_decimal(max_quantity)) if max_quantity is not None else None,
            allow_negative_stock=(
                allow_negative_stock
                if allow_negative_stock is not None
                else False
            ),
            is_active=is_active,
            updated_by=action_context.actor_user_id,
        )
    else:
        config.min_quantity = float(_to_decimal(min_quantity))
        config.max_quantity = float(_to_decimal(max_quantity)) if max_quantity is not None else None
        if allow_negative_stock is not None:
            config.allow_negative_stock = allow_negative_stock
        config.is_active = is_active
        config.updated_by = action_context.actor_user_id
    db.add(config)
    db.flush()
    audit_stock_action(
        db,
        context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        action="config.manage",
        entity_type="config",
        entity_id=config.id,
        details={
            "product_id": product_id,
            "product_sku": product.sku,
            "warehouse_id": warehouse_id,
            "warehouse_code": warehouse.code,
            "branch_id": warehouse.branch_id,
            "min_quantity": min_quantity,
            "max_quantity": max_quantity,
            "allow_negative_stock": config.allow_negative_stock,
            "is_active": is_active,
        },
    )
    return StockConfigRead(
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
        allow_negative_stock=config.allow_negative_stock,
        is_active=config.is_active,
        updated_at=config.updated_at,
        updated_by=config.updated_by,
    )
