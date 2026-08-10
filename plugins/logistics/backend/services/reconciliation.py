from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.dto.reconciliation import (
    InventoryDiscrepancyRead,
    ReconciliationLineRead,
    SessionReconciliationRead,
)
from plugins.logistics.backend.integrations.stock import get_warehouse_balances
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsInventoryDiscrepancy,
    LogisticsLoadSerialAssignment,
    LogisticsOperation,
    LogisticsOperationItem,
    LogisticsSessionReconciliation,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.services.rules import (
    ensure_session_can_close,
    has_open_discrepancies,
)
from plugins.productos.backend.models import Product


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


def _get_latest_transfer_in_operation(
    db: Session, *, session_id: str
) -> LogisticsOperation | None:
    return db.scalar(
        select(LogisticsOperation)
        .where(
            LogisticsOperation.session_id == session_id,
            LogisticsOperation.movement_type == "TRANSFER_IN",
            LogisticsOperation.status == "CONFIRMED",
        )
        .order_by(
            LogisticsOperation.performed_at.desc().nulls_last(),
            LogisticsOperation.created_at.desc(),
        )
    )


def _list_transfer_in_items(
    db: Session, *, operation_id: str
) -> list[LogisticsOperationItem]:
    return list(
        db.scalars(
            select(LogisticsOperationItem)
            .where(LogisticsOperationItem.operation_id == operation_id)
            .order_by(LogisticsOperationItem.created_at.asc())
        ).all()
    )


def _product_name(db: Session, *, product_id: str) -> str:
    product = db.scalar(select(Product).where(Product.id == product_id))
    return product.name if product is not None else product_id


_VEHICLE_PHYSICAL_STATES = ("CARGA_EN_VEHICULO", "EN_RUTA")


def _merge_expected_lines_with_physical_counts(
    *,
    expected_lines: list[ReconciliationLineRead],
    physical_counts: dict[str, float],
    product_name_resolver,
) -> list[ReconciliationLineRead]:
    merged = [
        ReconciliationLineRead(
            product_id=line.product_id,
            product_name=line.product_name,
            expected_quantity=float(line.expected_quantity),
        )
        for line in expected_lines
    ]
    existing_pids = {line.product_id for line in merged}
    for pid, qty in sorted(physical_counts.items()):
        if qty <= 0 or pid in existing_pids:
            continue
        merged.append(
            ReconciliationLineRead(
                product_id=pid,
                product_name=product_name_resolver(pid),
                expected_quantity=qty,
            )
        )
    return merged


def _count_physical_vehicle_cylinders(
    db: Session, *, session_id: str
) -> dict[str, float]:
    """Cuenta cilindros físicamente en el vehículo por producto.

    Usa assignments CONFIRMED/DELIVERY_SELECTED en estados de vehículo para
    reflejar lo que el chofer tiene físicamente al momento de la conciliación.
    """
    rows = db.execute(
        select(
            LogisticsLoadSerialAssignment.product_id,
            func.count(LogisticsLoadSerialAssignment.cylinder_id),
        )
        .join(
            LogisticsCylinder,
            LogisticsCylinder.id == LogisticsLoadSerialAssignment.cylinder_id,
        )
        .where(
            LogisticsLoadSerialAssignment.session_id == session_id,
            LogisticsLoadSerialAssignment.assignment_status.in_(
                {"CONFIRMED", "DELIVERY_SELECTED"}
            ),
            LogisticsCylinder.current_state.in_(_VEHICLE_PHYSICAL_STATES),
        )
        .group_by(LogisticsLoadSerialAssignment.product_id)
    ).all()
    return {product_id: float(count or 0) for product_id, count in rows}


