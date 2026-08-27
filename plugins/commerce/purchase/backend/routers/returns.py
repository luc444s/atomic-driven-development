from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from systutor.kernel.tenants.context import TenantContext

from plugins.commerce.purchase.backend.models import ComPurchaseOrder
from plugins.commerce.purchase.backend.routers.common import (
    DB_SESSION,
    REQUIRE_ORDER_MANAGE,
    REQUIRE_ORDER_READ,
    TENANT_CONTEXT,
)
from plugins.commerce.purchase.backend.schemas import (
    MerchandiseReturnAnnulRequest,
    MerchandiseReturnCompleteRequest,
    MerchandiseReturnCreate,
    MerchandiseReturnDetailRead,
    MerchandiseReturnEventRead,
    MerchandiseReturnLineRead,
    MerchandiseReturnRead,
)
from plugins.commerce.purchase.backend.services import orders as orders_service
from plugins.commerce.purchase.backend.services import returns as returns_service

router = APIRouter()


def _get_order(db: Session, tenant_id: str, order_id: str) -> ComPurchaseOrder:
    order = orders_service.get_order(db, tenant_id=tenant_id, order_id=order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order


def _get_return(db: Session, tenant_id: str, order_id: str, return_id: str):
    return_record = returns_service.get_return(
        db,
        tenant_id=tenant_id,
        order_id=order_id,
        return_id=return_id,
    )
    if return_record is None:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")
    return return_record


def _serialize_detail(db: Session, return_record) -> MerchandiseReturnDetailRead:
    base = MerchandiseReturnRead.model_validate(return_record)
    return MerchandiseReturnDetailRead(
        **base.model_dump(),
        lines=[
            MerchandiseReturnLineRead.model_validate(line)
            for line in returns_service.list_return_lines(db, return_record=return_record)
        ],
        events=[
            MerchandiseReturnEventRead.model_validate(event)
            for event in returns_service.list_events(db, return_record=return_record)
        ],
    )


@router.post(
    "/orders/{order_id}/returns",
    response_model=MerchandiseReturnRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def create_return(
    order_id: str,
    payload: MerchandiseReturnCreate,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> MerchandiseReturnRead:
    order = _get_order(db, tenant_context.current_tenant_id, order_id)
    try:
        return_record = returns_service.create_return(
            db,
            order=order,
            receipt_id=payload.receipt_id,
            claim_id=payload.claim_id,
            return_date=payload.return_date,
            notes=payload.notes,
            lines_payload=[line.model_dump() for line in payload.lines],
            created_by=tenant_context.current_user_id,
        )
    except returns_service.MerchandiseReturnReferenceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return MerchandiseReturnRead.model_validate(return_record)


@router.get(
    "/orders/{order_id}/returns",
    response_model=list[MerchandiseReturnRead],
    dependencies=[REQUIRE_ORDER_READ],
)
def list_returns(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> list[MerchandiseReturnRead]:
    order = _get_order(db, tenant_context.current_tenant_id, order_id)
    rows = returns_service.list_returns(db, order=order)
    return [MerchandiseReturnRead.model_validate(row) for row in rows]


@router.get(
    "/orders/{order_id}/returns/{return_id}",
    response_model=MerchandiseReturnDetailRead,
    dependencies=[REQUIRE_ORDER_READ],
)
def get_return(
    order_id: str,
    return_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> MerchandiseReturnDetailRead:
    _get_order(db, tenant_context.current_tenant_id, order_id)
    return_record = _get_return(db, tenant_context.current_tenant_id, order_id, return_id)
    return _serialize_detail(db, return_record)


@router.post(
    "/orders/{order_id}/returns/{return_id}/complete",
    response_model=MerchandiseReturnRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def complete_return(
    order_id: str,
    return_id: str,
    payload: MerchandiseReturnCompleteRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> MerchandiseReturnRead:
    _get_order(db, tenant_context.current_tenant_id, order_id)
    return_record = _get_return(db, tenant_context.current_tenant_id, order_id, return_id)
    try:
        return_record = returns_service.complete_return(
            db,
            return_record=return_record,
            resolution_notes=payload.resolution_notes,
            user_id=tenant_context.current_user_id,
        )
    except returns_service.MerchandiseReturnTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return MerchandiseReturnRead.model_validate(return_record)


@router.post(
    "/orders/{order_id}/returns/{return_id}/annul",
    response_model=MerchandiseReturnRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def annul_return(
    order_id: str,
    return_id: str,
    payload: MerchandiseReturnAnnulRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> MerchandiseReturnRead:
    _get_order(db, tenant_context.current_tenant_id, order_id)
    return_record = _get_return(db, tenant_context.current_tenant_id, order_id, return_id)
    try:
        return_record = returns_service.annul_return(
            db,
            return_record=return_record,
            reason=payload.reason,
            user_id=tenant_context.current_user_id,
        )
    except returns_service.MerchandiseReturnTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return MerchandiseReturnRead.model_validate(return_record)
