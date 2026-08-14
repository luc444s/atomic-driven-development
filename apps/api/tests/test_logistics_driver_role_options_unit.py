from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from apps.api.app.core.database import Base
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.permissions.models import Role, UserRole
from plugins.logistics.backend.services.sessions import list_driver_options


def _make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _add_user(db: Session, *, full_name: str, active: bool = True) -> User:
    user = User(
        tenant_id="tenant-1",
        email=f"{full_name.replace(' ', '-').lower()}@example.com",
        full_name=full_name,
        password_hash="x",
        is_active=active,
    )
    db.add(user)
    db.flush()
    return user


def _add_role(db: Session, *, name: str, active: bool = True) -> Role:
    role = Role(tenant_id="tenant-1", name=name, is_active=active)
    db.add(role)
    db.flush()
    return role


def _assign(db: Session, *, user: User, role: Role) -> None:
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()


def test_driver_options_filters_by_driver_role_not_category() -> None:
    db = _make_session()
    driver_role = _add_role(db, name="driver")
    admin_role = _add_role(db, name="admin")

    driver_by_role = _add_user(db, full_name="Conductor Rol")
    _assign(db, user=driver_by_role, role=driver_role)

    driver_by_category_only = _add_user(db, full_name="Categoria Legacy")
    driver_by_category_only.category = "driver"

    admin = _add_user(db, full_name="Admin")
    _assign(db, user=admin, role=admin_role)

    inactive_driver = _add_user(db, full_name="Conductor Inactivo", active=False)
    _assign(db, user=inactive_driver, role=driver_role)

    options = list_driver_options(db, tenant_id="tenant-1")

    assert [u.full_name for u in options] == ["Conductor Rol"]


def test_driver_options_excludes_inactive_driver_role() -> None:
    db = _make_session()
    driver_role = _add_role(db, name="driver", active=False)
    user = _add_user(db, full_name="Conductor")
    _assign(db, user=user, role=driver_role)

    assert list_driver_options(db, tenant_id="tenant-1") == []


def test_driver_options_excludes_other_tenant_users() -> None:
    db = _make_session()
    other_tenant_driver_role = Role(tenant_id="tenant-2", name="driver")
    db.add(other_tenant_driver_role)
    db.flush()

    other_tenant_user = User(
        tenant_id="tenant-2",
        email="other@example.com",
        full_name="Conductor Ajeno",
        password_hash="x",
        is_active=True,
    )
    db.add(other_tenant_user)
    db.flush()
    _assign(db, user=other_tenant_user, role=other_tenant_driver_role)

    assert list_driver_options(db, tenant_id="tenant-1") == []
    assert [u.full_name for u in list_driver_options(db, tenant_id="tenant-2")] == [
        "Conductor Ajeno"
    ]
