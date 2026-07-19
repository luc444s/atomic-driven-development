from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.dto.route_operations import (
    CurrentCompositionRead,
    RouteOperationCreateRequest,
    RouteOperationRead,
)
from plugins.logistics.backend.services.route_operations import (
    build_current_composition,
    confirm_route_operation,
    create_route_operation,
    list_route_operations,
)
from plugins.logistics.backend.services.sessions import get_vehicle_session

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-route-operations"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))
REQUIRE_SESSION_MANAGE = Depends(require_permission("logistics.session.manage"))


def _get_or_404(db: Session, *, tenant_id: str, session_id: str):
    session = get_vehicle_session(db, tenant_id=tenant_id, session_id=session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jornada no encontrada")
    return session


def _raise_service_error(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise exc


@router.get("/{session_id}/route-operations", response_model=list[RouteOperationRead])
def get_route_operations(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[RouteOperationRead]:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    return list_route_operations(db, session_id=session.id)


@router.post("/{session_id}/route-operations", response_model=RouteOperationRead)
def post_route_operation(
    session_id: str,
    payload: RouteOperationCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> RouteOperationRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        result = create_route_operation(
            db,
            session=session,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.post(
    "/{session_id}/route-operations/{operation_id}/confirm",
    response_model=RouteOperationRead,
)
def post_confirm_route_operation(
    session_id: str,
    operation_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> RouteOperationRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        result = confirm_route_operation(
            db,
            session=session,
            operation_id=operation_id,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.get("/{session_id}/composition/current", response_model=CurrentCompositionRead)
def get_current_composition(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> CurrentCompositionRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        return build_current_composition(db, session=session)
    except Exception as exc:
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc
