from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session, get_settings_dep
from apps.api.app.core.config import Settings
from apps.api.app.core.errors import AuthenticationError
from apps.api.app.kernel.audit.service import record_audit
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.auth.security import decode_access_token
from apps.api.app.kernel.auth.service import get_user_by_id
from apps.api.app.kernel.permissions.service import user_has_permission

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings_dep),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

    try:
        payload = decode_access_token(credentials.credentials, settings)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    user = get_user_by_id(db, subject)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not available")

    request.state.current_user_id = user.id
    request.state.current_tenant_id = user.tenant_id
    request.state.current_branch_id = user.branch_id
    return user


def require_permission(permission_name: str) -> Callable[..., User]:
    def dependency(
        request: Request,
        db: Session = Depends(get_db_session),
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.is_superadmin or user_has_permission(db, current_user.id, permission_name):
            return current_user

        record_audit(
            db,
            tenant_id=current_user.tenant_id,
            branch_id=current_user.branch_id,
            actor_user_id=current_user.id,
            actor_type="user",
            module="core",
            action="permission.denied",
            entity_type="permission",
            entity_id=permission_name,
            result="denied",
            correlation_id=getattr(request.state, "correlation_id", None),
            request_id=getattr(request.state, "request_id", None),
            details={"permission": permission_name},
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    return dependency
