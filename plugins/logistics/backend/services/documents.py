from __future__ import annotations

from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import (
    LogisticsAdrProductConfig,
    LogisticsCylinder,
    LogisticsDeliveryPoint,
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsRoute,
    LogisticsRouteStop,
    LogisticsVehicle,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import (
    AdrPointsItemRead,
    AdrPointsSummaryRead,
    DispatchTicketRead,
    RouteAgendaReportRead,
    RouteAgendaReportStopRead,
    TransferAlbaranRead,
    WaybillDetailItemRead,
    WaybillRead,
    WaybillSummaryRead,
)
from plugins.productos.backend.models import Product, ProductAdr


def _movement_items(db: Session, movement_id: str) -> list[LogisticsMovementItem]:
    return list(
        db.scalars(
            select(LogisticsMovementItem)
            .where(LogisticsMovementItem.movement_id == movement_id)
            .order_by(LogisticsMovementItem.created_at.asc())
        ).all()
    )


def _latest_adr_config(
    db: Session, *, tenant_id: str, product_id: str, today: date
) -> LogisticsAdrProductConfig | None:
    return db.scalar(
        select(LogisticsAdrProductConfig)
        .where(
            LogisticsAdrProductConfig.tenant_id == tenant_id,
            LogisticsAdrProductConfig.product_id == product_id,
            LogisticsAdrProductConfig.valid_from <= today,
            or_(
                LogisticsAdrProductConfig.valid_to.is_(None),
                LogisticsAdrProductConfig.valid_to >= today,
            ),
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
            or_(ProductAdr.valid_to.is_(None), ProductAdr.valid_to >= today),
        )
        .order_by(ProductAdr.valid_from.desc())
    )


def _product_weight(db: Session, *, tenant_id: str, product_id: str | None) -> float | None:
    if product_id is None:
        return None
    product = db.scalar(
        select(Product).where(Product.tenant_id == tenant_id, Product.id == product_id)
    )
    if product is None or product.weight_kg is None:
        return None
    return float(product.weight_kg)


def build_waybill(db: Session, *, movement: LogisticsMovement) -> WaybillRead:
    warehouse = None
    vehicle = None
    if movement.warehouse_id is not None:
        warehouse = db.scalar(
            select(LogisticsWarehouse).where(LogisticsWarehouse.id == movement.warehouse_id)
        )
    if movement.vehicle_id is not None:
        vehicle = db.scalar(
            select(LogisticsVehicle).where(LogisticsVehicle.id == movement.vehicle_id)
        )
    today = movement.created_at.date()
    items: list[WaybillDetailItemRead] = []
    total_packages = 0.0
    total_weight = 0.0
    total_points = 0.0
    for item in _movement_items(db, movement.id):
        quantity = float(item.quantity_out or item.quantity_in or item.quantity or 0)
        unit_weight = _product_weight(db, tenant_id=movement.tenant_id, product_id=item.product_id)
        total_item_weight = quantity * unit_weight if unit_weight is not None else None
        adr_points = None
        if item.product_id is not None:
            adr_cfg = _latest_adr_config(
                db, tenant_id=movement.tenant_id, product_id=item.product_id, today=today
            )
            if adr_cfg is not None and adr_cfg.adr_points is not None:
                adr_points = float(adr_cfg.adr_points) * quantity
            else:
                fallback = _fallback_prod_adr(
                    db, tenant_id=movement.tenant_id, product_id=item.product_id, today=today
                )
                if fallback is not None and fallback.points is not None:
                    adr_points = float(fallback.points) * quantity
        total_packages += quantity
        total_weight += total_item_weight or 0
        total_points += adr_points or 0
        items.append(
            WaybillDetailItemRead(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=quantity,
                unit_weight_kg=unit_weight,
                total_weight_kg=total_item_weight,
                adr_points=adr_points,
            )
        )
    return WaybillRead(
        movement_id=movement.id,
        movement_type=movement.movement_type,
        document=movement.full_document,
        warehouse_id=movement.warehouse_id,
        warehouse_name=warehouse.name if warehouse is not None else None,
        customer_id=movement.customer_id,
        customer_name=movement.customer_name,
        vehicle_id=movement.vehicle_id,
        vehicle_plate=vehicle.plate if vehicle is not None else movement.plate,
        driver_id=movement.driver_id,
        destination_place=movement.destination_place,
        destination_address=movement.destination_address,
        items=items,
        total_packages=total_packages,
        total_weight_kg=total_weight,
        total_adr_points=total_points,
    )


def build_waybill_summary(db: Session, *, movement: LogisticsMovement) -> WaybillSummaryRead:
    waybill = build_waybill(db, movement=movement)
    return WaybillSummaryRead(
        movement_id=movement.id,
        total_packages=waybill.total_packages,
        total_weight_kg=waybill.total_weight_kg,
        total_adr_points=waybill.total_adr_points,
    )


def build_route_agenda_report(db: Session, *, route: LogisticsRoute) -> RouteAgendaReportRead:
    stops: list[RouteAgendaReportStopRead] = []
    for stop in db.scalars(
        select(LogisticsRouteStop)
        .where(LogisticsRouteStop.route_id == route.id)
        .order_by(LogisticsRouteStop.stop_order)
    ).all():
        delivery_point = db.scalar(
            select(LogisticsDeliveryPoint).where(
                LogisticsDeliveryPoint.id == stop.delivery_point_id
            )
        )
        stops.append(
            RouteAgendaReportStopRead(
                stop_id=stop.id,
                stop_order=stop.stop_order,
                customer_name=delivery_point.customer_name if delivery_point is not None else None,
                address=delivery_point.address if delivery_point is not None else None,
                scheduled_time=stop.scheduled_time,
                status=stop.status,
            )
        )
    return RouteAgendaReportRead(
        route_id=route.id,
        route_date=route.route_date,
        driver_id=route.driver_id,
        vehicle_id=route.vehicle_id,
        stops=stops,
    )


def build_dispatch_ticket(db: Session, *, movement: LogisticsMovement) -> DispatchTicketRead:
    return DispatchTicketRead(**build_waybill(db, movement=movement).model_dump())


def build_transfer_albaran(db: Session, *, movement: LogisticsMovement) -> TransferAlbaranRead:
    return TransferAlbaranRead(**build_waybill(db, movement=movement).model_dump())


def build_adr_points_summary(db: Session, *, movement: LogisticsMovement) -> AdrPointsSummaryRead:
    today = movement.created_at.date()
    items: list[AdrPointsItemRead] = []
    total_points = 0.0
    for item in _movement_items(db, movement.id):
        quantity = float(item.quantity_out or item.quantity_in or item.quantity or 0)
        points_per_unit = 0.0
        if item.product_id is not None:
            adr_cfg = _latest_adr_config(
                db, tenant_id=movement.tenant_id, product_id=item.product_id, today=today
            )
            if adr_cfg is not None and adr_cfg.adr_points is not None:
                points_per_unit = float(adr_cfg.adr_points)
            else:
                fallback = _fallback_prod_adr(
                    db, tenant_id=movement.tenant_id, product_id=item.product_id, today=today
                )
                if fallback is not None and fallback.points is not None:
                    points_per_unit = float(fallback.points)
        total_item_points = points_per_unit * quantity
        total_points += total_item_points
        items.append(
            AdrPointsItemRead(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=quantity,
                adr_points_per_unit=points_per_unit,
                total_adr_points=total_item_points,
            )
        )
    return AdrPointsSummaryRead(movement_id=movement.id, total_adr_points=total_points, items=items)
