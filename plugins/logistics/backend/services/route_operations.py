from __future__ import annotations

import json
from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.crm.backend.models import CrmCustomer
from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.dto.route_operations import (
    CurrentCompositionRead,
    RouteIncidentRead,
    RouteOperationItemRead,
    RouteOperationRead,
    RouteStopProgressRead,
)
from plugins.logistics.backend.models import (
    LogisticsAdrProductConfig,
    LogisticsCylinder,
    LogisticsDeliveryPoint,
    LogisticsLoadSerialAssignment,
    LogisticsMovement,
    LogisticsRouteIncident,
    LogisticsRouteOperation,
    LogisticsRouteOperationItem,
    LogisticsRouteStop,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import MovementCreateRequest
from plugins.logistics.backend.services.customer_possession import append_customer_possession_event
from plugins.logistics.backend.services.load_serials import product_requires_serial_capture
from plugins.logistics.backend.services.movements import (
    confirm_movement,
    get_movement_type,
    list_movement_items,
)
from plugins.logistics.backend.services.route_control import get_latest_vehicle_location_event
from plugins.logistics.backend.services.route_operation_composition import (
    build_current_composition_v2,
)
from plugins.logistics.backend.services.route_operation_confirmation import (
    confirm_route_operation_effects,
)
from plugins.logistics.backend.services.stock_bridge import apply_stock_for_movement
from plugins.productos.backend.models import Product, ProductAdr

VALID_OPERATION_TYPES = {"DELIVERY", "PICKUP", "EXCHANGE"}
VALID_DIRECTIONS = {"OUT", "IN"}
ROUTE_MUTABLE_STATUSES = {"OUTBOUND", "RETURNING"}
VALID_CONTEXT_TYPES = {"STOP", "CUSTOMER", "WAREHOUSE"}
VALID_INCIDENT_MODES = {"NONE", "CREATE", "CORRECT_EXISTING"}
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


def _get_customer(db: Session, *, tenant_id: str, customer_id: str) -> CrmCustomer:
    customer = db.scalar(
        select(CrmCustomer).where(
            CrmCustomer.id == customer_id,
            CrmCustomer.tenant_id == tenant_id,
        )
    )
    if customer is None:
        raise LookupError("Cliente no encontrado")
    return customer


def _get_warehouse(db: Session, *, tenant_id: str, warehouse_id: str) -> LogisticsWarehouse:
    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == warehouse_id,
            LogisticsWarehouse.tenant_id == tenant_id,
        )
    )
    if warehouse is None:
        raise LookupError("Almacén no encontrado")
    return warehouse


def _customer_snapshot_name(customer: CrmCustomer) -> str:
    return customer.commercial_name or customer.legal_name


def _existing_operation_by_idempotency_key(
    db: Session, *, session_id: str, idempotency_key: str | None
) -> LogisticsRouteOperation | None:
    if not idempotency_key:
        return None
    return db.scalar(
        select(LogisticsRouteOperation).where(
            LogisticsRouteOperation.session_id == session_id,
            LogisticsRouteOperation.idempotency_key == idempotency_key,
        )
    )


