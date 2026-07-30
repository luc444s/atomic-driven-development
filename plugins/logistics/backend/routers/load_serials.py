from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.dto.load_serials import (
    LoadSerialAssignmentRead,
    LoadSerialReleaseRequest,
    LoadSerialSearchResultRead,
    LoadSerialSelectRequest,
)
from plugins.logistics.backend.services.load_serials import (
    list_selected_load_serial_assignments,
    release_load_serial,
    search_load_serial_candidates,
    select_load_serial,
)
from plugins.logistics.backend.services.sessions import get_vehicle_session

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-load-serials"])

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


@router.get("/{session_id}/load-serials/selected", response_model=list[LoadSerialAssignmentRead])
def get_selected_load_serials(
    session_id: str,
    product_id: str | None = Query(default=None),
    selection_context: str | None = Query(default=None),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[LoadSerialAssignmentRead]:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    return list_selected_load_serial_assignments(
        db,
        session_id=session.id,
        product_id=product_id,
        selection_context=selection_context,
    )


@router.get("/{session_id}/load-serials/search", response_model=list[LoadSerialSearchResultRead])
def get_load_serial_search(
    session_id: str,
    product_id: str = Query(...),
    query: str = Query(...),
    source_warehouse_id: str | None = Query(default=None),
    selection_context: str | None = Query(default=None),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[LoadSerialSearchResultRead]:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        return search_load_serial_candidates(
            db,
            session=session,
            product_id=product_id,
            source_warehouse_id=source_warehouse_id,
            selection_context=selection_context,
            query=query,
        )
    except Exception as exc:
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.put("/{session_id}/load-serials/select", response_model=LoadSerialAssignmentRead)
def put_select_load_serial(
    session_id: str,
    payload: LoadSerialSelectRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> LoadSerialAssignmentRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        result = select_load_serial(
            db,
            session=session,
            product_id=payload.product_id,
            source_warehouse_id=payload.source_warehouse_id,
            selection_context=payload.selection_context,
            serial=payload.serial,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.put(
    "/{session_id}/load-serials/{assignment_id}/release",
    response_model=LoadSerialAssignmentRead,
)
def put_release_load_serial(
    session_id: str,
    assignment_id: str,
    payload: LoadSerialReleaseRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> LoadSerialAssignmentRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        result = release_load_serial(
            db,
            session=session,
            assignment_id=assignment_id,
            release_reason=payload.release_reason,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc
