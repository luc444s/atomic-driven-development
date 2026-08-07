from __future__ import annotations

from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.integrations.stock import get_warehouse_balances
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsLoadPlan,
    LogisticsLoadPlanItem,
    LogisticsLoadSerialAssignment,
    LogisticsOperation,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.schemas import CylinderTransitionRequest
from plugins.logistics.backend.services.cylinders import transition_cylinder
from plugins.logistics.backend.services.load_serials import (
    confirm_selected_serials_for_operation,
    ensure_required_serials_for_load_plan,
    release_active_serial_assignments,
)
from plugins.logistics.backend.services.operations import confirm_transfer_in, confirm_transfer_out
from plugins.logistics.backend.services.rules import (
    ensure_capacity_not_exceeded,
    ensure_session_editable,
)
from plugins.productos.backend.models import Product, ProductAdr


def _require_product(db: Session, *, product_id: str) -> Product:
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise LookupError("Producto no encontrado")
    return product


def get_load_plan(db: Session, *, session_id: str) -> LogisticsLoadPlan | None:
    return db.scalar(
        select(LogisticsLoadPlan)
        .where(LogisticsLoadPlan.session_id == session_id)
        .order_by(LogisticsLoadPlan.updated_at.desc())
    )


def _ensure_positive_quantity_for_origin_line(
    *,
    product_name: str | None,
    planned_quantity: float,
    source_warehouse_id: str | None,
) -> None:
    if source_warehouse_id is None:
        return
    if planned_quantity > 0:
        return
    if product_name:
        raise ValueError(
            "La cantidad debe ser mayor que cero para la línea "
            f"'{product_name}' que sale desde almacén"
        )
    raise ValueError(
        "La cantidad debe ser mayor que cero para una línea que sale desde almacén"
    )


def _resolve_product_filled_weight_kg(db: Session, *, product: Product) -> float:
    # Si el producto tiene receta ADR activa con net_weight_kg, el peso real
    # lleno es la tara del envase + el peso del gas. Sin receta, usa la tara sola.
    today = date.today()
    active_adr = db.scalar(
        select(ProductAdr)
        .where(
            ProductAdr.product_id == product.id,
            ProductAdr.net_weight_kg.is_not(None),
            ProductAdr.net_weight_kg > 0,
            ProductAdr.valid_from <= today,
            (ProductAdr.valid_to.is_(None) | (ProductAdr.valid_to >= today)),
        )
        .order_by(ProductAdr.valid_from.desc())
    )
    tara = float(product.weight_kg or 0)
    if active_adr is not None:
        return tara + float(active_adr.net_weight_kg)
    return tara


def list_load_plan_items(db: Session, *, load_plan_id: str) -> list[LogisticsLoadPlanItem]:
    return list(
        db.scalars(
            select(LogisticsLoadPlanItem)
            .where(LogisticsLoadPlanItem.load_plan_id == load_plan_id)
            .order_by(LogisticsLoadPlanItem.created_at.asc())
        ).all()
    )


