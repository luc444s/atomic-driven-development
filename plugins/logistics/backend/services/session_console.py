from __future__ import annotations

from sqlalchemy.orm import Session

from plugins.logistics.backend.dto.session_console import SessionConsoleContextRead
from plugins.logistics.backend.integrations.stock import get_warehouse_balances
from plugins.logistics.backend.services.cylinders import summarize_serialized_cylinders_by_warehouse
from plugins.logistics.backend.services.load_plans import (
    build_load_plan_read,
    get_load_plan,
    list_load_plan_items,
)
from plugins.logistics.backend.services.operational_summary import build_operational_summary
from plugins.logistics.backend.services.reconciliation import get_reconciliation_view
from plugins.logistics.backend.services.sessions import get_vehicle_session
from plugins.logistics.backend.services.snapshots import build_session_snapshot


def build_session_console_context(
    db: Session,
    *,
    tenant_id: str,
    session_id: str,
) -> SessionConsoleContextRead:
    session = get_vehicle_session(db, tenant_id=tenant_id, session_id=session_id)
    if session is None:
        raise LookupError("Jornada no encontrada")

    load_plan = get_load_plan(db, session_id=session.id)
    items = list_load_plan_items(db, load_plan_id=load_plan.id) if load_plan is not None else []

    operational_summary = None
    try:
        operational_summary = build_operational_summary(db, session=session)
    except (LookupError, ValueError):
        # Estados donde el resumen operativo no aplica: la consola
        # degrada la seccion en vez de romper todo el contexto.
        operational_summary = None

    return SessionConsoleContextRead(
        session=build_session_snapshot(db, session=session),
        load_plan=build_load_plan_read(
            db,
            session=session,
            load_plan=load_plan,
            items=items,
        ),
        reconciliation=get_reconciliation_view(db, session=session),
        operational_summary=operational_summary,
        origin_balances=get_warehouse_balances(
            db,
            tenant_id=tenant_id,
            warehouse_id=session.origin_warehouse_id,
            ensure_catalog=True,
        ),
        mobile_balances=get_warehouse_balances(
            db,
            tenant_id=tenant_id,
            warehouse_id=session.mobile_warehouse_id,
            ensure_catalog=True,
        ),
        origin_serialized=summarize_serialized_cylinders_by_warehouse(
            db,
            tenant_id=tenant_id,
            warehouse_id=session.origin_warehouse_id,
        ),
    )
