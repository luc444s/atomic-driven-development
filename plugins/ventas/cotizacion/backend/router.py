from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.ventas.cotizacion.backend.models import QuoteDraft
from plugins.ventas.cotizacion.backend.schemas import (
    ExecuteCommandRequest,
    QuoteDraftListItem,
    QuoteDraftResponse,
)
from plugins.ventas.cotizacion.backend.services.cotizacion import handle_cotizar

router = APIRouter(tags=["ventas"])


@router.post(
    "/cotizaciones",
    response_model=QuoteDraftResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("ventas.cotizacion.create"))],
)
def create_cotizacion(
    body: ExecuteCommandRequest,
    request: Request,
    db: Session = Depends(get_db_session),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
):
    result = handle_cotizar(
        db=db,
        command=body.command,
        tenant_id=tenant_context.current_tenant_id,
        user_id=tenant_context.current_user_id,
    )

    if hasattr(result, "error"):
        if result.error == "validation_error":
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result.model_dump())
        if result.error == "ambiguity_error":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result.model_dump())

    return result


@router.get(
    "/cotizaciones",
    response_model=list[QuoteDraftListItem],
    dependencies=[Depends(require_permission("ventas.cotizacion.read"))],
)
def list_cotizaciones(
    db: Session = Depends(get_db_session),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
):
    drafts = db.execute(
        select(QuoteDraft)
        .where(QuoteDraft.tenant_id == tenant_context.current_tenant_id)
        .order_by(QuoteDraft.created_at.desc())
        .limit(50)
    ).scalars().all()
    return [QuoteDraftListItem.model_validate(d) for d in drafts]


@router.get(
    "/cotizaciones/{quote_id}",
    response_model=QuoteDraftResponse,
    dependencies=[Depends(require_permission("ventas.cotizacion.read"))],
)
def get_cotizacion(
    quote_id: str,
    db: Session = Depends(get_db_session),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
):
    from plugins.ventas.cotizacion.backend.models import QuoteItem
    from plugins.ventas.cotizacion.backend.schemas import (
        CustomerSummary,
        ProductSummary,
        QuoteItemResponse,
        VehicleSummary,
    )

    draft = db.execute(
        select(QuoteDraft)
        .where(QuoteDraft.id == quote_id, QuoteDraft.tenant_id == tenant_context.current_tenant_id)
    ).scalar_one_or_none()

    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cotización no encontrada")

    items = db.execute(
        select(QuoteItem).where(QuoteItem.quote_draft_id == draft.id)
    ).scalars().all()

    return QuoteDraftResponse(
        id=draft.id,
        status=draft.status,
        customer=CustomerSummary(id=draft.customer_id, name=draft.customer_name or "Desconocido"),
        items=[
            QuoteItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_weight_kg=item.unit_weight_kg,
            )
            for item in items
        ],
        delivery_date=draft.delivery_date,
        delivery_time=draft.delivery_time,
        vehicle=VehicleSummary(id=draft.vehicle_id, plate=draft.vehicle_plate) if draft.vehicle_id else None,
        conditions=draft.conditions,
        created_at=draft.created_at,
    )
