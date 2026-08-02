from __future__ import annotations

from typing import Never

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import (
    get_current_tenant_context,
    require_any_permission,
    require_permission,
)
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.stock.backend.common import audit_stock_action, build_action_context
from plugins.stock.backend.schemas import (
    StockAdjustRequest,
    StockAllocateRequest,
    StockAllocationRead,
    StockAllocationReleaseRequest,
    StockBalancePageRead,
    StockBalanceRead,
    StockConfigRead,
    StockConfigUpsertRequest,
    StockDamageOutRequest,
    StockLedgerRead,
    StockMovementResultRead,
    StockPurchaseInRequest,
    StockReturnInRequest,
    StockSaleOutRequest,
    StockTransferRequest,
    StockTransferResultRead,
    StockWarehouseRead,
)
from plugins.stock.backend.services.allocation import (
    allocate_stock,
    get_allocation,
    list_allocations,
    list_allocations_by_group,
    release_allocation,
    release_allocation_group,
)
from plugins.stock.backend.services.balances import (
    get_balance_detail,
    list_balances,
    list_configs,
    list_global_ledger,
    list_ledger_entries,
    list_product_balances,
)
from plugins.stock.backend.services.catalog import list_warehouses
from plugins.stock.backend.services.movements import (
    damage_out_stock,
    purchase_in_stock,
    return_in_stock,
    sale_out_stock,
)
from plugins.stock.backend.services.operations import (
    adjust_stock,
    transfer_stock,
    upsert_stock_config,
)

router = APIRouter(tags=["stock"])
DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)

REQUIRE_BALANCE_READ = Depends(require_permission("stock.balance.read"))
REQUIRE_BALANCE_ADJUST = Depends(require_permission("stock.balance.adjust"))
REQUIRE_TRANSFER_CREATE = Depends(require_permission("stock.transfer.create"))
REQUIRE_CONFIG_READ = Depends(require_permission("stock.config.read"))
REQUIRE_CONFIG_MANAGE = Depends(require_permission("stock.config.manage"))
REQUIRE_ALLOCATION_CREATE = Depends(require_permission("stock.allocation.create"))
REQUIRE_ALLOCATION_RELEASE = Depends(require_permission("stock.allocation.release"))
REQUIRE_ALLOCATION_READ = Depends(require_permission("stock.allocation.read"))
REQUIRE_MOVEMENT_SALE_OUT = Depends(require_permission("stock.movement.sale_out"))
REQUIRE_MOVEMENT_PURCHASE_IN = Depends(require_permission("stock.movement.purchase_in"))
REQUIRE_MOVEMENT_RETURN_IN = Depends(require_permission("stock.movement.return_in"))
REQUIRE_MOVEMENT_DAMAGE_OUT = Depends(require_permission("stock.movement.damage_out"))
REQUIRE_STOCK_CATALOG = Depends(
    require_any_permission(
        "stock.balance.read",
        "stock.balance.adjust",
        "stock.transfer.create",
        "stock.config.read",
        "stock.config.manage",
        "stock.allocation.create",
        "stock.allocation.release",
        "stock.allocation.read",
        "stock.movement.sale_out",
        "stock.movement.purchase_in",
        "stock.movement.return_in",
        "stock.movement.damage_out",
    )
)


def _bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def _not_found(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)


def _raise_service_error(exc: Exception) -> Never:
    if isinstance(exc, LookupError):
        raise _not_found(str(exc)) from exc
    if isinstance(exc, ValueError):
        raise _bad_request(str(exc)) from exc
    raise exc


def _ensure_warehouse_access(
    db: Session,
    *,
    tenant_context: TenantContext,
    request: Request,
    warehouse_id: str,
    action: str,
) -> None:
    if tenant_context.has_warehouse_access(warehouse_id):
        return
    audit_stock_action(
        db,
        context=build_action_context(request, tenant_context),
        action=action,
        entity_type="warehouse",
        entity_id=warehouse_id,
        result="denied",
        details={"warehouse_id": warehouse_id, "reason": "warehouse scope denied"},
    )
    db.commit()
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Warehouse access denied")


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


