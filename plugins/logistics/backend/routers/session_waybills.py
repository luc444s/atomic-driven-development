from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from apps.api.app.core.lifecycle import ensure_session_factory
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

TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))
REQUIRE_SESSION_MANAGE = Depends(require_permission("logistics.session.manage"))


def _make_sync_session(request: Request) -> Session:
    factory = ensure_session_factory(request.app)
    return factory()


def _get_or_404(db: Session, *, tenant_id: str, session_id: str):
    session = get_vehicle_session(db, tenant_id=tenant_id, session_id=session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jornada no encontrada",
        )
    return session


def _raise_service_error(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise exc


@router.get("/{session_id}/carta-porte", response_model=SessionWaybillStateRead)
async def get_session_waybill(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> SessionWaybillStateRead:
    def _load() -> SessionWaybillStateRead:
        db = _make_sync_session(request)
        try:
            session = _get_or_404(
                db,
                tenant_id=tenant_context.current_tenant_id,
                session_id=session_id,
            )
            return get_session_waybill_state(db, session=session)
        finally:
            db.close()

    try:
        return await asyncio.to_thread(_load)
    except Exception as exc:
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.get(
    "/{session_id}/carta-porte/history",
    response_model=list[SessionWaybillVersionRead],
)
async def get_session_waybill_history(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[SessionWaybillVersionRead]:
    def _load() -> list[SessionWaybillVersionRead]:
        db = _make_sync_session(request)
        try:
            session = _get_or_404(
                db,
                tenant_id=tenant_context.current_tenant_id,
                session_id=session_id,
            )
            return list_session_waybill_history(db, session=session)
        finally:
            db.close()

    return await asyncio.to_thread(_load)


@router.post(
    "/{session_id}/carta-porte/regenerate",
    response_model=SessionWaybillStateRead,
)
async def post_regenerate_session_waybill(
    session_id: str,
    payload: SessionWaybillRegenerateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> SessionWaybillStateRead:
    def _mutate() -> SessionWaybillStateRead:
        db = _make_sync_session(request)
        try:
            session = _get_or_404(
                db,
                tenant_id=tenant_context.current_tenant_id,
                session_id=session_id,
            )
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
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    try:
        return await asyncio.to_thread(_mutate)
    except Exception as exc:
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc
