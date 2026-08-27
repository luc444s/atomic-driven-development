from __future__ import annotations

import httpx  # noqa: F401 - parity con router previo
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from systutor.kernel.auth.dependencies import require_permission
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.context import TenantContext

from plugins.commerce.purchase.backend.models import ComPurchaseOrder
from plugins.commerce.purchase.backend.routers.common import (
    DB_SESSION,
    REQUIRE_ORDER_CREATE,
    REQUIRE_ORDER_MANAGE,
    REQUIRE_ORDER_READ,
    TENANT_CONTEXT,
)
from plugins.commerce.purchase.backend.schemas import (
    CancelOrderRequest,
    CloseOrderRequest,
    PurchaseOrderCreateRequest,
    PurchaseOrderDetailRead,
    PurchaseOrderPageRead,
    PurchaseOrderRead,
    PurchaseOrderUpdateRequest,
)
from plugins.commerce.purchase.backend.services import orders, receipts

router = APIRouter()


def _serialize_order(order: ComPurchaseOrder) -> dict:
    return {
        "id": order.id,
        "supplier": None,
        "status": order.status,
        "order_date": order.order_date,
        "expected_date": order.expected_date,
        "notes": order.notes,
        "created_by": order.created_by,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


def _serialize_order_detail(db: Session, order: ComPurchaseOrder) -> dict:
    result: dict = _serialize_order(order)  # type: ignore[assignment]
    result["items"] = [
        {
            "id": i.id,
            "product_id": i.product_id,
            "quantity": float(i.quantity),
            "unit_cost": float(i.unit_cost),
            "received_qty": float(i.received_qty),
        }
        for i in order.items  # type: ignore[attr-defined]
    ]
    result["receipts"] = []
    for r in order.receipts:  # type: ignore[attr-defined]
        cost = receipts.recompute_receipt_real_cost(r)
        result["receipts"].append(
            {
                "id": r.id,
                "warehouse_id": r.warehouse_id,
                "receipt_date": r.receipt_date,
                "dispatch_id": r.dispatch_id,
                "notes": r.notes,
                "created_at": r.created_at,
                "qty_accepted": r.qty_accepted,
                "qty_rejected": r.qty_rejected,
                "difference_type": r.difference_type,
                "incidence_notes": r.incidence_notes,
                "commercial_closed_at": r.commercial_closed_at,
                "commercial_closed_by": r.commercial_closed_by,
                "extra_total": cost["extra_total"],
                "real_total": cost["real_total"],
                "unit_cost_real": cost["unit_cost_real"],
                "cost_lines": [
                    {
                        "id": c.id,
                        "cost_type": c.cost_type,
                        "amount": float(c.amount),
                        "currency": c.currency,
                        "notes": c.notes,
                    }
                    for c in r.cost_lines
                ],
            }
        )
    result["events"] = [
        {
            "id": e.id,
            "from_status": e.from_status,
            "to_status": e.to_status,
            "reason": e.reason,
            "user_id": e.user_id,
            "created_at": e.created_at,
        }
        for e in sorted(
            order.events,  # type: ignore[attr-defined]
            key=lambda ev: ev.created_at,
        )
    ]
    return result


@router.get("", response_model=PurchaseOrderPageRead, dependencies=[REQUIRE_ORDER_READ])
def list_orders_endpoint(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    status: str | None = None,
    supplier_id: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    items, total = orders.list_orders(
        db,
        tenant_id=tenant_context.current_tenant_id,
        status=status,
        supplier_id=supplier_id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_serialize_order(o) for o in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "",
    response_model=PurchaseOrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_ORDER_CREATE],
)
def create_order_endpoint(
    payload: PurchaseOrderCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _user: User = Depends(require_permission("compras.order.create")),
) -> PurchaseOrderRead:
    item = orders.create_order(
        db,
        tenant_id=tenant_context.current_tenant_id,
        branch_id=tenant_context.current_branch_id,
        supplier_id=payload.supplier_id,
        items_payload=[i.model_dump() for i in payload.items],
        expected_date=payload.expected_date,
        notes=payload.notes,
        created_by=tenant_context.current_user_id,
    )
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))


@router.get("/{order_id}", response_model=PurchaseOrderDetailRead, dependencies=[REQUIRE_ORDER_READ])
def get_order(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderDetailRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return PurchaseOrderDetailRead.model_validate(_serialize_order_detail(db, item))


@router.patch(
    "/{order_id}",
    response_model=PurchaseOrderRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def update_order(
    order_id: str,
    payload: PurchaseOrderUpdateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    try:
        item = orders.update_order(
            db,
            order=item,
            payload=payload.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))


@router.post(
    "/{order_id}/confirm",
    response_model=PurchaseOrderRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def confirm_order(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    try:
        item = orders.confirm_order(db, order=item, user_id=tenant_context.current_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))


@router.post(
    "/{order_id}/cancel",
    response_model=PurchaseOrderRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def cancel_order(
    order_id: str,
    payload: CancelOrderRequest | None = None,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    try:
        item = orders.cancel_order(
            db,
            order=item,
            user_id=tenant_context.current_user_id,
            reason=payload.reason if payload else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))


@router.post(
    "/{order_id}/close",
    response_model=PurchaseOrderRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def close_order(
    order_id: str,
    payload: CloseOrderRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    try:
        item = orders.close_order(
            db,
            order=item,
            user_id=tenant_context.current_user_id,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))
