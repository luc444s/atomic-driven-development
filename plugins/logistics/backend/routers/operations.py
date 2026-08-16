from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from systutor.api.deps import get_db_session
from systutor.kernel.auth.dependencies import get_current_tenant_context, require_permission
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.context import TenantContext

from plugins.logistics.backend.dto.operations import LogisticsOperationRead
from plugins.logistics.backend.services.operations import (
    list_operation_items,
    list_session_operations,
)
from plugins.logistics.backend.services.sessions import get_vehicle_session

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-operations"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))


@router.get("/{session_id}/operations", response_model=list[LogisticsOperationRead])
def get_operations(
    session_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> list[LogisticsOperationRead]:
    session = get_vehicle_session(
        db, tenant_id=tenant_context.current_tenant_id, session_id=session_id
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jornada no encontrada")
    result = []
    for operation in list_session_operations(db, session_id=session.id):
        result.append(
            LogisticsOperationRead(
                id=operation.id,
                session_id=operation.session_id,
                movement_type=operation.movement_type,
                status=operation.status,
                external_movement_id=operation.external_movement_id,
                idempotency_key=operation.idempotency_key,
                performed_by=operation.performed_by,
                performed_at=operation.performed_at,
                notes=operation.notes,
                created_at=operation.created_at,
                updated_at=operation.updated_at,
                items=[
                    {
                        "id": item.id,
                        "product_id": item.product_id,
                        "product_name": item.product_name,
                        "quantity": float(item.quantity),
                        "weight_kg": float(item.weight_kg) if item.weight_kg is not None else None,
                        "notes": item.notes,
                        "created_at": item.created_at,
                    }
                    for item in list_operation_items(db, operation_id=operation.id)
                ],
            )
        )
    return result
