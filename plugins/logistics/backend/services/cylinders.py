# ruff: noqa: E501
from __future__ import annotations

from datetime import date, datetime
from typing import NamedTuple
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderEvent,
    LogisticsCylinderStateLog,
    LogisticsMovement,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import (
    CylinderCreateRequest,
    CylinderSummaryItem,
    CylinderTransitionRequest,
    CylinderUpdateRequest,
    MovementCreateRequest,
    WarehouseSerializedCylinderSummaryItem,
)
from plugins.logistics.backend.services.cylinder_location import (
    cylinder_is_at_warehouse,
    resolve_cylinder_current_warehouse,
)
from plugins.logistics.backend.services.envase import (
    CUSTOMER_POSSESSION_STATES,
    get_latest_ownership,
    register_ownership_change,
)
from plugins.logistics.backend.services.state_machine import (
    StateTransitionError,
    ensure_transition_allowed,
    has_valid_adr,
    has_valid_hydrotest,
    list_allowed_transitions,
)
from plugins.logistics.backend.services.stock_bridge import adjust_required_product_stock
from plugins.productos.backend.models import Product, ProductAdr

ENTRY_MODE_EMPTY_FROM_CUSTOMER = "EMPTY_FROM_CUSTOMER"
ENTRY_MODE_FULL_FROM_SUPPLIER = "FULL_FROM_SUPPLIER"
ENTRY_MODE_EMPTY_FROM_WAREHOUSE = "EMPTY_FROM_WAREHOUSE"
ENTRY_MODE_FULL_FROM_WAREHOUSE = "FULL_FROM_WAREHOUSE"

ENTRY_MODE_TARGET_STATE = {
    ENTRY_MODE_EMPTY_FROM_CUSTOMER: "EN_ALMACEN_VACIO",
    ENTRY_MODE_FULL_FROM_SUPPLIER: "LLENADO_OK",
    ENTRY_MODE_EMPTY_FROM_WAREHOUSE: "EN_ALMACEN_VACIO",
    ENTRY_MODE_FULL_FROM_WAREHOUSE: "LLENADO_OK",
}

ENTRY_MODE_MOVEMENT_TYPE = {
    ENTRY_MODE_EMPTY_FROM_CUSTOMER: "IC",
    ENTRY_MODE_FULL_FROM_SUPPLIER: "IFP",
    ENTRY_MODE_EMPTY_FROM_WAREHOUSE: None,
    ENTRY_MODE_FULL_FROM_WAREHOUSE: None,
}

ENTRY_MODE_DOCUMENT_TYPE = {
    ENTRY_MODE_EMPTY_FROM_CUSTOMER: "IC",
    ENTRY_MODE_FULL_FROM_SUPPLIER: "IP",
    ENTRY_MODE_EMPTY_FROM_WAREHOUSE: None,
    ENTRY_MODE_FULL_FROM_WAREHOUSE: None,
}

ENTRY_MODE_FULL_STATES = {
    ENTRY_MODE_FULL_FROM_SUPPLIER,
    ENTRY_MODE_FULL_FROM_WAREHOUSE,
}

SERIALIZED_WAREHOUSE_AVAILABILITY_STATES = ("EN_ALMACEN_VACIO", "LLENADO_OK")
EMPTY_FILL_STATUS = "VACIO"
LOADED_FILL_STATUS = "CARGADO"
FILL_OPERATION_ORIGIN = "LLENADO CILINDRO"
CRYOGENIC_FILL_OPERATION_ORIGIN = "LLENADO CRIOGENICO"
VACATE_OPERATION_ORIGIN = "VACIADO CILINDRO"
FILL_REASON_CODE = "FILL"
CRYOGENIC_FILL_REASON_CODE = "FILL_CRYO"
FILL_REASON_CODES = (FILL_REASON_CODE, CRYOGENIC_FILL_REASON_CODE)
VACATE_REASON_CODE = "VACATE"
FILLABLE_EMPTY_STATES = {"CREADO_VACIO", "EN_ALMACEN_VACIO", "VACIO_EN_ALMACEN"}
NON_WAREHOUSE_STATES = {
    "CARGA_EN_VEHICULO",
    "EN_RUTA",
    "EN_CLIENTE_LLENO",
    "EN_CLIENTE_VACIO",
    "PARA_TRASLADO",
}

SIMPLE_FILL_MODE = "SIMPLE"
CRYOGENIC_FILL_MODE = "CRYOGENIC"


class CryogenicFillRecipe(NamedTuple):
    result_product: Product
    source_product: Product
    source_quantity_liters: float
    result_m3_gas: float
    result_net_weight_kg: float


def list_cylinders(
    db: Session,
    *,
    tenant_id: str,
    search: str | None = None,
    state: str | None = None,
    active: bool | None = None,
    is_medical: bool | None = None,
    container_type: str | None = None,
) -> list[LogisticsCylinder]:
    stmt = select(LogisticsCylinder).where(LogisticsCylinder.tenant_id == tenant_id)
    if search:
        normalized_search = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                LogisticsCylinder.serial.ilike(normalized_search),
                LogisticsCylinder.description.ilike(normalized_search),
                LogisticsCylinder.barcode1.ilike(normalized_search),
                LogisticsCylinder.barcode2.ilike(normalized_search),
                LogisticsCylinder.location.ilike(normalized_search),
            )
        )
    if state:
        stmt = stmt.where(LogisticsCylinder.current_state == state)
    if active is not None:
        stmt = stmt.where(LogisticsCylinder.is_active == active)
    if is_medical is not None:
        stmt = stmt.where(LogisticsCylinder.is_medical == is_medical)
    if container_type:
        stmt = stmt.where(LogisticsCylinder.container_type == container_type)
    stmt = stmt.order_by(LogisticsCylinder.created_at.desc(), LogisticsCylinder.serial.asc())
    return list(db.scalars(stmt).all())


