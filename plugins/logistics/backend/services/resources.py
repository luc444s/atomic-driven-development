from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.models import (
    LogisticsDeliveryPoint,
    LogisticsVehicle,
    LogisticsWarehouse,
    LogisticsZone,
)
from plugins.logistics.backend.schemas import (
    DeliveryPointCreateRequest,
    DeliveryPointUpdateRequest,
    VehicleCreateRequest,
    VehicleUpdateRequest,
    WarehouseCreateRequest,
    WarehouseUpdateRequest,
    ZoneCreateRequest,
)


def list_warehouses(db: Session, *, tenant_id: str) -> list[LogisticsWarehouse]:
    return list(
        db.scalars(
            select(LogisticsWarehouse)
            .where(LogisticsWarehouse.tenant_id == tenant_id)
            .order_by(LogisticsWarehouse.is_active.desc(), LogisticsWarehouse.name)
        ).all()
    )


def get_warehouse(db: Session, *, tenant_id: str, warehouse_id: str) -> LogisticsWarehouse | None:
    return db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == warehouse_id,
            LogisticsWarehouse.tenant_id == tenant_id,
        )
    )


def create_warehouse(
    db: Session,
    *,
    tenant_id: str,
    payload: WarehouseCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsWarehouse:
    warehouse = LogisticsWarehouse(
        tenant_id=tenant_id,
        name=payload.name.strip(),
        code=payload.code.strip().upper(),
        address=payload.address,
        phone=payload.phone,
    )
    db.add(warehouse)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="warehouse.create",
        entity_type="warehouse",
        entity_id=warehouse.id,
        details={"name": warehouse.name, "code": warehouse.code},
    )
    return warehouse


def update_warehouse(
    db: Session,
    *,
    warehouse: LogisticsWarehouse,
    payload: WarehouseUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsWarehouse:
    if payload.name is not None:
        warehouse.name = payload.name.strip()
    if payload.code is not None:
        warehouse.code = payload.code.strip().upper()
    if payload.address is not None:
        warehouse.address = payload.address
    if payload.phone is not None:
        warehouse.phone = payload.phone
    if payload.is_active is not None:
        warehouse.is_active = payload.is_active
    db.add(warehouse)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="warehouse.update",
        entity_type="warehouse",
        entity_id=warehouse.id,
        details={"name": warehouse.name, "code": warehouse.code, "active": warehouse.is_active},
    )
    return warehouse


def list_zones(db: Session, *, tenant_id: str) -> list[LogisticsZone]:
    return list(
        db.scalars(
            select(LogisticsZone)
            .where(LogisticsZone.tenant_id == tenant_id)
            .order_by(LogisticsZone.is_active.desc(), LogisticsZone.name)
        ).all()
    )


def create_zone(
    db: Session,
    *,
    tenant_id: str,
    payload: ZoneCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsZone:
    zone = LogisticsZone(
        tenant_id=tenant_id,
        name=payload.name.strip(),
        code=payload.code.strip().upper(),
    )
    db.add(zone)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="zone.create",
        entity_type="zone",
        entity_id=zone.id,
        details={"name": zone.name, "code": zone.code},
    )
    return zone


def get_zone(db: Session, *, tenant_id: str, zone_id: str) -> LogisticsZone | None:
    return db.scalar(
        select(LogisticsZone).where(
            LogisticsZone.id == zone_id,
            LogisticsZone.tenant_id == tenant_id,
        )
    )


def list_vehicles(db: Session, *, tenant_id: str) -> list[LogisticsVehicle]:
    return list(
        db.scalars(
            select(LogisticsVehicle)
            .where(LogisticsVehicle.tenant_id == tenant_id)
            .order_by(LogisticsVehicle.is_active.desc(), LogisticsVehicle.plate)
        ).all()
    )


def get_vehicle(db: Session, *, tenant_id: str, vehicle_id: str) -> LogisticsVehicle | None:
    return db.scalar(
        select(LogisticsVehicle).where(
            LogisticsVehicle.id == vehicle_id,
            LogisticsVehicle.tenant_id == tenant_id,
        )
    )


