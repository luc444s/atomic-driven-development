from __future__ import annotations

from plugins.logistics.backend.models import LogisticsCylinder, LogisticsCylinderState
from plugins.logistics.backend.services.cylinders import summarize_cylinders


def test_full_summary_excludes_cryogenic_tanks(db_session, app) -> None:
    seeded_demo = app.state.settings
    # Reuse real tenant data so FK-bearing rows stay coherent enough for SQLite tests.
    from apps.api.app.commands.seed_demo import seed_demo_data

    seeded = seed_demo_data(db_session, seeded_demo, app.state.plugin_runtime.list_results())

    db_session.merge(LogisticsCylinderState(code="LLENADO_OK", is_final=False, description="Listo"))

    db_session.add(
        LogisticsCylinder(
            tenant_id=seeded["tenant_id"],
            serial="SUM-REAL-001",
            container_type="CYLINDER",
            current_state="LLENADO_OK",
        )
    )
    db_session.add(
        LogisticsCylinder(
            tenant_id=seeded["tenant_id"],
            serial="SUM-TANK-001",
            container_type="CRYOGENIC_TANK",
            current_state="LLENADO_OK",
        )
    )
    db_session.commit()

    summary = {
        item.state: item.count
        for item in summarize_cylinders(db_session, tenant_id=seeded["tenant_id"])
    }

    assert summary["LLENADO_OK"] == 1
