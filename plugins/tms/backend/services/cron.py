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

    @dramatiq.actor(periodic=timedelta(minutes=5))
    def sync_salidas_hoy_task() -> None:
        from systutor.core.database import build_engine, build_session_factory

        settings = Settings()
        SessionLocal = build_session_factory(settings)
        build_engine(settings)
        db = SessionLocal()
        try:
            client = LegacyApiClient(
                settings.legacy_api_base_url,
                settings.legacy_api_token,
                timeout_seconds=60,
            )
            asyncio.run(sync_salidas_hoy(db, client))
            db.commit()
        finally:
            db.close()