def _resolve_operation_context(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    route_stop_id: str | None,
    context_type: str | None,
    customer_id: str | None,
    warehouse_id: str | None,
    require_explicit: bool,
) -> dict[str, object]:
    resolved_context_type = context_type
    if resolved_context_type is None:
        if require_explicit:
            raise ValueError("context_type es obligatorio")
        if route_stop_id is not None:
            resolved_context_type = "STOP"
        else:
            return {
                "route_stop": None,
                "delivery_point": None,
                "context_type": None,
                "customer_id": None,
                "customer_name_snapshot": None,
                "warehouse_id": None,
                "warehouse_name_snapshot": None,
            }

    if resolved_context_type not in VALID_CONTEXT_TYPES:
        raise ValueError("context_type no soportado")

    if resolved_context_type == "STOP":
        if route_stop_id is None:
            raise ValueError("context_type STOP requiere route_stop_id")
        if customer_id is not None:
            raise ValueError("context_type STOP no permite customer_id explícito")
        route_stop = _get_route_stop(db, route_stop_id=route_stop_id)
        if route_stop is None:
            raise LookupError("Parada no encontrada")
        delivery_point = _get_delivery_point(db, route_stop=route_stop)
        if delivery_point is None and route_stop.customer_id is None:
            raise LookupError("Punto de entrega no encontrado para la parada")

        if delivery_point is not None and delivery_point.warehouse_id is not None:
            warehouse = _get_warehouse(
                db, tenant_id=session.tenant_id, warehouse_id=delivery_point.warehouse_id
            )
            return {
                "route_stop": route_stop,
                "delivery_point": delivery_point,
                "context_type": "WAREHOUSE",
                "customer_id": None,
                "customer_name_snapshot": None,
                "warehouse_id": delivery_point.warehouse_id,
                "warehouse_name_snapshot": warehouse.name,
            }

        resolved_customer_id = (
            delivery_point.customer_id if delivery_point is not None
            else route_stop.customer_id
        )
        resolved_customer_name = (
            delivery_point.customer_name if delivery_point is not None
            else route_stop.customer_name_snapshot
        )
        warehouse_name_snapshot = None
        if warehouse_id is not None:
            warehouse = _get_warehouse(db, tenant_id=session.tenant_id, warehouse_id=warehouse_id)
            warehouse_name_snapshot = warehouse.name
        return {
            "route_stop": route_stop,
            "delivery_point": delivery_point,
            "context_type": resolved_context_type,
            "customer_id": resolved_customer_id,
            "customer_name_snapshot": resolved_customer_name,
            "warehouse_id": warehouse_id,
            "warehouse_name_snapshot": warehouse_name_snapshot,
        }

    if route_stop_id is not None:
        raise ValueError("El contexto manual no permite route_stop_id")

    if resolved_context_type == "CUSTOMER":
        if customer_id is None:
            raise ValueError("context_type CUSTOMER requiere customer_id")
        customer = _get_customer(db, tenant_id=session.tenant_id, customer_id=customer_id)
        customer_name_snapshot = _customer_snapshot_name(customer)
        return {
            "route_stop": None,
            "delivery_point": SimpleNamespace(
                customer_id=customer.id,
                customer_name=customer_name_snapshot,
                address=None,
                address_id=None,
            ),
            "context_type": resolved_context_type,
            "customer_id": customer.id,
            "customer_name_snapshot": customer_name_snapshot,
            "warehouse_id": None,
            "warehouse_name_snapshot": None,
        }

    if warehouse_id is None:
        raise ValueError("context_type WAREHOUSE requiere warehouse_id")
    warehouse = _get_warehouse(db, tenant_id=session.tenant_id, warehouse_id=warehouse_id)
    return {
        "route_stop": None,
        "delivery_point": None,
        "context_type": resolved_context_type,
        "customer_id": None,
        "customer_name_snapshot": None,
        "warehouse_id": warehouse.id,
        "warehouse_name_snapshot": warehouse.name,
    }


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
        context_type=operation.context_type,
        customer_id=operation.customer_id,
        customer_name_snapshot=operation.customer_name_snapshot,
        warehouse_id=operation.warehouse_id,
        warehouse_name_snapshot=operation.warehouse_name_snapshot,
        operation_type=operation.operation_type,
        status=operation.status,
        movement_ids=_movement_ids(operation),
        idempotency_key=operation.idempotency_key,
        location_event_id=operation.location_event_id,
        location_lat=float(operation.location_lat) if operation.location_lat is not None else None,
        location_lng=float(operation.location_lng) if operation.location_lng is not None else None,
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


