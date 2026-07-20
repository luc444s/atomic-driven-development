from __future__ import annotations

import json
from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.dto.route_operations import (
    CompositionLineRead,
    CompositionTotalsRead,
    CurrentCompositionRead,
    RouteIncidentRead,
    RouteOperationItemRead,
    RouteOperationRead,
    RouteStopProgressRead,
)
from plugins.logistics.backend.models import (
    LogisticsAdrProductConfig,
    LogisticsDeliveryPoint,
    LogisticsMovement,
    LogisticsRouteIncident,
    LogisticsRouteOperation,
    LogisticsRouteOperationItem,
    LogisticsRouteStop,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.schemas import MovementCreateRequest
from plugins.logistics.backend.services.customer_possession import (
    EVENT_IN_TO_CUSTOMER,
    EVENT_OUT_FROM_CUSTOMER,
    SOURCE_MOBILE_DELIVERY,
    SOURCE_MOBILE_PICKUP,
    append_customer_possession_event,
)
from plugins.logistics.backend.services.movements import (
    confirm_movement,
    create_movement,
    list_movement_items,
)
from plugins.logistics.backend.services.stock_bridge import adjust_required_product_stock
from plugins.productos.backend.models import Product, ProductAdr

VALID_OPERATION_TYPES = {"DELIVERY", "PICKUP", "EXCHANGE"}
VALID_DIRECTIONS = {"OUT", "IN"}
ROUTE_MUTABLE_STATUSES = {"OUTBOUND", "RETURNING"}
VALID_INCIDENT_TYPES = {
    "QUANTITY_MISMATCH",
    "WRONG_PRODUCT",
    "EXCESS_DELIVERY",
    "MISSING_PICKUP",
    "CUSTOMER_ABSENT",
    "FAILED_DELIVERY",
    "UNPLANNED_RETURN",
}
RECONCILABLE_INCIDENT_TYPES = {
    "QUANTITY_MISMATCH",
    "WRONG_PRODUCT",
    "EXCESS_DELIVERY",
    "MISSING_PICKUP",
}
FAILED_INCIDENT_TYPES = {"CUSTOMER_ABSENT", "FAILED_DELIVERY"}


def _get_route_stop(db: Session, *, route_stop_id: str | None) -> LogisticsRouteStop | None:
    if route_stop_id is None:
        return None
    return db.scalar(select(LogisticsRouteStop).where(LogisticsRouteStop.id == route_stop_id))


def _get_delivery_point(
    db: Session, *, route_stop: LogisticsRouteStop | None
) -> LogisticsDeliveryPoint | None:
    if route_stop is None:
        return None
    return db.scalar(
        select(LogisticsDeliveryPoint).where(
            LogisticsDeliveryPoint.id == route_stop.delivery_point_id
        )
    )


def _require_product(db: Session, *, product_id: str) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise LookupError("Producto no encontrado")
    return product


def _latest_adr_config(
    db: Session, *, tenant_id: str, product_id: str, today: date
) -> LogisticsAdrProductConfig | None:
    return db.scalar(
        select(LogisticsAdrProductConfig)
        .where(
            LogisticsAdrProductConfig.tenant_id == tenant_id,
            LogisticsAdrProductConfig.product_id == product_id,
            LogisticsAdrProductConfig.valid_from <= today,
            (LogisticsAdrProductConfig.valid_to.is_(None))
            | (LogisticsAdrProductConfig.valid_to >= today),
        )
        .order_by(LogisticsAdrProductConfig.valid_from.desc())
    )


def _fallback_prod_adr(
    db: Session, *, tenant_id: str, product_id: str, today: date
) -> ProductAdr | None:
    return db.scalar(
        select(ProductAdr)
        .where(
            ProductAdr.tenant_id == tenant_id,
            ProductAdr.product_id == product_id,
            ProductAdr.valid_from <= today,
            (ProductAdr.valid_to.is_(None)) | (ProductAdr.valid_to >= today),
        )
        .order_by(ProductAdr.valid_from.desc())
    )


def _product_weight(db: Session, *, product_id: str) -> float | None:
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None or product.weight_kg is None:
        return None
    return float(product.weight_kg)


def _movement_ids(operation: LogisticsRouteOperation) -> list[str]:
    return json.loads(operation.movement_ids_json)


def _build_operation_read(
    db: Session, *, operation: LogisticsRouteOperation
) -> RouteOperationRead:
    items = list(
        db.scalars(
            select(LogisticsRouteOperationItem)
            .where(LogisticsRouteOperationItem.route_operation_id == operation.id)
            .order_by(LogisticsRouteOperationItem.created_at.asc())
        ).all()
    )
    return RouteOperationRead(
        id=operation.id,
        session_id=operation.session_id,
        route_stop_id=operation.route_stop_id,
        operation_type=operation.operation_type,
        status=operation.status,
        movement_ids=_movement_ids(operation),
        idempotency_key=operation.idempotency_key,
        notes=operation.notes,
        performed_by=operation.performed_by,
        performed_at=operation.performed_at,
        created_at=operation.created_at,
        updated_at=operation.updated_at,
        items=[
            RouteOperationItemRead(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=float(item.quantity),
                direction=item.direction,
                created_at=item.created_at,
            )
            for item in items
        ],
    )


def _build_incident_read(incident: LogisticsRouteIncident) -> RouteIncidentRead:
    return RouteIncidentRead(
        id=incident.id,
        session_id=incident.session_id,
        route_stop_id=incident.route_stop_id,
        related_operation_id=incident.related_operation_id,
        type=incident.incident_type,
        status=incident.status,
        corrective_operation_id=incident.corrective_operation_id,
        notes=incident.notes,
        created_by=incident.created_by,
        closed_by=incident.closed_by,
        created_at=incident.created_at,
        closed_at=incident.closed_at,
        updated_at=incident.updated_at,
    )


def list_route_operations(
    db: Session, *, session_id: str
) -> list[RouteOperationRead]:
    operations = list(
        db.scalars(
            select(LogisticsRouteOperation)
            .where(LogisticsRouteOperation.session_id == session_id)
            .order_by(LogisticsRouteOperation.created_at.desc())
        ).all()
    )
    return [_build_operation_read(db, operation=operation) for operation in operations]


def _validate_operation_payload(payload) -> None:
    if payload.operation_type not in VALID_OPERATION_TYPES:
        raise ValueError("Tipo de operación de ruta no soportado")
    if not payload.items:
        raise ValueError("La operación de ruta necesita al menos un item")
    directions = {item.direction for item in payload.items}
    if not directions.issubset(VALID_DIRECTIONS):
        raise ValueError("La dirección de items solo puede ser IN u OUT")
    if payload.operation_type == "DELIVERY" and directions != {"OUT"}:
        raise ValueError("DELIVERY solo admite items OUT")
    if payload.operation_type == "PICKUP" and directions != {"IN"}:
        raise ValueError("PICKUP solo admite items IN")
    if payload.operation_type == "EXCHANGE" and not ({"IN", "OUT"} <= directions):
        raise ValueError("EXCHANGE necesita al menos una línea IN y una OUT")


def _require_related_operation(
    db: Session, *, session_id: str, operation_id: str | None
) -> LogisticsRouteOperation | None:
    if operation_id is None:
        return None
    operation = db.scalar(
        select(LogisticsRouteOperation).where(
            LogisticsRouteOperation.id == operation_id,
            LogisticsRouteOperation.session_id == session_id,
        )
    )
    if operation is None:
        raise LookupError("Operación relacionada no encontrada en la jornada")
    return operation


def _validate_incident_payload(db: Session, *, session_id: str, payload) -> None:
    if payload.type not in VALID_INCIDENT_TYPES:
        raise ValueError("Tipo de incidencia de ruta no soportado")
    _require_related_operation(db, session_id=session_id, operation_id=payload.related_operation_id)


def create_route_operation(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    payload,
    action_context: LogisticsActionContext,
) -> RouteOperationRead:
    if session.status not in ROUTE_MUTABLE_STATUSES:
        raise ValueError("La jornada no permite registrar operaciones de ruta en este estado")
    _validate_operation_payload(payload)
    operation = LogisticsRouteOperation(
        tenant_id=session.tenant_id,
        session_id=session.id,
        route_stop_id=payload.route_stop_id,
        operation_type=payload.operation_type,
        status="DRAFT",
        movement_ids_json="[]",
        idempotency_key=payload.idempotency_key or f"{session.id}:{uuid4()}",
        notes=payload.notes,
    )
    db.add(operation)
    db.flush()
    for raw_item in payload.items:
        product = _require_product(db, product_id=raw_item.product_id)
        db.add(
            LogisticsRouteOperationItem(
                route_operation_id=operation.id,
                product_id=product.id,
                product_name=raw_item.product_name or product.name,
                quantity=float(raw_item.quantity),
                direction=raw_item.direction,
            )
        )
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.route_operation.create",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"operation_id": operation.id, "operation_type": operation.operation_type},
    )
    return _build_operation_read(db, operation=operation)


