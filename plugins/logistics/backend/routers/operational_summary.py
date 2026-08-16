from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from systutor.api.deps import get_db_session
from systutor.kernel.auth.dependencies import get_current_tenant_context, require_permission
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.context import TenantContext

from plugins.logistics.backend.dto.operational_summary import SessionOperationalSummaryRead
from plugins.logistics.backend.services.operational_summary import build_operational_summary
from plugins.logistics.backend.services.sessions import get_vehicle_session

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-operational-summary"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))


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


@router.get("/{session_id}/operational-summary", response_model=SessionOperationalSummaryRead)
def get_operational_summary(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> SessionOperationalSummaryRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        return build_operational_summary(db, session=session)
    except Exception as exc:
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc
