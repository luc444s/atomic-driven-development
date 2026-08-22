from __future__ import annotations

import re

from sqlalchemy import Select, select
from sqlalchemy.orm import Session
from systutor.kernel.auth.models import User
from systutor.kernel.auth.security import hash_password
from systutor.kernel.permissions.models import Role
from systutor.kernel.permissions.service import assign_role_to_user
from systutor.kernel.tenants.models import Branch, Tenant
from systutor.kernel.tenants.service import assign_branch_to_user

_DRIVER_ROLE_NAME = "driver"
_DRIVER_DOMAIN = "@oxipur.com"
_DNI_DIRTY_PREFIX = re.compile(r"^D(\d{8}?)\s*-", re.IGNORECASE)
_DNI_INLINE = re.compile(r"\bD(\d{8})\b", re.IGNORECASE)


def driver_email(dni: str) -> str:
    return f"{dni}{_DRIVER_DOMAIN}"


def normalize_driver_dni(dnichofer: str, transportista: str = "") -> str:
    """Resuelve el DNI real del chofer. El legacy guarda nombres sucios:
    'D44973574-HIRVING...' en Transportista y dnichofer inconsistente (4492/10725/1164).
    Prioridad: prefijo 'D<8dígitos>' del nombre; fallback dnichofer si tiene 8 dígitos.
    """
    if transportista:
        m = _DNI_DIRTY_PREFIX.search(transportista.strip())
        if m:
            return m.group(1)
        m = _DNI_INLINE.search(transportista.strip())
        if m:
            return m.group(1)
    clean = (dnichofer or "").strip()
    if re.fullmatch(r"\d{8}", clean):
        return clean
    return ""


def _get_or_create_driver_role(db: Session, tenant: Tenant) -> Role:
    stmt: Select[tuple[Role]] = select(Role).where(
        Role.tenant_id == tenant.id,
        Role.name == _DRIVER_ROLE_NAME,
    )
    role = db.scalar(stmt)
    if role is not None:
        return role
    role = Role(
        tenant_id=tenant.id,
        name=_DRIVER_ROLE_NAME,
        description="Conductor — operaciones de ruta y consulta de catalogo",
    )
    db.add(role)
    db.flush()
    return role


def ensure_driver_user(
    db: Session,
    *,
    tenant: Tenant,
    branch: Branch | None,
    dni: str,
    full_name: str,
    password_hash: str | None = None,
) -> User:
    dni = dni.strip()
    email = driver_email(dni)
    stmt: Select[tuple[User]] = select(User).where(User.email == email)
    user = db.scalar(stmt)
    if user is not None:
        return user

    user = User(
        tenant_id=tenant.id,
        branch_id=None,
        email=email,
        full_name=full_name.strip() or f"Conductor {dni}",
        password_hash=password_hash or hash_password(dni),
        is_active=True,
        category="driver",
    )
    db.add(user)
    db.flush()
    assign_branch_to_user(db, user, branch)
    role = _get_or_create_driver_role(db, tenant)
    assign_role_to_user(db, user=user, role=role)
    db.flush()
    return user