def create_exchange_route_operation(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    payload,
    action_context: LogisticsActionContext,
) -> RouteOperationRead:
    if not payload.delivered_lines or not payload.picked_up_lines:
        raise ValueError("EXCHANGE necesita líneas entregadas y recogidas")
    synthetic_payload = type(
        "SyntheticExchangePayload",
        (),
        {
            "route_stop_id": payload.route_stop_id,
            "operation_type": "EXCHANGE",
            "notes": payload.notes,
            "idempotency_key": payload.idempotency_key,
            "items": [
                *[
                    type(
                        "Line",
                        (),
                        {
                            "product_id": line.product_id,
                            "product_name": line.product_name,
                            "quantity": line.quantity,
                            "direction": "OUT",
                        },
                    )
                    for line in payload.delivered_lines
                ],
                *[
                    type(
                        "Line",
                        (),
                        {
                            "product_id": line.product_id,
                            "product_name": line.product_name,
                            "quantity": line.quantity,
                            "direction": "IN",
                        },
                    )
                    for line in payload.picked_up_lines
                ],
            ],
        },
    )()
    return create_route_operation(
        db,
        session=session,
        payload=synthetic_payload,
        action_context=action_context,
    )


def _build_movement_payload(
    *,
    session: LogisticsVehicleSession,
    delivery_point: LogisticsDeliveryPoint | None,
    route_stop_id: str | None,
    movement_type: str,
    items: list[LogisticsRouteOperationItem],
) -> MovementCreateRequest:
    return MovementCreateRequest.model_validate({
        "movement_type": movement_type,
        "route_id": session.route_id,
        "customer_id": delivery_point.customer_id if delivery_point is not None else None,
        "warehouse_id": session.mobile_warehouse_id,
        "driver_id": session.driver_id,
        "vehicle_id": session.vehicle_id,
        "plate": None,
        "destination_place": delivery_point.customer_name if delivery_point is not None else None,
        "destination_address": delivery_point.address if delivery_point is not None else None,
        "notes": f"RouteOperation {route_stop_id or session.id}",
        "items": [
            {
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": max(1, int(float(item.quantity))),
                "quantity_in": float(item.quantity) if movement_type == "IC" else 0,
                "quantity_out": float(item.quantity) if movement_type == "SC" else 0,
            }
            for item in items
        ],
    })