def _create_route_operation_record(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    payload,
    action_context: LogisticsActionContext,
    context: dict[str, object] | None = None,
) -> LogisticsRouteOperation:
    if session.status not in ROUTE_MUTABLE_STATUSES:
        raise ValueError("La jornada no permite registrar operaciones de ruta en este estado")
    _validate_operation_payload(payload)

    existing = _existing_operation_by_idempotency_key(
        db,
        session_id=session.id,
        idempotency_key=payload.idempotency_key,
    )
    if existing is not None:
        return existing

    context = context or {
        "context_type": None,
        "customer_id": None,
        "customer_name_snapshot": None,
        "warehouse_id": None,
        "warehouse_name_snapshot": None,
    }
    operation = LogisticsRouteOperation(
        tenant_id=session.tenant_id,
        session_id=session.id,
        route_stop_id=payload.route_stop_id,
        operation_type=payload.operation_type,
        context_type=context["context_type"],
        customer_id=context["customer_id"],
        customer_name_snapshot=context["customer_name_snapshot"],
        warehouse_id=context["warehouse_id"],
        warehouse_name_snapshot=context["warehouse_name_snapshot"],
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
    return operation


def create_route_operation(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    payload,
    action_context: LogisticsActionContext,
) -> RouteOperationRead:
    context = _resolve_operation_context(
        db,
        session=session,
        route_stop_id=payload.route_stop_id,
        context_type=getattr(payload, "context_type", None),
        customer_id=getattr(payload, "customer_id", None),
        warehouse_id=getattr(payload, "warehouse_id", None),
        require_explicit=False,
    )
    operation = _create_route_operation_record(
        db,
        session=session,
        payload=payload,
        action_context=action_context,
        context=context,
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


def _delivery_point_for_operation(
    db: Session, *, operation: LogisticsRouteOperation
) -> LogisticsDeliveryPoint | SimpleNamespace | None:
    route_stop = _get_route_stop(db, route_stop_id=operation.route_stop_id)
    if route_stop is not None:
        dp = _get_delivery_point(db, route_stop=route_stop)
        if dp is not None:
            return dp
    if operation.customer_id is not None:
        return SimpleNamespace(
            customer_id=operation.customer_id,
            customer_name=operation.customer_name_snapshot,
            address=None,
            address_id=None,
        )
    return None


class SerialResolutionError(ValueError):
    """Seriales insuficientes o en estado incorrecto para la operación."""


_STATE_BY_MOVEMENT_TYPE: dict[str, tuple[str, ...]] = {
    "SC": ("CARGA_EN_VEHICULO", "EN_RUTA"),
    "IC": ("EN_CLIENTE_VACIO", "EN_CLIENTE_LLENO"),
    "SP": (
        "EN_ALMACEN_VACIO", "EN_ALMACEN_LLENO",
        "OBSERVADO", "PARA_REPARACION",
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
    """Devuelve cylinder_ids bloqueados, filtrados por estado, orden determinista."""
    states = _STATE_BY_MOVEMENT_TYPE.get(movement_type)
    if states is None:
        return []

    return list(db.scalars(
        select(LogisticsLoadSerialAssignment.cylinder_id)
        .join(LogisticsCylinder,
              LogisticsCylinder.id == LogisticsLoadSerialAssignment.cylinder_id)
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
        .limit(quantity)
    ).all())


def _build_item_dict(
    item: LogisticsRouteOperationItem,
    movement_type: str,
    cylinder_id: str | None = None,
    quantity: int | None = None,
) -> dict[str, object]:
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
                    db, tenant_id=session.tenant_id,
                    session_id=session.id,
                    product_id=item.product_id,
                    source_warehouse_id=None,
                )
            requires_serials = serial_cache[cache_key]

            if not requires_serials:
                result.append(_build_item_dict(item, movement_type))
                continue

            serials = _resolve_serial_ids(
                db, session_id=session.id,
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
                    f"requeridos={int(item.quantity)} | "
                    f"disponibles={len(serials)} | "
                    f"movement_type={movement_type} | session={session.id}"
                )

            for cyl_id in serials:
                result.append(_build_item_dict(
                    item, movement_type, cylinder_id=cyl_id, quantity=1,
                ))
        else:
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
        db, session=session, items=items, movement_type=movement_type,
    )
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
        "items": built_items,
    })


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
            f"Stock bridge error during confirm. Check stock_bridge_log "
            f"for movement {movement.id}"
        )
        db.add(movement)
        db.flush()
        raise

    movement = confirm_movement(
        db,
        tenant_id=tenant_id,
        movement=movement,
        action_context=action_context,
    )
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

    delivery_point = cast(Any, _delivery_point_for_operation(db, operation=operation))
    items = list(
        db.scalars(
            select(LogisticsRouteOperationItem)
            .where(LogisticsRouteOperationItem.route_operation_id == operation.id)
            .order_by(LogisticsRouteOperationItem.created_at.asc())
        ).all()
    )
    movement_ids, effect_summary = confirm_route_operation_effects(
        db,
        session=session,
        operation=operation,
        delivery_point=delivery_point,
        items=items,
        action_context=action_context,
    )
    operation.movement_ids_json = json.dumps(movement_ids)
    operation.status = "CONFIRMED"
    operation.performed_by = action_context.actor_user_id
    operation.performed_at = datetime.now(UTC)
    latest_location = get_latest_vehicle_location_event(db, session_id=session.id)
    if latest_location is not None:
        operation.location_event_id = latest_location.id
        operation.location_lat = float(latest_location.lat)
        operation.location_lng = float(latest_location.lng)
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
            "effect_summary": effect_summary,
            "financial_omission_reason": effect_summary.get("financial_omission_reason"),
        },
    )
    return _build_operation_read(db, operation=operation)


