from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from apps.api.app.core.config import get_settings
from apps.api.app.core.lifecycle import ensure_session_factory
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import LogisticsActionContext, build_action_context
from plugins.logistics.backend.dto.sessions import (
    AssignRouteRequest,
    DriverOptionRead,
    SessionActionRequest,
    SessionHistoryEntryRead,
    VehicleSessionCreateRequest,
    VehicleSessionCreateWithRouteRequest,
    VehicleSessionDetailRead,
    VehicleSessionPageRead,
    VehicleSessionRead,
)
from plugins.logistics.backend.services.sessions import (
    assign_route_to_session,
    cancel_session,
    create_vehicle_session,
    create_vehicle_session_with_route,
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

TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))
REQUIRE_SESSION_MANAGE = Depends(require_permission("logistics.session.manage"))


def _make_sync_session(request: Request) -> Session:
    factory = ensure_session_factory(request.app)
    return factory()


async def _run_sync[T](
    request: Request,
    fn: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    def _call() -> T:
        db = _make_sync_session(request)
        try:
            result = fn(db, *args, **kwargs)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return await asyncio.to_thread(_call)


async def _run_sync_readonly[T](
    request: Request,
    fn: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    def _call() -> T:
        db = _make_sync_session(request)
        try:
            return fn(db, *args, **kwargs)
        finally:
            db.close()

    return await asyncio.to_thread(_call)


def _raise_service_error(exc: Exception) -> NoReturn:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise exc


def _get_session_or_404(db: Session, *, tenant_id: str, session_id: str):
    session = get_vehicle_session(db, tenant_id=tenant_id, session_id=session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Jornada no encontrada",
        )
    return session


def _session_list(
    db: Session,
    *,
    tenant_id: str,
    status_filter: str | None,
    active_only: bool,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[VehicleSessionRead], int]:
    sessions, total = list_vehicle_sessions(
        db, tenant_id=tenant_id, status=status_filter, active_only=active_only,
        page=page, per_page=per_page,
    )
    return [build_session_list_item(db, session=s) for s in sessions], total


async def _transition(
    request: Request,
    session_id: str,
    tenant_context: TenantContext,
    action_context: LogisticsActionContext,
    transition_fn: Callable[..., Any],
    **extra: Any,
) -> VehicleSessionDetailRead:
    def _call() -> VehicleSessionDetailRead:
        db = _make_sync_session(request)
        try:
            session = _get_session_or_404(
                db, tenant_id=tenant_context.current_tenant_id,
                session_id=session_id,
            )
            session = transition_fn(
                db, session=session, action_context=action_context,
                **extra,
            )
            result = build_session_snapshot(db, session=session)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return await asyncio.to_thread(_call)


# ── Read-only endpoints ──────────────────────────────────────────────


@router.get("/drivers/catalog", response_model=list[DriverOptionRead])
async def get_driver_catalog(
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[DriverOptionRead]:
    def _load(db: Session) -> list[DriverOptionRead]:
        users = list_driver_options(db, tenant_id=tenant_context.current_tenant_id)
        return [
            DriverOptionRead(id=u.id, full_name=u.full_name, email=u.email)
            for u in users
        ]

    return await _run_sync_readonly(request, _load)


@router.get("/active", response_model=list[VehicleSessionRead])
async def get_active_sessions(
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[VehicleSessionRead]:
    def _load(db: Session) -> list[VehicleSessionRead]:
        items, _ = _session_list(
            db, tenant_id=tenant_context.current_tenant_id,
            status_filter=None, active_only=True,
        )
        return items

    return await _run_sync_readonly(request, _load)


@router.get("", response_model=VehicleSessionPageRead)
async def get_sessions(
    request: Request,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> VehicleSessionPageRead:
    def _load(db: Session) -> VehicleSessionPageRead:
        items, total = _session_list(
            db, tenant_id=tenant_context.current_tenant_id,
            status_filter=status_filter, active_only=status_filter == "active",
            page=page, per_page=per_page,
        )
        total_pages = max(1, -(-total // per_page))
        return VehicleSessionPageRead(
            items=items, total=total, page=page, per_page=per_page, total_pages=total_pages,
        )

    return await _run_sync_readonly(request, _load)


@router.post(
    "/create-with-route",
    response_model=VehicleSessionDetailRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_session_with_route(
    payload: VehicleSessionCreateWithRouteRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    def _call() -> VehicleSessionDetailRead:
        db = _make_sync_session(request)
        try:
            session = create_vehicle_session_with_route(
                db,
                tenant_id=tenant_context.current_tenant_id,
                payload=payload,
                action_context=build_action_context(request, tenant_context),
                settings=get_settings(),
            )
            result = build_session_snapshot(db, session=session)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    try:
        return await asyncio.to_thread(_call)
    except Exception as exc:
        _raise_service_error(exc)


@router.get("/{session_id}", response_model=VehicleSessionDetailRead)
async def get_session_detail(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> VehicleSessionDetailRead:
    def _load(db: Session) -> VehicleSessionDetailRead:
        s = _get_session_or_404(
            db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
        )
        return build_session_snapshot(db, session=s)

    return await _run_sync_readonly(request, _load)


@router.get("/{session_id}/history", response_model=list[SessionHistoryEntryRead])
async def get_session_history(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
):
    def _load(db: Session) -> list[SessionHistoryEntryRead]:
        s = _get_session_or_404(
            db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
        )
        return build_session_snapshot(db, session=s).history

    return await _run_sync_readonly(request, _load)


# ── Mutation endpoints ───────────────────────────────────────────────


@router.post(
    "",
    response_model=VehicleSessionDetailRead,
    status_code=status.HTTP_201_CREATED,
)
async def post_session(
    payload: VehicleSessionCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    def _call() -> VehicleSessionDetailRead:
        db = _make_sync_session(request)
        try:
            session = create_vehicle_session(
                db,
                tenant_id=tenant_context.current_tenant_id,
                payload=payload,
                action_context=build_action_context(request, tenant_context),
            )
            result = build_session_snapshot(db, session=session)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    try:
        return await asyncio.to_thread(_call)
    except Exception as exc:
        _raise_service_error(exc)


@router.post("/{session_id}/start-loading", response_model=VehicleSessionDetailRead)
async def post_start_loading(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    try:
        return await _transition(
            request,
            session_id,
            tenant_context,
            build_action_context(request, tenant_context),
            start_loading_session,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.post("/{session_id}/ready", response_model=VehicleSessionDetailRead)
async def post_ready(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    try:
        return await _transition(
            request,
            session_id,
            tenant_context,
            build_action_context(request, tenant_context),
            mark_session_ready,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.post("/{session_id}/depart", response_model=VehicleSessionDetailRead)
async def post_depart(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    try:
        return await _transition(
            request,
            session_id,
            tenant_context,
            build_action_context(request, tenant_context),
            depart_session,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.post("/{session_id}/mark-returning", response_model=VehicleSessionDetailRead)
async def post_mark_returning(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    try:
        return await _transition(
            request,
            session_id,
            tenant_context,
            build_action_context(request, tenant_context),
            mark_session_returning,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.post("/{session_id}/cancel", response_model=VehicleSessionDetailRead)
async def post_cancel(
    session_id: str,
    payload: SessionActionRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    try:
        return await _transition(
            request,
            session_id,
            tenant_context,
            build_action_context(request, tenant_context),
            cancel_session,
            notes=payload.notes,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.post("/{session_id}/assign-route", response_model=VehicleSessionDetailRead)
async def post_assign_route(
    session_id: str,
    payload: AssignRouteRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    try:
        return await _transition(
            request,
            session_id,
            tenant_context,
            build_action_context(request, tenant_context),
            assign_route_to_session,
            route_id=payload.route_id,
        )
    except Exception as exc:
        _raise_service_error(exc)
