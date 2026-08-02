"""Ejecución única del sweep de exceso de contratos (SPEC 0023AD.4).

Se llama desde cron (medianoche) o manualmente:
    .venv/bin/python tools/dev/contract_excess_sweep.py
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text

from apps.api.app.core.config import get_settings
from apps.api.app.core.database import build_session_factory
from plugins.logistics.backend.services.contracts_excess import sweep_contract_excess


def main() -> None:
    settings = get_settings()
    session_factory = build_session_factory(settings)
    with session_factory() as db:
        tenant_id = str(
            db.execute(text("SELECT id FROM tenants ORDER BY created_at LIMIT 1")).scalar_one()
        )
        result = sweep_contract_excess(db, tenant_id=tenant_id, now=datetime.now(UTC))
    print(f"[{datetime.now(UTC).isoformat()}] sweep: {result}", flush=True)


if __name__ == "__main__":
    main()
