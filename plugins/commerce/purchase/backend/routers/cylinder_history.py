"""COMPRAS-016: endpoint de solo lectura del historial del envase."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from systutor.kernel.tenants.context import TenantContext

from plugins.commerce.purchase.backend.routers.common import (
    DB_SESSION,
    REQUIRE_ORDER_READ,
    TENANT_CONTEXT,
)
from plugins.commerce.purchase.backend.schemas import CylinderHistoryRead
from plugins.commerce.purchase.backend.services import (
    cylinder_history as cylinder_history_service,
)

router = APIRouter()


@router.get(
    "/cylinders/{serial}/history",
    response_model=CylinderHistoryRead,
    dependencies=[REQUIRE_ORDER_READ],
)
def get_cylinder_history(
    serial: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> CylinderHistoryRead:
    try:
        history = cylinder_history_service.get_cylinder_history(
            db, tenant_id=tenant_context.current_tenant_id, serial=serial
        )
    except cylinder_history_service.SerialNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CylinderHistoryRead.model_validate(history)
