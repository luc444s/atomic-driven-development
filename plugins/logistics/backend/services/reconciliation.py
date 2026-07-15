from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.dto.reconciliation import (
    InventoryDiscrepancyRead,
    ReconciliationLineRead,
    SessionReconciliationRead,
)
from plugins.logistics.backend.integrations.stock import get_warehouse_balances
from plugins.logistics.backend.models import (
    LogisticsInventoryDiscrepancy,
    LogisticsSessionReconciliation,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.services.rules import (
    ensure_session_can_close,
    has_open_discrepancies,
)


def _get_reconciliation(db: Session, *, session_id: str) -> LogisticsSessionReconciliation | None:
    return db.scalar(
        select(LogisticsSessionReconciliation)
        .where(LogisticsSessionReconciliation.session_id == session_id)
        .order_by(LogisticsSessionReconciliation.updated_at.desc())
    )


def _list_discrepancies(
    db: Session, *, reconciliation_id: str
) -> list[LogisticsInventoryDiscrepancy]:
    return list(
        db.scalars(
            select(LogisticsInventoryDiscrepancy)
            .where(LogisticsInventoryDiscrepancy.reconciliation_id == reconciliation_id)
            .order_by(LogisticsInventoryDiscrepancy.product_name.asc())
        ).all()
    )


def get_reconciliation_view(
    db: Session, *, session: LogisticsVehicleSession
) -> SessionReconciliationRead:
    balances = get_warehouse_balances(
        db,
        tenant_id=session.tenant_id,
        warehouse_id=session.mobile_warehouse_id,
    ).items
    reconciliation = _get_reconciliation(db, session_id=session.id)
    discrepancy_map: dict[str, LogisticsInventoryDiscrepancy] = {}
    discrepancies: list[InventoryDiscrepancyRead] = []
    if reconciliation is not None:
        stored = _list_discrepancies(db, reconciliation_id=reconciliation.id)
        discrepancy_map = {item.product_id: item for item in stored}
        discrepancies = [
            InventoryDiscrepancyRead(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                expected_quantity=float(item.expected_quantity),
                counted_quantity=float(item.counted_quantity),
                difference_quantity=float(item.difference_quantity),
                status=item.status,
                resolution_notes=item.resolution_notes,
            )
            for item in stored
        ]
    lines = []
    for balance in balances:
        discrepancy = discrepancy_map.get(balance.product_id)
        lines.append(
            ReconciliationLineRead(
                product_id=balance.product_id,
                product_name=balance.product_name,
                expected_quantity=float(balance.quantity),
                counted_quantity=float(discrepancy.counted_quantity)
                if discrepancy is not None
                else None,
                difference_quantity=float(discrepancy.difference_quantity)
                if discrepancy is not None
                else None,
            )
        )
    status = reconciliation.status if reconciliation is not None else "AWAITING_RECONCILIATION"
    can_close = reconciliation is not None and reconciliation.status == "MATCHED"
    return SessionReconciliationRead(
        id=reconciliation.id if reconciliation is not None else None,
        session_id=session.id,
        status=status,
        counted_by=reconciliation.counted_by if reconciliation is not None else None,
        counted_at=reconciliation.counted_at if reconciliation is not None else None,
        notes=reconciliation.notes if reconciliation is not None else None,
        can_close=can_close,
        lines=lines,
        discrepancies=discrepancies,
    )


def record_reconciliation_count(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    payload,
    action_context: LogisticsActionContext,
) -> SessionReconciliationRead:
    if session.status != "AWAITING_RECONCILIATION":
        raise ValueError("La jornada debe estar en AWAITING_RECONCILIATION para contar")
    balances = get_warehouse_balances(
        db,
        tenant_id=session.tenant_id,
        warehouse_id=session.mobile_warehouse_id,
    ).items
    counted_by_product = {item.product_id: float(item.counted_quantity) for item in payload.items}
    reconciliation = _get_reconciliation(db, session_id=session.id)
    if reconciliation is None:
        reconciliation = LogisticsSessionReconciliation(
            tenant_id=session.tenant_id,
            session_id=session.id,
        )
        db.add(reconciliation)
        db.flush()
    else:
        db.execute(
            delete(LogisticsInventoryDiscrepancy).where(
                LogisticsInventoryDiscrepancy.reconciliation_id == reconciliation.id
            )
        )
    reconciliation.counted_by = action_context.actor_user_id
    reconciliation.counted_at = datetime.now(UTC)
    reconciliation.notes = payload.notes
    reconciliation.status = "MATCHED"
    db.add(reconciliation)
    for balance in balances:
        expected = float(balance.quantity)
        counted = counted_by_product.get(balance.product_id, 0.0)
        diff = counted - expected
        if abs(diff) > 0.0001:
            reconciliation.status = "HAS_DIFF"
            discrepancy = LogisticsInventoryDiscrepancy(
                reconciliation_id=reconciliation.id,
                product_id=balance.product_id,
                product_name=balance.product_name,
                expected_quantity=expected,
                counted_quantity=counted,
                difference_quantity=diff,
                status="OPEN",
            )
            db.add(discrepancy)
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.reconciliation.count",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"items": len(payload.items), "status": reconciliation.status},
    )
    return get_reconciliation_view(db, session=session)


def close_vehicle_session(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleSession:
    reconciliation = _get_reconciliation(db, session_id=session.id)
    if reconciliation is None:
        raise ValueError("La jornada no tiene conciliacion registrada")
    ensure_session_can_close(
        session,
        has_open_discrepancies=has_open_discrepancies(db, reconciliation_id=reconciliation.id),
        reconciliation_status=reconciliation.status,
    )
    reconciliation.status = "CLOSED"
    reconciliation.closed_by = action_context.actor_user_id
    reconciliation.closed_at = datetime.now(UTC)
    if notes:
        reconciliation.notes = notes
    db.add(reconciliation)
    session.status = "CLOSED"
    session.closed_at = datetime.now(UTC)
    session.closing_notes = notes or session.closing_notes
    session.updated_by = action_context.actor_user_id
    db.add(session)
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.close",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"reconciliation_id": reconciliation.id},
    )
    return session
