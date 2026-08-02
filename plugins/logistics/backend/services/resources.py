from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.kernel.tenants.service import get_branch_for_tenant
from plugins.crm.backend.services.customers import require_customer
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
            .where(
                LogisticsWarehouse.tenant_id == tenant_id,
                LogisticsWarehouse.warehouse_type != "MOBILE",
            )
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
    branch_id = payload.branch_id if payload.branch_id is not None else action_context.branch_id
    if branch_id is not None and get_branch_for_tenant(db, tenant_id, branch_id) is None:
        raise ValueError("La sucursal no pertenece al tenant")

    warehouse = LogisticsWarehouse(
        tenant_id=tenant_id,
        branch_id=branch_id,
        name=payload.name.strip(),
        code=payload.code.strip().upper(),
        address=payload.address,
        phone=payload.phone,
        latitude=payload.latitude,
        longitude=payload.longitude,
        formatted_address=payload.formatted_address,
        place_id=payload.place_id,
        geocode_source=payload.geocode_source,
    )
    db.add(warehouse)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="warehouse.create",
        entity_type="warehouse",
        entity_id=warehouse.id,
        details={"name": warehouse.name, "code": warehouse.code, "branch_id": warehouse.branch_id},
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
    if "branch_id" in payload.model_fields_set:
        if (
            payload.branch_id is not None
            and get_branch_for_tenant(db, warehouse.tenant_id, payload.branch_id) is None
        ):
            raise ValueError("La sucursal no pertenece al tenant")
        warehouse.branch_id = payload.branch_id
    if payload.address is not None:
        warehouse.address = payload.address
    if payload.phone is not None:
        warehouse.phone = payload.phone
    for field_name in ["latitude", "longitude", "formatted_address", "place_id", "geocode_source"]:
        if field_name in payload.model_fields_set:
            setattr(warehouse, field_name, getattr(payload, field_name))
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
        details={
            "name": warehouse.name,
            "code": warehouse.code,
            "branch_id": warehouse.branch_id,
            "active": warehouse.is_active,
        },
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
            .order_by(LogisticsDeliveryPoint.is_primary.desc(), LogisticsDeliveryPoint.address)
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
    customer = require_customer(db, tenant_id=tenant_id, customer_id=payload.customer_id)
    delivery_point = LogisticsDeliveryPoint(
        tenant_id=tenant_id,
        customer_id=customer.id,
        customer_name=customer.legal_name,
        contact_name=payload.contact_name,
        contact_email=payload.contact_email,
        address=payload.address.strip(),
        phone=payload.phone,
        zone_id=payload.zone_id,
        warehouse_id=payload.warehouse_id,
        address_id=payload.address_id,
        is_primary=payload.is_primary,
        delivery_day=payload.delivery_day,
        visit_day=payload.visit_day,
        time_window=payload.time_window,
        instructions=payload.instructions,
        service_time_min=payload.service_time_min,
        demand_units=payload.demand_units,
        demand_weight_kg=payload.demand_weight_kg,
        agent_user_id=payload.agent_user_id,
        fiscal_operation_document=payload.fiscal_operation_document,
        fiscal_operation_type=payload.fiscal_operation_type,
        gps_link=payload.gps_link,
        gps_coordinates=payload.gps_coordinates,
    )
    db.add(delivery_point)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="delivery_point.create",
        entity_type="delivery_point",
        entity_id=delivery_point.id,
        details={"customer_id": delivery_point.customer_id, "address": delivery_point.address},
    )
    return delivery_point


def update_delivery_point(
    db: Session,
    *,
    delivery_point: LogisticsDeliveryPoint,
    payload: DeliveryPointUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsDeliveryPoint:
    if payload.customer_id is not None and (
        payload.customer_id != delivery_point.customer_id or not delivery_point.customer_name
    ):
        customer = require_customer(
            db,
            tenant_id=delivery_point.tenant_id,
            customer_id=payload.customer_id,
        )
        delivery_point.customer_id = customer.id
        delivery_point.customer_name = customer.legal_name
    if payload.contact_name is not None:
        delivery_point.contact_name = payload.contact_name
    if payload.contact_email is not None:
        delivery_point.contact_email = payload.contact_email
    if payload.address is not None:
        delivery_point.address = payload.address.strip()
    if payload.phone is not None:
        delivery_point.phone = payload.phone
    if payload.zone_id is not None:
        delivery_point.zone_id = payload.zone_id
    if payload.warehouse_id is not None:
        delivery_point.warehouse_id = payload.warehouse_id
    if payload.address_id is not None:
        delivery_point.address_id = payload.address_id
    if payload.is_primary is not None:
        delivery_point.is_primary = payload.is_primary
    if payload.delivery_day is not None:
        delivery_point.delivery_day = payload.delivery_day
    if payload.visit_day is not None:
        delivery_point.visit_day = payload.visit_day
    if payload.time_window is not None:
        delivery_point.time_window = payload.time_window
    if payload.instructions is not None:
        delivery_point.instructions = payload.instructions
    if payload.service_time_min is not None:
        delivery_point.service_time_min = payload.service_time_min
    if payload.demand_units is not None:
        delivery_point.demand_units = payload.demand_units
    if payload.demand_weight_kg is not None:
        delivery_point.demand_weight_kg = payload.demand_weight_kg
    if payload.agent_user_id is not None:
        delivery_point.agent_user_id = payload.agent_user_id
    if payload.fiscal_operation_document is not None:
        delivery_point.fiscal_operation_document = payload.fiscal_operation_document
    if payload.fiscal_operation_type is not None:
        delivery_point.fiscal_operation_type = payload.fiscal_operation_type
    if payload.gps_link is not None:
        delivery_point.gps_link = payload.gps_link
    if payload.gps_coordinates is not None:
        delivery_point.gps_coordinates = payload.gps_coordinates
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
            "customer_id": delivery_point.customer_id,
            "address": delivery_point.address,
            "active": delivery_point.is_active,
        },
    )
    return delivery_point


def set_primary_warehouse(
    db: Session,
    *,
    warehouse: LogisticsWarehouse,
    action_context: LogisticsActionContext,
) -> LogisticsWarehouse:
    """Marca un almacén como principal (excluyente: desmarca los demás)."""
    from sqlalchemy import update

    if not warehouse.is_active:
        raise ValueError("No se puede marcar como principal un almacén inactivo")
    db.execute(
        update(LogisticsWarehouse)
        .where(LogisticsWarehouse.tenant_id == warehouse.tenant_id)
        .values(is_primary=False)
    )
    warehouse.is_primary = True
    db.add(warehouse)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="warehouse.set_primary",
        entity_type="warehouse",
        entity_id=warehouse.id,
        details={"name": warehouse.name, "code": warehouse.code},
    )
    return warehouse
