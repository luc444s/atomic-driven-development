from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsOrder,
    LogisticsOrderItem,
    LogisticsPlanPreload,
    LogisticsPlanPreloadItem,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import (
    MovementRead,
    OrderItemRead,
    PlanningGeneratePreloadRequest,
    PlanningPendingOrderItemRead,
    PlanningPendingOrderRead,
    PlanningPlanOrderRequest,
    PlanningPlanOrderResult,
    PlanningPreloadActionResult,
    PlanningPreloadItemRead,
    PlanningPreloadRead,
    PlanningStockSummaryItem,
)
from plugins.productos.backend.models import Product
from plugins.stock.backend.models import StockBalance

OPEN_ORDER_STATUSES = ("PENDIENTE", "PLANIFICADO")
ACTIVE_PRELOAD_STATUSES = ("PENDIENTE", "ACEPTADA")


def _coverage_status(*, available: float, required: float) -> str:
    if required <= 0:
        return "green"
    if available >= required:
        return "green"
    if available > 0:
        return "yellow"
    return "red"


def _product_name_map(db: Session, *, tenant_id: str, product_ids: set[str]) -> dict[str, str]:
    if not product_ids:
        return {}
    rows = db.execute(
        select(Product.id, Product.name).where(
            Product.tenant_id == tenant_id,
            Product.id.in_(product_ids),
        )
    ).all()
    return {row.id: row.name for row in rows}


def _stock_actual_by_product(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str,
    product_ids: set[str],
) -> dict[str, float]:
    if not product_ids:
        return {}
    rows = db.execute(
        select(StockBalance.product_id, func.coalesce(func.sum(StockBalance.quantity), 0))
        .where(
            StockBalance.tenant_id == tenant_id,
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.product_id.in_(product_ids),
        )
        .group_by(StockBalance.product_id)
    ).all()
    return {row[0]: float(row[1] or 0) for row in rows}


def _stock_comprometido_by_product(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str,
    product_ids: set[str],
    exclude_order_id: str | None = None,
) -> dict[str, float]:
    if not product_ids:
        return {}
    stmt = (
        select(
            LogisticsOrderItem.product_id,
            func.coalesce(func.sum(LogisticsOrderItem.quantity_planned), 0),
        )
        .join(LogisticsOrder, LogisticsOrder.id == LogisticsOrderItem.order_id)
        .where(
            LogisticsOrder.tenant_id == tenant_id,
            LogisticsOrder.warehouse_id == warehouse_id,
            LogisticsOrder.status.in_(OPEN_ORDER_STATUSES),
            LogisticsOrderItem.product_id.is_not(None),
            LogisticsOrderItem.product_id.in_(product_ids),
        )
        .group_by(LogisticsOrderItem.product_id)
    )
    if exclude_order_id is not None:
        stmt = stmt.where(LogisticsOrder.id != exclude_order_id)
    rows = db.execute(stmt).all()
    return {row[0]: float(row[1] or 0) for row in rows}


def _stock_planificado_by_product(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str,
    product_ids: set[str],
) -> dict[str, float]:
    if not product_ids:
        return {}
    rows = db.execute(
        select(
            LogisticsPlanPreloadItem.product_id,
            func.coalesce(func.sum(LogisticsPlanPreloadItem.quantity_planned), 0),
        )
        .join(LogisticsPlanPreload, LogisticsPlanPreload.id == LogisticsPlanPreloadItem.preload_id)
        .where(
            LogisticsPlanPreload.tenant_id == tenant_id,
            LogisticsPlanPreload.warehouse_id == warehouse_id,
            LogisticsPlanPreload.status == "PENDIENTE",
            LogisticsPlanPreloadItem.product_id.in_(product_ids),
        )
        .group_by(LogisticsPlanPreloadItem.product_id)
    ).all()
    return {row[0]: float(row[1] or 0) for row in rows}


def list_stock_summary(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str,
    product_ids: set[str],
) -> list[PlanningStockSummaryItem]:
    names = _product_name_map(db, tenant_id=tenant_id, product_ids=product_ids)
    actual = _stock_actual_by_product(
        db, tenant_id=tenant_id, warehouse_id=warehouse_id, product_ids=product_ids
    )
    comprometido = _stock_comprometido_by_product(
        db, tenant_id=tenant_id, warehouse_id=warehouse_id, product_ids=product_ids
    )
    planificado = _stock_planificado_by_product(
        db, tenant_id=tenant_id, warehouse_id=warehouse_id, product_ids=product_ids
    )
    items: list[PlanningStockSummaryItem] = []
    for product_id in sorted(product_ids):
        stock_actual = actual.get(product_id, 0)
        stock_comprometido = comprometido.get(product_id, 0)
        stock_planificado = planificado.get(product_id, 0)
        stock_disponible = stock_actual - stock_comprometido - stock_planificado
        items.append(
            PlanningStockSummaryItem(
                product_id=product_id,
                product_name=names.get(product_id, product_id),
                warehouse_id=warehouse_id,
                stock_actual=stock_actual,
                stock_comprometido=stock_comprometido,
                stock_planificado=stock_planificado,
                stock_disponible=stock_disponible,
                coverage_status=_coverage_status(available=stock_disponible, required=1),
            )
        )
    return items


