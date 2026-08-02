"""Workers del plugin logistics (SPEC 0023AD.4 — motor de exceso de contratos).

El actor se registra al importar este módulo. Lanzamiento del worker
(proceso separado, scheduling externo vía cron/systemd cada hora):

    .venv/bin/dramatiq apps.api.app.kernel.events.tasks plugins.logistics.backend.tasks

La lógica es idempotente y protegida contra ejecución concurrente
(lock optimista sobre el tracking).
"""
from __future__ import annotations

import importlib
from datetime import UTC, datetime

from apps.api.app.core.config import get_settings
from apps.api.app.core.database import build_session_factory
from apps.api.app.kernel.tasks.broker import configure_dramatiq_broker

settings = get_settings()
configure_dramatiq_broker(settings)


def _run_excess_sweep_impl() -> dict[str, int]:
    session_factory = build_session_factory(settings)
    from sqlalchemy import text

    from plugins.logistics.backend.services.contracts_excess import sweep_contract_excess

    with session_factory() as db:
        tenant_id = str(
            db.execute(text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")).scalar_one()
        )
        result = sweep_contract_excess(db, tenant_id=tenant_id, now=datetime.now(UTC))
    return result


dramatiq = importlib.import_module("dramatiq")
contract_excess_sweep = dramatiq.actor(queue_name="contracts")(_run_excess_sweep_impl)
