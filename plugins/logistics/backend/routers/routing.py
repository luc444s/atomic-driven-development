from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.core.config import get_settings
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.schemas import (
    RoutingCalculationRequestRead,
    RoutingCalculationResponseRead,
)
from plugins.logistics.backend.services.routing.service import RoutingService

router = APIRouter(prefix="/routing", tags=["logistics-routing"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
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
