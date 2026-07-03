# ruff: noqa: E501
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderStateLog,
    LogisticsGasProduct,
)
from plugins.logistics.backend.schemas import (
    CylinderCreateRequest,
    CylinderSummaryItem,
    CylinderTransitionRequest,
    CylinderUpdateRequest,
    MovementCreateRequest,
)
from plugins.logistics.backend.services.state_machine import (
    ensure_transition_allowed,
    list_allowed_transitions,
)
from plugins.logistics.backend.services.stock_bridge import adjust_required_product_stock
from plugins.productos.backend.models import Product

ENTRY_MODE_EMPTY_FROM_CUSTOMER = "EMPTY_FROM_CUSTOMER"
ENTRY_MODE_FULL_FROM_SUPPLIER = "FULL_FROM_SUPPLIER"

ENTRY_MODE_TARGET_STATE = {
    ENTRY_MODE_EMPTY_FROM_CUSTOMER: "EN_ALMACEN_VACIO",
    ENTRY_MODE_FULL_FROM_SUPPLIER: "LLENADO_OK",
}

ENTRY_MODE_MOVEMENT_TYPE = {
    ENTRY_MODE_EMPTY_FROM_CUSTOMER: "IC",
    ENTRY_MODE_FULL_FROM_SUPPLIER: "IFP",
}


def list_cylinders(
    db: Session,
    *,
    tenant_id: str,
    search: str | None = None,
    state: str | None = None,
    active: bool | None = None,
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
    stmt = stmt.order_by(LogisticsCylinder.created_at.desc(), LogisticsCylinder.serial.asc())
    return list(db.scalars(stmt).all())


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


def create_cylinder(
    db: Session,
    *,
    tenant_id: str,
    payload: CylinderCreateRequest,
    warehouse_id: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsCylinder:
    _validate_initial_entry_payload(payload, warehouse_id=warehouse_id)
    cylinder = LogisticsCylinder(
        tenant_id=tenant_id,
        serial=payload.serial.strip().upper(),
        is_active=True,
    )
    _apply_cylinder_payload(cylinder, payload)
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
    _apply_cylinder_payload(cylinder, payload, partial=True)
    db.add(cylinder)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.update",
        entity_type="cylinder",
        entity_id=cylinder.id,
        details={
            "serial": cylinder.serial,
            "barcode1": cylinder.barcode1,
            "barcode2": cylinder.barcode2,
            "state": cylinder.current_state,
        },
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
    return cylinder


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
        "manufacturer_code": payload.manufacturer_code.strip().upper()
        if payload.manufacturer_code
        else None,
        "adr_category": payload.adr_category.strip().upper() if payload.adr_category else None,
        "adr_un_number": payload.adr_un_number.strip().upper() if payload.adr_un_number else None,
        "adr_label": payload.adr_label.strip().upper() if payload.adr_label else None,
        "adr_package_type": payload.adr_package_type.strip().upper()
        if payload.adr_package_type
        else None,
        "adr_merchandise": payload.adr_merchandise.strip() if payload.adr_merchandise else None,
        "adr_tunnel": payload.adr_tunnel.strip().upper() if payload.adr_tunnel else None,
        "adr_subline": payload.adr_subline.strip().upper() if payload.adr_subline else None,
        "adr_unit_measure": payload.adr_unit_measure.strip().upper()
        if payload.adr_unit_measure
        else None,
        "location": payload.location.strip() if payload.location else None,
    }
    for field_name, value in text_fields.items():
        if should_apply(field_name):
            setattr(cylinder, field_name, value)

    for field_name in [
        "branch_id",
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
        "adr_weight_kg",
        "adr_factor",
        "adr_points",
    ]:
        if should_apply(field_name):
            setattr(cylinder, field_name, getattr(payload, field_name))

    if should_apply("is_service") and payload.is_service is not None:
        cylinder.is_service = payload.is_service
    is_active = getattr(payload, "is_active", None)
    if should_apply("is_active") and is_active is not None:
        cylinder.is_active = is_active


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
    if not payload.document_type:
        raise ValueError("El tipo de documento es obligatorio para el alta operativa del envase")
    if not payload.document_number:
        raise ValueError("El numero de documento es obligatorio para el alta operativa del envase")
    if payload.entry_mode == ENTRY_MODE_EMPTY_FROM_CUSTOMER and not payload.customer_id:
        raise ValueError("customer_id es obligatorio cuando el envase entra vacio desde cliente")
    if payload.entry_mode == ENTRY_MODE_FULL_FROM_SUPPLIER:
        if payload.product_id is None and payload.gas_group_id is None:
            raise ValueError("product_id es obligatorio cuando el envase entra lleno desde proveedor")
        if payload.content_kg is None or payload.content_kg <= 0:
            raise ValueError("content_kg debe ser mayor que cero cuando el envase entra lleno desde proveedor")


def _build_document_reference(payload: CylinderCreateRequest) -> str | None:
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
    if product_id is not None:
        product = db.scalar(
            select(Product).where(
                Product.tenant_id == tenant_id,
                Product.id == product_id,
                Product.is_active.is_(True),
            )
        )
        if product is None:
            raise LookupError(
                "No se encontro el producto maestro asociado al envase. Ajusta el catalogo antes de crear un envase lleno desde proveedor."
            )
        return product
    gas = db.scalar(
        select(LogisticsGasProduct).where(
            LogisticsGasProduct.tenant_id == tenant_id,
            LogisticsGasProduct.id == gas_group_id,
        )
    )
    if gas is None:
        raise LookupError("Gas product not found")
    product = db.scalar(
        select(Product).where(
            Product.tenant_id == tenant_id,
            Product.sku == gas.code,
            Product.condition_code == "GAS",
            Product.is_active.is_(True),
        )
    )
    if product is None:
        raise LookupError(
            f"No se encontro el producto maestro para el gas {gas.code}. Ajusta el catalogo antes de crear un envase lleno desde proveedor."
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
    if payload.entry_mode == ENTRY_MODE_FULL_FROM_SUPPLIER and (
        payload.product_id is not None or payload.gas_group_id is not None
    ):
        product = _resolve_stock_product_for_gas(
            db,
            tenant_id=tenant_id,
            product_id=payload.product_id,
            gas_group_id=payload.gas_group_id or "",
        )

    movement = create_movement(
        db,
        tenant_id=tenant_id,
        created_by=action_context.actor_user_id,
        payload=MovementCreateRequest(
            branch_id=payload.branch_id,
            movement_type=ENTRY_MODE_MOVEMENT_TYPE[payload.entry_mode or ENTRY_MODE_EMPTY_FROM_CUSTOMER],
            document_series=payload.document_type,
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
                    "quantity_in": payload.content_kg if payload.entry_mode == ENTRY_MODE_FULL_FROM_SUPPLIER and payload.content_kg is not None else 1,
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

    if payload.entry_mode == ENTRY_MODE_FULL_FROM_SUPPLIER and product is not None and payload.content_kg is not None:
        adjust_required_product_stock(
            db,
            tenant_id=tenant_id,
            warehouse_id=warehouse_id,
            product_id=product.id,
            quantity=payload.content_kg,
            reason=f"Alta cilindro lleno desde proveedor: {document_reference or cylinder.serial}",
            idempotency_key=f"cylinder-create:{cylinder.id}:stock",
            action_context=action_context,
        )
