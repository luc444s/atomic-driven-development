from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsDeliveryPoint,
    LogisticsLoadSerialAssignment,
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsRouteOperation,
    LogisticsRouteOperationItem,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.schemas import CylinderTransitionRequest, MovementCreateRequest
from plugins.logistics.backend.services.customer_possession import (
    EVENT_IN_TO_CUSTOMER,
    EVENT_OUT_FROM_CUSTOMER,
    SOURCE_MOBILE_DELIVERY,
    SOURCE_MOBILE_PICKUP,
    append_customer_possession_event,
)
from plugins.logistics.backend.services.cylinders import transition_cylinder
from plugins.logistics.backend.services.load_serials import (
    ACTIVE_ASSIGNMENT_STATUSES,
    product_requires_serial_capture,
)
from plugins.logistics.backend.services.movements import (
    confirm_movement,
    create_movement,
    get_movement_type,
    list_movement_items,
)
from plugins.logistics.backend.services.stock_bridge import apply_stock_for_movement


class SerialResolutionError(ValueError):
    """Seriales insuficientes o en estado incorrecto para la operación."""


_STATE_BY_MOVEMENT_TYPE: dict[str, tuple[str, ...]] = {
    "SC": ("CARGA_EN_VEHICULO", "EN_RUTA"),
    "IC": ("EN_CLIENTE_VACIO",),
    "SP": (
        "EN_ALMACEN_VACIO",
        "EN_ALMACEN_LLENO",
        "OBSERVADO",
        "PARA_REPARACION",
    ),
}


def _resolve_serial_ids(
    db: Session,
    *,
    session_id: str,
    product_id: str,
    quantity: int,
    movement_type: str,
) -> list[str]:
    states = _STATE_BY_MOVEMENT_TYPE.get(movement_type)
    if states is None:
        return []

    # Priorizar seriales marcados explícitamente para esta entrega (DELIVERY_SELECTED)
    delivery_selected = list(
        db.scalars(
            select(LogisticsLoadSerialAssignment.cylinder_id)
            .join(
                LogisticsCylinder,
                LogisticsCylinder.id == LogisticsLoadSerialAssignment.cylinder_id,
            )
            .where(
                LogisticsLoadSerialAssignment.session_id == session_id,
                LogisticsLoadSerialAssignment.product_id == product_id,
                LogisticsLoadSerialAssignment.assignment_status == "DELIVERY_SELECTED",
                LogisticsCylinder.current_state.in_(states),
            )
            .order_by(
                LogisticsLoadSerialAssignment.selected_at.asc(),
                LogisticsLoadSerialAssignment.cylinder_id.asc(),
            )
            .with_for_update(skip_locked=True)
        ).all()
    )

    remaining = quantity - len(delivery_selected)
    if remaining > 0:
        confirmed = list(
            db.scalars(
                select(LogisticsLoadSerialAssignment.cylinder_id)
                .join(
                    LogisticsCylinder,
                    LogisticsCylinder.id == LogisticsLoadSerialAssignment.cylinder_id,
                )
                .where(
                    LogisticsLoadSerialAssignment.session_id == session_id,
                    LogisticsLoadSerialAssignment.product_id == product_id,
                    LogisticsLoadSerialAssignment.assignment_status == "CONFIRMED",
                    LogisticsCylinder.current_state.in_(states),
                )
                .order_by(
                    LogisticsLoadSerialAssignment.selected_at.asc(),
                    LogisticsLoadSerialAssignment.cylinder_id.asc(),
                )
                .with_for_update(skip_locked=True)
                .limit(remaining)
            ).all()
        )
        return delivery_selected + confirmed

    return delivery_selected[:quantity]


