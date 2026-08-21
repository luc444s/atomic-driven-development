from __future__ import annotations

import asyncio
from datetime import timedelta

try:
    import dramatiq  # type: ignore

    _HAS_DRAMATIQ = True
except Exception:  # pragma: no cover - sin broker configurado
    _HAS_DRAMATIQ = False

from apps.api.app.config import GasSettings as Settings
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.services.sync import sync_salidas_hoy

if _HAS_DRAMATIQ:

    def _resolver_contexto(db):
        from sqlalchemy import select
        from systutor.kernel.auth.models import User
        from systutor.kernel.tenants.models import Branch, Tenant

        settings = Settings()
        stmt = select(Tenant).where(Tenant.slug == settings.seed_demo_tenant_slug)
        tenant = db.scalar(stmt)
        branch = None
        actor = None
        if tenant is not None:
            stmt_branch = select(Branch).where(
                Branch.tenant_id == tenant.id,
                Branch.code == settings.seed_demo_branch_code,
            )
            branch = db.scalar(stmt_branch)
            stmt_user = select(User).where(User.email == settings.seed_admin_email)
            actor = db.scalar(stmt_user)
        return tenant, branch, actor

    @dramatiq.actor(periodic=timedelta(minutes=5))
    def sync_salidas_hoy_task() -> None:
        from systutor.core.database import build_engine, build_session_factory

        settings = Settings()
        SessionLocal = build_session_factory(settings)
        build_engine(settings)
        db = SessionLocal()
        try:
            tenant, branch, actor = _resolver_contexto(db)
            client = LegacyApiClient(
                settings.legacy_api_base_url,
                settings.legacy_api_token,
                timeout_seconds=60,
            )
            asyncio.run(
                sync_salidas_hoy(
                    db,
                    client,
                    tenant=tenant,
                    branch=branch,
                    actor_user_id=actor.id if actor is not None else None,
                )
            )
            db.commit()
        finally:
            db.close()