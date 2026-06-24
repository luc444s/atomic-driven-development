from __future__ import annotations

from sqlalchemy import Select, distinct, select
from sqlalchemy.orm import Session

from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.permissions.models import Permission, Role, RolePermission, UserRole
from apps.api.app.kernel.tenants.service import TenantScopeError


def list_user_permissions(db: Session, *, user_id: str, tenant_id: str) -> list[str]:
    stmt: Select[tuple[str]] = (
        select(distinct(Permission.name))
        .select_from(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(User.id == user_id, User.tenant_id == tenant_id, Role.tenant_id == tenant_id)
        .order_by(Permission.name.asc())
    )
    return list(db.scalars(stmt))


def user_has_permission(db: Session, *, user_id: str, tenant_id: str, permission_name: str) -> bool:
    stmt = (
        select(Permission.id)
        .select_from(User)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(
            User.id == user_id,
            User.tenant_id == tenant_id,
            Role.tenant_id == tenant_id,
            Permission.name == permission_name,
        )
        .limit(1)
    )
    return db.scalar(stmt) is not None


def list_roles_for_tenant(db: Session, *, tenant_id: str) -> list[Role]:
    stmt: Select[tuple[Role]] = (
        select(Role).where(Role.tenant_id == tenant_id).order_by(Role.name.asc())
    )
    return list(db.scalars(stmt))


def get_role_for_tenant(db: Session, *, tenant_id: str, role_id: str) -> Role | None:
    stmt: Select[tuple[Role]] = select(Role).where(Role.id == role_id, Role.tenant_id == tenant_id)
    return db.scalar(stmt)


def create_role_for_tenant(
    db: Session,
    *,
    tenant_id: str,
    name: str,
    description: str | None,
) -> Role:
    role = Role(tenant_id=tenant_id, name=name, description=description)
    db.add(role)
    db.flush()
    return role


def update_role_for_tenant(
    db: Session,
    *,
    role: Role,
    name: str | None = None,
    description: str | None = None,
) -> Role:
    if name is not None:
        role.name = name
    if description is not None:
        role.description = description
    db.add(role)
    db.flush()
    return role


def delete_role_for_tenant(db: Session, *, role: Role) -> None:
    db.delete(role)
    db.flush()


def assign_role_to_user(db: Session, *, user: User, role: Role) -> UserRole:
    if user.tenant_id != role.tenant_id:
        raise TenantScopeError("Role does not belong to the user's tenant")

    stmt: Select[tuple[UserRole]] = select(UserRole).where(
        UserRole.user_id == user.id,
        UserRole.role_id == role.id,
    )
    existing = db.scalar(stmt)
    if existing is not None:
        return existing

    user_role = UserRole(user_id=user.id, role_id=role.id)
    db.add(user_role)
    db.flush()
    return user_role


def remove_role_from_user(db: Session, *, user: User, role: Role) -> bool:
    if user.tenant_id != role.tenant_id:
        raise TenantScopeError("Role does not belong to the user's tenant")

    stmt: Select[tuple[UserRole]] = select(UserRole).where(
        UserRole.user_id == user.id,
        UserRole.role_id == role.id,
    )
    user_role = db.scalar(stmt)
    if user_role is None:
        return False

    db.delete(user_role)
    db.flush()
    return True


def list_permissions(db: Session) -> list[Permission]:
    stmt: Select[tuple[Permission]] = select(Permission).order_by(Permission.name.asc())
    return list(db.scalars(stmt))


def get_permission_by_id(db: Session, *, permission_id: str) -> Permission | None:
    stmt: Select[tuple[Permission]] = select(Permission).where(Permission.id == permission_id)
    return db.scalar(stmt)