def _build_item_dict(
    item: LogisticsRouteOperationItem,
    movement_type: str,
    cylinder_id: str | None = None,
    quantity: int | None = None,
) -> dict[str, object]:
    # qty es la cantidad POR SERIAL (1 cuando viene de _build_items_for_operation),
    # NO la cantidad total de la operación. Usar item.quantity acá causaba que
    # cada serial intentara deducir el total (ej. 2 seriales × 2 = 4 del stock).
    qty = quantity if quantity is not None else max(1, int(float(item.quantity)))
    return {
        "product_id": item.product_id,
        "product_name": item.product_name,
        "cylinder_id": cylinder_id,
        "quantity": qty,
        "quantity_in": float(qty) if movement_type == "IC" else 0,
        "quantity_out": float(qty) if movement_type == "SC" else 0,
    }


def _build_items_for_operation(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    items: list[LogisticsRouteOperationItem],
    movement_type: str,
) -> list[dict[str, object]]:
    mt = get_movement_type(db, code=movement_type)
    serial_cache: dict[tuple[str, str], bool] = {}
    result: list[dict[str, object]] = []

    for item in items:
        if mt and mt.moves_cylinders:
            cache_key = (session.id, item.product_id)
            if cache_key not in serial_cache:
                serial_cache[cache_key] = product_requires_serial_capture(
                    db,
                    tenant_id=session.tenant_id,
                    session_id=session.id,
                    product_id=item.product_id,
                    source_warehouse_id=None,
                )
            requires_serials = serial_cache[cache_key]

            if not requires_serials:
                result.append(_build_item_dict(item, movement_type))
                continue

            serials = _resolve_serial_ids(
                db,
                session_id=session.id,
                product_id=item.product_id,
                quantity=int(item.quantity),
                movement_type=movement_type,
            )
            if not serials:
                raise SerialResolutionError(
                    f"Seriales insuficientes | producto={item.product_name} | "
                    f"requeridos={int(item.quantity)} | disponibles=0 | "
                    f"movement_type={movement_type} | session={session.id}"
                )
            if len(serials) < int(item.quantity):
                raise SerialResolutionError(
                    f"Seriales insuficientes | producto={item.product_name} | "
                    f"requeridos={int(item.quantity)} | disponibles={len(serials)} | "
                    f"movement_type={movement_type} | session={session.id}"
                )
            for cylinder_id in serials:
                result.append(
                    _build_item_dict(
                        item,
                        movement_type,
                        cylinder_id=cylinder_id,
                        quantity=1,
                    )
                )
            continue

        result.append(_build_item_dict(item, movement_type))
    return result


def _build_movement_payload(
    *,
    db: Session,
    session: LogisticsVehicleSession,
    delivery_point: LogisticsDeliveryPoint | None,
    route_stop_id: str | None,
    movement_type: str,
    items: list[LogisticsRouteOperationItem],
) -> MovementCreateRequest:
    built_items = _build_items_for_operation(
        db,
        session=session,
        items=items,
        movement_type=movement_type,
    )
    return MovementCreateRequest.model_validate(
        {
            "movement_type": movement_type,
            "route_id": session.route_id,
            "customer_id": delivery_point.customer_id if delivery_point is not None else None,
            "warehouse_id": session.mobile_warehouse_id,
            "driver_id": session.driver_id,
            "vehicle_id": session.vehicle_id,
            "plate": None,
            "destination_place": (
                delivery_point.customer_name if delivery_point is not None else None
            ),
            "destination_address": delivery_point.address if delivery_point is not None else None,
            "notes": f"RouteOperation {route_stop_id or session.id}",
            "items": built_items,
        }
    )


def _confirm_and_apply_movement(
    db: Session,
    *,
    tenant_id: str,
    movement: LogisticsMovement,
    action_context: LogisticsActionContext,
    apply_cylinder_state: bool = True,
) -> LogisticsMovement:
    try:
        if movement.warehouse_id is not None:
            items = list_movement_items(db, movement_id=movement.id)
            apply_stock_for_movement(
                db,
                movement=movement,
                items=items,
                action_context=action_context,
            )
    except Exception:
        movement.last_stock_sync_error = (
            f"Stock bridge error during confirm. Check stock_bridge_log for movement {movement.id}"
        )
        db.add(movement)
        db.flush()
        raise

    return confirm_movement(
        db,
        tenant_id=tenant_id,
        movement=movement,
        action_context=action_context,
        apply_cylinder_state=apply_cylinder_state,
    )


