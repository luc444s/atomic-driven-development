from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.permissions.service import list_user_permissions


@dataclass(slots=True, frozen=True)
class TenantContext:
    current_tenant_id: str
    current_branch_id: str | None
    current_user_id: str
    current_permissions: tuple[str, ...]
    is_superadmin: bool

    def has_permission(self, permission_name: str) -> bool:
        return self.is_superadmin or permission_name in self.current_permissions


def build_tenant_context(db: Session, user: User) -> TenantContext:
    permissions = tuple(list_user_permissions(db, user_id=user.id, tenant_id=user.tenant_id))
    return TenantContext(
        current_tenant_id=user.tenant_id,
        current_branch_id=user.branch_id,
        current_user_id=user.id,
        current_permissions=permissions,
        is_superadmin=user.is_superadmin,
    )
