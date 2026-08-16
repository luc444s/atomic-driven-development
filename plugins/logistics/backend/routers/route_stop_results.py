from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from systutor.api.deps import get_db_session
from systutor.kernel.auth.dependencies import get_current_tenant_context, require_permission
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.context import TenantContext

from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.dto.route_stop_results import (
    RouteStopResultRead,
    RouteStopResultUpsertRequest,
)
from plugins.logistics.backend.services.route_stop_results import (
    list_route_stop_results,
    upsert_route_stop_result,
)
from plugins.logistics.backend.services.sessions import get_vehicle_session

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-route-stop-results"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))
REQUIRE_SESSION_MANAGE = Depends(require_permission("logistics.session.manage"))
REQUIRE_SESSION_ROUTE_EXECUTE = Depends(require_permission("logistics.session.route_execute"))


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


@router.get("/{session_id}/route-stop-results", response_model=list[RouteStopResultRead])
def get_route_stop_results(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[RouteStopResultRead]:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    return list_route_stop_results(db, session_id=session.id)


@router.put(
    "/{session_id}/route-stop-results/{route_stop_id}",
    response_model=RouteStopResultRead,
)
def put_route_stop_result(
    session_id: str,
    route_stop_id: str,
    payload: RouteStopResultUpsertRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_ROUTE_EXECUTE,
) -> RouteStopResultRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        result = upsert_route_stop_result(
            db,
            session=session,
            route_stop_id=route_stop_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc
