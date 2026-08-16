from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from systutor.core.lifecycle import ensure_session_factory
from systutor.kernel.auth.dependencies import get_current_tenant_context, require_permission
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.context import TenantContext

from plugins.logistics.backend.dto.route_context import RouteContextRead
from plugins.logistics.backend.services.route_context import build_route_context

router = APIRouter(prefix="/vehicle-sessions", tags=["logistics-route-context"])

TENANT_CONTEXT = Depends(get_current_tenant_context)
REQUIRE_SESSION_READ = Depends(require_permission("logistics.session.read"))


def _make_sync_session(request: Request) -> Session:
    factory = ensure_session_factory(request.app)
    return factory()


async def _run_sync_readonly[T](
    request: Request,
    fn: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    def _call() -> T:
        db = _make_sync_session(request)
        try:
            return fn(db, *args, **kwargs)
        finally:
            db.close()

    return await asyncio.to_thread(_call)


@router.get("/{session_id}/route-context", response_model=RouteContextRead)
async def get_route_context(
    session_id: str,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_READ,
) -> RouteContextRead:
    try:
        return await _run_sync_readonly(
            request,
            build_route_context,
            tenant_id=tenant_context.current_tenant_id,
            session_id=session_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