def _append_customer_possession_from_movement(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str | None,
    movement: LogisticsMovement,
    items: list[LogisticsRouteOperationItem],
    source_type: str,
    event_type: str,
    action_context: LogisticsActionContext,
) -> None:
    if customer_id is None:
        return
    for item in items:
        append_customer_possession_event(
            db,
            tenant_id=tenant_id,
            customer_id=customer_id,
            source_type=source_type,
            source_id=f"{movement.id}:{item.id}",
            event_type=event_type,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=float(item.quantity),
            created_by=action_context.actor_user_id,
            occurred_at=datetime.now(UTC),
            notes=movement.notes,
        )


def _record_delivery_cylinder_events(
    db: Session,
    *,
    tenant_id: str,
    session: LogisticsVehicleSession,
    movement: LogisticsMovement,
    items: list[LogisticsRouteOperationItem],
    customer_id: str | None,
    action_context: LogisticsActionContext,
) -> None:
    if customer_id is None:
        return

    from datetime import UTC, datetime

    from plugins.logistics.backend.services.cylinders import record_cylinder_event

    movement_items = list_movement_items(db, movement_id=movement.id)
    for mitem in movement_items:
        if mitem.cylinder_id is None:
            continue
        record_cylinder_event(
            db,
            cylinder_id=mitem.cylinder_id,
            tenant_id=tenant_id,
            event_type="CUSTOMER_DELIVERY",
            location_type="CUSTOMER",
            location_id=customer_id,
            warehouse_id=None,
            session_id=session.id,
            customer_id=customer_id,
            source_type="ROUTE_OPERATION",
            source_id=movement.id,
            occurred_at=datetime.now(UTC),
            action_context=action_context,
        )
        cylinder = db.scalar(
            select(LogisticsCylinder).where(LogisticsCylinder.id == mitem.cylinder_id)
        )
        if cylinder is not None:
            cylinder.session_id = None
            db.add(cylinder)

        # Marcar el assignment como entregado
        assignment = db.scalar(
            select(LogisticsLoadSerialAssignment)
            .where(
                LogisticsLoadSerialAssignment.cylinder_id == mitem.cylinder_id,
                LogisticsLoadSerialAssignment.session_id == session.id,
                LogisticsLoadSerialAssignment.assignment_status.in_(
                    {"CONFIRMED", "DELIVERY_SELECTED"}
                ),
            )
            .with_for_update()
        )
        if assignment is not None:
            assignment.assignment_status = "DELIVERED"
            db.add(assignment)


def _record_pickup_cylinder_events(
    db: Session,
    *,
    tenant_id: str,
    session: LogisticsVehicleSession,
    movement: LogisticsMovement,
    customer_id: str | None,
    action_context: LogisticsActionContext,
) -> None:
    if customer_id is None:
        return

    from plugins.logistics.backend.services.cylinders import record_cylinder_event

    movement_items = list_movement_items(db, movement_id=movement.id)
    now = datetime.now(UTC)
    for mitem in movement_items:
        if mitem.cylinder_id is None:
            continue
        record_cylinder_event(
            db,
            cylinder_id=mitem.cylinder_id,
            tenant_id=tenant_id,
            event_type="CUSTOMER_PICKUP",
            location_type="VEHICLE",
            location_id=session.id,
            warehouse_id=None,
            session_id=session.id,
            customer_id=None,
            source_type="ROUTE_OPERATION",
            source_id=movement.id,
            occurred_at=now,
            action_context=action_context,
        )
        transition_cylinder(
            db,
            tenant_id=tenant_id,
            cylinder_id=mitem.cylinder_id,
            payload=CylinderTransitionRequest(
                to_state="EN_RUTA",
                session_id=session.id,
                movement_id=movement.id,
                origin="ROUTE_PICKUP",
                notes=movement.notes,
            ),
            action_context=action_context,
        )


