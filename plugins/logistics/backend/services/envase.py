# ruff: noqa: E501
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.crm.backend.services.customers import require_customer
from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderLabelHistory,
    LogisticsCylinderOwnership,
    LogisticsCylinderRetimbrado,
    LogisticsCylinderService,
)
from plugins.logistics.backend.schemas import (
    CylinderRetimbradoCreateRequest,
    CylinderServiceCreateRequest,
    CylinderServiceUpdateRequest,
    PrintLabelRequest,
)
from plugins.logistics.backend.services.product_bridge import (
    resolve_brand_name,
    resolve_gas_product_name,
)
from plugins.productos.backend.models import Product

CUSTOMER_POSSESSION_STATES = {"EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO"}


def list_retimbrados(db: Session, *, cylinder_id: str) -> list[LogisticsCylinderRetimbrado]:
    return list(
        db.scalars(
            select(LogisticsCylinderRetimbrado)
            .where(LogisticsCylinderRetimbrado.cylinder_id == cylinder_id)
            .order_by(
                LogisticsCylinderRetimbrado.retimbrado_date.desc(),
                LogisticsCylinderRetimbrado.created_at.desc(),
            )
        ).all()
    )


def create_retimbrado(
    db: Session,
    *,
    cylinder: LogisticsCylinder,
    payload: CylinderRetimbradoCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderRetimbrado:
    retimbrado = LogisticsCylinderRetimbrado(
        cylinder_id=cylinder.id,
        retimbrado_date=payload.retimbrado_date,
        manufacture_code=payload.manufacture_code,
        manufacture_year=payload.manufacture_year,
        serial_number=payload.serial_number,
        weight_origin=payload.weight_origin,
        weight_current=payload.weight_current,
        service_pressure=payload.service_pressure,
        test_pressure=payload.test_pressure,
        approval_number=payload.approval_number,
        danger_class=payload.danger_class,
        marking1=payload.marking1,
        marking2=payload.marking2,
        package_format=payload.package_format,
        transport_code=payload.transport_code,
        adr_label=payload.adr_label,
        adr_tunnel=payload.adr_tunnel,
        un_number=payload.un_number,
        food_registry=payload.food_registry,
        movement_id=payload.movement_id,
        notes=payload.notes,
        created_by=action_context.actor_user_id,
    )
    if payload.manufacture_code:
        cylinder.manufacturer_code = payload.manufacture_code.strip().upper()
    if payload.manufacture_year is not None:
        cylinder.manufacture_year = payload.manufacture_year
    if payload.weight_origin is not None:
        cylinder.weight_origin = payload.weight_origin
    if payload.weight_current is not None:
        cylinder.weight_current = payload.weight_current
    db.add(cylinder)
    db.add(retimbrado)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.retimbrado.create",
        entity_type="cylinder_retimbrado",
        entity_id=retimbrado.id,
        details={"cylinder_id": cylinder.id, "serial": cylinder.serial},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.retimbrado_registered",
        entity_type="cylinder_retimbrado",
        entity_id=retimbrado.id,
        payload={"cylinder_id": cylinder.id, "serial": cylinder.serial},
    )
    return retimbrado


def list_ownership_history(db: Session, *, cylinder_id: str) -> list[LogisticsCylinderOwnership]:
    return list(
        db.scalars(
            select(LogisticsCylinderOwnership)
            .where(LogisticsCylinderOwnership.cylinder_id == cylinder_id)
            .order_by(
                LogisticsCylinderOwnership.change_date.desc(),
                LogisticsCylinderOwnership.created_at.desc(),
            )
        ).all()
    )


def get_latest_ownership(
    db: Session, *, cylinder_id: str
) -> LogisticsCylinderOwnership | None:
    return db.scalar(
        select(LogisticsCylinderOwnership)
        .where(LogisticsCylinderOwnership.cylinder_id == cylinder_id)
        .order_by(
            LogisticsCylinderOwnership.change_date.desc(),
            LogisticsCylinderOwnership.created_at.desc(),
        )
        .limit(1)
    )


