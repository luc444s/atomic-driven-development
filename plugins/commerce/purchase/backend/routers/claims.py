from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
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
    ClaimAnnulRequest,
    ClaimDerivationResult,
    ClaimResolveRequest,
    SupplierClaimCreate,
    SupplierClaimDetailRead,
    SupplierClaimEventRead,
    SupplierClaimRead,
)
from plugins.commerce.purchase.backend.services import claims as claims_service
from plugins.commerce.purchase.backend.services import orders as orders_service

router = APIRouter()


def _get_order(db: Session, tenant_id: str, order_id: str) -> ComPurchaseOrder:
    order = orders_service.get_order(db, tenant_id=tenant_id, order_id=order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return order


def _get_claim(db: Session, tenant_id: str, order_id: str, claim_id: str):
    claim = claims_service.get_claim(
        db, tenant_id=tenant_id, order_id=order_id, claim_id=claim_id
    )
    if claim is None:
        raise HTTPException(status_code=404, detail="Reclamación no encontrada")
    return claim


def _transition_response(db: Session, claim) -> SupplierClaimRead:
    db.commit()
    return SupplierClaimRead.model_validate(claim)


@router.post(
    "/orders/{order_id}/claims",
    response_model=SupplierClaimRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def create_claim(
    order_id: str,
    payload: SupplierClaimCreate,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierClaimRead:
    order = _get_order(db, tenant_context.current_tenant_id, order_id)
    try:
        claim = claims_service.create_claim(
            db,
            order=order,
            reason=payload.reason,
            description=payload.description,
            opened_by=tenant_context.current_user_id,
            receipt_id=payload.receipt_id,
            invoice_id=payload.invoice_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return SupplierClaimRead.model_validate(claim)


@router.get(
    "/orders/{order_id}/claims",
    response_model=list[SupplierClaimRead],
    dependencies=[REQUIRE_ORDER_READ],
)
def list_claims(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> list[SupplierClaimRead]:
    order = _get_order(db, tenant_context.current_tenant_id, order_id)
    rows = claims_service.list_claims(db, order=order)
    return [SupplierClaimRead.model_validate(r) for r in rows]


@router.get(
    "/orders/{order_id}/claims/{claim_id}",
    response_model=SupplierClaimDetailRead,
    dependencies=[REQUIRE_ORDER_READ],
)
def get_claim(
    order_id: str,
    claim_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierClaimDetailRead:
    _get_order(db, tenant_context.current_tenant_id, order_id)
    claim = _get_claim(db, tenant_context.current_tenant_id, order_id, claim_id)
    base = SupplierClaimRead.model_validate(claim)
    events = [
        SupplierClaimEventRead.model_validate(e)
        for e in claims_service.list_events(db, claim=claim)
    ]
    return SupplierClaimDetailRead(**base.model_dump(), events=events)


@router.post(
    "/orders/{order_id}/claims/{claim_id}/start",
    response_model=SupplierClaimRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def start_claim(
    order_id: str,
    claim_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierClaimRead:
    _get_order(db, tenant_context.current_tenant_id, order_id)
    claim = _get_claim(db, tenant_context.current_tenant_id, order_id, claim_id)
    try:
        claim = claims_service.start_claim(db, claim=claim, user_id=tenant_context.current_user_id)
    except claims_service.ClaimTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _transition_response(db, claim)


@router.post(
    "/orders/{order_id}/claims/{claim_id}/resolve",
    response_model=SupplierClaimRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def resolve_claim(
    order_id: str,
    claim_id: str,
    payload: ClaimResolveRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierClaimRead:
    _get_order(db, tenant_context.current_tenant_id, order_id)
    claim = _get_claim(db, tenant_context.current_tenant_id, order_id, claim_id)
    try:
        claim = claims_service.resolve_claim(
            db,
            claim=claim,
            resolution_notes=payload.resolution_notes,
            user_id=tenant_context.current_user_id,
        )
    except claims_service.ClaimTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _transition_response(db, claim)


@router.post(
    "/orders/{order_id}/claims/{claim_id}/annul",
    response_model=SupplierClaimRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def annul_claim(
    order_id: str,
    claim_id: str,
    payload: ClaimAnnulRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierClaimRead:
    _get_order(db, tenant_context.current_tenant_id, order_id)
    claim = _get_claim(db, tenant_context.current_tenant_id, order_id, claim_id)
    try:
        claim = claims_service.annul_claim(
            db, claim=claim, reason=payload.reason, user_id=tenant_context.current_user_id
        )
    except claims_service.ClaimTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return _transition_response(db, claim)


@router.post(
    "/orders/{order_id}/claims/derive",
    response_model=ClaimDerivationResult,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def derive_claims(
    order_id: str,
    response: Response,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> ClaimDerivationResult:
    order = _get_order(db, tenant_context.current_tenant_id, order_id)
    created, skipped = claims_service.derive_claims_from_reconciliation(
        db, order=order, opened_by=tenant_context.current_user_id
    )
    db.commit()
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return ClaimDerivationResult(
        created=[SupplierClaimRead.model_validate(c) for c in created],
        skipped=skipped,
    )