def _apply_stock_for_movement(
    db: Session,
    *,
    movement: LogisticsMovement,
    action_context: LogisticsActionContext,
) -> None:
    if movement.warehouse_id is None:
        return
    items = list_movement_items(db, movement_id=movement.id)
    deltas: dict[tuple[str | None, str | None], float] = {}
    for item in items:
        key = (item.product_id, item.product_name)
        delta = 0.0
        if movement.movement_type == "SC":
            delta = -float(item.quantity_out or 0)
        elif movement.movement_type == "IC":
            delta = float(item.quantity_in or 0)
        if delta == 0:
            continue
        deltas[key] = deltas.get(key, 0) + delta
    for index, ((product_id, product_name), quantity) in enumerate(deltas.items(), start=1):
        if product_id is None or quantity == 0:
            continue
        adjust_required_product_stock(
            db,
            tenant_id=movement.tenant_id,
            warehouse_id=movement.warehouse_id,
            product_id=product_id,
            quantity=quantity,
            reason=f"Movement {movement.id} confirmed: {product_name or product_id}",
            idempotency_key=f"{movement.id}:route-op:{index}:{product_id}",
            action_context=action_context,
        )


def _append_customer_possession(
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


def _confirm_and_apply_movement(
    db: Session,
    *,
    tenant_id: str,
    movement: LogisticsMovement,
    action_context: LogisticsActionContext,
) -> LogisticsMovement:
    movement = confirm_movement(
        db,
        tenant_id=tenant_id,
        movement=movement,
        action_context=action_context,
    )
    _apply_stock_for_movement(db, movement=movement, action_context=action_context)
    return movement


def confirm_route_operation(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    operation_id: str,
    action_context: LogisticsActionContext,
) -> RouteOperationRead:
    operation = db.scalar(
        select(LogisticsRouteOperation).where(
            LogisticsRouteOperation.id == operation_id,
            LogisticsRouteOperation.session_id == session.id,
        )
    )
    if operation is None:
        raise LookupError("Operación de ruta no encontrada")
    if operation.status != "DRAFT":
        raise ValueError("Solo se pueden confirmar operaciones de ruta en borrador")

    route_stop = _get_route_stop(db, route_stop_id=operation.route_stop_id)
    delivery_point = _get_delivery_point(db, route_stop=route_stop)
    items = list(
        db.scalars(
            select(LogisticsRouteOperationItem)
            .where(LogisticsRouteOperationItem.route_operation_id == operation.id)
            .order_by(LogisticsRouteOperationItem.created_at.asc())
        ).all()
    )

    out_items = [item for item in items if item.direction == "OUT"]
    in_items = [item for item in items if item.direction == "IN"]
    movement_ids: list[str] = []

    if out_items:
        out_payload = _build_movement_payload(
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
        _append_customer_possession(
            db,
            tenant_id=session.tenant_id,
            customer_id=delivery_point.customer_id if delivery_point is not None else None,
            movement=out_movement,
            items=out_items,
            source_type=SOURCE_MOBILE_DELIVERY,
            event_type=EVENT_IN_TO_CUSTOMER,
            action_context=action_context,
        )

    if in_items:
        in_payload = _build_movement_payload(
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
        in_movement = _confirm_and_apply_movement(
            db,
            tenant_id=session.tenant_id,
            movement=in_movement,
            action_context=action_context,
        )
        movement_ids.append(in_movement.id)
        _append_customer_possession(
            db,
            tenant_id=session.tenant_id,
            customer_id=delivery_point.customer_id if delivery_point is not None else None,
            movement=in_movement,
            items=in_items,
            source_type=SOURCE_MOBILE_PICKUP,
            event_type=EVENT_OUT_FROM_CUSTOMER,
            action_context=action_context,
        )

    movement_ids.sort()
    operation.movement_ids_json = json.dumps(movement_ids)
    operation.status = "CONFIRMED"
    operation.performed_by = action_context.actor_user_id
    operation.performed_at = datetime.now(UTC)
    db.add(operation)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.route_operation.confirm",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "operation_id": operation.id,
            "operation_type": operation.operation_type,
            "movement_ids": movement_ids,
        },
    )
    return _build_operation_read(db, operation=operation)


def build_current_composition(
    db: Session, *, session: LogisticsVehicleSession
) -> CurrentCompositionRead:
    from plugins.logistics.backend.integrations.stock import get_warehouse_balances

    balances = get_warehouse_balances(
        db,
        tenant_id=session.tenant_id,
        warehouse_id=session.mobile_warehouse_id,
    )
    reference_date = (session.departed_at or session.opened_at).date()
    product_lines: list[CompositionLineRead] = []
    total_packages = 0.0
    total_weight = 0.0
    total_adr_points = 0.0
    for balance in balances.items:
        quantity = float(balance.quantity)
        if quantity <= 0:
            continue
        weight_kg = _product_weight(db, product_id=balance.product_id)
        total_line_weight = weight_kg * quantity if weight_kg is not None else None
        adr_points = None
        adr_cfg = _latest_adr_config(
            db,
            tenant_id=session.tenant_id,
            product_id=balance.product_id,
            today=reference_date,
        )
        if adr_cfg is not None and adr_cfg.adr_points is not None:
            adr_points = float(adr_cfg.adr_points) * quantity
        else:
            fallback = _fallback_prod_adr(
                db,
                tenant_id=session.tenant_id,
                product_id=balance.product_id,
                today=reference_date,
            )
            if fallback is not None and fallback.points is not None:
                adr_points = float(fallback.points) * quantity
        product_lines.append(
            CompositionLineRead(
                product_id=balance.product_id,
                product_name=balance.product_name,
                quantity=quantity,
                weight_kg=total_line_weight,
                adr_points=adr_points,
            )
        )
        total_packages += quantity
        total_weight += total_line_weight or 0
        total_adr_points += adr_points or 0
    product_lines.sort(key=lambda line: line.product_id)
    confirmed_ops = db.scalar(
        select(func.count(LogisticsRouteOperation.id))
        .where(
            LogisticsRouteOperation.session_id == session.id,
            LogisticsRouteOperation.status == "CONFIRMED",
        )
    )
    return CurrentCompositionRead(
        session_id=session.id,
        composition_version=(int(confirmed_ops or 0) + 1),
        product_lines=product_lines,
        totals=CompositionTotalsRead(
            total_packages=total_packages,
            total_weight_kg=total_weight,
            total_adr_points=total_adr_points,
        ),
    )


def list_route_incidents(db: Session, *, session_id: str) -> list[RouteIncidentRead]:
    incidents = list(
        db.scalars(
            select(LogisticsRouteIncident)
            .where(LogisticsRouteIncident.session_id == session_id)
            .order_by(LogisticsRouteIncident.created_at.desc())
        ).all()
    )
    return [_build_incident_read(incident) for incident in incidents]


def create_route_incident(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    payload,
    action_context: LogisticsActionContext,
) -> RouteIncidentRead:
    if session.status not in ROUTE_MUTABLE_STATUSES:
        raise ValueError("La jornada no permite registrar incidencias de ruta en este estado")
    _validate_incident_payload(db, session_id=session.id, payload=payload)
    incident = LogisticsRouteIncident(
        tenant_id=session.tenant_id,
        session_id=session.id,
        route_stop_id=payload.route_stop_id,
        related_operation_id=payload.related_operation_id,
        incident_type=payload.type,
        status="OPEN",
        notes=payload.notes,
        created_by=action_context.actor_user_id,
    )
    db.add(incident)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.route_incident.create",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"incident_id": incident.id, "incident_type": incident.incident_type},
    )
    return _build_incident_read(incident)