def build_current_composition(
    db: Session, *, session: LogisticsVehicleSession
) -> CurrentCompositionRead:
    return build_current_composition_v2(db, session=session)


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


def _validate_route_event_payload(
    db: Session, *, session: LogisticsVehicleSession, payload
) -> None:
    if payload.incident_mode not in VALID_INCIDENT_MODES:
        raise ValueError("incident_mode no soportado")

    if payload.incident_mode == "NONE":
        if payload.type is not None:
            raise ValueError("incident_mode NONE no permite type")
        if payload.target_incident_id is not None:
            raise ValueError("incident_mode NONE no permite target_incident_id")
        return

    if payload.incident_mode == "CREATE":
        if payload.type is None:
            raise ValueError("incident_mode CREATE requiere type")
        if payload.target_incident_id is not None:
            raise ValueError("incident_mode CREATE no permite target_incident_id")
        if payload.type not in VALID_INCIDENT_TYPES:
            raise ValueError("Tipo de incidencia de ruta no soportado")
        _require_related_operation(
            db,
            session_id=session.id,
            operation_id=payload.related_operation_id,
        )
        return

    if payload.target_incident_id is None:
        raise ValueError("incident_mode CORRECT_EXISTING requiere target_incident_id")


def confirm_route_event(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    payload,
    action_context: LogisticsActionContext,
) -> RouteOperationRead:
    if session.status not in ROUTE_MUTABLE_STATUSES:
        raise ValueError("La jornada no permite registrar operaciones de ruta en este estado")

    _validate_operation_payload(payload)
    _validate_route_event_payload(db, session=session, payload=payload)

    existing = _existing_operation_by_idempotency_key(
        db,
        session_id=session.id,
        idempotency_key=payload.idempotency_key,
    )
    if existing is not None:
        return _build_operation_read(db, operation=existing)

    context = _resolve_operation_context(
        db,
        session=session,
        route_stop_id=payload.route_stop_id,
        context_type=payload.context_type,
        customer_id=payload.customer_id,
        warehouse_id=payload.warehouse_id,
        require_explicit=True,
    )

    operation = _create_route_operation_record(
        db,
        session=session,
        payload=payload,
        action_context=action_context,
        context=context,
    )
    confirmed_operation = confirm_route_operation(
        db,
        session=session,
        operation_id=operation.id,
        action_context=action_context,
    )

    if payload.incident_mode == "CREATE":
        incident_payload = type(
            "SyntheticRouteIncidentCreatePayload",
            (),
            {
                "route_stop_id": payload.route_stop_id,
                "related_operation_id": payload.related_operation_id or confirmed_operation.id,
                "type": payload.type,
                "notes": payload.incident_notes or payload.notes,
            },
        )()
        create_route_incident(
            db,
            session=session,
            payload=incident_payload,
            action_context=action_context,
        )
        return confirmed_operation

    if payload.incident_mode == "CORRECT_EXISTING":
        incident = db.scalar(
            select(LogisticsRouteIncident).where(
                LogisticsRouteIncident.id == payload.target_incident_id,
                LogisticsRouteIncident.session_id == session.id,
            )
        )
        if incident is None:
            raise LookupError("Incidencia de ruta no encontrada")
        if incident.status != "OPEN":
            raise ValueError("La incidencia ya no está abierta para corrección")
        if incident.incident_type not in RECONCILABLE_INCIDENT_TYPES:
            raise ValueError("Esta incidencia no admite corrección operativa en este slice")
        incident.status = "CORRECTED"
        incident.corrective_operation_id = confirmed_operation.id
        incident.closed_by = action_context.actor_user_id
        incident.closed_at = datetime.now(UTC)
        if payload.incident_notes:
            incident.notes = f"{incident.notes or ''}\nCorrección: {payload.incident_notes}".strip()
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

    return confirmed_operation


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
