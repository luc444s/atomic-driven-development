from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from apps.api.app.core.config import Settings, get_settings
from apps.api.app.core.database import build_session_factory
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.auth.security import hash_password
from apps.api.app.kernel.permissions.models import Permission, Role, RolePermission
from apps.api.app.kernel.permissions.service import assign_role_to_user
from apps.api.app.kernel.plugins.runtime import LoadedPlugin, PluginManifestRegistry, PluginRuntime
from apps.api.app.kernel.plugins.service import sync_plugin_registry
from apps.api.app.kernel.tenants.models import Branch, Tenant
from apps.api.app.kernel.tenants.service import assign_branch_to_user

BASE_PERMISSIONS = [
    "core.auth.me",
    "core.plugin.read",
    "core.plugin.manage",
    "core.audit.read",
    "core.event.read",
    "core.user.manage",
    "core.users.read",
    "core.users.create",
    "core.users.update",
    "core.users.delete",
    "core.role.manage",
    "core.roles.read",
    "core.roles.manage",
    "core.permission.manage",
    "core.branches.manage",
]


def _get_or_create_tenant(db: Session, settings: Settings) -> Tenant:
    stmt: Select[tuple[Tenant]] = select(Tenant).where(
        Tenant.slug == settings.seed_demo_tenant_slug
    )
    tenant = db.scalar(stmt)
    if tenant is not None:
        return tenant

    tenant = Tenant(name=settings.seed_demo_tenant_name, slug=settings.seed_demo_tenant_slug)
    db.add(tenant)
    db.flush()
    return tenant


def _get_or_create_branch(db: Session, tenant: Tenant, settings: Settings) -> Branch:
    stmt: Select[tuple[Branch]] = select(Branch).where(
        Branch.tenant_id == tenant.id,
        Branch.code == settings.seed_demo_branch_code,
    )
    branch = db.scalar(stmt)
    if branch is not None:
        return branch

    branch = Branch(
        tenant_id=tenant.id,
        name=settings.seed_demo_branch_name,
        code=settings.seed_demo_branch_code,
    )
    db.add(branch)
    db.flush()
    return branch


def _get_or_create_role(db: Session, tenant: Tenant) -> Role:
    stmt: Select[tuple[Role]] = select(Role).where(
        Role.tenant_id == tenant.id,
        Role.name == "admin",
    )
    role = db.scalar(stmt)
    if role is not None:
        return role

    role = Role(
        tenant_id=tenant.id,
        name="admin",
        description="Administrative role for demo tenant",
    )
    db.add(role)
    db.flush()
    return role


def _get_or_create_permission(db: Session, permission_name: str) -> Permission:
    stmt: Select[tuple[Permission]] = select(Permission).where(Permission.name == permission_name)
    permission = db.scalar(stmt)
    if permission is not None:
        return permission

    permission = Permission(name=permission_name, description=f"Base permission {permission_name}")
    db.add(permission)
    db.flush()
    return permission


def _ensure_role_permission(db: Session, role_id: str, permission_id: str) -> None:
    stmt: Select[tuple[RolePermission]] = select(RolePermission).where(
        RolePermission.role_id == role_id,
        RolePermission.permission_id == permission_id,
    )
    if db.scalar(stmt) is not None:
        return

    db.add(RolePermission(role_id=role_id, permission_id=permission_id))
    db.flush()


def _get_or_create_admin_user(
    db: Session,
    tenant: Tenant,
    branch: Branch,
    settings: Settings,
) -> User:
    stmt: Select[tuple[User]] = select(User).where(User.email == settings.seed_admin_email)
    user = db.scalar(stmt)
    if user is not None:
        user.tenant_id = tenant.id
        user.full_name = settings.seed_admin_full_name
        user.is_active = True
        user.is_superadmin = False
        if not user.password_hash:
            user.password_hash = hash_password(settings.seed_admin_password)
        db.add(user)
        db.flush()
        assign_branch_to_user(db, user, branch)
        return user

    user = User(
        tenant_id=tenant.id,
        branch_id=branch.id,
        email=settings.seed_admin_email,
        full_name=settings.seed_admin_full_name,
        password_hash=hash_password(settings.seed_admin_password),
        is_active=True,
        is_superadmin=False,
    )
    db.add(user)
    db.flush()
    return user
def seed_demo_data(
    db: Session,
    settings: Settings,
    plugins: Sequence[LoadedPlugin],
) -> dict[str, str]:
    tenant = _get_or_create_tenant(db, settings)
    branch = _get_or_create_branch(db, tenant, settings)
    role = _get_or_create_role(db, tenant)

    plugin_permissions = [
        plugin.manifest.permissions
        for plugin in plugins
        if plugin.manifest is not None
    ]
    permission_names = sorted(set(BASE_PERMISSIONS).union(*plugin_permissions))
    for permission_name in permission_names:
        permission = _get_or_create_permission(db, permission_name)
        _ensure_role_permission(db, role.id, permission.id)

    user = _get_or_create_admin_user(db, tenant, branch, settings)
    assign_role_to_user(db, user=user, role=role)
    sync_plugin_registry(db, list(plugins))
    db.commit()

    return {
        "tenant_id": tenant.id,
        "branch_id": branch.id,
        "role_id": role.id,
        "user_id": user.id,
        "user_email": user.email,
    }


def main() -> None:
    settings = get_settings()
    session_factory = build_session_factory(settings)
    manifest_registry = PluginManifestRegistry(settings.plugins_dir)
    manifest_registry.discover()
    runtime = PluginRuntime(manifest_registry)
    runtime.load()

    with session_factory() as db:
        result = seed_demo_data(db, settings, runtime.list_results())

    print("Seed demo completed")
    print(f"tenant_id={result['tenant_id']}")
    print(f"branch_id={result['branch_id']}")
    print(f"user_id={result['user_id']}")
    print(f"user_email={result['user_email']}")


if __name__ == "__main__":
    main()