def upsert_load_plan(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    payload,
    action_context: LogisticsActionContext,
) -> LogisticsLoadPlan:
    ensure_session_editable(session)
    if session.status not in {"DRAFT", "LOADING", "READY_TO_DEPART"}:
        raise ValueError("La jornada ya no permite editar el plan de carga")

    load_plan = get_load_plan(db, session_id=session.id)
    if load_plan is None:
        load_plan = LogisticsLoadPlan(
            tenant_id=session.tenant_id,
            session_id=session.id,
            status="DRAFT",
            notes=payload.notes,
            created_by=action_context.actor_user_id,
        )
        db.add(load_plan)
        db.flush()
    else:
        existing_items = list_load_plan_items(db, load_plan_id=load_plan.id)
        incoming_product_ids = {item.product_id for item in payload.items}
        removed_product_ids = {
            item.product_id
            for item in existing_items
            if item.product_id not in incoming_product_ids
        }
        if removed_product_ids:
            for product_id in removed_product_ids:
                release_active_serial_assignments(
                    db,
                    session_id=session.id,
                    product_id=product_id,
                    release_reason="MANUAL",
                )
        load_plan.notes = payload.notes
        db.add(load_plan)
        db.flush()
        db.execute(
            delete(LogisticsLoadPlanItem).where(LogisticsLoadPlanItem.load_plan_id == load_plan.id)
        )

    total_weight = 0.0
    for item in payload.items:
        resolved_source_warehouse_id = item.source_warehouse_id or session.origin_warehouse_id
        _ensure_positive_quantity_for_origin_line(
            product_name=None,
            planned_quantity=float(item.planned_quantity),
            source_warehouse_id=resolved_source_warehouse_id,
        )
        product = _require_product(db, product_id=item.product_id)
        # El peso del producto base es la tara (envase vacio). Si hay receta ADR
        # activa, el peso real lleno es tara + gas. Ej: B10 vacio = 10 kg,
        # B10 lleno = 10 + 1.90 = 11.90 kg.
        filled_weight_kg = _resolve_product_filled_weight_kg(db, product=product)
        planned_weight = filled_weight_kg * float(item.planned_quantity)
        plan_item = LogisticsLoadPlanItem(
            load_plan_id=load_plan.id,
            product_id=product.id,
            product_name=product.name,
            planned_quantity=float(item.planned_quantity),
            planned_weight_kg=planned_weight,
            source_warehouse_id=resolved_source_warehouse_id,
            notes=item.notes,
        )
        db.add(plan_item)
        total_weight += planned_weight

    session.planned_weight_kg = total_weight
    session.updated_by = action_context.actor_user_id
    db.add(session)
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.load_plan.upsert",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"items": len(payload.items), "planned_weight_kg": total_weight},
    )
    return load_plan


