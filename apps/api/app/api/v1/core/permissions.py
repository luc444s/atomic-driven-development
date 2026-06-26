from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.api.v1.core.schemas import CorePermissionRead
from apps.api.app.kernel.auth.dependencies import require_any_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.permissions.service import list_permissions

router = APIRouter(prefix="/core/permissions", tags=["core"])
DB_SESSION = Depends(get_db_session)
REQUIRE_PERMISSION_CATALOG = Depends(
    require_any_permission("core.roles.manage", "core.permission.manage")
)


@router.get("", response_model=list[CorePermissionRead])
def get_permissions(
    db: Session = DB_SESSION,
    _: User = REQUIRE_PERMISSION_CATALOG,
) -> list[CorePermissionRead]:
    return [CorePermissionRead.model_validate(permission) for permission in list_permissions(db)]
