from __future__ import annotations

from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.kernel.auth.models import User
from plugins.logistics.backend.dto.sessions import (
    SessionHistoryEntryRead,
    SessionStockSummaryRead,
    VehicleSessionDetailRead,
    VehicleSessionRead,
)
from plugins.logistics.backend.integrations.stock import get_warehouse_balances
from plugins.logistics.backend.models import (
    LogisticsOperation,
    LogisticsRouteOperation,
    LogisticsSessionReconciliation,
    LogisticsVehicle,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.logistics.backend.services.rules import (
    get_next_transition_blocker,
    get_session_start_queue_blocker,
    has_open_discrepancies,
)


def _get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.id == user_id))


def _get_vehicle(db: Session, vehicle_id: str) -> LogisticsVehicle:
    vehicle = db.scalar(select(LogisticsVehicle).where(LogisticsVehicle.id == vehicle_id))
    if vehicle is None:
        raise LookupError("Vehiculo no encontrado")
    return vehicle


def _get_warehouse(db: Session, warehouse_id: str) -> LogisticsWarehouse:
    warehouse = db.scalar(select(LogisticsWarehouse).where(LogisticsWarehouse.id == warehouse_id))
    if warehouse is None:
        raise LookupError("Warehouse no encontrado")
    return warehouse


def _build_stock_summary(
    db: Session, *, tenant_id: str, mobile_warehouse_id: str
) -> SessionStockSummaryRead:
    balances = get_warehouse_balances(
        db,
        tenant_id=tenant_id,
        warehouse_id=mobile_warehouse_id,
    )
    mobile_warehouse = _get_warehouse(db, mobile_warehouse_id)
    return SessionStockSummaryRead(
        warehouse_id=mobile_warehouse.id,
        warehouse_code=mobile_warehouse.code,
        warehouse_name=mobile_warehouse.name,
        total_products=len([item for item in balances.items if item.quantity > 0]),
        total_units=sum(float(item.quantity) for item in balances.items),
    )


def _get_latest_reconciliation(
    db: Session, *, session_id: str
) -> LogisticsSessionReconciliation | None:
    return db.scalar(
        select(LogisticsSessionReconciliation)
        .where(LogisticsSessionReconciliation.session_id == session_id)
        .order_by(LogisticsSessionReconciliation.updated_at.desc())
    )


def build_session_history(
    db: Session, *, session: LogisticsVehicleSession
) -> list[SessionHistoryEntryRead]:
    history: list[SessionHistoryEntryRead] = [
        SessionHistoryEntryRead(
            occurred_at=session.opened_at,
            category="session",
            label="Jornada creada",
        )
    ]
    if session.ready_at:
        history.append(
            SessionHistoryEntryRead(
                occurred_at=session.ready_at, category="session", label="Jornada lista para salir"
            )
        )
    if session.departed_at:
        history.append(
            SessionHistoryEntryRead(
                occurred_at=session.departed_at, category="session", label="Vehiculo salio"
            )
        )
    if session.returned_at:
        history.append(
            SessionHistoryEntryRead(
                occurred_at=session.returned_at, category="session", label="Vehiculo retorno"
            )
        )
    if session.closed_at:
        history.append(
            SessionHistoryEntryRead(
                occurred_at=session.closed_at, category="session", label="Jornada cerrada"
            )
        )

    operations = list(
        db.scalars(
            select(LogisticsOperation)
            .where(
                LogisticsOperation.session_id == session.id,
                LogisticsOperation.status == "CONFIRMED",
            )
            .order_by(
                LogisticsOperation.performed_at.asc().nulls_last(),
                LogisticsOperation.created_at.asc(),
            )
        ).all()
    )
    for operation in operations:
        history.append(
            SessionHistoryEntryRead(
                occurred_at=operation.performed_at or operation.created_at,
                category="operation",
                label=f"Operacion {operation.movement_type} confirmada",
            )
        )

    route_operations = list(
        db.scalars(
            select(LogisticsRouteOperation)
            .where(
                LogisticsRouteOperation.session_id == session.id,
                LogisticsRouteOperation.status == "CONFIRMED",
            )
            .order_by(
                LogisticsRouteOperation.performed_at.asc().nulls_last(),
                LogisticsRouteOperation.created_at.asc(),
            )
        ).all()
    )
    for route_operation in route_operations:
        history.append(
            SessionHistoryEntryRead(
                occurred_at=route_operation.performed_at or route_operation.created_at,
                category="route_operation",
                label=f"Operacion de ruta {route_operation.operation_type} confirmada",
            )
        )

    def _sort_key(item: SessionHistoryEntryRead):
        occurred_at = item.occurred_at
        if occurred_at.tzinfo is None:
            return occurred_at.replace(tzinfo=UTC)
        return occurred_at

    history.sort(key=_sort_key)
    return history


