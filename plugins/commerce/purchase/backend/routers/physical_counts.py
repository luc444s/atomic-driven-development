from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from systutor.kernel.tenants.context import TenantContext

from plugins.commerce.purchase.backend.routers.common import (
    DB_SESSION,
    REQUIRE_DISPATCH_MANAGE,
    REQUIRE_DISPATCH_READ,
    TENANT_CONTEXT,
)
from plugins.commerce.purchase.backend.schemas import (
    PhysicalCountCloseRequest,
    PhysicalCountCreate,
    PhysicalCountDetailRead,
    PhysicalCountEventRead,
    PhysicalCountExpectedSerialRead,
    PhysicalCountItemRead,
    PhysicalCountItemResolveRequest,
    PhysicalCountRead,
)
from plugins.commerce.purchase.backend.services import physical_counts as counts_service

# OJO: este router se registra ANTES que el router dispatches en
# routers/__init__.py para que GET /dispatches/physical-counts no sea
# capturado por GET /dispatches/{dispatch_id} (test_list_physical_counts_
# not_shadowed lo demuestra).
router = APIRouter()


def _get_count_or_404(db: Session, tenant_id: str, count_id: str):
    count = counts_service.get_count(db, tenant_id=tenant_id, count_id=count_id)
    if count is None:
        raise HTTPException(status_code=404, detail="Conteo físico no encontrado")
    return count


def _serialize_detail(db: Session, count) -> PhysicalCountDetailRead:
    base = PhysicalCountRead.model_validate(count)
    return PhysicalCountDetailRead(
        **base.model_dump(),
        expected_serials=[
            PhysicalCountExpectedSerialRead.model_validate(r)
            for r in counts_service.list_expected_serials(db, count=count)
        ],
        items=[
            PhysicalCountItemRead.model_validate(i)
            for i in counts_service.list_items(db, count=count)
        ],
        events=[
            PhysicalCountEventRead.model_validate(e)
            for e in counts_service.list_events(db, count=count)
        ],
    )


@router.post(
    "/dispatches/physical-counts",
    response_model=PhysicalCountRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_DISPATCH_MANAGE],
)
def create_physical_count(
    payload: PhysicalCountCreate,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PhysicalCountRead:
    try:
        count = counts_service.create_count(
            db,
            tenant_id=tenant_context.current_tenant_id,
            supplier_id=payload.supplier_id,
            order_id=payload.order_id,
            dispatch_id=payload.dispatch_id,
            notes=payload.notes,
            counted_by=tenant_context.current_user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return PhysicalCountRead.model_validate(count)


@router.get(
    "/dispatches/physical-counts",
    response_model=list[PhysicalCountRead],
    dependencies=[REQUIRE_DISPATCH_READ],
)
def list_physical_counts(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    supplier_id: str | None = None,
    status_filter: str | None = None,
) -> list[PhysicalCountRead]:
    items, _total = counts_service.list_counts(
        db,
        tenant_id=tenant_context.current_tenant_id,
        supplier_id=supplier_id,
        status=status_filter,
    )
    return [PhysicalCountRead.model_validate(c) for c in items]


@router.get(
    "/dispatches/physical-counts/{count_id}",
    response_model=PhysicalCountDetailRead,
    dependencies=[REQUIRE_DISPATCH_READ],
)
def get_physical_count(
    count_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PhysicalCountDetailRead:
    count = _get_count_or_404(db, tenant_context.current_tenant_id, count_id)
    return _serialize_detail(db, count)


@router.post(
    "/dispatches/physical-counts/{count_id}/close",
    response_model=PhysicalCountRead,
    dependencies=[REQUIRE_DISPATCH_MANAGE],
)
def close_physical_count(
    count_id: str,
    payload: PhysicalCountCloseRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PhysicalCountRead:
    count = _get_count_or_404(db, tenant_context.current_tenant_id, count_id)
    try:
        count = counts_service.close_count(
            db,
            count=count,
            found_payload=[f.model_dump() for f in payload.found],
            closed_by=tenant_context.current_user_id,
            notes=payload.notes,
        )
    except counts_service.PhysicalCountStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return PhysicalCountRead.model_validate(count)


@router.post(
    "/dispatches/physical-counts/{count_id}/items/{item_id}/resolve",
    response_model=PhysicalCountDetailRead,
    dependencies=[REQUIRE_DISPATCH_MANAGE],
)
def resolve_physical_count_item(
    count_id: str,
    item_id: str,
    payload: PhysicalCountItemResolveRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PhysicalCountDetailRead:
    count = _get_count_or_404(db, tenant_context.current_tenant_id, count_id)
    try:
        counts_service.resolve_item(
            db,
            count=count,
            item_id=item_id,
            resolution=payload.resolution,
            reason=payload.reason,
            resolved_by=tenant_context.current_user_id,
        )
    except counts_service.PhysicalCountStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return _serialize_detail(db, count)
