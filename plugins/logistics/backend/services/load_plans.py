from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.integrations.stock import get_warehouse_balances
from plugins.logistics.backend.models import (
    LogisticsLoadPlan,
    LogisticsLoadPlanItem,
    LogisticsOperation,
    LogisticsVehicleSession,
)
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
from plugins.productos.backend.models import Product


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
        product = _require_product(db, product_id=item.product_id)
        planned_weight = float(product.weight_kg or 0) * float(item.planned_quantity)
        plan_item = LogisticsLoadPlanItem(
            load_plan_id=load_plan.id,
            product_id=product.id,
            product_name=product.name,
            planned_quantity=float(item.planned_quantity),
            planned_weight_kg=planned_weight,
            source_warehouse_id=item.source_warehouse_id or session.origin_warehouse_id,
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
        raise ValueError("El plan de carga no tiene items")
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
