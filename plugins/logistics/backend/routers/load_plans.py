from __future__ import annotations

from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from systutor.api.deps import get_db_session
from systutor.kernel.auth.dependencies import get_current_tenant_context, require_permission
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.context import TenantContext

from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.dto.load_plans import (
    ConfirmLoadRequest,
    LoadPlanRead,
    LoadPlanUpsertRequest,
    ReturnRemainingRequest,
)
from plugins.logistics.backend.dto.sessions import VehicleSessionDetailRead
from plugins.logistics.backend.services.load_plans import (
    build_load_plan_read,
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
REQUIRE_SESSION_ROUTE_EXECUTE = Depends(require_permission("logistics.session.route_execute"))


def _get_session_or_404(db: Session, *, tenant_id: str, session_id: str):
    session = get_vehicle_session(db, tenant_id=tenant_id, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jornada no encontrada")
    return session


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
    session = _get_session_or_404(
        db,
        tenant_id=tenant_context.current_tenant_id,
        session_id=session_id,
    )
    load_plan = get_load_plan(db, session_id=session_id)
    if load_plan is None:
        return LoadPlanRead(session_id=session_id, status="DRAFT")
    items = list_load_plan_items(db, load_plan_id=load_plan.id)
    return build_load_plan_read(db, session=session, load_plan=load_plan, items=items)


@router.put("/{session_id}/load-plan", response_model=LoadPlanRead)
def put_session_load_plan(
    session_id: str,
    payload: LoadPlanUpsertRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_ROUTE_EXECUTE,
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
        return build_load_plan_read(db, session=session, load_plan=load_plan, items=items)
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
    _: User = REQUIRE_SESSION_ROUTE_EXECUTE,
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
    _: User = REQUIRE_SESSION_ROUTE_EXECUTE,
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
    _: User = REQUIRE_SESSION_ROUTE_EXECUTE,
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
