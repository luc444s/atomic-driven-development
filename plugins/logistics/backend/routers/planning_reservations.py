from __future__ import annotations

from datetime import datetime
from typing import Never

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.schemas import (
    PlanningReservationCreateRequest,
    PlanningReservationRead,
    PlanningReservationUpdateRequest,
)
from plugins.logistics.backend.services.planning_reservations import (
    activate_reservation,
    build_reservation_read,
    cancel_reservation,
    create_reservation,
    get_reservation,
    list_reservations,
    update_reservation,
)

router = APIRouter(prefix="/planning", tags=["logistics-planning-reservations"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_PLANNING_READ = Depends(require_permission("logistics.order.read"))
REQUIRE_PLANNING_MANAGE = Depends(require_permission("logistics.order.manage"))
REQUIRE_SESSION_MANAGE = Depends(require_permission("logistics.session.manage"))
START_QUERY = Query(default=None)
END_QUERY = Query(default=None)
VEHICLE_QUERY = Query(default=None)


def _get_or_404(db: Session, *, tenant_id: str, reservation_id: str, for_update: bool = False):
    reservation = get_reservation(
        db,
        tenant_id=tenant_id,
        reservation_id=reservation_id,
        for_update=for_update,
    )
    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Planificación no encontrada",
        )
    return reservation


def _raise_service_error(exc: Exception) -> Never:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if isinstance(exc, IntegrityError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La planificación entra en conflicto con otra reserva del vehículo",
        ) from exc
    raise exc


@router.get("/calendar", response_model=list[PlanningReservationRead])
def get_planning_calendar(
    start: datetime | None = START_QUERY,
    end: datetime | None = END_QUERY,
    vehicle_id: str | None = VEHICLE_QUERY,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_PLANNING_READ,
) -> list[PlanningReservationRead]:
    return list_reservations(
        db,
        tenant_id=tenant_context.current_tenant_id,
        range_start=start,
        range_end=end,
        vehicle_id=vehicle_id,
    )


@router.get("/reservations", response_model=list[PlanningReservationRead])
def get_planning_reservations(
    start: datetime | None = START_QUERY,
    end: datetime | None = END_QUERY,
    vehicle_id: str | None = VEHICLE_QUERY,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_PLANNING_READ,
) -> list[PlanningReservationRead]:
    return list_reservations(
        db,
        tenant_id=tenant_context.current_tenant_id,
        range_start=start,
        range_end=end,
        vehicle_id=vehicle_id,
    )


@router.post(
    "/reservations",
    response_model=PlanningReservationRead,
    status_code=status.HTTP_201_CREATED,
)
def post_planning_reservation(
    payload: PlanningReservationCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_PLANNING_MANAGE,
) -> PlanningReservationRead:
    try:
        reservation = create_reservation(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_reservation_read(db, reservation=reservation)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.patch("/reservations/{reservation_id}", response_model=PlanningReservationRead)
def patch_planning_reservation(
    reservation_id: str,
    payload: PlanningReservationUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_PLANNING_MANAGE,
) -> PlanningReservationRead:
    reservation = _get_or_404(
        db,
        tenant_id=tenant_context.current_tenant_id,
        reservation_id=reservation_id,
    )
    try:
        reservation = update_reservation(
            db,
            reservation=reservation,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_reservation_read(db, reservation=reservation)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/reservations/{reservation_id}/activate", response_model=PlanningReservationRead)
def post_activate_planning_reservation(
    reservation_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> PlanningReservationRead:
    reservation = _get_or_404(
        db,
        tenant_id=tenant_context.current_tenant_id,
        reservation_id=reservation_id,
        for_update=True,
    )
    try:
        reservation = activate_reservation(
            db,
            reservation=reservation,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_reservation_read(db, reservation=reservation)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/reservations/{reservation_id}/cancel", response_model=PlanningReservationRead)
def post_cancel_planning_reservation(
    reservation_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_PLANNING_MANAGE,
) -> PlanningReservationRead:
    reservation = _get_or_404(
        db,
        tenant_id=tenant_context.current_tenant_id,
        reservation_id=reservation_id,
    )
    try:
        reservation = cancel_reservation(
            db,
            reservation=reservation,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return build_reservation_read(db, reservation=reservation)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