def _build_session_read(
    db: Session, *, session: LogisticsVehicleSession, include_history: bool
) -> VehicleSessionRead | VehicleSessionDetailRead:
    vehicle = _get_vehicle(db, session.vehicle_id)
    driver = _get_user(db, session.driver_id)
    origin = _get_warehouse(db, session.origin_warehouse_id)
    mobile = _get_warehouse(db, session.mobile_warehouse_id)
    stock_summary = _build_stock_summary(
        db, tenant_id=session.tenant_id, mobile_warehouse_id=session.mobile_warehouse_id
    )
    occupancy_percent = None
    max_weight = float(vehicle.useful_load or vehicle.capacity_weight or 0)
    if max_weight > 0 and session.loaded_weight_kg is not None:
        occupancy_percent = round((float(session.loaded_weight_kg) / max_weight) * 100, 1)

    reconciliation = _get_latest_reconciliation(db, session_id=session.id)
    start_queue_blocker = get_session_start_queue_blocker(db, session=session)
    next_transition_blocker = get_next_transition_blocker(
        session,
        has_open_discrepancies=(
            has_open_discrepancies(db, reconciliation_id=reconciliation.id)
            if reconciliation is not None
            else False
        ),
        reconciliation_status=reconciliation.status if reconciliation is not None else None,
        start_queue_blocker=start_queue_blocker,
    )

    history = build_session_history(db, session=session)
    last_activity = history[-1].label if history else None
    if include_history:
        return VehicleSessionDetailRead(
            id=session.id,
            vehicle_id=vehicle.id,
            vehicle_plate=vehicle.plate,
            driver_id=session.driver_id,
            driver_name=driver.full_name if driver else session.driver_id,
            origin_warehouse_id=origin.id,
            origin_warehouse_name=origin.name,
            mobile_warehouse_id=mobile.id,
            mobile_warehouse_code=mobile.code,
            mobile_warehouse_name=mobile.name,
            route_id=session.route_id,
            status=session.status,
            opened_at=session.opened_at,
            ready_at=session.ready_at,
            departed_at=session.departed_at,
            returned_at=session.returned_at,
            closed_at=session.closed_at,
            planned_weight_kg=(
                float(session.planned_weight_kg) if session.planned_weight_kg is not None else None
            ),
            loaded_weight_kg=(
                float(session.loaded_weight_kg) if session.loaded_weight_kg is not None else None
            ),
            occupancy_percent=occupancy_percent,
            last_activity=last_activity,
            can_depart=session.status == "READY_TO_DEPART",
            can_close=session.status == "AWAITING_RECONCILIATION",
            next_transition_allowed=next_transition_blocker is None,
            next_transition_blocker=next_transition_blocker,
            current_stock=stock_summary,
            history=history,
        )
    return VehicleSessionRead(
        id=session.id,
        vehicle_id=vehicle.id,
        vehicle_plate=vehicle.plate,
        driver_id=session.driver_id,
        driver_name=driver.full_name if driver else session.driver_id,
        origin_warehouse_id=origin.id,
        origin_warehouse_name=origin.name,
        mobile_warehouse_id=mobile.id,
        mobile_warehouse_code=mobile.code,
        mobile_warehouse_name=mobile.name,
        route_id=session.route_id,
        status=session.status,
        opened_at=session.opened_at,
        ready_at=session.ready_at,
        departed_at=session.departed_at,
        returned_at=session.returned_at,
        closed_at=session.closed_at,
        planned_weight_kg=(
            float(session.planned_weight_kg) if session.planned_weight_kg is not None else None
        ),
        loaded_weight_kg=(
            float(session.loaded_weight_kg) if session.loaded_weight_kg is not None else None
        ),
        occupancy_percent=occupancy_percent,
        last_activity=last_activity,
        can_depart=session.status == "READY_TO_DEPART",
        can_close=session.status == "AWAITING_RECONCILIATION",
        next_transition_allowed=next_transition_blocker is None,
        next_transition_blocker=next_transition_blocker,
        current_stock=stock_summary,
    )


def build_session_snapshot(
    db: Session, *, session: LogisticsVehicleSession
) -> VehicleSessionDetailRead:
    result = _build_session_read(db, session=session, include_history=True)
    assert isinstance(result, VehicleSessionDetailRead)
    return result


def build_session_list_item(db: Session, *, session: LogisticsVehicleSession) -> VehicleSessionRead:
    result = _build_session_read(db, session=session, include_history=False)
    assert isinstance(result, VehicleSessionRead)
    return result