def list_cylinders_page(
    db: Session,
    *,
    tenant_id: str,
    page: int,
    per_page: int,
    search: str | None = None,
    state: str | None = None,
    active: bool | None = None,
    is_medical: bool | None = None,
    container_type: str | None = None,
) -> tuple[list[LogisticsCylinder], int]:
    stmt = select(LogisticsCylinder).where(LogisticsCylinder.tenant_id == tenant_id)
    if search:
        normalized_search = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                LogisticsCylinder.serial.ilike(normalized_search),
                LogisticsCylinder.description.ilike(normalized_search),
                LogisticsCylinder.barcode1.ilike(normalized_search),
                LogisticsCylinder.barcode2.ilike(normalized_search),
                LogisticsCylinder.location.ilike(normalized_search),
            )
        )
    if state:
        stmt = stmt.where(LogisticsCylinder.current_state == state)
    if active is not None:
        stmt = stmt.where(LogisticsCylinder.is_active == active)
    if is_medical is not None:
        stmt = stmt.where(LogisticsCylinder.is_medical == is_medical)
    if container_type:
        stmt = stmt.where(LogisticsCylinder.container_type == container_type)

    total = int(db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0)
    offset = (page - 1) * per_page
    items = list(
        db.scalars(
            stmt.order_by(LogisticsCylinder.created_at.desc(), LogisticsCylinder.serial.asc())
            .offset(offset)
            .limit(per_page)
        ).all()
    )
    return items, total


def get_cylinder(db: Session, *, tenant_id: str, cylinder_id: str) -> LogisticsCylinder | None:
    return db.scalar(
        select(LogisticsCylinder).where(
            LogisticsCylinder.id == cylinder_id,
            LogisticsCylinder.tenant_id == tenant_id,
        )
    )


def get_cylinder_by_serial(
    db: Session,
    *,
    tenant_id: str,
    serial_or_barcode: str,
) -> LogisticsCylinder | None:
    normalized = serial_or_barcode.strip().upper()
    return db.scalar(
        select(LogisticsCylinder).where(
            LogisticsCylinder.tenant_id == tenant_id,
            or_(
                LogisticsCylinder.serial == normalized,
                LogisticsCylinder.barcode1 == normalized,
                LogisticsCylinder.barcode2 == normalized,
            ),
        )
    )


def list_cylinder_trace(
    db: Session,
    *,
    tenant_id: str,
    cylinder_id: str,
) -> list[LogisticsCylinderStateLog]:
    return list(
        db.scalars(
            select(LogisticsCylinderStateLog)
            .where(
                LogisticsCylinderStateLog.tenant_id == tenant_id,
                LogisticsCylinderStateLog.cylinder_id == cylinder_id,
            )
            .order_by(
                LogisticsCylinderStateLog.created_at.desc(), LogisticsCylinderStateLog.id.desc()
            )
        ).all()
    )


def summarize_cylinders(db: Session, *, tenant_id: str) -> list[CylinderSummaryItem]:
    rows = db.execute(
        select(LogisticsCylinder.current_state, func.count(LogisticsCylinder.id))
        .where(LogisticsCylinder.tenant_id == tenant_id)
        .group_by(LogisticsCylinder.current_state)
        .order_by(LogisticsCylinder.current_state)
    ).all()
    return [CylinderSummaryItem(state=row[0], count=row[1]) for row in rows]


def summarize_serialized_cylinders_by_warehouse(
    db: Session, *, tenant_id: str, warehouse_id: str
) -> list[WarehouseSerializedCylinderSummaryItem]:
    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == warehouse_id,
            LogisticsWarehouse.tenant_id == tenant_id,
        )
    )
    if warehouse is None:
        raise LookupError("Warehouse not found")

    cylinders = list(
        db.scalars(
            select(LogisticsCylinder)
            .where(
                LogisticsCylinder.tenant_id == tenant_id,
                LogisticsCylinder.is_active.is_(True),
                LogisticsCylinder.current_state.in_(SERIALIZED_WAREHOUSE_AVAILABILITY_STATES),
            )
            .order_by(LogisticsCylinder.serial.asc())
        ).all()
    )

    counts_by_product: dict[str, int] = {}
    for cylinder in cylinders:
        if not cylinder_is_at_warehouse(
            db,
            tenant_id=tenant_id,
            warehouse_id=warehouse.id,
            cylinder=cylinder,
        ):
            continue
        product_id = cylinder.product_id or cylinder.gas_group_id
        if product_id is None:
            continue
        counts_by_product[product_id] = counts_by_product.get(product_id, 0) + 1

    if not counts_by_product:
        return []

    product_rows = db.execute(
        select(Product.id, Product.sku, Product.name).where(
            Product.tenant_id == tenant_id,
            Product.id.in_(counts_by_product.keys()),
        )
    ).all()
    product_map = {row[0]: (row[1], row[2]) for row in product_rows}

    items: list[WarehouseSerializedCylinderSummaryItem] = []
    for product_id, serialized_count in counts_by_product.items():
        product_sku, product_name = product_map.get(product_id, (product_id, product_id))
        items.append(
            WarehouseSerializedCylinderSummaryItem(
                product_id=product_id,
                product_sku=product_sku,
                product_name=product_name,
                serialized_count=serialized_count,
            )
        )
    return sorted(items, key=lambda item: (-item.serialized_count, item.product_sku, item.product_name))


def _resolve_initial_content_kg(
    db: Session, payload: CylinderCreateRequest
) -> float | None:
    """Deriva el content_kg del gas cuando el envase entra lleno sin peso explícito."""
    if payload.entry_mode not in ENTRY_MODE_FULL_STATES:
        return payload.content_kg
    if payload.content_kg is not None and payload.content_kg > 0:
        return payload.content_kg
    product_id = payload.product_id or payload.gas_group_id
    if product_id:
        product = db.get(Product, product_id)
        if product is not None and product.weight_kg and product.weight_kg > 0:
            return float(product.weight_kg)
    return payload.content_kg


