from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plugins.stock.backend.common import StockActionContext, audit_stock_action, emit_stock_event
from plugins.stock.backend.models import StockAllocation, StockBalance, StockLedger
from plugins.stock.backend.schemas import StockAllocationRead
from plugins.stock.backend.services.catalog import require_product, require_warehouse

THREE_DECIMALS = Decimal("0.001")


def _to_decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(THREE_DECIMALS, rounding=ROUND_HALF_UP)


def _lock_balance(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    actor_user_id: str,
) -> StockBalance:
    stmt = (
        select(StockBalance)
        .where(
            StockBalance.tenant_id == tenant_id,
            StockBalance.product_id == product_id,
            StockBalance.warehouse_id == warehouse_id,
        )
        .with_for_update()
    )
    balance = db.scalar(stmt)
    if balance is not None:
        return balance

    savepoint = db.begin_nested()
    try:
        balance = StockBalance(
            tenant_id=tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity=Decimal("0.000"),
            reserved_quantity=Decimal("0.000"),
            total_cost=Decimal("0.0000"),
            updated_by=actor_user_id,
        )
        db.add(balance)
        db.flush()
        savepoint.commit()
        return balance
    except IntegrityError:
        savepoint.rollback()
        balance = db.scalar(stmt)
        if balance is None:
            raise
        return balance


def _build_allocation_read(allocation: StockAllocation) -> StockAllocationRead:
    return StockAllocationRead.model_validate(allocation)


def allocate_stock(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    quantity: float,
    reference_type: str,
    reference_id: str,
    allocation_group_id: str | None,
    expires_at: str | None,
    action_context: StockActionContext,
) -> StockAllocationRead:
    product = require_product(db, tenant_id=tenant_id, product_id=product_id)
    warehouse = require_warehouse(db, tenant_id=tenant_id, warehouse_id=warehouse_id)
    qty = _to_decimal(quantity)

    balance = _lock_balance(
        db,
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        actor_user_id=action_context.actor_user_id,
    )
    current_qty = Decimal(str(balance.quantity))
    current_reserved = Decimal(str(balance.reserved_quantity))
    available = current_qty - current_reserved

    if available < qty:
        raise ValueError(
            f"Stock insuficiente: disponible={float(available)}, solicitado={quantity}"
        )

    balance.reserved_quantity = float(current_reserved + qty)
    db.add(balance)
    db.flush()

    allocation = StockAllocation(
        tenant_id=tenant_id,
        allocation_group_id=allocation_group_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=float(qty),
        remaining_quantity=float(qty),
        reference_type=reference_type,
        reference_id=reference_id,
        status="active",
        created_by=action_context.actor_user_id,
    )
    if expires_at:
        allocation.expires_at = expires_at  # type: ignore[assignment]

    db.add(allocation)
    db.flush()

    ledger = StockLedger(
        tenant_id=tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        operation="reserve",
        quantity=0,
        balance_after=float(current_qty),
        reference_type="allocation",
        reference_id=allocation.id,
        notes=f"Allocation for {reference_type}:{reference_id}",
        created_by=action_context.actor_user_id,
    )
    db.add(ledger)

    audit_stock_action(
        db,
        context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        action="allocation.create",
        entity_type="allocation",
        entity_id=allocation.id,
        details={
            "product_id": product_id,
            "product_sku": product.sku,
            "warehouse_id": warehouse_id,
            "warehouse_code": warehouse.code,
            "quantity": float(qty),
            "reserved_after": float(current_reserved + qty),
            "available_after": float(available - qty),
            "reference_type": reference_type,
            "reference_id": reference_id,
        },
    )
    emit_stock_event(
        db,
        context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        event_name="stock.allocation.reserved",
        entity_type="allocation",
        entity_id=allocation.id,
        payload={
            "product_id": product_id,
            "warehouse_id": warehouse_id,
            "quantity": float(qty),
            "allocation_group_id": allocation_group_id,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "expires_at": expires_at,
        },
    )

    return _build_allocation_read(allocation)


