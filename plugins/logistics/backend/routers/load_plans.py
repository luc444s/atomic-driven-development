from __future__ import annotations

from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.dto.load_plans import (
    ConfirmLoadRequest,
    LoadPlanItemRead,
    LoadPlanRead,
    LoadPlanUpsertRequest,
    ReturnRemainingRequest,
)
from plugins.logistics.backend.dto.sessions import VehicleSessionDetailRead
from plugins.logistics.backend.services.load_plans import (
    confirm_load_plan,
    get_load_plan,
    list_load_plan_items,
    return_remaining_stock,
    upsert_load_plan,
)
from plugins.logistics.backend.services.sessions import get_vehicle_session, mark_session_ready
from plugins.logistics.backend.services.snapshots import build_session_snapshot

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-load-plans"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))
REQUIRE_SESSION_MANAGE = Depends(require_permission("logistics.session.manage"))


def _get_session_or_404(db: Session, *, tenant_id: str, session_id: str):
    session = get_vehicle_session(db, tenant_id=tenant_id, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jornada no encontrada")
    return session


def _to_read(load_plan, items) -> LoadPlanRead:
    return LoadPlanRead(
        id=load_plan.id if load_plan is not None else None,
        session_id=load_plan.session_id if load_plan is not None else "",
        status=load_plan.status if load_plan is not None else "DRAFT",
        notes=load_plan.notes if load_plan is not None else None,
        planned_weight_kg=sum(float(item.planned_weight_kg or 0) for item in items),
        items=[
            LoadPlanItemRead(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                planned_quantity=float(item.planned_quantity),
                planned_weight_kg=(
                    float(item.planned_weight_kg) if item.planned_weight_kg is not None else None
                ),
                source_warehouse_id=item.source_warehouse_id,
                notes=item.notes,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


def _raise_service_error(exc: Exception) -> NoReturn:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise exc


@router.get("/{session_id}/load-plan", response_model=LoadPlanRead)
def get_session_load_plan(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> LoadPlanRead:
    _get_session_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    load_plan = get_load_plan(db, session_id=session_id)
    if load_plan is None:
        return LoadPlanRead(session_id=session_id, status="DRAFT")
    items = list_load_plan_items(db, load_plan_id=load_plan.id)
    return _to_read(load_plan, items)


@router.put("/{session_id}/load-plan", response_model=LoadPlanRead)
def put_session_load_plan(
    session_id: str,
    payload: LoadPlanUpsertRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> LoadPlanRead:
    session = _get_session_or_404(
        db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
    )
    try:
        load_plan = upsert_load_plan(
            db,
            session=session,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        items = list_load_plan_items(db, load_plan_id=load_plan.id)
        return _to_read(load_plan, items)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/{session_id}/confirm-load", response_model=dict)
def post_confirm_load(
    session_id: str,
    payload: ConfirmLoadRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> dict:
    session = _get_session_or_404(
        db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
    )
    try:
        session = confirm_load_plan(
            db,
            session=session,
            notes=payload.notes,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return {"session_id": session.id, "loaded_weight_kg": float(session.loaded_weight_kg or 0)}
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/{session_id}/confirm-and-ready", response_model=VehicleSessionDetailRead)
def post_confirm_and_ready(
    session_id: str,
    payload: ConfirmLoadRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    session = _get_session_or_404(
        db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
    )
    try:
        action_context = build_action_context(request, tenant_context)
        session = confirm_load_plan(
            db,
            session=session,
            notes=payload.notes,
            action_context=action_context,
        )
        session = mark_session_ready(
            db,
            session=session,
            action_context=action_context,
        )
        db.commit()
        return build_session_snapshot(db, session=session)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/{session_id}/return-remaining", response_model=dict)
def post_return_remaining(
    session_id: str,
    payload: ReturnRemainingRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> dict:
    session = _get_session_or_404(
        db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
    )
    try:
        session = return_remaining_stock(
            db,
            session=session,
            destination_warehouse_id=payload.destination_warehouse_id,
            notes=payload.notes,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return {"session_id": session.id, "status": session.status}
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