def register_ownership_change(
    db: Session,
    *,
    cylinder: LogisticsCylinder,
    movement_id: str | None,
    customer_id: str | None,
    customer_name: str | None,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderOwnership:
    existing = None
    if movement_id is not None:
        existing = db.scalar(
            select(LogisticsCylinderOwnership).where(
                LogisticsCylinderOwnership.cylinder_id == cylinder.id,
                LogisticsCylinderOwnership.movement_id == movement_id,
            )
        )
    if existing is not None:
        return existing

    resolved_customer_name = customer_name
    if customer_id is not None:
        customer = require_customer(db, tenant_id=action_context.tenant_id, customer_id=customer_id)
        resolved_customer_name = customer.legal_name

    ownership = LogisticsCylinderOwnership(
        cylinder_id=cylinder.id,
        customer_id=customer_id,
        customer_name=resolved_customer_name,
        movement_id=movement_id,
        condition=cylinder.condition,
        notes=notes,
        created_by=action_context.actor_user_id,
    )
    db.add(ownership)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.ownership.change",
        entity_type="cylinder_ownership",
        entity_id=ownership.id,
        details={"cylinder_id": cylinder.id, "customer_name": resolved_customer_name},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.ownership_changed",
        entity_type="cylinder_ownership",
        entity_id=ownership.id,
        payload={"cylinder_id": cylinder.id, "customer_name": resolved_customer_name},
    )
    return ownership


def list_label_history(db: Session, *, cylinder_id: str) -> list[LogisticsCylinderLabelHistory]:
    return list(
        db.scalars(
            select(LogisticsCylinderLabelHistory)
            .where(LogisticsCylinderLabelHistory.cylinder_id == cylinder_id)
            .order_by(LogisticsCylinderLabelHistory.printed_at.desc())
        ).all()
    )


def build_label_data(db: Session, *, cylinder: LogisticsCylinder) -> dict[str, object | None]:
    brand_name = resolve_brand_name(db, cylinder.brand_id) if cylinder.brand_id else None
    gas_name = None
    if cylinder.product_id is not None:
        gas_name = db.scalar(select(Product.name).where(Product.id == cylinder.product_id))
    if gas_name is None and cylinder.gas_group_id is not None:
        gas_name = resolve_gas_product_name(db, cylinder.gas_group_id, cylinder.tenant_id)
    latest_retimbrado = db.scalar(
        select(LogisticsCylinderRetimbrado)
        .where(LogisticsCylinderRetimbrado.cylinder_id == cylinder.id)
        .order_by(
            LogisticsCylinderRetimbrado.retimbrado_date.desc(),
            LogisticsCylinderRetimbrado.created_at.desc(),
        )
    )
    latest_label = db.scalar(
        select(LogisticsCylinderLabelHistory)
        .where(LogisticsCylinderLabelHistory.cylinder_id == cylinder.id)
        .order_by(LogisticsCylinderLabelHistory.printed_at.desc())
    )
    return {
        "cylinder_id": cylinder.id,
        "serial": cylinder.serial,
        "barcode2": cylinder.barcode2,
        "description": cylinder.description,
        "brand_name": brand_name,
        "gas_product_name": gas_name,
        "manufacturer_code": cylinder.manufacturer_code,
        "manufacture_year": cylinder.manufacture_year,
        "approval_number": latest_retimbrado.approval_number if latest_retimbrado else None,
        "danger_class": latest_retimbrado.danger_class if latest_retimbrado else None,
        "un_number": latest_retimbrado.un_number if latest_retimbrado else cylinder.adr_un_number,
        "last_hydrotest_date": cylinder.last_hydrotest_date,
        "next_hydrotest_date": cylinder.next_hydrotest_date,
        "adr_label": cylinder.adr_label,
        "adr_un_number": cylinder.adr_un_number,
        "is_medical": cylinder.is_medical,
        "medical_notes": cylinder.medical_notes,
        "label_origin": latest_label.origin if latest_label else None,
    }


