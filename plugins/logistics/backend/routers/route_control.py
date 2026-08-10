from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.dto.route_control import (
    RouteControlStateRead,
    VehicleLocationEventRead,
    VehicleLocationRecordRequest,
)
from plugins.logistics.backend.services.route_control import (
    get_route_control_state,
    list_vehicle_location_history,
    mark_route_stop_arrived,
    mark_route_stop_departed,
    record_vehicle_location,
)
from plugins.logistics.backend.services.sessions import get_vehicle_session

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-route-control"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))
REQUIRE_SESSION_MANAGE = Depends(require_permission("logistics.session.manage"))
REQUIRE_SESSION_ROUTE_EXECUTE = Depends(require_permission("logistics.session.route_execute"))
FromRecordedAt = Annotated[datetime | None, Query(alias="from")]
ToRecordedAt = Annotated[datetime | None, Query(alias="to")]
HistoryLimit = Annotated[int, Query(ge=1, le=1000)]


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


@router.post(
    "/{session_id}/location",
    response_model=VehicleLocationEventRead,
    status_code=status.HTTP_201_CREATED,
)
def post_vehicle_location(
    session_id: str,
    payload: VehicleLocationRecordRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_ROUTE_EXECUTE,
) -> VehicleLocationEventRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        event = record_vehicle_location(
            db,
            session=session,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return event
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.get("/{session_id}/control-state", response_model=RouteControlStateRead)
def get_vehicle_session_control_state(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> RouteControlStateRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    state = get_route_control_state(db, session=session)
    db.commit()
    return state


@router.get("/{session_id}/location-history", response_model=list[VehicleLocationEventRead])
def get_vehicle_session_location_history(
    session_id: str,
    from_recorded_at: FromRecordedAt = None,
    to_recorded_at: ToRecordedAt = None,
    limit: HistoryLimit = 200,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[VehicleLocationEventRead]:
    _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    return list_vehicle_location_history(
        db,
        session_id=session_id,
        from_recorded_at=from_recorded_at,
        to_recorded_at=to_recorded_at,
        limit=limit,
    )


@router.post("/{session_id}/stops/{stop_id}/arrive", response_model=RouteControlStateRead)
def post_route_stop_arrive(
    session_id: str,
    stop_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_ROUTE_EXECUTE,
) -> RouteControlStateRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        state = mark_route_stop_arrived(
            db,
            session=session,
            stop_id=stop_id,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return state
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc


@router.post("/{session_id}/stops/{stop_id}/depart", response_model=RouteControlStateRead)
def post_route_stop_depart(
    session_id: str,
    stop_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_ROUTE_EXECUTE,
) -> RouteControlStateRead:
    session = _get_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        state = mark_route_stop_departed(
            db,
            session=session,
            stop_id=stop_id,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return state
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
        raise AssertionError("unreachable") from exc