@router.get(
    "/catalog/warehouses",
    response_model=list[StockWarehouseRead],
    dependencies=[REQUIRE_STOCK_CATALOG],
)
def get_stock_warehouses_catalog(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[StockWarehouseRead]:
    warehouses = list_warehouses(
        db,
        tenant_id=tenant_context.current_tenant_id,
        allowed_warehouse_ids=tenant_context.current_warehouse_ids,
    )
    return [
        StockWarehouseRead(
            id=warehouse.id,
            tenant_id=warehouse.tenant_id,
            branch_id=warehouse.branch_id,
            name=warehouse.name,
            code=warehouse.code,
            address=warehouse.address,
            phone=warehouse.phone,
            is_active=warehouse.is_active,
            is_primary=warehouse.is_primary,
            created_at=warehouse.created_at,
            updated_at=warehouse.updated_at,
        )
        for warehouse in warehouses
    ]


# ---------------------------------------------------------------------------
# Balances
# ---------------------------------------------------------------------------


@router.get("/balance", response_model=StockBalancePageRead, dependencies=[REQUIRE_BALANCE_READ])
def get_balances(
    request: Request,
    q: str | None = Query(default=None),
    product_id: str | None = Query(default=None),
    warehouse_id: str | None = Query(default=None),
    below_min_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockBalancePageRead:
    if warehouse_id is not None:
        _ensure_warehouse_access(
            db, tenant_context=tenant_context, request=request,
            warehouse_id=warehouse_id, action="balance.read",
        )
    return list_balances(
        db,
        tenant_id=tenant_context.current_tenant_id,
        q=q,
        product_id=product_id,
        warehouse_id=warehouse_id,
        below_min_only=below_min_only,
        allowed_warehouse_ids=tenant_context.current_warehouse_ids,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/balance/{product_id}",
    response_model=list[StockBalanceRead],
    dependencies=[REQUIRE_BALANCE_READ],
)
def get_product_balances(
    product_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[StockBalanceRead]:
    try:
        return list_product_balances(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=product_id,
            allowed_warehouse_ids=tenant_context.current_warehouse_ids,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.get(
    "/balance/{product_id}/{warehouse_id}",
    response_model=StockBalanceRead,
    dependencies=[REQUIRE_BALANCE_READ],
)
def get_balance_by_product_warehouse(
    product_id: str,
    warehouse_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockBalanceRead:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=warehouse_id, action="balance.read",
    )
    try:
        return get_balance_detail(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
        )
    except Exception as exc:
        _raise_service_error(exc)


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------


@router.get(
    "/ledger/{product_id}",
    response_model=list[StockLedgerRead],
    dependencies=[REQUIRE_BALANCE_READ],
)
def get_product_ledger(
    product_id: str,
    request: Request,
    warehouse_id: str | None = Query(default=None),
    operation: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[StockLedgerRead]:
    if warehouse_id is not None:
        _ensure_warehouse_access(
            db, tenant_context=tenant_context, request=request,
            warehouse_id=warehouse_id, action="ledger.read",
        )
    try:
        return list_ledger_entries(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            operation=operation,
            allowed_warehouse_ids=tenant_context.current_warehouse_ids,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.get(
    "/ledger/{product_id}/{warehouse_id}",
    response_model=list[StockLedgerRead],
    dependencies=[REQUIRE_BALANCE_READ],
)
def get_product_warehouse_ledger(
    product_id: str,
    warehouse_id: str,
    request: Request,
    operation: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[StockLedgerRead]:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=warehouse_id, action="ledger.read",
    )
    try:
        return list_ledger_entries(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=product_id,
            warehouse_id=warehouse_id,
            operation=operation,
            allowed_warehouse_ids=tenant_context.current_warehouse_ids,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.get(
    "/ledger",
    response_model=list[StockLedgerRead],
    dependencies=[REQUIRE_BALANCE_READ],
)
def get_global_ledger(
    request: Request,
    product_id: str | None = Query(default=None),
    warehouse_id: str | None = Query(default=None),
    operation: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[StockLedgerRead]:
    if warehouse_id is not None:
        _ensure_warehouse_access(
            db, tenant_context=tenant_context, request=request,
            warehouse_id=warehouse_id, action="ledger.read",
        )
    return list_global_ledger(
        db,
        tenant_id=tenant_context.current_tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        operation=operation,
        allowed_warehouse_ids=tenant_context.current_warehouse_ids,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# Adjust
# ---------------------------------------------------------------------------


@router.post(
    "/adjust",
    response_model=StockBalanceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_BALANCE_ADJUST],
)
def post_adjust_stock(
    payload: StockAdjustRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockBalanceRead:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=payload.warehouse_id, action="balance.adjust",
    )
    try:
        result = adjust_stock(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            quantity=payload.quantity,
            reason=payload.reason,
            unit_cost=payload.unit_cost,
            idempotency_key=payload.idempotency_key,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


# ---------------------------------------------------------------------------
# Transfer
# ---------------------------------------------------------------------------


@router.post(
    "/transfer",
    response_model=StockTransferResultRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_TRANSFER_CREATE],
)
def post_transfer_stock(
    payload: StockTransferRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockTransferResultRead:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=payload.from_warehouse_id, action="transfer.create",
    )
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=payload.to_warehouse_id, action="transfer.create",
    )
    try:
        result = transfer_stock(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=payload.product_id,
            from_warehouse_id=payload.from_warehouse_id,
            to_warehouse_id=payload.to_warehouse_id,
            quantity=payload.quantity,
            notes=payload.notes,
            idempotency_key=payload.idempotency_key,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@router.get("/config", response_model=list[StockConfigRead], dependencies=[REQUIRE_CONFIG_READ])
def get_stock_configs(
    request: Request,
    product_id: str | None = Query(default=None),
    warehouse_id: str | None = Query(default=None),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[StockConfigRead]:
    if warehouse_id is not None:
        _ensure_warehouse_access(
            db, tenant_context=tenant_context, request=request,
            warehouse_id=warehouse_id, action="config.read",
        )
    return list_configs(
        db,
        tenant_id=tenant_context.current_tenant_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        allowed_warehouse_ids=tenant_context.current_warehouse_ids,
    )


@router.put("/config", response_model=StockConfigRead, dependencies=[REQUIRE_CONFIG_MANAGE])
def put_stock_config(
    payload: StockConfigUpsertRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockConfigRead:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=payload.warehouse_id, action="config.manage",
    )
    try:
        result = upsert_stock_config(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            min_quantity=payload.min_quantity,
            max_quantity=payload.max_quantity,
            allow_negative_stock=payload.allow_negative_stock,
            is_active=payload.is_active,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


# ---------------------------------------------------------------------------
# Allocations
# ---------------------------------------------------------------------------


@router.post(
    "/allocate",
    response_model=StockAllocationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_ALLOCATION_CREATE],
)
def post_allocate_stock(
    payload: StockAllocateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockAllocationRead:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=payload.warehouse_id, action="allocation.create",
    )
    try:
        result = allocate_stock(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            quantity=payload.quantity,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            allocation_group_id=payload.allocation_group_id,
            expires_at=payload.expires_at.isoformat() if payload.expires_at else None,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post(
    "/allocate/{allocation_id}/release",
    response_model=StockAllocationRead,
    dependencies=[REQUIRE_ALLOCATION_RELEASE],
)
def post_release_allocation(
    allocation_id: str,
    payload: StockAllocationReleaseRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockAllocationRead:
    try:
        result = release_allocation(
            db,
            allocation_id=allocation_id,
            reason=payload.reason,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post(
    "/allocate/group/{group_id}/release",
    response_model=list[StockAllocationRead],
    dependencies=[REQUIRE_ALLOCATION_RELEASE],
)
def post_release_allocation_group(
    group_id: str,
    payload: StockAllocationReleaseRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[StockAllocationRead]:
    try:
        result = release_allocation_group(
            db,
            group_id=group_id,
            reason=payload.reason,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.get(
    "/allocations",
    response_model=list[StockAllocationRead],
    dependencies=[REQUIRE_ALLOCATION_READ],
)
def get_allocations(
    status_filter: str | None = Query(None, alias="status"),
    reference_type: str | None = Query(default=None),
    allocation_group_id: str | None = Query(default=None),
    product_id: str | None = Query(default=None),
    warehouse_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[StockAllocationRead]:
    return list_allocations(
        db,
        tenant_id=tenant_context.current_tenant_id,
        status=status_filter,
        reference_type=reference_type,
        allocation_group_id=allocation_group_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/allocations/{allocation_id}",
    response_model=StockAllocationRead,
    dependencies=[REQUIRE_ALLOCATION_READ],
)
def get_allocation_detail(
    allocation_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockAllocationRead:
    try:
        return get_allocation(
            db, tenant_id=tenant_context.current_tenant_id,
            allocation_id=allocation_id,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.get(
    "/allocations/group/{group_id}",
    response_model=list[StockAllocationRead],
    dependencies=[REQUIRE_ALLOCATION_READ],
)
def get_allocations_by_group(
    group_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[StockAllocationRead]:
    return list_allocations_by_group(
        db, tenant_id=tenant_context.current_tenant_id, group_id=group_id,
    )


# ---------------------------------------------------------------------------
# Movements
# ---------------------------------------------------------------------------


@router.post(
    "/sale-out",
    response_model=StockMovementResultRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_MOVEMENT_SALE_OUT],
)
def post_sale_out(
    payload: StockSaleOutRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockMovementResultRead:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=payload.warehouse_id, action="movement.sale_out",
    )
    try:
        result = sale_out_stock(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            quantity=payload.quantity,
            source=payload.source,
            allocation_id=payload.allocation_id,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            idempotency_key=payload.idempotency_key,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post(
    "/purchase-in",
    response_model=StockMovementResultRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_MOVEMENT_PURCHASE_IN],
)
def post_purchase_in(
    payload: StockPurchaseInRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockMovementResultRead:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=payload.warehouse_id, action="movement.purchase_in",
    )
    try:
        result = purchase_in_stock(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            quantity=payload.quantity,
            unit_cost=payload.unit_cost,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            idempotency_key=payload.idempotency_key,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post(
    "/return-in",
    response_model=StockMovementResultRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_MOVEMENT_RETURN_IN],
)
def post_return_in(
    payload: StockReturnInRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockMovementResultRead:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=payload.warehouse_id, action="movement.return_in",
    )
    try:
        result = return_in_stock(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            quantity=payload.quantity,
            original_sale_ledger_id=payload.original_sale_ledger_id,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            idempotency_key=payload.idempotency_key,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post(
    "/damage-out",
    response_model=StockMovementResultRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_MOVEMENT_DAMAGE_OUT],
)
def post_damage_out(
    payload: StockDamageOutRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> StockMovementResultRead:
    _ensure_warehouse_access(
        db, tenant_context=tenant_context, request=request,
        warehouse_id=payload.warehouse_id, action="movement.damage_out",
    )
    try:
        result = damage_out_stock(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=payload.product_id,
            warehouse_id=payload.warehouse_id,
            quantity=payload.quantity,
            reason=payload.reason,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            idempotency_key=payload.idempotency_key,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
