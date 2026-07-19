from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.dto.sessions import (
    SessionWaybillRegenerateRequest,
    SessionWaybillStateRead,
    SessionWaybillVersionRead,
)
from plugins.logistics.backend.services.session_waybills import (
    get_session_waybill_state,
    list_session_waybill_history,
    regenerate_session_waybill,
)
from plugins.logistics.backend.services.sessions import get_vehicle_session

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-session-waybill"])

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


@router.get("/{session_id}/carta-porte", response_model=SessionWaybillStateRead)
def get_session_waybill(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> SessionWaybillStateRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        return get_session_waybill_state(db, session=session)
    except Exception as exc:
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.get("/{session_id}/carta-porte/history", response_model=list[SessionWaybillVersionRead])
def get_session_waybill_history(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[SessionWaybillVersionRead]:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    return list_session_waybill_history(db, session=session)


@router.post("/{session_id}/carta-porte/regenerate", response_model=SessionWaybillStateRead)
def post_regenerate_session_waybill(
    session_id: str,
    payload: SessionWaybillRegenerateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> SessionWaybillStateRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        result = regenerate_session_waybill(
            db,
            session=session,
            event=payload.event,
            reason=payload.reason,
            idempotency_key=payload.idempotency_key,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc
