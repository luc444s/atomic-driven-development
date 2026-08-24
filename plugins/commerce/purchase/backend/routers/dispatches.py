from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from systutor.kernel.tenants.context import TenantContext

from plugins.commerce.purchase.backend.schemas import (
    CustodyEntryRead,
    CustodySummaryRow,
    DispatchCreateRequest,
    DispatchPageRead,
    DispatchRead,
    DispatchReturnRequest,
    DispatchSessionLinkRequest,
)
from plugins.commerce.purchase.backend.routers.common import (
    DB_SESSION,
    REQUIRE_DISPATCH_MANAGE,
    REQUIRE_DISPATCH_READ,
    TENANT_CONTEXT,
)
from plugins.commerce.purchase.backend.services import dispatches

router = APIRouter()


def _serial_map(db: Session, tenant_id: str, cylinder_ids: list[str]) -> dict[str, str | None]:
    from plugins.logistics.backend.models.cylinder import LogisticsCylinder

    if not cylinder_ids:
        return {}
    rows = db.execute(
        select(LogisticsCylinder.id, LogisticsCylinder.serial).where(
            LogisticsCylinder.id.in_(cylinder_ids),
            LogisticsCylinder.tenant_id == tenant_id,
        )
    ).all()
    return {row_id: serial for row_id, serial in rows}


def _serialize_dispatch(db: Session, dispatch) -> dict:
    serials = _serial_map(db, dispatch.tenant_id, [c.cylinder_id for c in dispatch.cylinders])  # type: ignore[attr-defined]
    supplier_name = None
    from plugins.commerce.purchase.backend.models import ComSupplier

    supplier = db.scalar(
        select(ComSupplier.name).where(ComSupplier.id == dispatch.supplier_id)
    )
    if supplier is not None:
        supplier_name = supplier
    return {
        "id": dispatch.id,
        "supplier_id": dispatch.supplier_id,
        "supplier_name": supplier_name,
        "order_id": dispatch.order_id,
        "warehouse_id": dispatch.warehouse_id,
        "dispatch_date": dispatch.dispatch_date,
        "carrier": dispatch.carrier,
        "vehicle_plate": dispatch.vehicle_plate,
        "driver_name": dispatch.driver_name,
        "status": dispatch.status,
        "notes": dispatch.notes,
        "created_by": dispatch.created_by,
        "created_at": dispatch.created_at,
        "cylinders": [
            {
                "id": c.id,
                "cylinder_id": c.cylinder_id,
                "serial": serials.get(c.cylinder_id),
                "product_id": c.product_id,
                "service_type": c.service_type,
                "status": c.status,
                "returned_at": c.returned_at,
                "notes": c.notes,
            }
            for c in dispatch.cylinders  # type: ignore[attr-defined]
        ],
    }


@router.post(
    "",
    response_model=DispatchRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_DISPATCH_MANAGE],
)
def create_dispatch(
    payload: DispatchCreateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> DispatchRead:
    try:
        item = dispatches.create_dispatch(
            db,
            tenant_id=tenant_context.current_tenant_id,
            supplier_id=payload.supplier_id,
            order_id=payload.order_id,
            warehouse_id=payload.warehouse_id,
            dispatch_date=payload.dispatch_date,
            carrier=payload.carrier,
            vehicle_plate=payload.vehicle_plate,
            driver_name=payload.driver_name,
            notes=payload.notes,
            cylinders_payload=[c.model_dump() for c in payload.cylinders],
            created_by=tenant_context.current_user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return DispatchRead.model_validate(_serialize_dispatch(db, item))


@router.get("", response_model=DispatchPageRead, dependencies=[REQUIRE_DISPATCH_READ])
def list_dispatches_endpoint(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    supplier_id: str | None = None,
    status_filter: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    items, total = dispatches.list_dispatches(
        db,
        tenant_id=tenant_context.current_tenant_id,
        supplier_id=supplier_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_serialize_dispatch(db, d) for d in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/custody/summary", response_model=list[CustodySummaryRow], dependencies=[REQUIRE_DISPATCH_READ])
def custody_summary(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> list[dict]:
    return dispatches.custody_summary(db, tenant_id=tenant_context.current_tenant_id)


@router.get(
    "/suppliers/{supplier_id}/custody",
    response_model=list[CustodyEntryRead],
    dependencies=[REQUIRE_DISPATCH_READ],
)
def supplier_custody(
    supplier_id: str,
    days_gt: int | None = None,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> list[dict]:
    return dispatches.custody_entries(
        db,
        tenant_id=tenant_context.current_tenant_id,
        supplier_id=supplier_id,
        days_gt=days_gt,
    )


@router.get("/{dispatch_id}", response_model=DispatchRead, dependencies=[REQUIRE_DISPATCH_READ])
def get_dispatch(
    dispatch_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> DispatchRead:
    item = dispatches.get_dispatch(db, tenant_id=tenant_context.current_tenant_id, dispatch_id=dispatch_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Despacho no encontrado")
    return DispatchRead.model_validate(_serialize_dispatch(db, item))


@router.post(
    "/{dispatch_id}/confirm",
    response_model=DispatchRead,
    dependencies=[REQUIRE_DISPATCH_MANAGE],
)
def confirm_dispatch(    dispatch_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> DispatchRead:
    item = dispatches.get_dispatch(db, tenant_id=tenant_context.current_tenant_id, dispatch_id=dispatch_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Despacho no encontrado")
    try:
        item = dispatches.transition(db, dispatch=item, target="DESPACHADO")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return DispatchRead.model_validate(_serialize_dispatch(db, item))


@router.post(
    "/{dispatch_id}/cancel",
    response_model=DispatchRead,
    dependencies=[REQUIRE_DISPATCH_MANAGE],
)
def cancel_dispatch(
    dispatch_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> DispatchRead:
    item = dispatches.get_dispatch(db, tenant_id=tenant_context.current_tenant_id, dispatch_id=dispatch_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Despacho no encontrado")
    try:
        item = dispatches.transition(db, dispatch=item, target="CANCELADO")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return DispatchRead.model_validate(_serialize_dispatch(db, item))


@router.post(
    "/{dispatch_id}/return",
    response_model=DispatchRead,
    dependencies=[REQUIRE_DISPATCH_MANAGE],
)
def register_return(
    dispatch_id: str,
    payload: DispatchReturnRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> DispatchRead:
    item = dispatches.get_dispatch(db, tenant_id=tenant_context.current_tenant_id, dispatch_id=dispatch_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Despacho no encontrado")
    try:
        item = dispatches.register_return(
            db,
            tenant_id=tenant_context.current_tenant_id,
            dispatch=item,
            cylinder_ids=[c.cylinder_id for c in payload.cylinders],
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return DispatchRead.model_validate(_serialize_dispatch(db, item))


@router.patch(
    "/{dispatch_id}/session-link",
    response_model=DispatchRead,
    dependencies=[REQUIRE_DISPATCH_MANAGE],
)
def set_session_link(
    dispatch_id: str,
    payload: DispatchSessionLinkRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> DispatchRead:
    item = dispatches.get_dispatch(db, tenant_id=tenant_context.current_tenant_id, dispatch_id=dispatch_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Despacho no encontrado")
    try:
        item = dispatches.set_session_link(
            db,
            tenant_id=tenant_context.current_tenant_id,
            dispatch=item,
            kind=payload.kind,
            session_id=payload.session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return DispatchRead.model_validate(_serialize_dispatch(db, item))
