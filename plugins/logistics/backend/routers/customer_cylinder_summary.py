from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from systutor.api.deps import get_db_session
from systutor.kernel.auth.dependencies import get_current_tenant_context, require_permission
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.context import TenantContext

from plugins.logistics.backend.customer_cylinder_summary_schemas import (
    CustomerCylinderSummaryRead,
)
from plugins.logistics.backend.schemas import ContractExcessTrackingRead
from plugins.logistics.backend.services.customer_cylinder_summary import (
    get_customer_cylinder_summary,
)

router = APIRouter(prefix="/customers", tags=["logistics-customer-cylinders"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_CYLINDER_READ = Depends(require_permission("logistics.cylinder.read"))
REQUIRE_CONTRACT_VIEW = Depends(require_permission("logistics.contract.view"))
INCLUDE_SERIALS_QUERY = Query(default=False)
AS_OF_QUERY = Query(default=None)


@router.get("/{customer_id}/cylinders/summary", response_model=CustomerCylinderSummaryRead)
def get_customer_cylinders_summary(
    customer_id: str,
    include_serials: bool = INCLUDE_SERIALS_QUERY,
    as_of: datetime | None = AS_OF_QUERY,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> CustomerCylinderSummaryRead:
    try:
        return get_customer_cylinder_summary(
            db,
            tenant_id=tenant_context.current_tenant_id,
            customer_id=customer_id,
            include_serials=include_serials,
            as_of=as_of,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/{customer_id}/excess-tracking",
    response_model=list[ContractExcessTrackingRead],
)
def list_customer_excess_tracking_endpoint(
    customer_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_VIEW,
) -> list[ContractExcessTrackingRead]:
    from plugins.logistics.backend.services.contracts_excess import (
        list_customer_excess_tracking as service_list,
    )

    return service_list(
        db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id
    )