def list_pending_orders(
    db: Session,
    *,
    tenant_id: str,
    allowed_warehouse_ids: tuple[str, ...] | None,
    warehouse_id: str | None = None,
) -> list[PlanningPendingOrderRead]:
    stmt = select(LogisticsOrder).where(
        LogisticsOrder.tenant_id == tenant_id,
        LogisticsOrder.status.in_(OPEN_ORDER_STATUSES),
    )
    if warehouse_id is not None:
        stmt = stmt.where(LogisticsOrder.warehouse_id == warehouse_id)
    if allowed_warehouse_ids is not None:
        stmt = stmt.where(LogisticsOrder.warehouse_id.in_(allowed_warehouse_ids))
    orders = list(db.scalars(stmt.order_by(LogisticsOrder.created_at.desc())).all())
    result: list[PlanningPendingOrderRead] = []
    for order in orders:
        items = list(
            db.scalars(
                select(LogisticsOrderItem)
                .where(LogisticsOrderItem.order_id == order.id)
                .order_by(LogisticsOrderItem.created_at.asc())
            ).all()
        )
        product_ids = {item.product_id for item in items if item.product_id is not None}
        available_map = (
            {
                item.product_id: item.stock_disponible
                for item in list_stock_summary(
                    db,
                    tenant_id=tenant_id,
                    warehouse_id=order.warehouse_id or "",
                    product_ids=product_ids,
                )
            }
            if order.warehouse_id is not None
            else {}
        )
        item_reads: list[PlanningPendingOrderItemRead] = []
        order_status = "green"
        for item in items:
            pending = max(float(item.quantity_requested) - float(item.quantity_planned), 0)
            available = available_map.get(item.product_id, 0) if item.product_id is not None else 0
            coverage = _coverage_status(available=available, required=pending)
            if coverage == "red":
                order_status = "red"
            elif coverage == "yellow" and order_status != "red":
                order_status = "yellow"
            item_reads.append(
                PlanningPendingOrderItemRead(
                    order_item_id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity_requested=float(item.quantity_requested),
                    quantity_planned=float(item.quantity_planned),
                    quantity_pending=pending,
                    stock_disponible=available,
                    coverage_status=coverage,
                )
            )
        result.append(
            PlanningPendingOrderRead(
                order_id=order.id,
                customer_id=order.customer_id,
                customer_name=order.customer_name,
                warehouse_id=order.warehouse_id,
                status=order.status,
                coverage_status=order_status,
                items=item_reads,
            )
        )
    return result


def _get_preload_items(db: Session, *, preload_id: str) -> list[LogisticsPlanPreloadItem]:
    return list(
        db.scalars(
            select(LogisticsPlanPreloadItem)
            .where(LogisticsPlanPreloadItem.preload_id == preload_id)
            .order_by(LogisticsPlanPreloadItem.created_at.asc())
        ).all()
    )


def _build_preload_read(db: Session, preload: LogisticsPlanPreload) -> PlanningPreloadRead:
    items = [
        PlanningPreloadItemRead.model_validate(item)
        for item in _get_preload_items(db, preload_id=preload.id)
    ]
    return PlanningPreloadRead(
        id=preload.id,
        tenant_id=preload.tenant_id,
        warehouse_id=preload.warehouse_id,
        branch_id=preload.branch_id,
        preload_date=preload.preload_date,
        status=preload.status,
        notes=preload.notes,
        created_by=preload.created_by,
        created_at=preload.created_at,
        updated_at=preload.updated_at,
        items=items,
    )


def build_preload_read(db: Session, preload: LogisticsPlanPreload) -> PlanningPreloadRead:
    return _build_preload_read(db, preload)


def list_preloads(
    db: Session,
    *,
    tenant_id: str,
    allowed_warehouse_ids: tuple[str, ...] | None,
    warehouse_id: str | None = None,
    preload_date: date | None = None,
    status: str | None = None,
) -> list[PlanningPreloadRead]:
    stmt = select(LogisticsPlanPreload).where(LogisticsPlanPreload.tenant_id == tenant_id)
    if warehouse_id is not None:
        stmt = stmt.where(LogisticsPlanPreload.warehouse_id == warehouse_id)
    if preload_date is not None:
        stmt = stmt.where(LogisticsPlanPreload.preload_date == preload_date)
    if status is not None:
        stmt = stmt.where(LogisticsPlanPreload.status == status)
    if allowed_warehouse_ids is not None:
        stmt = stmt.where(LogisticsPlanPreload.warehouse_id.in_(allowed_warehouse_ids))
    preloads = list(
        db.scalars(
            stmt.order_by(
                LogisticsPlanPreload.preload_date.desc(), LogisticsPlanPreload.created_at.desc()
            )
        ).all()
    )
    return [_build_preload_read(db, preload) for preload in preloads]


def get_preload(db: Session, *, tenant_id: str, preload_id: str) -> LogisticsPlanPreload | None:
    return db.scalar(
        select(LogisticsPlanPreload).where(
            LogisticsPlanPreload.id == preload_id,
            LogisticsPlanPreload.tenant_id == tenant_id,
        )
    )


def plan_order(
    db: Session,
    *,
    order: LogisticsOrder,
    payload: PlanningPlanOrderRequest,
    action_context: LogisticsActionContext,
) -> PlanningPlanOrderResult:
    if order.warehouse_id is None:
        raise ValueError("Order must have a warehouse to be planned")
    items = list(
        db.scalars(
            select(LogisticsOrderItem)
            .where(LogisticsOrderItem.order_id == order.id)
            .order_by(LogisticsOrderItem.created_at.asc())
        ).all()
    )
    product_ids = {item.product_id for item in items if item.product_id is not None}
    if len(product_ids) != len(items):
        raise ValueError("All order items must have product_id before planning")

    actual = _stock_actual_by_product(
        db,
        tenant_id=order.tenant_id,
        warehouse_id=order.warehouse_id,
        product_ids=product_ids,
    )
    committed = _stock_comprometido_by_product(
        db,
        tenant_id=order.tenant_id,
        warehouse_id=order.warehouse_id,
        product_ids=product_ids,
        exclude_order_id=order.id,
    )
    planned = _stock_planificado_by_product(
        db,
        tenant_id=order.tenant_id,
        warehouse_id=order.warehouse_id,
        product_ids=product_ids,
    )
    available_map = {
        product_id: actual.get(product_id, 0)
        - committed.get(product_id, 0)
        - planned.get(product_id, 0)
        for product_id in product_ids
    }

    if payload.mode in {"all", "full"} and not payload.permit_without_stock:
        for item in items:
            assert item.product_id is not None
            pending = max(float(item.quantity_requested) - float(item.quantity_planned), 0)
            if available_map.get(item.product_id, 0) < pending:
                raise ValueError("Insufficient stock for full planning mode")

    updated_items: list[OrderItemRead] = []
    for item in items:
        assert item.product_id is not None
        pending = max(float(item.quantity_requested) - float(item.quantity_planned), 0)
        if pending <= 0:
            updated_items.append(OrderItemRead.model_validate(item))
            continue
        available = available_map.get(item.product_id, 0)
        if payload.mode in {"all", "full"}:
            planned_now = pending if (available >= pending or payload.permit_without_stock) else 0
        else:
            planned_now = (
                pending if payload.permit_without_stock else min(pending, max(available, 0))
            )
        item.quantity_planned = float(item.quantity_planned) + planned_now
        if item.quantity_planned > 0:
            item.status = 1
        db.add(item)
        available_map[item.product_id] = available - planned_now
        updated_items.append(OrderItemRead.model_validate(item))

    order.status = "PLANIFICADO"
    db.add(order)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=order.branch_id,
        action="planning.plan_order",
        entity_type="order",
        entity_id=order.id,
        details={"mode": payload.mode, "warehouse_id": order.warehouse_id},
    )
    return PlanningPlanOrderResult(
        order_id=order.id, mode=payload.mode, updated_items=updated_items
    )


def generate_preload(
    db: Session,
    *,
    tenant_id: str,
    created_by: str,
    payload: PlanningGeneratePreloadRequest,
    action_context: LogisticsActionContext,
) -> PlanningPreloadRead:
    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == payload.warehouse_id,
            LogisticsWarehouse.tenant_id == tenant_id,
        )
    )
    if warehouse is None:
        raise LookupError("Warehouse not found")
    existing = db.scalar(
        select(LogisticsPlanPreload).where(
            LogisticsPlanPreload.tenant_id == tenant_id,
            LogisticsPlanPreload.warehouse_id == payload.warehouse_id,
            LogisticsPlanPreload.preload_date == payload.preload_date,
            LogisticsPlanPreload.status.in_(ACTIVE_PRELOAD_STATUSES),
        )
    )
    if existing is not None:
        raise ValueError("An active preload already exists for the selected date and warehouse")

    order_stmt = select(LogisticsOrder).where(
        LogisticsOrder.tenant_id == tenant_id,
        LogisticsOrder.warehouse_id == payload.warehouse_id,
        LogisticsOrder.status.in_(OPEN_ORDER_STATUSES),
    )
    if payload.order_ids:
        order_stmt = order_stmt.where(LogisticsOrder.id.in_(payload.order_ids))
    orders = list(db.scalars(order_stmt).all())
    preload = LogisticsPlanPreload(
        tenant_id=tenant_id,
        warehouse_id=payload.warehouse_id,
        branch_id=warehouse.branch_id,
        preload_date=payload.preload_date,
        status="PENDIENTE",
        notes=payload.notes,
        created_by=created_by,
    )
    db.add(preload)
    db.flush()
    created_items = 0
    for order in orders:
        items = list(
            db.scalars(
                select(LogisticsOrderItem).where(LogisticsOrderItem.order_id == order.id)
            ).all()
        )
        for item in items:
            if item.product_id is None or float(item.quantity_planned) <= 0:
                continue
            db.add(
                LogisticsPlanPreloadItem(
                    tenant_id=tenant_id,
                    preload_id=preload.id,
                    order_item_id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity_planned=float(item.quantity_planned),
                    quantity_loaded=0,
                )
            )
            created_items += 1
    if created_items == 0:
        raise ValueError("No planned order items available to generate preload")
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=warehouse.branch_id,
        action="planning.preload.generate",
        entity_type="preload",
        entity_id=preload.id,
        details={
            "warehouse_id": preload.warehouse_id,
            "preload_date": preload.preload_date.isoformat(),
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        branch_id=warehouse.branch_id,
        event_name="logistics.planning.preload_generated",
        entity_type="preload",
        entity_id=preload.id,
        payload={
            "warehouse_id": preload.warehouse_id,
            "preload_date": preload.preload_date.isoformat(),
        },
    )
    return _build_preload_read(db, preload)


def accept_preload(
    db: Session,
    *,
    preload: LogisticsPlanPreload,
    action_context: LogisticsActionContext,
) -> PlanningPreloadActionResult:
    if preload.status != "PENDIENTE":
        raise ValueError("Only pending preloads can be accepted")
    movement = LogisticsMovement(
        tenant_id=preload.tenant_id,
        branch_id=preload.branch_id,
        movement_type="TR",
        warehouse_id=preload.warehouse_id,
        status="PENDIENTE",
        notes=preload.notes,
        created_by=action_context.actor_user_id,
    )
    db.add(movement)
    db.flush()
    for preload_item in _get_preload_items(db, preload_id=preload.id):
        db.add(
            LogisticsMovementItem(
                movement_id=movement.id,
                cylinder_id=None,
                product_id=preload_item.product_id,
                product_name=preload_item.product_name,
                quantity_in=0,
                quantity_out=float(preload_item.quantity_planned),
                quantity=0,
                quantity_planned=float(preload_item.quantity_planned),
                item_status="P",
                notes="Generated from preload acceptance",
            )
        )
    preload.status = "ACEPTADA"
    db.add(preload)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=preload.branch_id,
        action="planning.preload.accept",
        entity_type="preload",
        entity_id=preload.id,
        details={"movement_id": movement.id, "warehouse_id": preload.warehouse_id},
    )
    emit_logistics_event(
        db,
        context=action_context,
        branch_id=preload.branch_id,
        event_name="logistics.planning.preload_accepted",
        entity_type="preload",
        entity_id=preload.id,
        payload={"movement_id": movement.id, "warehouse_id": preload.warehouse_id},
    )
    return PlanningPreloadActionResult(
        preload=_build_preload_read(db, preload),
        movement=MovementRead.model_validate(movement),
    )


def cancel_preload(
    db: Session,
    *,
    preload: LogisticsPlanPreload,
    action_context: LogisticsActionContext,
) -> PlanningPreloadRead:
    if preload.status == "CANCELADA":
        return _build_preload_read(db, preload)
    preload.status = "CANCELADA"
    db.add(preload)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=preload.branch_id,
        action="planning.preload.cancel",
        entity_type="preload",
        entity_id=preload.id,
        details={"warehouse_id": preload.warehouse_id},
    )
    return _build_preload_read(db, preload)
