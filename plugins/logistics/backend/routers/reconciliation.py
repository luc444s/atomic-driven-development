from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.dto.reconciliation import (
    CloseSessionRequest,
    ReconciliationCountRequest,
    SessionReconciliationRead,
)
from plugins.logistics.backend.services.reconciliation import (
    close_vehicle_session,
    get_reconciliation_view,
    record_reconciliation_count,
)
from plugins.logistics.backend.services.sessions import get_vehicle_session
from plugins.logistics.backend.services.snapshots import build_session_snapshot

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-reconciliation"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))
REQUIRE_SESSION_MANAGE = Depends(require_permission("logistics.session.manage"))


def _get_session_or_404(db: Session, *, tenant_id: str, session_id: str):
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


@router.get("/{session_id}/reconciliation", response_model=SessionReconciliationRead)
def get_session_reconciliation(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> SessionReconciliationRead:
    session = _get_session_or_404(
        db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
    )
    return get_reconciliation_view(db, session=session)


@router.post("/{session_id}/reconciliation/count", response_model=SessionReconciliationRead)
def post_reconciliation_count(
    session_id: str,
    payload: ReconciliationCountRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> SessionReconciliationRead:
    session = _get_session_or_404(
        db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
    )
    try:
        result = record_reconciliation_count(
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


@router.post("/{session_id}/close", response_model=dict)
def post_close_session(
    session_id: str,
    payload: CloseSessionRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> dict:
    session = _get_session_or_404(
        db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
    )
    try:
        session = close_vehicle_session(
            db,
            session=session,
            notes=payload.notes,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        snapshot = build_session_snapshot(db, session=session)
        return {"session_id": snapshot.id, "status": snapshot.status}
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