def get_reconciliation_view(
    db: Session, *, session: LogisticsVehicleSession
) -> SessionReconciliationRead:
    latest_transfer_in = _get_latest_transfer_in_operation(db, session_id=session.id)
    physical_counts = _count_physical_vehicle_cylinders(db, session_id=session.id)
    if latest_transfer_in is not None:
        expected_lines = [
            ReconciliationLineRead(
                product_id=item.product_id,
                product_name=item.product_name,
                expected_quantity=float(item.quantity),
            )
            for item in _list_transfer_in_items(db, operation_id=latest_transfer_in.id)
        ]
        # Complementar con conteo físico de cilindros en el vehículo.
        # El transfer_in puede no incluir cilindros recogidos en ruta.
        if physical_counts:
            expected_lines = _merge_expected_lines_with_physical_counts(
                expected_lines=expected_lines,
                physical_counts=physical_counts,
                product_name_resolver=lambda pid: _product_name(db, product_id=pid),
            )
    else:
        balances = get_warehouse_balances(
            db,
            tenant_id=session.tenant_id,
            warehouse_id=session.mobile_warehouse_id,
        ).items
        balance_map = {
            balance.product_id: balance for balance in balances
        }
        # Conteo físico de cilindros en el vehículo (CARGA_EN_VEHICULO / EN_RUTA).
        # Complementa los balances del almacén: los cilindros recogidos en ruta
        # que aún no impactaron stock o que están físicamente en el camión deben
        # aparecer en la conciliación para que el chofer los cuente.
        physical_counts = _count_physical_vehicle_cylinders(db, session_id=session.id)
        all_product_ids = set(balance_map) | set(physical_counts)
        expected_lines = []
        for pid in sorted(all_product_ids):
            balance = balance_map.get(pid)
            qty = float(balance.quantity) if balance is not None else 0.0
            qty += physical_counts.get(pid, 0.0)
            if qty <= 0:
                continue
            name = balance.product_name if balance is not None else (
                _product_name(db, product_id=pid)
            )
            expected_lines.append(
                ReconciliationLineRead(
                    product_id=pid,
                    product_name=name,
                    expected_quantity=qty,
                )
            )
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
    for expected_line in expected_lines:
        discrepancy = discrepancy_map.get(expected_line.product_id)
        lines.append(
            ReconciliationLineRead(
                product_id=expected_line.product_id,
                product_name=expected_line.product_name,
                expected_quantity=expected_line.expected_quantity,
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
    expected_lines = get_reconciliation_view(db, session=session).lines
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
    for line in expected_lines:
        expected = float(line.expected_quantity)
        counted = counted_by_product.get(line.product_id, 0.0)
        diff = counted - expected
        if abs(diff) > 0.0001:
            reconciliation.status = "HAS_DIFF"
            discrepancy = LogisticsInventoryDiscrepancy(
                reconciliation_id=reconciliation.id,
                product_id=line.product_id,
                product_name=line.product_name,
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
    if reconciliation.status == "MATCHED":
        close_vehicle_session(
            db,
            session=session,
            notes=payload.notes,
            action_context=action_context,
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

    from plugins.logistics.backend.services.load_serials import (
        release_active_serial_assignments,
    )

    release_active_serial_assignments(
        db,
        session_id=session.id,
        release_reason="SESSION_CLOSED",
    )

    from plugins.logistics.backend.services.load_plans import (
        _return_session_cylinders_to_warehouse,
    )
    from plugins.logistics.backend.services.planning_reservations import (
        sync_reservation_from_session,
    )

    sync_reservation_from_session(db, session=session)

    transit_remaining = db.scalar(
        select(func.count(LogisticsCylinder.id)).where(
            LogisticsCylinder.tenant_id == session.tenant_id,
            LogisticsCylinder.session_id == session.id,
            LogisticsCylinder.current_state.in_(
                ("CARGA_EN_VEHICULO", "EN_RUTA")
            ),
        )
    )
    latest_transfer_in = _get_latest_transfer_in_operation(db, session_id=session.id)
    if transit_remaining and transit_remaining > 0 and latest_transfer_in is not None:
        _return_session_cylinders_to_warehouse(
            db,
            session=session,
            warehouse_id=session.origin_warehouse_id,
            notes=notes,
            action_context=action_context,
        )
        transit_remaining = db.scalar(
            select(func.count(LogisticsCylinder.id)).where(
                LogisticsCylinder.tenant_id == session.tenant_id,
                LogisticsCylinder.session_id == session.id,
                LogisticsCylinder.current_state.in_(
                    ("CARGA_EN_VEHICULO", "EN_RUTA")
                ),
            )
        )
    if transit_remaining and transit_remaining > 0:
        raise ValueError(
            f"No se puede cerrar la sesión: {transit_remaining} cilindros "
            f"aún en tránsito. Ejecuta el retorno primero."
        )

    db.execute(
        update(LogisticsCylinder)
        .where(
            LogisticsCylinder.tenant_id == session.tenant_id,
            LogisticsCylinder.session_id == session.id,
        )
        .values(session_id=None)
    )

    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.close",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"reconciliation_id": reconciliation.id},
    )
    return session
