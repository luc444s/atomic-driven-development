from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import select
from systutor.core.database import build_session_factory
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.models import Branch, Tenant

from apps.api.app.config import get_settings
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.services.sync import sync_salidas_hoy

logger = logging.getLogger("tms.cron")


def _resolver_contexto(db):
    settings = get_settings()
    tenant = db.scalar(select(Tenant).where(Tenant.slug == settings.seed_demo_tenant_slug))
    branch = None
    actor = None
    if tenant is not None:
        branch = db.scalar(
            select(Branch).where(
                Branch.tenant_id == tenant.id,
                Branch.code == settings.seed_demo_branch_code,
            )
        )
        actor = db.scalar(select(User).where(User.email == settings.seed_admin_email))
    return tenant, branch, actor


def sync_salidas_hoy_once() -> dict:
    settings = get_settings()
    session_factory = build_session_factory(settings)
    client = LegacyApiClient(
        settings.legacy_api_base_url,
        settings.legacy_api_token,
        timeout_seconds=60,
    )
    with session_factory() as db:
        tenant, branch, actor = _resolver_contexto(db)
        result = asyncio.run(
            sync_salidas_hoy(
                db,
                client,
                tenant=tenant,
                branch=branch,
                actor_user_id=actor.id if actor is not None else None,
            )
        )
        db.commit()
        return result


def run_scheduler(interval: timedelta = timedelta(minutes=5)) -> None:
    """Loop del daemon: corre el sync de salidas cada `interval` minutos."""
    import time

    logger.info("Inicio scheduler TMS cada %s", interval)
    while True:
        try:
            result = sync_salidas_hoy_once()
            logger.info("sync salidas -> %s", result)
        except Exception as exc:  # pragma: no cover - loop vivo
            logger.exception("Fallo en corrida del sync salidas: %s", exc)
        time.sleep(interval.total_seconds())