def _record_physical_pickup_events(
    db: Session,
    *,
    tenant_id: str,
    session: LogisticsVehicleSession,
    operation: LogisticsRouteOperation,
    items: list[LogisticsRouteOperationItem],
    customer_id: str | None,
    action_context: LogisticsActionContext,
) -> None:
    if customer_id is None:
        return

    from plugins.logistics.backend.services.cylinders import record_cylinder_event

    now = datetime.now(UTC)
    for item in items:
        if not _item_is_serialized(db, session=session, item=item):
            continue
        serials = _resolve_serial_ids_nocheck(
            db,
            session_id=session.id,
            product_id=item.product_id,
            quantity=int(item.quantity),
        )
        for cylinder_id in serials:
            record_cylinder_event(
                db,
                cylinder_id=cylinder_id,
                tenant_id=tenant_id,
                event_type="CUSTOMER_PICKUP",
                location_type="CUSTOMER",
                location_id=customer_id,
                warehouse_id=None,
                session_id=session.id,
                customer_id=customer_id,
                source_type="ROUTE_OPERATION",
                source_id=operation.id,
                occurred_at=now,
                action_context=action_context,
            )


def _item_is_serialized(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    item: LogisticsRouteOperationItem,
) -> bool:
    return product_requires_serial_capture(
        db,
        tenant_id=session.tenant_id,
        session_id=session.id,
        product_id=item.product_id,
        source_warehouse_id=None,
    )


def _resolve_serial_ids_nocheck(
    db: Session, *, session_id: str, product_id: str, quantity: int
) -> list[str]:
    return list(
        db.scalars(
            select(LogisticsLoadSerialAssignment.cylinder_id)
            .join(
                LogisticsCylinder,
                LogisticsCylinder.id == LogisticsLoadSerialAssignment.cylinder_id,
            )
            .where(
                LogisticsLoadSerialAssignment.session_id == session_id,
                LogisticsLoadSerialAssignment.product_id == product_id,
                LogisticsLoadSerialAssignment.assignment_status == "CONFIRMED",
                LogisticsCylinder.current_state == "EN_CLIENTE_VACIO",
            )
            .order_by(LogisticsLoadSerialAssignment.selected_at.asc())
            .limit(quantity)
        ).all()
    )


def _apply_physical_only_pickup(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    operation: LogisticsRouteOperation,
    delivery_point: LogisticsDeliveryPoint | None,
    items: list[LogisticsRouteOperationItem],
    action_context: LogisticsActionContext,
) -> None:
    customer_id = delivery_point.customer_id if delivery_point is not None else None
    for item in items:
        _promote_route_pickup_assignments(
            db,
            session_id=session.id,
            product_id=item.product_id,
        )
        serialized = product_requires_serial_capture(
            db,
            tenant_id=session.tenant_id,
            session_id=session.id,
            product_id=item.product_id,
            source_warehouse_id=None,
        )
        if serialized:
            quantity = float(item.quantity)
            if not quantity.is_integer():
                raise ValueError("Los pickups serializados requieren cantidades enteras")
            serials = _resolve_serial_ids(
                db,
                session_id=session.id,
                product_id=item.product_id,
                quantity=int(quantity),
                movement_type="IC",
            )
            if len(serials) < int(quantity):
                raise SerialResolutionError(
                    f"Seriales insuficientes para pickup | producto={item.product_name} | "
                    f"requeridos={int(quantity)} | disponibles={len(serials)}"
                )
            for cylinder_id in serials:
                transition_cylinder(
                    db,
                    tenant_id=session.tenant_id,
                    cylinder_id=cylinder_id,
                    payload=CylinderTransitionRequest(
                        to_state="EN_RUTA",
                        session_id=session.id,
                        origin="ROUTE_OPERATION_PICKUP",
                        notes=f"RouteOperation {operation.id}",
                    ),
                    action_context=action_context,
                )
                if customer_id is None:
                    continue
                append_customer_possession_event(
                    db,
                    tenant_id=session.tenant_id,
                    customer_id=customer_id,
                    source_type=SOURCE_MOBILE_PICKUP,
                    source_id=f"{operation.id}:{item.id}:{cylinder_id}",
                    event_type=EVENT_OUT_FROM_CUSTOMER,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=1,
                    created_by=action_context.actor_user_id,
                    occurred_at=datetime.now(UTC),
                    notes=operation.notes,
                    cylinder_id=cylinder_id,
                )
            continue

        if customer_id is None:
            continue
        append_customer_possession_event(
            db,
            tenant_id=session.tenant_id,
            customer_id=customer_id,
            source_type=SOURCE_MOBILE_PICKUP,
            source_id=f"{operation.id}:{item.id}",
            event_type=EVENT_OUT_FROM_CUSTOMER,
            product_id=item.product_id,
            product_name=item.product_name,
            quantity=float(item.quantity),
            created_by=action_context.actor_user_id,
            occurred_at=datetime.now(UTC),
            notes=operation.notes,
        )

    _record_physical_pickup_events(
        db,
        tenant_id=session.tenant_id,
        session=session,
        operation=operation,
        items=items,
        customer_id=customer_id,
        action_context=action_context,
    )


