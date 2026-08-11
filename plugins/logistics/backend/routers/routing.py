from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.core.config import get_settings
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.schemas import (
    RoutingAssignedRouteRead,
    RoutingCalculationRequestRead,
    RoutingCalculationResponseRead,
    RoutingCommitOrderRequestRead,
    RoutingCommitOrderResponseRead,
)
from plugins.logistics.backend.services.routing.service import RoutingService

router = APIRouter(prefix="/routing", tags=["logistics-routing"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_ROUTE_READ = Depends(require_permission("logistics.route.read"))
REQUIRE_ROUTE_MANAGE = Depends(require_permission("logistics.route.manage"))


@router.post("/preview", response_model=RoutingCalculationResponseRead)
def post_routing_preview(
    payload: RoutingCalculationRequestRead,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RoutingCalculationResponseRead:
    del db, tenant_context
    service = RoutingService(get_settings())
    try:
        return RoutingCalculationResponseRead.model_validate(service.calculate_preview(payload))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post("/optimize", response_model=RoutingCalculationResponseRead)
def post_routing_optimize(
    payload: RoutingCalculationRequestRead,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RoutingCalculationResponseRead:
    del db, tenant_context
    service = RoutingService(get_settings())
    try:
        return RoutingCalculationResponseRead.model_validate(service.calculate_preview(payload))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post("/commit-order", response_model=RoutingCommitOrderResponseRead)
def post_routing_commit_order(
    payload: RoutingCommitOrderRequestRead,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RoutingCommitOrderResponseRead:
    service = RoutingService(get_settings())
    try:
        response = service.commit_order(
            db,
            tenant_id=tenant_context.current_tenant_id,
            actor_user_id=tenant_context.current_user_id,
            payload=payload,
        )
        db.commit()
        return RoutingCommitOrderResponseRead.model_validate(response)
    except LookupError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/assigned-route/{route_id}", response_model=RoutingAssignedRouteRead | None)
def get_assigned_route_snapshot(
    route_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> RoutingAssignedRouteRead | None:
    service = RoutingService(get_settings())
    snapshot = service.get_latest_assigned_route(
        db,
        tenant_id=tenant_context.current_tenant_id,
        route_id=route_id,
    )
    if snapshot is None:
        return None
    return RoutingAssignedRouteRead.model_validate(snapshot)
