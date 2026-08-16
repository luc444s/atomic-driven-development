from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from systutor.api.deps import get_db_session
from systutor.kernel.auth.dependencies import get_current_tenant_context, require_permission
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.context import TenantContext

from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.schemas import (
    OrderCreateRequest,
    OrderItemCreateRequest,
    OrderItemRead,
    OrderItemUpdateRequest,
    OrderRead,
    OrderUpdateRequest,
)
from plugins.logistics.backend.services.orders import (
    create_order,
    create_order_item,
    delete_order_item,
    get_order,
    get_order_item,
    list_order_items,
    list_orders,
    update_order,
    update_order_item,
)

router = APIRouter(tags=["logistics-orders"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)

REQUIRE_ORDER_READ = Depends(require_permission("logistics.order.read"))
REQUIRE_ORDER_CREATE = Depends(require_permission("logistics.order.create"))
REQUIRE_ORDER_MANAGE = Depends(require_permission("logistics.order.manage"))


def _conflict(exc: IntegrityError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc.orig or exc))


def _not_found(entity_name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found")


@router.get("/orders", response_model=list[OrderRead])
def get_orders(
    customer: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[OrderRead]:
    return [
        OrderRead.model_validate(item)
        for item in list_orders(
            db,
            tenant_id=tenant_context.current_tenant_id,
            customer=customer,
            status=status_filter,
        )
    ]


@router.get("/orders/pending", response_model=list[OrderRead])
def get_pending_orders(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[OrderRead]:
    return [
        OrderRead.model_validate(item)
        for item in list_orders(db, tenant_id=tenant_context.current_tenant_id, status="PENDIENTE")
    ]


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order_detail(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> OrderRead:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    return OrderRead.model_validate(order)


@router.get("/orders/{order_id}/items", response_model=list[OrderItemRead])
def get_order_items(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[OrderItemRead]:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    return [OrderItemRead.model_validate(item) for item in list_order_items(db, order_id=order_id)]


@router.post("/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order_endpoint(
    payload: OrderCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_CREATE,
) -> OrderRead:
    try:
        order = create_order(
            db,
            tenant_id=tenant_context.current_tenant_id,
            created_by=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return OrderRead.model_validate(order)


@router.patch("/orders/{order_id}", response_model=OrderRead)
def update_order_endpoint(
    order_id: str,
    payload: OrderUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> OrderRead:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    order = update_order(
        db,
        order=order,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return OrderRead.model_validate(order)


@router.post(
    "/orders/{order_id}/items", response_model=OrderItemRead, status_code=status.HTTP_201_CREATED
)
def create_order_item_endpoint(
    order_id: str,
    payload: OrderItemCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> OrderItemRead:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    item = create_order_item(
        db,
        order=order,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return OrderItemRead.model_validate(item)


@router.patch("/orders/{order_id}/items/{item_id}", response_model=OrderItemRead)
def update_order_item_endpoint(
    order_id: str,
    item_id: str,
    payload: OrderItemUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> OrderItemRead:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    item = get_order_item(db, order_id=order_id, item_id=item_id)
    if item is None:
        raise _not_found("Order item")
    item = update_order_item(
        db,
        item=item,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return OrderItemRead.model_validate(item)


@router.delete("/orders/{order_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_item_endpoint(
    order_id: str,
    item_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> None:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    item = get_order_item(db, order_id=order_id, item_id=item_id)
    if item is None:
        raise _not_found("Order item")
    delete_order_item(db, item=item, action_context=build_action_context(request, tenant_context))
    db.commit()