def _promote_route_pickup_assignments(
    db: Session,
    *,
    session_id: str,
    product_id: str,
) -> None:
    assignments = list(
        db.scalars(
            select(LogisticsLoadSerialAssignment)
            .join(
                LogisticsCylinder,
                LogisticsCylinder.id == LogisticsLoadSerialAssignment.cylinder_id,
            )
            .where(
                LogisticsLoadSerialAssignment.session_id == session_id,
                LogisticsLoadSerialAssignment.product_id == product_id,
                LogisticsLoadSerialAssignment.assignment_status.in_(ACTIVE_ASSIGNMENT_STATUSES),
                LogisticsCylinder.current_state == "EN_CLIENTE_VACIO",
            )
            .with_for_update()
        ).all()
    )
    if not assignments:
        return
    now = datetime.now(UTC)
    for assignment in assignments:
        if assignment.assignment_status == "CONFIRMED":
            continue
        assignment.assignment_status = "CONFIRMED"
        assignment.confirmed_at = now
        db.add(assignment)
    db.flush()


def _resolve_pickup_origin_movement(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    delivery_point: LogisticsDeliveryPoint | None,
    in_movement: LogisticsMovement,
) -> LogisticsMovement | None:
    """Resuelve el SC histórico que llevó al cliente los cilindros recogidos.

    Cuando el recojo es puro (sin salida en la misma parada), `out_movement`
    es None y el IC quedaría con `origin_movement_id=None`. El stock bridge
    exige que el IC referencie el sale_out original para liquidar el ledger.
    Aquí se busca el último SC realizado para los mismos cilindros de la misma
    jornada/parada que dejó esos envases en el cliente.
    """
    if delivery_point is None:
        return None
    customer_id = delivery_point.customer_id

    cylinder_ids = {
        item.cylinder_id
        for item in list_movement_items(db, movement_id=in_movement.id)
        if item.cylinder_id is not None
    }
    if not cylinder_ids:
        return None

    # El SC de origen debió salir desde el mismo storage móvil/vehículo hacia este cliente.
    origin = db.scalar(
        select(LogisticsMovement)
        .join(
            LogisticsMovementItem,
            LogisticsMovementItem.movement_id == LogisticsMovement.id,
        )
        .where(
            LogisticsMovement.tenant_id == session.tenant_id,
            LogisticsMovement.movement_type == "SC",
            LogisticsMovement.customer_id == customer_id,
            LogisticsMovement.status == "COMPLETADO",
            LogisticsMovementItem.cylinder_id.in_(cylinder_ids),
        )
        .order_by(LogisticsMovement.created_at.desc())
        .limit(1)
    )
    return origin


