from __future__ import annotations

from sqlalchemy import Select, distinct, select
from sqlalchemy.orm import Session

from apps.api.app.kernel.permissions.models import Permission, RolePermission, UserRole


def list_user_permissions(db: Session, user_id: str) -> list[str]:
    stmt: Select[tuple[str]] = (
        select(distinct(Permission.name))
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
        .order_by(Permission.name.asc())
    )
    return list(db.scalars(stmt))


def user_has_permission(db: Session, user_id: str, permission_name: str) -> bool:
    stmt = (
        select(Permission.id)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id, Permission.name == permission_name)
        .limit(1)
    )
    return db.scalar(stmt) is not None
