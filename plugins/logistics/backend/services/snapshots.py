from __future__ import annotations

from datetime import UTC, date

from sqlalchemy import select
from sqlalchemy.orm import Session
from systutor.kernel.auth.models import User

from plugins.logistics.backend.dto.sessions import (
    SessionHistoryEntryRead,
    SessionStockSummaryRead,
    VehicleSessionDetailRead,
    VehicleSessionRead,
)
from plugins.logistics.backend.integrations.stock import get_warehouse_balances
from plugins.logistics.backend.models import (
    LogisticsAdrProductConfig,
    LogisticsOperation,
    LogisticsRoute,
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
from plugins.productos.backend.models import ProductAdr


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


def _get_route(db: Session, route_id: str) -> LogisticsRoute | None:
    return db.scalar(select(LogisticsRoute).where(LogisticsRoute.id == route_id))


def _session_last_activity_label(session: LogisticsVehicleSession) -> str | None:
    candidates = [
        (session.closed_at, "Jornada cerrada"),
        (session.returned_at, "Vehiculo retorno"),
        (session.departed_at, "Vehiculo salio"),
        (session.ready_at, "Jornada lista para salir"),
        (session.opened_at, "Jornada creada"),
    ]
    for occurred_at, label in candidates:
        if occurred_at is not None:
            return label
    return None


def _load_adr_points_map(
    db: Session,
    *,
    tenant_id: str,
    product_ids: list[str],
    today: date,
) -> dict[str, float]:
    result: dict[str, float] = {}
    if not product_ids:
        return result

    configs = list(
        db.scalars(
            select(LogisticsAdrProductConfig)
            .where(
                LogisticsAdrProductConfig.tenant_id == tenant_id,
                LogisticsAdrProductConfig.product_id.in_(product_ids),
                LogisticsAdrProductConfig.valid_from <= today,
                (LogisticsAdrProductConfig.valid_to.is_(None))
                | (LogisticsAdrProductConfig.valid_to >= today),
            )
            .order_by(LogisticsAdrProductConfig.valid_from.desc())
        ).all()
    )
    for config in configs:
        if config.product_id in result:
            continue
        if config.adr_points is not None:
            result[config.product_id] = float(config.adr_points)

    missing = [product_id for product_id in product_ids if product_id not in result]
    if missing:
        fallbacks = list(
            db.scalars(
                select(ProductAdr)
                .where(
                    ProductAdr.tenant_id == tenant_id,
                    ProductAdr.product_id.in_(missing),
                    ProductAdr.valid_from <= today,
                    (ProductAdr.valid_to.is_(None)) | (ProductAdr.valid_to >= today),
                )
                .order_by(ProductAdr.valid_from.desc())
            ).all()
        )
        for fallback in fallbacks:
            if fallback.product_id in result:
                continue
            if fallback.points is not None:
                result[fallback.product_id] = float(fallback.points)

    return result


def _build_stock_summary(
    db: Session, *, tenant_id: str, mobile_warehouse_id: str,
    reference_date: date | None = None,
) -> SessionStockSummaryRead:
    balances = get_warehouse_balances(
        db,
        tenant_id=tenant_id,
        warehouse_id=mobile_warehouse_id,
    )
    mobile_warehouse = _get_warehouse(db, mobile_warehouse_id)

    today = reference_date or date.today()
    positive_ids = [item.product_id for item in balances.items if float(item.quantity) > 0]
    adr_points_map = _load_adr_points_map(
        db,
        tenant_id=tenant_id,
        product_ids=positive_ids,
        today=today,
    )

    total_adr = 0.0
    for item in balances.items:
        quantity = float(item.quantity)
        if quantity <= 0:
            continue
        points = adr_points_map.get(item.product_id)
        if points is not None:
            total_adr += points * quantity

    return SessionStockSummaryRead(
        warehouse_id=mobile_warehouse.id,
        warehouse_code=mobile_warehouse.code,
        warehouse_name=mobile_warehouse.name,
        total_products=len([item for item in balances.items if item.quantity > 0]),
        total_units=sum(float(item.quantity) for item in balances.items),
        total_adr_points=total_adr,
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
    route = _get_route(db, session.route_id) if session.route_id else None
    route_date = route.route_date if route is not None else None
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

    if include_history:
        history = build_session_history(db, session=session)
        last_activity = history[-1].label if history else None
    else:
        history = []
        last_activity = _session_last_activity_label(session)
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
            route_date=route_date,
            route_origin_label=route.origin_label if route is not None else None,
            route_destination_label=route.destination_label if route is not None else None,
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
        route_date=route_date,
        route_origin_label=route.origin_label if route is not None else None,
        route_destination_label=route.destination_label if route is not None else None,
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


def build_session_list_items(
    db: Session,
    *,
    sessions: list[LogisticsVehicleSession],
) -> list[VehicleSessionRead]:
    if not sessions:
        return []

    vehicle_ids = list({session.vehicle_id for session in sessions})
    driver_ids = list({session.driver_id for session in sessions})
    warehouse_ids = list(
        {session.origin_warehouse_id for session in sessions}
        | {session.mobile_warehouse_id for session in sessions}
    )
    route_ids = list({session.route_id for session in sessions if session.route_id})
    session_ids = [session.id for session in sessions]

    vehicles = {
        vehicle.id: vehicle
        for vehicle in db.scalars(
            select(LogisticsVehicle).where(LogisticsVehicle.id.in_(vehicle_ids))
        ).all()
    }
    drivers = {
        user.id: user
        for user in db.scalars(select(User).where(User.id.in_(driver_ids))).all()
    }
    warehouses = {
        warehouse.id: warehouse
        for warehouse in db.scalars(
            select(LogisticsWarehouse).where(LogisticsWarehouse.id.in_(warehouse_ids))
        ).all()
    }
    routes = {
        route.id: route
        for route in db.scalars(
            select(LogisticsRoute).where(LogisticsRoute.id.in_(route_ids))
        ).all()
    }
    latest_reconciliation_by_session: dict[str, LogisticsSessionReconciliation] = {}
    for reconciliation in db.scalars(
        select(LogisticsSessionReconciliation)
        .where(LogisticsSessionReconciliation.session_id.in_(session_ids))
        .order_by(LogisticsSessionReconciliation.updated_at.desc())
    ).all():
        latest_reconciliation_by_session.setdefault(reconciliation.session_id, reconciliation)

    stock_summary_by_warehouse: dict[str, SessionStockSummaryRead] = {}
    for mobile_warehouse_id in {session.mobile_warehouse_id for session in sessions}:
        stock_summary_by_warehouse[mobile_warehouse_id] = _build_stock_summary(
            db,
            tenant_id=sessions[0].tenant_id,
            mobile_warehouse_id=mobile_warehouse_id,
        )

    items: list[VehicleSessionRead] = []
    for session in sessions:
        vehicle = vehicles.get(session.vehicle_id)
        if vehicle is None:
            raise LookupError("Vehiculo no encontrado")
        driver = drivers.get(session.driver_id)
        origin = warehouses.get(session.origin_warehouse_id)
        mobile = warehouses.get(session.mobile_warehouse_id)
        if origin is None or mobile is None:
            raise LookupError("Warehouse no encontrado")
        route = routes.get(session.route_id) if session.route_id else None
        route_date = route.route_date if route is not None else None
        stock_summary = stock_summary_by_warehouse[session.mobile_warehouse_id]

        occupancy_percent = None
        max_weight = float(vehicle.useful_load or vehicle.capacity_weight or 0)
        if max_weight > 0 and session.loaded_weight_kg is not None:
            occupancy_percent = round((float(session.loaded_weight_kg) / max_weight) * 100, 1)

        reconciliation = latest_reconciliation_by_session.get(session.id)
        start_queue_blocker = get_session_start_queue_blocker(db, session=session)
        next_transition_blocker = get_next_transition_blocker(
            session,
            has_open_discrepancies=(
                has_open_discrepancies(db, reconciliation_id=reconciliation.id)
                if reconciliation is not None
                else False
            ),
            reconciliation_status=(
                reconciliation.status if reconciliation is not None else None
            ),
            start_queue_blocker=start_queue_blocker,
        )

        items.append(
            VehicleSessionRead(
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
                route_date=route_date,
                route_origin_label=route.origin_label if route is not None else None,
                route_destination_label=(
                    route.destination_label if route is not None else None
                ),
                status=session.status,
                opened_at=session.opened_at,
                ready_at=session.ready_at,
                departed_at=session.departed_at,
                returned_at=session.returned_at,
                closed_at=session.closed_at,
                planned_weight_kg=(
                    float(session.planned_weight_kg)
                    if session.planned_weight_kg is not None
                    else None
                ),
                loaded_weight_kg=(
                    float(session.loaded_weight_kg)
                    if session.loaded_weight_kg is not None
                    else None
                ),
                occupancy_percent=occupancy_percent,
                last_activity=_session_last_activity_label(session),
                can_depart=session.status == "READY_TO_DEPART",
                can_close=session.status == "AWAITING_RECONCILIATION",
                next_transition_allowed=next_transition_blocker is None,
                next_transition_blocker=next_transition_blocker,
                current_stock=stock_summary,
            )
        )
    return items