def confirm_route_operation_effects(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    operation: LogisticsRouteOperation,
    delivery_point: LogisticsDeliveryPoint | None,
    items: list[LogisticsRouteOperationItem],
    action_context: LogisticsActionContext,
) -> tuple[list[str], dict[str, object]]:
    out_items = [item for item in items if item.direction == "OUT"]
    in_items = [item for item in items if item.direction == "IN"]
    movement_ids: list[str] = []
    movement_types: list[str] = []
    out_movement: LogisticsMovement | None = None

    if out_items:
        out_payload = _build_movement_payload(
            db=db,
            session=session,
            delivery_point=delivery_point,
            route_stop_id=operation.route_stop_id,
            movement_type="SC",
            items=out_items,
        )
        out_movement = create_movement(
            db,
            tenant_id=session.tenant_id,
            created_by=action_context.actor_user_id,
            payload=out_payload,
            action_context=action_context,
        )
        out_movement = _confirm_and_apply_movement(
            db,
            tenant_id=session.tenant_id,
            movement=out_movement,
            action_context=action_context,
        )
        movement_ids.append(out_movement.id)
        movement_types.append("SC")
        _append_customer_possession_from_movement(
            db,
            tenant_id=session.tenant_id,
            customer_id=delivery_point.customer_id if delivery_point is not None else None,
            movement=out_movement,
            items=out_items,
            source_type=SOURCE_MOBILE_DELIVERY,
            event_type=EVENT_IN_TO_CUSTOMER,
            action_context=action_context,
        )
        _record_delivery_cylinder_events(
            db,
            tenant_id=session.tenant_id,
            session=session,
            movement=out_movement,
            items=out_items,
            customer_id=delivery_point.customer_id if delivery_point is not None else None,
            action_context=action_context,
        )

    if in_items:
        for item in in_items:
            _promote_route_pickup_assignments(
                db,
                session_id=session.id,
                product_id=item.product_id,
            )
        in_payload = _build_movement_payload(
            db=db,
            session=session,
            delivery_point=delivery_point,
            route_stop_id=operation.route_stop_id,
            movement_type="IC",
            items=in_items,
        )
        in_movement = create_movement(
            db,
            tenant_id=session.tenant_id,
            created_by=action_context.actor_user_id,
            payload=in_payload,
            action_context=action_context,
        )
        pickup_origin: LogisticsMovement | None = None
        if out_movement is not None:
            pickup_origin = out_movement
        else:
            # Recojo puro: el SC de origen histórico debe resolver la trazabilidad
            # del ledger (el IC referencia el sale_out original del cilindro).
            pickup_origin = _resolve_pickup_origin_movement(
                db,
                session=session,
                delivery_point=delivery_point,
                in_movement=in_movement,
            )
        if pickup_origin is not None:
            in_movement.origin_movement_id = pickup_origin.id
            db.add(in_movement)
            db.flush()
            in_movement = _confirm_and_apply_movement(
                db,
                tenant_id=session.tenant_id,
                movement=in_movement,
                action_context=action_context,
                apply_cylinder_state=False,
            )
            movement_ids.append(in_movement.id)
            movement_types.append("IC")
            _append_customer_possession_from_movement(
                db,
                tenant_id=session.tenant_id,
                customer_id=delivery_point.customer_id if delivery_point is not None else None,
                movement=in_movement,
                items=in_items,
                source_type=SOURCE_MOBILE_PICKUP,
                event_type=EVENT_OUT_FROM_CUSTOMER,
                action_context=action_context,
            )
        _record_pickup_cylinder_events(
            db,
            tenant_id=session.tenant_id,
            session=session,
            movement=in_movement,
            customer_id=delivery_point.customer_id if delivery_point is not None else None,
            action_context=action_context,
        )

    movement_ids.sort()
    effect_summary: dict[str, object] = {
        "physical": bool(items),
        "financial": bool(movement_ids),
        "documentary": True,
        "movement_types": movement_types,
    }
    if in_items and "IC" not in movement_types:
        effect_summary["financial_omission_reason"] = "pickup_without_origin"
    return movement_ids, effect_summary