def release_allocation(
    db: Session,
    *,
    allocation_id: str,
    reason: str | None,
    action_context: StockActionContext,
) -> StockAllocationRead:
    allocation = db.execute(
        select(StockAllocation).where(
            StockAllocation.id == allocation_id,
            StockAllocation.tenant_id == action_context.tenant_id,
        ).with_for_update()
    ).scalar_one_or_none()

    if allocation is None:
        raise LookupError("Allocation not found")
    if allocation.status not in ("active", "partially_consumed"):
        raise ValueError(f"Cannot release allocation with status '{allocation.status}'")

    warehouse = require_warehouse(
        db,
        tenant_id=action_context.tenant_id,
        warehouse_id=allocation.warehouse_id,
    )

    released_qty = Decimal(str(allocation.remaining_quantity))

    balance = _lock_balance(
        db,
        tenant_id=action_context.tenant_id,
        product_id=allocation.product_id,
        warehouse_id=allocation.warehouse_id,
        actor_user_id=action_context.actor_user_id,
    )
    balance.reserved_quantity = float(Decimal(str(balance.reserved_quantity)) - released_qty)
    db.add(balance)

    allocation.status = "released"
    allocation.released_at = allocation.released_at or None  # preserve existing if set
    from datetime import UTC, datetime
    allocation.released_at = datetime.now(UTC)  # type: ignore[assignment]
    allocation.released_by = action_context.actor_user_id
    allocation.release_reason = reason
    db.add(allocation)
    db.flush()

    ledger = StockLedger(
        tenant_id=action_context.tenant_id,
        product_id=allocation.product_id,
        warehouse_id=allocation.warehouse_id,
        operation="release",
        quantity=0,
        balance_after=float(Decimal(str(balance.quantity))),
        reference_type="allocation",
        reference_id=allocation.id,
        notes=f"Released: {reason or 'manual'}",
        created_by=action_context.actor_user_id,
    )
    db.add(ledger)

    audit_stock_action(
        db,
        context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        action="allocation.release",
        entity_type="allocation",
        entity_id=allocation.id,
        details={
            "product_id": allocation.product_id,
            "warehouse_id": allocation.warehouse_id,
            "released_quantity": float(released_qty),
            "reason": reason,
        },
    )
    emit_stock_event(
        db,
        context=action_context,
        branch_id=warehouse.branch_id or action_context.branch_id,
        event_name="stock.allocation.released",
        entity_type="allocation",
        entity_id=allocation.id,
        payload={
            "product_id": allocation.product_id,
            "warehouse_id": allocation.warehouse_id,
            "quantity": float(released_qty),
            "allocation_group_id": allocation.allocation_group_id,
            "reference_type": allocation.reference_type,
            "reference_id": allocation.reference_id,
            "reason": reason,
        },
    )

    return _build_allocation_read(allocation)


def release_allocation_group(
    db: Session,
    *,
    group_id: str,
    reason: str | None,
    action_context: StockActionContext,
) -> list[StockAllocationRead]:
    allocations = db.execute(
        select(StockAllocation).where(
            StockAllocation.tenant_id == action_context.tenant_id,
            StockAllocation.allocation_group_id == group_id,
            StockAllocation.status.in_(("active", "partially_consumed")),
        ).with_for_update()
    ).scalars().all()

    results: list[StockAllocationRead] = []
    for allocation in allocations:
        released = release_allocation(
            db,
            allocation_id=allocation.id,
            reason=reason or "group-release",
            action_context=action_context,
        )
        results.append(released)

    return results


def get_allocation(db: Session, *, tenant_id: str, allocation_id: str) -> StockAllocationRead:
    allocation = db.execute(
        select(StockAllocation).where(
            StockAllocation.id == allocation_id,
            StockAllocation.tenant_id == tenant_id,
        )
    ).scalar_one_or_none()
    if allocation is None:
        raise LookupError("Allocation not found")
    return _build_allocation_read(allocation)


def list_allocations(
    db: Session,
    *,
    tenant_id: str,
    status: str | None,
    reference_type: str | None,
    allocation_group_id: str | None,
    product_id: str | None,
    warehouse_id: str | None,
    limit: int,
    offset: int,
) -> list[StockAllocationRead]:
    stmt = select(StockAllocation).where(StockAllocation.tenant_id == tenant_id)

    if status:
        stmt = stmt.where(StockAllocation.status == status)
    if reference_type:
        stmt = stmt.where(StockAllocation.reference_type == reference_type)
    if allocation_group_id:
        stmt = stmt.where(StockAllocation.allocation_group_id == allocation_group_id)
    if product_id:
        stmt = stmt.where(StockAllocation.product_id == product_id)
    if warehouse_id:
        stmt = stmt.where(StockAllocation.warehouse_id == warehouse_id)

    allocations = db.execute(
        stmt.order_by(StockAllocation.created_at.desc()).offset(offset).limit(limit)
    ).scalars().all()

    return [_build_allocation_read(a) for a in allocations]


def list_allocations_by_group(
    db: Session,
    *,
    tenant_id: str,
    group_id: str,
) -> list[StockAllocationRead]:
    allocations = db.execute(
        select(StockAllocation).where(
            StockAllocation.tenant_id == tenant_id,
            StockAllocation.allocation_group_id == group_id,
        ).order_by(StockAllocation.created_at.asc())
    ).scalars().all()
    return [_build_allocation_read(a) for a in allocations]