def resolve_route_incident(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    incident_id: str,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> RouteIncidentRead:
    incident = db.scalar(
        select(LogisticsRouteIncident).where(
            LogisticsRouteIncident.id == incident_id,
            LogisticsRouteIncident.session_id == session.id,
        )
    )
    if incident is None:
        raise LookupError("Incidencia de ruta no encontrada")
    if incident.status == "RESOLVED":
        return _build_incident_read(incident)
    if incident.status == "CORRECTED":
        raise ValueError("La incidencia ya fue corregida con una operación posterior")
    incident.status = "RESOLVED"
    incident.closed_by = action_context.actor_user_id
    incident.closed_at = datetime.now(UTC)
    if notes:
        incident.notes = f"{incident.notes or ''}\nResolución: {notes}".strip()
    db.add(incident)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.route_incident.resolve",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"incident_id": incident.id, "incident_type": incident.incident_type},
    )
    return _build_incident_read(incident)


def correct_route_incident(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    incident_id: str,
    payload,
    action_context: LogisticsActionContext,
) -> RouteIncidentRead:
    incident = db.scalar(
        select(LogisticsRouteIncident).where(
            LogisticsRouteIncident.id == incident_id,
            LogisticsRouteIncident.session_id == session.id,
        )
    )
    if incident is None:
        raise LookupError("Incidencia de ruta no encontrada")
    if incident.status == "CORRECTED":
        return _build_incident_read(incident)
    if incident.status == "RESOLVED":
        raise ValueError("La incidencia ya fue cerrada sin corrección operativa")
    if incident.incident_type not in RECONCILABLE_INCIDENT_TYPES:
        raise ValueError("Esta incidencia no admite corrección operativa en este slice")

    related_operation = _require_related_operation(
        db,
        session_id=session.id,
        operation_id=incident.related_operation_id,
    )
    synthetic_payload = type(
        "SyntheticIncidentCorrectionPayload",
        (),
        {
            "route_stop_id": payload.route_stop_id or incident.route_stop_id,
            "operation_type": payload.operation_type,
            "notes": payload.notes
            or f"Reconciliación de incidencia {incident.id}"
            + (
                f" sobre operación {related_operation.id}"
                if related_operation is not None
                else ""
            ),
            "idempotency_key": payload.idempotency_key,
            "items": payload.items,
        },
    )()
    created_operation = create_route_operation(
        db,
        session=session,
        payload=synthetic_payload,
        action_context=action_context,
    )
    confirmed_operation = confirm_route_operation(
        db,
        session=session,
        operation_id=created_operation.id,
        action_context=action_context,
    )

    incident.status = "CORRECTED"
    incident.corrective_operation_id = confirmed_operation.id
    incident.closed_by = action_context.actor_user_id
    incident.closed_at = datetime.now(UTC)
    if payload.notes:
        incident.notes = f"{incident.notes or ''}\nCorrección: {payload.notes}".strip()
    db.add(incident)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.route_incident.correct",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "incident_id": incident.id,
            "incident_type": incident.incident_type,
            "corrective_operation_id": confirmed_operation.id,
        },
    )
    return _build_incident_read(incident)