def create_vehicle(
    db: Session,
    *,
    tenant_id: str,
    payload: VehicleCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsVehicle:
    vehicle = LogisticsVehicle(
        tenant_id=tenant_id,
        plate=payload.plate.strip().upper(),
        vehicle_type=payload.vehicle_type,
        brand=payload.brand,
        model=payload.model,
        capacity_weight=payload.capacity_weight,
        capacity_volume=payload.capacity_volume,
        useful_load=payload.useful_load,
        adr_class=payload.adr_class,
        status=payload.status or "DISPONIBLE",
        warehouse_id=payload.warehouse_id,
    )
    db.add(vehicle)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle.create",
        entity_type="vehicle",
        entity_id=vehicle.id,
        details={"plate": vehicle.plate, "status": vehicle.status},
    )
    return vehicle


def update_vehicle(
    db: Session,
    *,
    vehicle: LogisticsVehicle,
    payload: VehicleUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsVehicle:
    for field in [
        "vehicle_type",
        "brand",
        "model",
        "capacity_weight",
        "capacity_volume",
        "useful_load",
        "adr_class",
        "status",
        "warehouse_id",
        "is_active",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(vehicle, field, value)
    db.add(vehicle)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle.update",
        entity_type="vehicle",
        entity_id=vehicle.id,
        details={"plate": vehicle.plate, "status": vehicle.status, "active": vehicle.is_active},
    )
    return vehicle


def list_delivery_points(db: Session, *, tenant_id: str) -> list[LogisticsDeliveryPoint]:
    return list(
        db.scalars(
            select(LogisticsDeliveryPoint)
            .where(LogisticsDeliveryPoint.tenant_id == tenant_id)
            .order_by(
                LogisticsDeliveryPoint.is_primary.desc(),
                LogisticsDeliveryPoint.customer_name,
                LogisticsDeliveryPoint.address,
            )
        ).all()
    )


def get_delivery_point(
    db: Session,
    *,
    tenant_id: str,
    delivery_point_id: str,
) -> LogisticsDeliveryPoint | None:
    return db.scalar(
        select(LogisticsDeliveryPoint).where(
            LogisticsDeliveryPoint.id == delivery_point_id,
            LogisticsDeliveryPoint.tenant_id == tenant_id,
        )
    )


def create_delivery_point(
    db: Session,
    *,
    tenant_id: str,
    payload: DeliveryPointCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsDeliveryPoint:
    delivery_point = LogisticsDeliveryPoint(
        tenant_id=tenant_id,
        customer_id=payload.customer_id,
        customer_name=payload.customer_name.strip(),
        contact_name=payload.contact_name,
        address=payload.address.strip(),
        phone=payload.phone,
        zone_id=payload.zone_id,
        is_primary=payload.is_primary,
        delivery_day=payload.delivery_day,
        gps_link=payload.gps_link,
    )
    db.add(delivery_point)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="delivery_point.create",
        entity_type="delivery_point",
        entity_id=delivery_point.id,
        details={"customer_name": delivery_point.customer_name, "address": delivery_point.address},
    )
    return delivery_point


def update_delivery_point(
    db: Session,
    *,
    delivery_point: LogisticsDeliveryPoint,
    payload: DeliveryPointUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsDeliveryPoint:
    if payload.customer_name is not None:
        delivery_point.customer_name = payload.customer_name.strip()
    if payload.contact_name is not None:
        delivery_point.contact_name = payload.contact_name
    if payload.address is not None:
        delivery_point.address = payload.address.strip()
    if payload.phone is not None:
        delivery_point.phone = payload.phone
    if payload.zone_id is not None:
        delivery_point.zone_id = payload.zone_id
    if payload.is_primary is not None:
        delivery_point.is_primary = payload.is_primary
    if payload.delivery_day is not None:
        delivery_point.delivery_day = payload.delivery_day
    if payload.gps_link is not None:
        delivery_point.gps_link = payload.gps_link
    if payload.is_active is not None:
        delivery_point.is_active = payload.is_active
    db.add(delivery_point)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="delivery_point.update",
        entity_type="delivery_point",
        entity_id=delivery_point.id,
        details={
            "customer_name": delivery_point.customer_name,
            "address": delivery_point.address,
            "active": delivery_point.is_active,
        },
    )
    return delivery_point