def create_cylinder(
    db: Session,
    *,
    tenant_id: str,
    payload: CylinderCreateRequest,
    warehouse_id: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsCylinder:
    resolved_content_kg = _resolve_initial_content_kg(db, payload)
    if resolved_content_kg != payload.content_kg:
        payload = payload.model_copy(update={"content_kg": resolved_content_kg})
    _validate_initial_entry_payload(payload, warehouse_id=warehouse_id)
    cylinder = LogisticsCylinder(
        tenant_id=tenant_id,
        serial=payload.serial.strip().upper(),
        is_active=True,
    )
    _apply_cylinder_payload(cylinder, payload)
    _validate_container_type_coherence(db, tenant_id=tenant_id, cylinder=cylinder)
    if payload.entry_mode is not None:
        cylinder.current_state = ENTRY_MODE_TARGET_STATE[payload.entry_mode]
    db.add(cylinder)
    db.flush()

    document_reference = _build_document_reference(payload)
    state_notes = (
        _build_initial_state_notes(payload=payload, warehouse_id=warehouse_id, document_reference=document_reference)
        if payload.entry_mode is not None
        else "Initial cylinder registration"
    )
    state_metadata = (
        _build_initial_state_metadata(payload=payload, warehouse_id=warehouse_id, document_reference=document_reference)
        if payload.entry_mode is not None
        else {}
    )

    db.add(
        LogisticsCylinderStateLog(
            tenant_id=tenant_id,
            cylinder_id=cylinder.id,
            from_state=None,
            to_state=cylinder.current_state,
            changed_by=action_context.actor_user_id,
            origin="ALTA CILINDRO" if payload.entry_mode is not None else "PLUGIN_CREATE",
            notes=state_notes,
            metadata_json=state_metadata,
        )
    )

    if payload.entry_mode is not None and warehouse_id is not None:
        _register_initial_entry(
            db,
            tenant_id=tenant_id,
            cylinder=cylinder,
            payload=payload,
            warehouse_id=warehouse_id,
            document_reference=document_reference,
            action_context=action_context,
        )

    if (
        cylinder.container_type == "CRYOGENIC_TANK"
        and warehouse_id is not None
    ):
        cylinder.location = f"TANK_WH:{warehouse_id}"
        db.add(cylinder)

    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.create",
        entity_type="cylinder",
        entity_id=cylinder.id,
        details={
            "serial": cylinder.serial,
            "state": cylinder.current_state,
            "entry_mode": payload.entry_mode,
            "warehouse_id": warehouse_id,
            "is_medical": cylinder.is_medical,
            "medical_notes": cylinder.medical_notes,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.created",
        entity_type="cylinder",
        entity_id=cylinder.id,
        payload={
            "serial": cylinder.serial,
            "current_state": cylinder.current_state,
            "entry_mode": payload.entry_mode or "MANUAL",
            "warehouse_id": warehouse_id,
            "is_medical": cylinder.is_medical,
        },
    )
    return cylinder


def update_cylinder(
    db: Session,
    *,
    cylinder: LogisticsCylinder,
    payload: CylinderUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinder:
    previous_is_medical = cylinder.is_medical
    previous_medical_notes = cylinder.medical_notes
    _apply_cylinder_payload(cylinder, payload, partial=True)
    _validate_container_type_coherence(db, tenant_id=cylinder.tenant_id, cylinder=cylinder)
    db.add(cylinder)
    db.flush()
    audit_details: dict[str, object] = {
        "serial": cylinder.serial,
        "barcode1": cylinder.barcode1,
        "barcode2": cylinder.barcode2,
        "state": cylinder.current_state,
        "is_medical": cylinder.is_medical,
        "medical_notes": cylinder.medical_notes,
    }
    if previous_is_medical != cylinder.is_medical:
        audit_details["old_is_medical"] = previous_is_medical
        audit_details["new_is_medical"] = cylinder.is_medical
        audit_details["trace_origin"] = "ACTUALIZACION_FICHA"
    if previous_medical_notes != cylinder.medical_notes:
        audit_details["old_medical_notes"] = previous_medical_notes
        audit_details["new_medical_notes"] = cylinder.medical_notes
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.update",
        entity_type="cylinder",
        entity_id=cylinder.id,
        details=audit_details,
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.updated",
        entity_type="cylinder",
        entity_id=cylinder.id,
        payload={
            "serial": cylinder.serial,
            "barcode1": cylinder.barcode1,
            "barcode2": cylinder.barcode2,
            "is_medical": cylinder.is_medical,
        },
    )
    return cylinder


def get_allowed_transitions(
    db: Session,
    *,
    tenant_id: str,
    cylinder_id: str,
):
    cylinder = get_cylinder(db, tenant_id=tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        return None
    return list_allowed_transitions(db, from_state=cylinder.current_state)


def transition_cylinder(
    db: Session,
    *,
    tenant_id: str,
    cylinder_id: str,
    payload: CylinderTransitionRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinder | None:
    cylinder = get_cylinder(db, tenant_id=tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        return None

    transition = ensure_transition_allowed(db, cylinder=cylinder, to_state=payload.to_state)
    previous_state = cylinder.current_state
    cylinder.current_state = transition.to_state

    if payload.session_id:
        cylinder.session_id = payload.session_id
    elif transition.to_state in ("CARGA_EN_VEHICULO", "EN_RUTA") and cylinder.session_id is None:
        raise ValueError(
            f"Transición a '{transition.to_state}' requiere session_id. "
            "Usa el state machine con contexto de sesión."
        )

    db.add(cylinder)
    db.flush()

    db.add(
        LogisticsCylinderStateLog(
            tenant_id=tenant_id,
            cylinder_id=cylinder.id,
            from_state=previous_state,
            to_state=transition.to_state,
            changed_by=action_context.actor_user_id,
            movement_id=payload.movement_id,
            origin=payload.origin,
            reason_code=payload.reason_code,
            notes=payload.notes,
            metadata_json=dict(payload.metadata_json),
        )
    )

    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.transition",
        entity_type="cylinder",
        entity_id=cylinder.id,
        details={
            "serial": cylinder.serial,
            "from_state": previous_state,
            "to_state": transition.to_state,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.state_changed",
        entity_type="cylinder",
        entity_id=cylinder.id,
        payload={
            "serial": cylinder.serial,
            "from_state": previous_state,
            "to_state": transition.to_state,
            "origin": payload.origin,
            "reason_code": payload.reason_code,
        },
    )
    _sync_cylinder_ownership_for_transition(
        db,
        cylinder=cylinder,
        previous_state=previous_state,
        payload=payload,
        action_context=action_context,
    )
    return cylinder


def fill_cylinder(
    db: Session,
    *,
    tenant_id: str,
    cylinder: LogisticsCylinder,
    warehouse_id: str,
    source_product_id: str | None,
    content_kg: float | None,
    volume_m3: float | None,
    weight_current: float | None,
    fill_operation_id: str | None,
    source_cylinder_id: str | None,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsCylinder:
    _ensure_fillable_cylinder(db, tenant_id=tenant_id, cylinder=cylinder, warehouse_id=warehouse_id)
    recipe = _resolve_active_cryogenic_fill_recipe(
        db,
        tenant_id=tenant_id,
        cylinder=cylinder,
        source_product_id=source_product_id,
    )

    fill_operation_id = fill_operation_id or str(uuid4())
    previous_state = cylinder.current_state

    if recipe is None:
        _validate_fill_payload(content_kg=content_kg, volume_m3=volume_m3)
        product = _resolve_stock_product_for_gas(
            db,
            tenant_id=tenant_id,
            product_id=cylinder.product_id,
            gas_group_id=cylinder.gas_group_id or "",
        )
        resolved_content_kg = content_kg
        resolved_volume_m3 = volume_m3
        stock_product = product
        stock_quantity = _resolve_fill_stock_quantity(
            content_kg=resolved_content_kg,
            volume_m3=resolved_volume_m3,
        )
        origin = FILL_OPERATION_ORIGIN
        reason_code = FILL_REASON_CODE
        action_name = "cylinder.fill"
        fill_mode = SIMPLE_FILL_MODE
        metadata_details: dict[str, object] = {
            "product_id": product.id,
            "product_name": product.name,
        }
        event_details: dict[str, object] = {
            "product_id": product.id,
            "product_name": product.name,
        }
    else:
        resolved_content_kg, resolved_volume_m3 = _resolve_cryogenic_fill_payload(
            recipe=recipe,
            content_kg=content_kg,
            volume_m3=volume_m3,
        )
        stock_product = recipe.source_product
        stock_quantity = recipe.source_quantity_liters
        origin = CRYOGENIC_FILL_OPERATION_ORIGIN
        reason_code = CRYOGENIC_FILL_REASON_CODE
        action_name = "cylinder.fill_cryogenic"
        fill_mode = CRYOGENIC_FILL_MODE
        metadata_details = {
            "source_product_id": recipe.source_product.id,
            "source_product_name": recipe.source_product.name,
            "source_quantity_liters": recipe.source_quantity_liters,
            "result_product_id": recipe.result_product.id,
            "result_product_name": recipe.result_product.name,
            "result_m3_gas": recipe.result_m3_gas,
            "result_net_weight_kg": recipe.result_net_weight_kg,
        }
        event_details = dict(metadata_details)

    adjust_required_product_stock(
        db,
        tenant_id=tenant_id,
        warehouse_id=warehouse_id,
        product_id=stock_product.id,
        quantity=-stock_quantity,
        reason=f"{origin.title()} cilindro {cylinder.serial}",
        idempotency_key=_build_fill_idempotency_key(
            cylinder_id=cylinder.id,
            warehouse_id=warehouse_id,
            source_product_id=stock_product.id,
            content_kg=resolved_content_kg,
            volume_m3=resolved_volume_m3,
            fill_operation_id=fill_operation_id,
        ),
        action_context=action_context,
    )

    # Si se especifico un tanque criogenico fuente, descontar el gas
    # consumido de su content_kg. El stock ya fue ajustado por
    # adjust_required_product_stock, pero el content_kg del tanque
    # fuente debe reflejar la nueva realidad fisica.
    # La densidad del producto criogenico se obtiene del default_weight_kg
    # del producto fuente (ej. LOX: 1141 kg/m3 = 1.141 kg/L).
    if source_cylinder_id is not None and stock_quantity is not None and stock_quantity > 0:
        source_tank = get_cylinder(db, tenant_id=tenant_id, cylinder_id=source_cylinder_id)
        if source_tank is not None and (source_tank.content_kg or 0) > 0:
            product_density_kg_per_l = _get_product_density_kg_per_l(
                db, product_id=stock_product.id
            )
            source_tank.content_kg = max(
                0.0,
                float(source_tank.content_kg or 0) - float(stock_quantity) * product_density_kg_per_l,
            )
            db.add(source_tank)

    cylinder.content_kg = resolved_content_kg if resolved_content_kg is not None else None
    cylinder.volume_m3 = resolved_volume_m3 if resolved_volume_m3 is not None else None
    cylinder.weight_current = _resolve_filled_weight_current(
        cylinder,
        content_kg=resolved_content_kg,
        weight_current=weight_current,
    )
    cylinder.current_state = "LLENADO_OK"
    db.add(cylinder)
    db.flush()

    warehouse = _require_warehouse(db, tenant_id=tenant_id, warehouse_id=warehouse_id)
    db.add(
        LogisticsCylinderStateLog(
            tenant_id=tenant_id,
            cylinder_id=cylinder.id,
            from_state=previous_state,
            to_state=cylinder.current_state,
            changed_by=action_context.actor_user_id,
            origin=origin,
            reason_code=reason_code,
            notes=notes,
            metadata_json={
                "operation": "fill",
                "fill_mode": fill_mode,
                "fill_operation_id": fill_operation_id,
                "warehouse_id": warehouse.id,
                "warehouse_name": warehouse.name,
                "content_kg": resolved_content_kg,
                "volume_m3": resolved_volume_m3,
                "weight_current": cylinder.weight_current,
                **metadata_details,
            },
        )
    )

    audit_logistics_action(
        db,
        context=action_context,
        action=action_name,
        entity_type="cylinder",
        entity_id=cylinder.id,
        details={
            "serial": cylinder.serial,
            "fill_mode": fill_mode,
            "fill_operation_id": fill_operation_id,
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "product_id": stock_product.id,
            "product_name": stock_product.name,
            "content_kg": resolved_content_kg,
            "volume_m3": resolved_volume_m3,
            "from_state": previous_state,
            "to_state": cylinder.current_state,
            **metadata_details,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.state_changed",
        entity_type="cylinder",
        entity_id=cylinder.id,
        payload={
            "serial": cylinder.serial,
            "from_state": previous_state,
            "to_state": cylinder.current_state,
            "origin": origin,
            "reason_code": reason_code,
            "fill_mode": fill_mode,
            "fill_operation_id": fill_operation_id,
            "warehouse_id": warehouse.id,
            "content_kg": resolved_content_kg,
            "volume_m3": resolved_volume_m3,
            **event_details,
        },
    )
    return cylinder


def vacate_cylinder(
    db: Session,
    *,
    tenant_id: str,
    cylinder: LogisticsCylinder,
    warehouse_id: str,
    weight_current: float | None,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsCylinder:
    _ensure_vacatable_cylinder(db, tenant_id=tenant_id, cylinder=cylinder, warehouse_id=warehouse_id)
    previous_state = cylinder.current_state
    warehouse = _require_warehouse(db, tenant_id=tenant_id, warehouse_id=warehouse_id)

    cylinder.content_kg = 0
    cylinder.volume_m3 = 0
    cylinder.weight_current = _resolve_vacated_weight_current(cylinder, weight_current=weight_current)
    cylinder.current_state = "EN_ALMACEN_VACIO"
    db.add(cylinder)
    db.flush()

    db.add(
        LogisticsCylinderStateLog(
            tenant_id=tenant_id,
            cylinder_id=cylinder.id,
            from_state=previous_state,
            to_state=cylinder.current_state,
            changed_by=action_context.actor_user_id,
            origin=VACATE_OPERATION_ORIGIN,
            reason_code=VACATE_REASON_CODE,
            notes=notes,
            metadata_json={
                "operation": "vacate",
                "warehouse_id": warehouse.id,
                "warehouse_name": warehouse.name,
                "weight_current": cylinder.weight_current,
            },
        )
    )

    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.vacate",
        entity_type="cylinder",
        entity_id=cylinder.id,
        details={
            "serial": cylinder.serial,
            "warehouse_id": warehouse.id,
            "warehouse_name": warehouse.name,
            "from_state": previous_state,
            "to_state": cylinder.current_state,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.state_changed",
        entity_type="cylinder",
        entity_id=cylinder.id,
        payload={
            "serial": cylinder.serial,
            "from_state": previous_state,
            "to_state": cylinder.current_state,
            "origin": VACATE_OPERATION_ORIGIN,
            "reason_code": VACATE_REASON_CODE,
            "warehouse_id": warehouse.id,
        },
    )
    return cylinder


def _resolve_transition_customer_context(
    db: Session, *, payload: CylinderTransitionRequest
) -> tuple[str | None, str | None]:
    if payload.customer_id is not None:
        return payload.customer_id, payload.customer_name
    if payload.movement_id is None:
        return None, None
    movement = db.scalar(
        select(LogisticsMovement).where(LogisticsMovement.id == payload.movement_id)
    )
    if movement is None:
        return None, None
    return movement.customer_id, movement.customer_name


def _validate_fill_payload(*, content_kg: float | None, volume_m3: float | None) -> None:
    if content_kg is not None and content_kg <= 0:
        raise ValueError("content_kg debe ser mayor que cero cuando se registra un llenado")
    if volume_m3 is not None and volume_m3 <= 0:
        raise ValueError("volume_m3 debe ser mayor que cero cuando se registra un llenado")
    if content_kg is None and volume_m3 is None:
        raise ValueError("Debes registrar al menos content_kg o volume_m3 para llenar el cilindro")


def _resolve_fill_stock_quantity(*, content_kg: float | None, volume_m3: float | None) -> float:
    if content_kg is not None:
        return content_kg
    assert volume_m3 is not None
    return volume_m3


def _resolve_active_cryogenic_fill_recipe(
    db: Session,
    *,
    tenant_id: str,
    cylinder: LogisticsCylinder,
    source_product_id: str | None,
) -> CryogenicFillRecipe | None:
    if cylinder.product_id is None:
        if source_product_id is not None:
            raise ValueError("El cilindro no tiene result_product_id para llenado criogenico")
        return None

    today = date.today()
    adr = db.scalar(
        select(ProductAdr)
        .where(
            ProductAdr.product_id == cylinder.product_id,
            ProductAdr.tenant_id == tenant_id,
            ProductAdr.valid_from <= today,
            or_(ProductAdr.valid_to.is_(None), ProductAdr.valid_to >= today),
        )
        .order_by(ProductAdr.valid_from.desc(), ProductAdr.created_at.desc())
        .limit(1)
    )
    if adr is None or adr.source_product_id is None:
        if source_product_id is not None:
            raise ValueError("El producto resultado no tiene receta criogenica activa")
        return None
    if source_product_id is not None and adr.source_product_id != source_product_id:
        raise ValueError("source_product_id no coincide con la receta criogenica activa del producto resultado")
    if (
        adr.source_quantity_liters is None
        or adr.net_volume_m3 is None
        or adr.net_weight_kg is None
    ):
        raise ValueError(
            "La receta criogenica activa esta incompleta: requiere source_quantity_liters, net_volume_m3 y net_weight_kg"
        )

    result_product = _require_product(db, tenant_id=tenant_id, product_id=cylinder.product_id)
    source_product = _require_product(db, tenant_id=tenant_id, product_id=adr.source_product_id)
    return CryogenicFillRecipe(
        result_product=result_product,
        source_product=source_product,
        source_quantity_liters=float(adr.source_quantity_liters),
        result_m3_gas=float(adr.net_volume_m3),
        result_net_weight_kg=float(adr.net_weight_kg),
    )


def _resolve_cryogenic_fill_payload(
    *,
    recipe: CryogenicFillRecipe,
    content_kg: float | None,
    volume_m3: float | None,
) -> tuple[float, float]:
    if content_kg is not None and abs(content_kg - recipe.result_net_weight_kg) > 1e-9:
        raise ValueError(
            "content_kg no coincide con la receta criogenica activa del producto resultado"
        )
    if volume_m3 is not None and abs(volume_m3 - recipe.result_m3_gas) > 1e-9:
        raise ValueError(
            "volume_m3 no coincide con la receta criogenica activa del producto resultado"
        )
    return recipe.result_net_weight_kg, recipe.result_m3_gas


def _get_product_density_kg_per_l(db: Session, *, product_id: str) -> float:
    # Devuelve la densidad en kg/L del producto criogenico.
    # Usa default_weight_kg (kg/m3) / 1000 para convertir a kg/L.
    # Si no hay dato, asume 1.141 (LOX) como fallback seguro.
    from plugins.productos.backend.models import Product

    product = db.get(Product, product_id)
    if product is not None:
        weight_per_m3 = product.default_weight_kg or product.weight_kg
        if weight_per_m3 is not None and weight_per_m3 > 0:
            return float(weight_per_m3) / 1000.0
    return 1.141


def _build_fill_idempotency_key(
    *,
    cylinder_id: str,
    warehouse_id: str,
    source_product_id: str,
    content_kg: float | None,
    volume_m3: float | None,
    fill_operation_id: str,
) -> str:
    return (
        f"cylinder-fill:{cylinder_id}:{warehouse_id}:{source_product_id}:"
        f"{content_kg}:{volume_m3}:{fill_operation_id}"
    )


def _require_product(db: Session, *, tenant_id: str, product_id: str) -> Product:
    product = db.scalar(
        select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id)
    )
    if product is None:
        raise LookupError("Product not found")
    return product


def _has_positive_load(cylinder: LogisticsCylinder) -> bool:
    return any(
        value is not None and float(value) > 0
        for value in (cylinder.content_kg, cylinder.volume_m3)
    )


def _require_warehouse(
    db: Session, *, tenant_id: str, warehouse_id: str
) -> LogisticsWarehouse:
    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == warehouse_id,
            LogisticsWarehouse.tenant_id == tenant_id,
        )
    )
    if warehouse is None:
        raise LookupError("Warehouse not found")
    return warehouse


def _ensure_cylinder_matches_warehouse(
    db: Session,
    *,
    tenant_id: str,
    cylinder: LogisticsCylinder,
    warehouse_id: str,
) -> None:
    current_warehouse = resolve_cylinder_current_warehouse(
        db,
        tenant_id=tenant_id,
        cylinder=cylinder,
    )
    if current_warehouse.warehouse_id is None:
        return
    if current_warehouse.warehouse_id == warehouse_id:
        return
    raise ValueError(
        "El cilindro no está ubicado en el almacén origen seleccionado para esta operación"
    )


def _ensure_fillable_cylinder(
    db: Session,
    *,
    tenant_id: str,
    cylinder: LogisticsCylinder,
    warehouse_id: str,
) -> None:
    if cylinder.current_state in NON_WAREHOUSE_STATES:
        raise ValueError("Solo se puede llenar un cilindro que esté en almacén")
    if _has_positive_load(cylinder) or cylinder.current_state == "LLENADO_OK":
        raise ValueError("El cilindro ya tiene carga registrada. Debes vaciarlo antes de volver a llenarlo")
    if cylinder.current_state not in FILLABLE_EMPTY_STATES:
        raise ValueError(
            f"El estado actual '{cylinder.current_state}' no admite llenado operativo"
        )
    if not has_valid_adr(db, cylinder):
        raise ValueError("El cilindro requiere datos ADR válidos del producto antes de llenarlo")
    if not has_valid_hydrotest(cylinder):
        raise ValueError("El cilindro requiere prueba hidrostática vigente antes de llenarlo")
    _ensure_cylinder_matches_warehouse(
        db,
        tenant_id=tenant_id,
        cylinder=cylinder,
        warehouse_id=warehouse_id,
    )


def _ensure_vacatable_cylinder(
    db: Session,
    *,
    tenant_id: str,
    cylinder: LogisticsCylinder,
    warehouse_id: str,
) -> None:
    if cylinder.current_state in NON_WAREHOUSE_STATES:
        raise ValueError("Solo se puede vaciar un cilindro que esté en almacén")
    if not _has_positive_load(cylinder) and cylinder.current_state != "LLENADO_OK":
        raise ValueError("El cilindro ya está vacío")
    _ensure_cylinder_matches_warehouse(
        db,
        tenant_id=tenant_id,
        cylinder=cylinder,
        warehouse_id=warehouse_id,
    )


def _resolve_filled_weight_current(
    cylinder: LogisticsCylinder,
    *,
    content_kg: float | None,
    weight_current: float | None,
) -> float | None:
    if weight_current is not None:
        return weight_current
    if content_kg is not None and cylinder.weight_origin is not None:
        return float(cylinder.weight_origin) + content_kg
    return float(cylinder.weight_current) if cylinder.weight_current is not None else None


def _resolve_vacated_weight_current(
    cylinder: LogisticsCylinder,
    *,
    weight_current: float | None,
) -> float | None:
    if weight_current is not None:
        return weight_current
    if cylinder.weight_origin is not None:
        return float(cylinder.weight_origin)
    return None


def _ownership_label_for_non_customer_state(target_state: str) -> str:
    if target_state in {"EN_ALMACEN_VACIO", "VACIO_EN_ALMACEN", "LLENADO_OK"}:
        return "ALMACEN"
    return "JORNADA"


def _sync_cylinder_ownership_for_transition(
    db: Session,
    *,
    cylinder: LogisticsCylinder,
    previous_state: str,
    payload: CylinderTransitionRequest,
    action_context: LogisticsActionContext,
) -> None:
    target_state = payload.to_state
    customer_id, customer_name = _resolve_transition_customer_context(db, payload=payload)

    if target_state in CUSTOMER_POSSESSION_STATES:
        if customer_id is None:
            raise StateTransitionError(
                f"Transición a '{target_state}' requiere customer_id o movement_id con cliente trazable"
            )
        register_ownership_change(
            db,
            cylinder=cylinder,
            movement_id=payload.movement_id,
            customer_id=customer_id,
            customer_name=customer_name,
            notes=payload.notes,
            action_context=action_context,
        )
        return

    if previous_state not in CUSTOMER_POSSESSION_STATES:
        return

    latest_ownership = get_latest_ownership(db, cylinder_id=cylinder.id)
    if latest_ownership is not None and latest_ownership.customer_id is None:
        return
    register_ownership_change(
        db,
        cylinder=cylinder,
        movement_id=payload.movement_id,
        customer_id=None,
        customer_name=_ownership_label_for_non_customer_state(target_state),
        notes=payload.notes,
        action_context=action_context,
    )


def _apply_cylinder_payload(
    cylinder: LogisticsCylinder,
    payload: CylinderCreateRequest | CylinderUpdateRequest,
    *,
    partial: bool = False,
) -> None:
    field_set = payload.model_fields_set

    def should_apply(field_name: str) -> bool:
        return not partial or field_name in field_set

    serial = getattr(payload, "serial", None)
    if serial and should_apply("serial"):
        cylinder.serial = serial.strip().upper()

    text_fields = {
        "description": payload.description.strip() if payload.description else None,
        "barcode1": payload.barcode1.strip().upper() if payload.barcode1 else None,
        "barcode2": payload.barcode2.strip().upper() if payload.barcode2 else None,
        "condition": payload.condition.strip().upper() if payload.condition else None,
        "country_code": payload.country_code.strip().upper() if payload.country_code else None,
        "box_number": payload.box_number.strip().upper() if payload.box_number else None,
        "medical_notes": payload.medical_notes.strip() if payload.medical_notes else None,
        "manufacturer_code": payload.manufacturer_code.strip().upper()
        if payload.manufacturer_code
        else None,
        "location": payload.location.strip() if payload.location else None,
    }
    for field_name, value in text_fields.items():
        if should_apply(field_name):
            setattr(cylinder, field_name, value)

    for field_name in [
        "branch_id",
        "container_type",
        "gas_group_id",
        "product_id",
        "content_kg",
        "volume_m3",
        "brand_id",
        "cost",
        "price",
        "manufacturer_date",
        "manufacture_year",
        "weight_origin",
        "weight_current",
        "last_hydrotest_date",
        "next_hydrotest_date",
    ]:
        if should_apply(field_name):
            setattr(cylinder, field_name, getattr(payload, field_name))

    if should_apply("is_service") and payload.is_service is not None:
        cylinder.is_service = payload.is_service
    is_medical = getattr(payload, "is_medical", None)
    if should_apply("is_medical") and is_medical is not None:
        cylinder.is_medical = is_medical
    is_active = getattr(payload, "is_active", None)
    if should_apply("is_active") and is_active is not None:
        cylinder.is_active = is_active


def _validate_container_type_coherence(
    db: Session,
    *,
    tenant_id: str,
    cylinder: LogisticsCylinder,
) -> None:
    if cylinder.container_type != "CRYOGENIC_TANK":
        return
    if cylinder.product_id is None:
        raise ValueError(
            "Un envase criogenico (CRYOGENIC_TANK) requiere product_id del gas liquido"
        )
    is_cryogenic_source = db.scalar(
        select(ProductAdr.id)
        .where(
            ProductAdr.tenant_id == tenant_id,
            ProductAdr.source_product_id == cylinder.product_id,
            ProductAdr.source_quantity_liters.is_not(None),
            ProductAdr.source_quantity_liters > 0,
        )
        .limit(1)
    )
    if is_cryogenic_source is None:
        raise ValueError(
            "El gas liquido del tanque criogenico debe ser producto fuente de al menos una receta criogenica"
        )


def _validate_initial_entry_payload(
    payload: CylinderCreateRequest,
    *,
    warehouse_id: str | None,
) -> None:
    if payload.entry_mode is None:
        return
    if warehouse_id is None:
        raise ValueError(
            "No se pudo resolver un almacen activo unico para el usuario. Ajusta el contexto operativo antes de crear el envase."
        )
    if payload.entry_mode == ENTRY_MODE_EMPTY_FROM_CUSTOMER and not payload.customer_id:
        raise ValueError("customer_id es obligatorio cuando el envase entra vacio desde cliente")
    if payload.entry_mode in ENTRY_MODE_FULL_STATES:
        if payload.product_id is None and payload.gas_group_id is None:
            raise ValueError("product_id es obligatorio cuando el envase entra lleno")
        if not payload.minimal_route_create and (payload.content_kg is None or payload.content_kg <= 0):
            raise ValueError("content_kg debe ser mayor que cero cuando el envase entra lleno")


def _build_document_reference(payload: CylinderCreateRequest) -> str | None:
    if payload.entry_mode is not None and payload.document_number:
        document_type = ENTRY_MODE_DOCUMENT_TYPE.get(payload.entry_mode, payload.document_type)
        if document_type:
            return f"{document_type}:{payload.document_number}"
    if not payload.document_type or not payload.document_number:
        return None
    return f"{payload.document_type}:{payload.document_number}"


def _build_initial_state_notes(
    *,
    payload: CylinderCreateRequest,
    warehouse_id: str | None,
    document_reference: str | None,
) -> str:
    labels = {
        ENTRY_MODE_EMPTY_FROM_CUSTOMER: "ALTA CILINDRO VACIO DESDE CLIENTE",
        ENTRY_MODE_FULL_FROM_SUPPLIER: "ALTA CILINDRO LLENO DESDE PROVEEDOR",
    }
    parts = [labels.get(payload.entry_mode or "", "ALTA CILINDRO")]
    if warehouse_id:
        parts.append(f"almacen={warehouse_id}")
    if document_reference:
        parts.append(f"doc={document_reference}")
    return " | ".join(parts)


def _build_initial_state_metadata(
    *,
    payload: CylinderCreateRequest,
    warehouse_id: str | None,
    document_reference: str | None,
) -> dict[str, object]:
    data: dict[str, object] = {
        "entry_mode": payload.entry_mode,
        "warehouse_id": warehouse_id,
    }
    if payload.entry_mode is not None:
        data["entry_document_type"] = ENTRY_MODE_DOCUMENT_TYPE.get(payload.entry_mode)
    if document_reference is not None:
        data["document_reference"] = document_reference
    if payload.customer_id is not None:
        data["customer_id"] = payload.customer_id
    return data


def _resolve_stock_product_for_gas(
    db: Session,
    *,
    tenant_id: str,
    product_id: str | None,
    gas_group_id: str,
) -> Product:
    target_id = product_id or gas_group_id
    if target_id is None:
        raise LookupError("Se requiere product_id o gas_group_id")
    product = db.scalar(
        select(Product).where(
            Product.tenant_id == tenant_id,
            Product.id == target_id,
            Product.is_active.is_(True),
        )
    )
    if product is None:
        raise LookupError(
            "No se encontro el producto maestro asociado al envase. Ajusta el catalogo antes de crear un envase lleno desde proveedor."
        )
    return product


def _register_initial_entry(
    db: Session,
    *,
    tenant_id: str,
    cylinder: LogisticsCylinder,
    payload: CylinderCreateRequest,
    warehouse_id: str,
    document_reference: str | None,
    action_context: LogisticsActionContext,
) -> None:
    from plugins.logistics.backend.services.movements import confirm_movement, create_movement

    product = None
    if payload.entry_mode in ENTRY_MODE_FULL_STATES and (
        payload.product_id is not None or payload.gas_group_id is not None
    ):
        product = _resolve_stock_product_for_gas(
            db,
            tenant_id=tenant_id,
            product_id=payload.product_id,
            gas_group_id=payload.gas_group_id or "",
        )

    movement_type = ENTRY_MODE_MOVEMENT_TYPE.get(payload.entry_mode or "")
    if movement_type is not None:
        movement = create_movement(
            db,
            tenant_id=tenant_id,
            created_by=action_context.actor_user_id,
            payload=MovementCreateRequest(
                branch_id=payload.branch_id,
                movement_type=movement_type,
                document_series=ENTRY_MODE_DOCUMENT_TYPE.get(payload.entry_mode or ""),
                document_number=payload.document_number,
                customer_id=payload.customer_id,
                warehouse_id=warehouse_id,
                notes=_build_initial_state_notes(
                    payload=payload,
                    warehouse_id=warehouse_id,
                    document_reference=document_reference,
                ),
                items=[
                    {
                        "cylinder_id": cylinder.id,
                        "product_id": product.id if product is not None else None,
                        "product_name": product.name if product is not None else None,
                        "quantity": 1,
                        "quantity_in": payload.content_kg if payload.entry_mode in ENTRY_MODE_FULL_STATES and payload.content_kg is not None else 1,
                        "notes": document_reference,
                    }
                ],
            ),
            action_context=action_context,
        )
        confirm_movement(
            db,
            tenant_id=tenant_id,
            movement=movement,
            action_context=action_context,
        )

    if payload.entry_mode in ENTRY_MODE_FULL_STATES and product is not None and payload.content_kg is not None:
        adjust_required_product_stock(
            db,
            tenant_id=tenant_id,
            warehouse_id=warehouse_id,
            product_id=product.id,
            quantity=payload.content_kg,
            reason=f"Alta cilindro lleno: {document_reference or cylinder.serial}",
            idempotency_key=f"cylinder-create:{cylinder.id}:stock",
            action_context=action_context,
        )


_LOCATION_DEFINING_EVENTS = {
    "WAREHOUSE_IN",
    "VEHICLE_LOAD",
    "CUSTOMER_DELIVERY",
    "CUSTOMER_PICKUP",
}

_VALID_TRANSITIONS: dict[str | None, set[str]] = {
    None: {"WAREHOUSE_IN"},
    "WAREHOUSE": {"VEHICLE_LOAD"},
    "VEHICLE": {"CUSTOMER_DELIVERY", "WAREHOUSE_IN"},
    "CUSTOMER": {"CUSTOMER_PICKUP", "VEHICLE_LOAD", "WAREHOUSE_IN"},
}


def record_cylinder_event(
    db: Session,
    *,
    cylinder_id: str,
    tenant_id: str,
    event_type: str,
    location_type: str,
    location_id: str,
    warehouse_id: str | None,
    session_id: str | None,
    customer_id: str | None,
    source_type: str,
    source_id: str | None,
    occurred_at: datetime,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderEvent:
    from uuid import uuid4 as _uuid4

    previous = get_cylinder_current_location(db, cylinder_id=cylinder_id)
    previous_ltype = previous[0] if previous else None

    allowed = _VALID_TRANSITIONS.get(previous_ltype, set())
    if event_type not in allowed and previous_ltype is not None:
        raise ValueError(
            f"Transición inválida: {previous_ltype} → {event_type} "
            f"para cilindro {cylinder_id}"
        )

    existing = db.scalar(
        select(LogisticsCylinderEvent).where(
            LogisticsCylinderEvent.cylinder_id == cylinder_id,
            LogisticsCylinderEvent.event_type == event_type,
            LogisticsCylinderEvent.location_id == location_id,
            LogisticsCylinderEvent.source_type == source_type,
            LogisticsCylinderEvent.source_id == source_id,
        )
    )
    if existing is not None:
        return existing

    event = LogisticsCylinderEvent(
        id=str(_uuid4()),
        tenant_id=tenant_id,
        cylinder_id=cylinder_id,
        event_type=event_type,
        location_type=location_type,
        location_id=location_id,
        warehouse_id=warehouse_id,
        session_id=session_id,
        customer_id=customer_id,
        source_type=source_type,
        source_id=source_id,
        occurred_at=occurred_at,
        created_by=action_context.actor_user_id,
    )
    db.add(event)
    db.flush()

    audit_logistics_action(
        db,
        context=action_context,
        action=f"cylinder.event.{event_type.lower()}",
        entity_type="cylinder",
        entity_id=cylinder_id,
        details={
            "event_id": event.id,
            "location_type": location_type,
            "location_id": location_id,
            "source_type": source_type,
            "source_id": source_id,
        },
    )
    return event


def get_last_location_event(
    db: Session, *, cylinder_id: str
) -> LogisticsCylinderEvent | None:
    return db.scalar(
        select(LogisticsCylinderEvent)
        .where(
            LogisticsCylinderEvent.cylinder_id == cylinder_id,
            LogisticsCylinderEvent.event_type.in_(_LOCATION_DEFINING_EVENTS),
        )
        .order_by(
            LogisticsCylinderEvent.occurred_at.desc(),
            LogisticsCylinderEvent.created_at.desc(),
        )
        .limit(1)
    )


def get_cylinder_current_location(
    db: Session, *, cylinder_id: str
) -> tuple[str, str] | None:
    event = get_last_location_event(db, cylinder_id=cylinder_id)
    if event is None:
        return None
    return (event.location_type, event.location_id)


def list_cylinder_events(
    db: Session, *, cylinder_id: str, limit: int = 50
) -> list[LogisticsCylinderEvent]:
    return list(
        db.scalars(
            select(LogisticsCylinderEvent)
            .where(LogisticsCylinderEvent.cylinder_id == cylinder_id)
            .order_by(
                LogisticsCylinderEvent.occurred_at.desc(),
                LogisticsCylinderEvent.created_at.desc(),
            )
            .limit(limit)
        ).all()
    )


def list_cylinders_at_customers(
    db: Session, *, tenant_id: str
) -> list[dict[str, object]]:
    """Devuelve cilindros actualmente en posesión de clientes usando lg_cylinder_events."""
    from sqlalchemy import and_

    sub = (
        select(
            LogisticsCylinderEvent.cylinder_id,
            func.max(LogisticsCylinderEvent.occurred_at).label("max_occurred"),
        )
        .where(
            LogisticsCylinderEvent.tenant_id == tenant_id,
            LogisticsCylinderEvent.event_type.in_(
                ("CUSTOMER_DELIVERY", "CUSTOMER_PICKUP", "WAREHOUSE_IN")
            ),
        )
        .group_by(LogisticsCylinderEvent.cylinder_id)
        .subquery()
    )

    latest_events = (
        select(LogisticsCylinderEvent)
        .join(
            sub,
            and_(
                LogisticsCylinderEvent.cylinder_id == sub.c.cylinder_id,
                LogisticsCylinderEvent.occurred_at == sub.c.max_occurred,
            ),
        )
        .where(
            LogisticsCylinderEvent.location_type == "CUSTOMER",
            LogisticsCylinderEvent.tenant_id == tenant_id,
        )
        .subquery()
    )

    results = list(
        db.execute(
            select(
                latest_events.c.cylinder_id,
                latest_events.c.customer_id,
                latest_events.c.location_id,
                LogisticsCylinder.serial,
                LogisticsCylinder.current_state,
            )
            .join(
                LogisticsCylinder,
                LogisticsCylinder.id == latest_events.c.cylinder_id,
            )
            .order_by(LogisticsCylinder.serial)
        ).all()
    )

    return [
        {
            "cylinder_id": r.cylinder_id,
            "serial": r.serial,
            "customer_id": r.customer_id,
            "current_state": r.current_state,
        }
        for r in results
    ]