def build_route_stop_progress(
    db: Session, *, session: LogisticsVehicleSession
) -> list[RouteStopProgressRead]:
    if session.route_id is None:
        return []
    stops = list(
        db.scalars(
            select(LogisticsRouteStop)
            .where(LogisticsRouteStop.route_id == session.route_id)
            .order_by(LogisticsRouteStop.stop_order.asc())
        ).all()
    )
    progress_items: list[RouteStopProgressRead] = []
    for stop in stops:
        confirmed_count = db.scalar(
            select(func.count(LogisticsRouteOperation.id)).where(
                LogisticsRouteOperation.session_id == session.id,
                LogisticsRouteOperation.route_stop_id == stop.id,
                LogisticsRouteOperation.status == "CONFIRMED",
            )
        )
        draft_count = db.scalar(
            select(func.count(LogisticsRouteOperation.id)).where(
                LogisticsRouteOperation.session_id == session.id,
                LogisticsRouteOperation.route_stop_id == stop.id,
                LogisticsRouteOperation.status == "DRAFT",
            )
        )
        incidents = list(
            db.scalars(
                select(LogisticsRouteIncident).where(
                    LogisticsRouteIncident.session_id == session.id,
                    LogisticsRouteIncident.route_stop_id == stop.id,
                    LogisticsRouteIncident.status == "OPEN",
                )
            ).all()
        )
        last_operation_at = db.scalar(
            select(func.max(LogisticsRouteOperation.performed_at)).where(
                LogisticsRouteOperation.session_id == session.id,
                LogisticsRouteOperation.route_stop_id == stop.id,
                LogisticsRouteOperation.status == "CONFIRMED",
            )
        )
        has_failed_incident = any(
            incident.incident_type in FAILED_INCIDENT_TYPES for incident in incidents
        )
        if has_failed_incident and not int(confirmed_count or 0):
            progress_status = "FAILED"
        elif incidents and int(confirmed_count or 0):
            progress_status = "PARTIAL"
        elif incidents:
            progress_status = "PARTIAL"
        elif int(confirmed_count or 0):
            progress_status = "COMPLETED"
        elif int(draft_count or 0):
            progress_status = "IN_PROGRESS"
        else:
            progress_status = "PENDING"
        progress_items.append(
            RouteStopProgressRead(
                route_stop_id=stop.id,
                progress_status=progress_status,
                last_operation_at=last_operation_at,
                open_incidents=len(incidents),
            )
        )
    return progress_items
