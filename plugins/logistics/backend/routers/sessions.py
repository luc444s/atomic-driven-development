from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.dto.sessions import (
    DriverOptionRead,
    SessionActionRequest,
    SessionHistoryEntryRead,
    VehicleSessionCreateRequest,
    VehicleSessionDetailRead,
    VehicleSessionRead,
)
from plugins.logistics.backend.services.sessions import (
    cancel_session,
    create_vehicle_session,
    depart_session,
    get_vehicle_session,
    list_driver_options,
    list_vehicle_sessions,
    mark_session_ready,
    mark_session_returning,
    start_loading_session,
)
from plugins.logistics.backend.services.snapshots import (
    build_session_list_item,
    build_session_snapshot,
)

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-vehicle-sessions"])

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


@router.get("/drivers/catalog", response_model=list[DriverOptionRead])
def get_driver_catalog(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[DriverOptionRead]:
    return [
        DriverOptionRead(id=user.id, full_name=user.full_name, email=user.email)
        for user in list_driver_options(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.get("/active", response_model=list[VehicleSessionRead])
def get_active_sessions(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[VehicleSessionRead]:
    return [
        build_session_list_item(db, session=session)
        for session in list_vehicle_sessions(
            db,
            tenant_id=tenant_context.current_tenant_id,
            active_only=True,
        )
    ]


@router.get("", response_model=list[VehicleSessionRead])
def get_sessions(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[VehicleSessionRead]:
    return [
        build_session_list_item(db, session=session)
        for session in list_vehicle_sessions(
            db,
            tenant_id=tenant_context.current_tenant_id,
            status=status_filter,
            active_only=status_filter == "active",
        )
    ]


@router.post("", response_model=VehicleSessionDetailRead, status_code=status.HTTP_201_CREATED)
def post_session(
    payload: VehicleSessionCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    try:
        session = create_vehicle_session(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_session_snapshot(db, session=session)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.get("/{session_id}", response_model=VehicleSessionDetailRead)
def get_session_detail(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> VehicleSessionDetailRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    return build_session_snapshot(db, session=session)


@router.get("/{session_id}/history", response_model=list[SessionHistoryEntryRead])
def get_session_history(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
):
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    return build_session_snapshot(db, session=session).history


@router.post("/{session_id}/start-loading", response_model=VehicleSessionDetailRead)
def post_start_loading(
    session_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        session = start_loading_session(
            db,
            session=session,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_session_snapshot(db, session=session)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/{session_id}/ready", response_model=VehicleSessionDetailRead)
def post_ready(
    session_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        session = mark_session_ready(
            db,
            session=session,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_session_snapshot(db, session=session)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/{session_id}/depart", response_model=VehicleSessionDetailRead)
def post_depart(
    session_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        session = depart_session(
            db,
            session=session,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_session_snapshot(db, session=session)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/{session_id}/mark-returning", response_model=VehicleSessionDetailRead)
def post_mark_returning(
    session_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        session = mark_session_returning(
            db,
            session=session,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_session_snapshot(db, session=session)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/{session_id}/cancel", response_model=VehicleSessionDetailRead)
def post_cancel(
    session_id: str,
    payload: SessionActionRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        session = cancel_session(
            db,
            session=session,
            notes=payload.notes,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_session_snapshot(db, session=session)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
