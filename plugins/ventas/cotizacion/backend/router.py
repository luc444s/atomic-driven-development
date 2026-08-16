# ═══════════════════════════════════════════════════════════════════
# MODULO DESHABILITADO — Ver plugin.py para contexto completo.
# ═══════════════════════════════════════════════════════════════════
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from systutor.api.deps import get_db_session
from systutor.kernel.auth.dependencies import get_current_tenant_context, require_permission
from systutor.kernel.tenants.context import TenantContext

from plugins.ventas.cotizacion.backend.models import QuoteDraft
from plugins.ventas.cotizacion.backend.schemas import (
    ExecuteCommandRequest,
    PatchQuoteStatusRequest,
    QuoteDraftListItem,
    QuoteDraftResponse,
)
from plugins.ventas.cotizacion.backend.services.cotizacion import handle_cotizar

router = APIRouter(tags=["ventas"])


def _resolve_warehouse_for_quote(
    db: Session, draft: QuoteDraft, tenant_context: TenantContext
) -> str:
    from plugins.logistics.backend.models import LogisticsVehicle, LogisticsWarehouse

    if draft.vehicle_id:
        vehicle = db.scalar(
            select(LogisticsVehicle).where(
                LogisticsVehicle.id == draft.vehicle_id,
                LogisticsVehicle.tenant_id == tenant_context.current_tenant_id,
            )
        )
        if vehicle and vehicle.warehouse_id:
            return vehicle.warehouse_id

    warehouse = db.scalar(
        select(LogisticsWarehouse.id).where(
            LogisticsWarehouse.tenant_id == tenant_context.current_tenant_id,
            LogisticsWarehouse.is_active.is_(True),
            LogisticsWarehouse.warehouse_type != "MOBILE",
        ).order_by(LogisticsWarehouse.name).limit(1)
    )
    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay almacenes disponibles para reservar stock",
        )
    return warehouse


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
    status_filter: str | None = Query(
        None, alias="status", description="Filtrar por estado (DRAFT, CONFIRMED, etc.)"
    ),
    date_from: str | None = Query(
        None, alias="date_from", description="Fecha desde (YYYY-MM-DD)"
    ),
    date_to: str | None = Query(
        None, alias="date_to", description="Fecha hasta (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db_session),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
):
    stmt = select(QuoteDraft).where(QuoteDraft.tenant_id == tenant_context.current_tenant_id)

    if status_filter:
        stmt = stmt.where(QuoteDraft.status == status_filter.upper())

    if date_from:
        stmt = stmt.where(QuoteDraft.delivery_date >= date.fromisoformat(date_from[:10]))

    if date_to:
        stmt = stmt.where(QuoteDraft.delivery_date <= date.fromisoformat(date_to[:10]))

    stmt = stmt.order_by(QuoteDraft.delivery_date.asc()).limit(100)

    drafts = db.execute(stmt).scalars().all()
    return [QuoteDraftListItem.model_validate(d) for d in drafts]


@router.patch(
    "/cotizaciones/{quote_id}/status",
    response_model=QuoteDraftResponse,
    dependencies=[Depends(require_permission("ventas.cotizacion.confirm"))],
)
def patch_cotizacion_status(
    quote_id: str,
    body: PatchQuoteStatusRequest,
    db: Session = Depends(get_db_session),
    tenant_context: TenantContext = Depends(get_current_tenant_context),
):
    from plugins.ventas.cotizacion.backend.models import QuoteItem
    from plugins.ventas.cotizacion.backend.schemas import (
        CustomerSummary,
        QuoteItemResponse,
        VehicleSummary,
    )

    draft = db.execute(
        select(QuoteDraft).where(
            QuoteDraft.id == quote_id,
            QuoteDraft.tenant_id == tenant_context.current_tenant_id,
        )
    ).scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada",
        )

    if body.status == "CONFIRMED" and draft.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo cotizaciones en estado DRAFT pueden confirmarse",
        )

    if body.status == "CONVERTED" and draft.status != "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo cotizaciones en estado CONFIRMED pueden convertirse",
        )

    draft.status = body.status
    db.flush()

    if body.status == "CONFIRMED":
        from plugins.stock.backend.common import StockActionContext
        from plugins.stock.backend.services.allocation import allocate_stock

        items = db.execute(
            select(QuoteItem).where(QuoteItem.quote_draft_id == draft.id)
        ).scalars().all()

        warehouse_id = _resolve_warehouse_for_quote(db, draft, tenant_context)

        ctx = StockActionContext(
            tenant_id=tenant_context.current_tenant_id,
            branch_id=tenant_context.current_branch_id,
            actor_user_id=tenant_context.current_user_id,
            correlation_id=None,
            request_id=None,
        )

        for item in items:
            try:
                allocate_stock(
                    db,
                    tenant_id=tenant_context.current_tenant_id,
                    product_id=item.product_id,
                    warehouse_id=warehouse_id,
                    quantity=float(item.quantity),
                    reference_type="quote",
                    reference_id=draft.id,
                    allocation_group_id=draft.id,
                    expires_at=None,
                    action_context=ctx,
                )
            except ValueError as exc:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Stock insuficiente para {item.product_name}: {exc}",
                ) from exc

    items = db.execute(
        select(QuoteItem).where(QuoteItem.quote_draft_id == draft.id)
    ).scalars().all()
    db.commit()
    db.refresh(draft)

    vehicle = (
        VehicleSummary(id=draft.vehicle_id, plate=draft.vehicle_plate)
        if draft.vehicle_id
        else None
    )
    return QuoteDraftResponse(
        id=draft.id,
        status=draft.status,
        customer=CustomerSummary(
            id=draft.customer_id, name=draft.customer_name or "Desconocido"
        ),
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
        vehicle=vehicle,
        conditions=draft.conditions,
        created_at=draft.created_at,
    )


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
        QuoteItemResponse,
        VehicleSummary,
    )

    draft = db.execute(
        select(QuoteDraft)
        .where(QuoteDraft.id == quote_id, QuoteDraft.tenant_id == tenant_context.current_tenant_id)
    ).scalar_one_or_none()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cotización no encontrada",
        )

    items = db.execute(
        select(QuoteItem).where(QuoteItem.quote_draft_id == draft.id)
    ).scalars().all()

    vehicle = (
        VehicleSummary(id=draft.vehicle_id, plate=draft.vehicle_plate)
        if draft.vehicle_id
        else None
    )
    return QuoteDraftResponse(
        id=draft.id,
        status=draft.status,
        customer=CustomerSummary(
            id=draft.customer_id, name=draft.customer_name or "Desconocido"
        ),
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
        vehicle=vehicle,
        conditions=draft.conditions,
        created_at=draft.created_at,
    )