def confirm_load_plan(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleSession:
    load_plan = get_load_plan(db, session_id=session.id)
    if load_plan is None:
        raise ValueError("La jornada no tiene un plan de carga")
    items = list_load_plan_items(db, load_plan_id=load_plan.id)
    if not items:
        session.loaded_weight_kg = 0
        session.updated_by = action_context.actor_user_id
        db.add(session)
        return session
    for item in items:
        _ensure_positive_quantity_for_origin_line(
            product_name=item.product_name,
            planned_quantity=float(item.planned_quantity or 0),
            source_warehouse_id=item.source_warehouse_id,
        )
    ensure_required_serials_for_load_plan(db, session=session, load_plan_items=items)
    total_weight = sum(float(item.planned_weight_kg or 0) for item in items)
    from plugins.logistics.backend.models import LogisticsVehicle  # local import to avoid cycle

    vehicle_model = db.scalar(
        select(LogisticsVehicle).where(LogisticsVehicle.id == session.vehicle_id)
    )
    if vehicle_model is None:
        raise LookupError("Vehiculo no encontrado")
    ensure_capacity_not_exceeded(vehicle_model, total_weight)
    confirmed_weight = confirm_transfer_out(
        db,
        session=session,
        load_plan_items=items,
        notes=notes,
        action_context=action_context,
    )
    operation = db.scalar(
        select(LogisticsOperation)
        .where(
            LogisticsOperation.session_id == session.id,
            LogisticsOperation.movement_type == "TRANSFER_OUT",
            LogisticsOperation.status == "CONFIRMED",
        )
        .order_by(LogisticsOperation.created_at.desc())
    )
    if operation is None:
        raise LookupError("No se pudo reconstruir la operación confirmada de carga")
    confirm_selected_serials_for_operation(
        db,
        tenant_id=session.tenant_id,
        session_id=session.id,
        product_ids={item.product_id for item in items},
        operation=operation,
        action_context=action_context,
    )
    session.loaded_weight_kg = confirmed_weight
    session.updated_by = action_context.actor_user_id
    db.add(session)

    _record_vehicle_load_cylinder_events(
        db,
        tenant_id=session.tenant_id,
        session=session,
        action_context=action_context,
    )

    return session


def return_remaining_stock(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    destination_warehouse_id: str | None,
    notes: str | None,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleSession:
    if session.status not in {"RETURNING", "OUTBOUND"}:
        raise ValueError("Solo una jornada OUTBOUND o RETURNING puede retornar remanente")
    balances = get_warehouse_balances(
        db,
        tenant_id=session.tenant_id,
        warehouse_id=session.mobile_warehouse_id,
    ).items
    target = destination_warehouse_id or session.origin_warehouse_id
    confirm_transfer_in(
        db,
        session=session,
        destination_warehouse_id=target,
        balances=balances,
        notes=notes,
        action_context=action_context,
    )

    # 2. DESPUÉS: transicionar seriales a EN_ALMACEN_VACIO
    #    TODO(0031.1): bulk transition para N > 100
    cylinders = list(db.scalars(
        select(LogisticsCylinder).where(
            LogisticsCylinder.tenant_id == session.tenant_id,
            LogisticsCylinder.session_id == session.id,
            LogisticsCylinder.current_state.in_(
                ("CARGA_EN_VEHICULO", "EN_RUTA",
                 "EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO")
            ),
        )
    ).all())
    for cylinder in cylinders:
        transition_cylinder(
            db, tenant_id=session.tenant_id,
            cylinder_id=cylinder.id,
            payload=CylinderTransitionRequest(
                to_state="EN_ALMACEN_VACIO",
                session_id=session.id,
                origin="SESSION_RETURN",
                notes=f"Retorno sesión {session.id}",
            ),
            action_context=action_context,
        )
        _record_warehouse_in_event(
            db,
            tenant_id=session.tenant_id,
            session=session,
            cylinder_id=cylinder.id,
            warehouse_id=target,
            action_context=action_context,
        )

    session.status = "AWAITING_RECONCILIATION"
    session.updated_by = action_context.actor_user_id
    db.add(session)
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.return_remaining",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={"destination_warehouse_id": target},
    )
    return session


def _record_vehicle_load_cylinder_events(
    db: Session,
    *,
    tenant_id: str,
    session: LogisticsVehicleSession,
    action_context: LogisticsActionContext,
) -> None:
    from datetime import UTC, datetime

    from plugins.logistics.backend.services.cylinders import record_cylinder_event

    assignments = list(
        db.scalars(
            select(LogisticsLoadSerialAssignment).where(
                LogisticsLoadSerialAssignment.session_id == session.id,
                LogisticsLoadSerialAssignment.assignment_status == "CONFIRMED",
            )
        ).all()
    )
    now = datetime.now(UTC)
    for assignment in assignments:
        record_cylinder_event(
            db,
            cylinder_id=assignment.cylinder_id,
            tenant_id=tenant_id,
            event_type="VEHICLE_LOAD",
            location_type="VEHICLE",
            location_id=session.id,
            warehouse_id=None,
            session_id=session.id,
            customer_id=None,
            source_type="LOAD",
            source_id=assignment.id,
            occurred_at=now,
            action_context=action_context,
        )


def _record_warehouse_in_event(
    db: Session,
    *,
    tenant_id: str,
    session: LogisticsVehicleSession,
    cylinder_id: str,
    warehouse_id: str,
    action_context: LogisticsActionContext,
) -> None:
    from datetime import UTC, datetime

    from plugins.logistics.backend.services.cylinders import record_cylinder_event

    record_cylinder_event(
        db,
        cylinder_id=cylinder_id,
        tenant_id=tenant_id,
        event_type="WAREHOUSE_IN",
        location_type="WAREHOUSE",
        location_id=warehouse_id,
        warehouse_id=warehouse_id,
        session_id=session.id,
        customer_id=None,
        source_type="SESSION_RETURN",
        source_id=session.id,
        occurred_at=datetime.now(UTC),
        action_context=action_context,
    )
