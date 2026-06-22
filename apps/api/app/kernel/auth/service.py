from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.auth.security import create_access_token, verify_password
from apps.api.app.kernel.permissions.service import list_user_permissions


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt: Select[tuple[User]] = select(User).where(User.email == email)
    return db.scalar(stmt)


def get_user_by_id(db: Session, user_id: str) -> User | None:
    stmt: Select[tuple[User]] = select(User).where(User.id == user_id)
    return db.scalar(stmt)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def mark_user_logged_in(db: Session, user: User) -> None:
    user.last_login_at = datetime.now(UTC)
    db.add(user)
    db.flush()


def build_user_profile(db: Session, user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "branch_id": user.branch_id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superadmin": user.is_superadmin,
        "permissions": list_user_permissions(db, user.id),
    }


def issue_access_token(settings, user: User) -> str:
    return create_access_token(
        settings=settings,
        subject=user.id,
        email=user.email,
        tenant_id=user.tenant_id,
        branch_id=user.branch_id,
        is_superadmin=user.is_superadmin,
    )
