from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context, emit_logistics_event
from plugins.logistics.backend.schemas import CylinderEventRead, CylinderTraceabilityRead
from plugins.logistics.backend.services.cylinders import (
    get_cylinder_current_location,
)
from plugins.logistics.backend.services.cylinders import (
    list_cylinder_events as list_events_svc,
)
from plugins.logistics.backend.services.traceability import get_cylinder_traceability

router = APIRouter(tags=["logistics"])
DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_CYLINDER_TRACE = Depends(require_permission("logistics.cylinder.trace"))


@router.get(
    "/cylinders/{cylinder_id}/traceability",
    response_model=CylinderTraceabilityRead,
)
def get_traceability(
    cylinder_id: str,
    request: Request,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
    user: User = REQUIRE_CYLINDER_TRACE,
) -> CylinderTraceabilityRead:
    result = get_cylinder_traceability(
        db,
        tenant_id=tenant_context.current_tenant_id,
        cylinder_id=cylinder_id,
        page=page,
        per_page=per_page,
    )
    emit_logistics_event(
        db,
        context=build_action_context(request, tenant_context),
        event_name="logistics.cylinder.traceability_viewed",
        entity_type="cylinder",
        entity_id=cylinder_id,
        payload={"page": page, "per_page": per_page},
    )
    return result


@router.get(
    "/cylinders/{cylinder_id}/events",
    response_model=list[CylinderEventRead],
)
def get_cylinder_events(
    cylinder_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = DB_SESSION,
    _: User = REQUIRE_CYLINDER_TRACE,
) -> list[CylinderEventRead]:
    return [
        CylinderEventRead.model_validate(event)
        for event in list_events_svc(db, cylinder_id=cylinder_id, limit=limit)
    ]


@router.get("/cylinders/{cylinder_id}/location")
def get_cylinder_location(
    cylinder_id: str,
    db: Session = DB_SESSION,
    _: User = REQUIRE_CYLINDER_TRACE,
) -> dict[str, object]:
    location = get_cylinder_current_location(db, cylinder_id=cylinder_id)
    if location is None:
        return {"location_type": None, "location_id": None}
    return {"location_type": location[0], "location_id": location[1]}