def print_label(
    db: Session,
    *,
    cylinder: LogisticsCylinder,
    payload: PrintLabelRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderLabelHistory:
    origin = payload.origin.strip().upper()
    if origin == "REIMPRESION" and not payload.reason:
        raise ValueError("La reimpresión requiere un motivo")
    label_history = LogisticsCylinderLabelHistory(
        cylinder_id=cylinder.id,
        origin=origin,
        reason=payload.reason,
        printer_name=payload.printer_name,
        copies=payload.copies,
        printed_by=action_context.actor_user_id,
    )
    db.add(label_history)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.label.print",
        entity_type="cylinder_label_history",
        entity_id=label_history.id,
        details={"cylinder_id": cylinder.id, "origin": origin, "copies": payload.copies},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.label_printed",
        entity_type="cylinder_label_history",
        entity_id=label_history.id,
        payload={"cylinder_id": cylinder.id, "origin": origin, "copies": payload.copies},
    )
    return label_history


def list_cylinder_services(db: Session, *, cylinder_id: str) -> list[LogisticsCylinderService]:
    return list(
        db.scalars(
            select(LogisticsCylinderService)
            .where(LogisticsCylinderService.cylinder_id == cylinder_id)
            .order_by(LogisticsCylinderService.created_at.desc())
        ).all()
    )


def get_cylinder_service(
    db: Session,
    *,
    cylinder_id: str,
    service_id: str,
) -> LogisticsCylinderService | None:
    return db.scalar(
        select(LogisticsCylinderService).where(
            LogisticsCylinderService.id == service_id,
            LogisticsCylinderService.cylinder_id == cylinder_id,
        )
    )


def create_cylinder_service(
    db: Session,
    *,
    cylinder: LogisticsCylinder,
    payload: CylinderServiceCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderService:
    service = LogisticsCylinderService(
        cylinder_id=cylinder.id,
        order_id=payload.order_id,
        order_item_id=payload.order_item_id,
        movement_id=payload.movement_id,
        service_type_id=payload.service_type_id,
        status=payload.status or "PENDIENTE",
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes,
        purchase_price=payload.purchase_price,
        sale_price=payload.sale_price,
        stock_in=payload.stock_in,
        stock_out=payload.stock_out,
        group_code=payload.group_code,
        discount_pct=payload.discount_pct,
        discount_amount=payload.discount_amount,
        total_amount=payload.total_amount,
        created_by=action_context.actor_user_id,
    )
    db.add(service)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.service.create",
        entity_type="cylinder_service",
        entity_id=service.id,
        details={"cylinder_id": cylinder.id, "service_type_id": service.service_type_id},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.service_registered",
        entity_type="cylinder_service",
        entity_id=service.id,
        payload={"cylinder_id": cylinder.id, "service_type_id": service.service_type_id},
    )
    return service


def update_cylinder_service(
    db: Session,
    *,
    service: LogisticsCylinderService,
    payload: CylinderServiceUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderService:
    for field_name in [
        "service_type_id",
        "status",
        "start_date",
        "end_date",
        "notes",
        "purchase_price",
        "sale_price",
        "stock_in",
        "stock_out",
        "group_code",
        "discount_pct",
        "discount_amount",
        "total_amount",
    ]:
        value = getattr(payload, field_name)
        if value is not None:
            setattr(service, field_name, value)
    db.add(service)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.service.update",
        entity_type="cylinder_service",
        entity_id=service.id,
        details={"status": service.status, "service_type_id": service.service_type_id},
    )
    if service.status == "REALIZADO":
        emit_logistics_event(
            db,
            context=action_context,
            event_name="logistics.cylinder.service_completed",
            entity_type="cylinder_service",
            entity_id=service.id,
            payload={"status": service.status, "service_type_id": service.service_type_id},
        )
    return service


def delete_cylinder_service(
    db: Session,
    *,
    service: LogisticsCylinderService,
    action_context: LogisticsActionContext,
) -> None:
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder.service.delete",
        entity_type="cylinder_service",
        entity_id=service.id,
        details={"status": service.status, "service_type_id": service.service_type_id},
    )
    db.delete(service)
