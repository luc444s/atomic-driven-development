from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from plugins.tms.backend import ports
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.services.sync import sync_salidas_hoy

logger = logging.getLogger("tms.cron")


def sync_salidas_hoy_once() -> dict:
    p = ports.get_ports()
    settings = p.get_settings()
    session_factory = p.session_factory()
    client = LegacyApiClient(
        settings.legacy_api_base_url,
        settings.legacy_api_token,
        timeout_seconds=60,
    )
    with session_factory() as db:
        ctx = p.resolve_sync_context(db)
        result = asyncio.run(
            sync_salidas_hoy(
                db,
                client,
                tenant_id=ctx.tenant.id if ctx.tenant else None,
                branch_id=ctx.branch.id if ctx.branch else None,
                actor_user_id=ctx.actor_user_id,
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
