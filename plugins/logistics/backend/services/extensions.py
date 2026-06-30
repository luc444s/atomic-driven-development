from __future__ import annotations

from datetime import date

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.models import (
    LogisticsAdrIncompatibility,
    LogisticsAdrProductConfig,
    LogisticsAgendaTask,
    LogisticsCylinder,
    LogisticsDriverParameter,
    LogisticsEquipment,
    LogisticsLoad,
    LogisticsMovement,
    LogisticsMovementEquipment,
    LogisticsRoute,
    LogisticsRouteStop,
    LogisticsRouteWeekday,
    LogisticsVehicle,
    LogisticsVehicleDeliveryPoint,
    LogisticsVehicleRouteRestriction,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import (
    AdrIncompatibilityCreateRequest,
    AdrProductConfigUpsertRequest,
    AgendaDailySummaryBucket,
    CylinderWeightRead,
    DriverParameterRead,
    DriverParametersUpsertRequest,
    EquipmentCreateRequest,
    LoadWeightSummaryRead,
    MovementEquipmentAssignRequest,
    MovementEquipmentReturnRequest,
    ProductContentRead,
    RouteWeekdayRead,
    RouteWeekdayUpdateRequest,
    VehicleDeliveryPointCreateRequest,
    VehicleDeliveryPointRead,
    VehicleEligibilityRead,
    VehicleRouteRestrictionUpsertRequest,
)
from plugins.productos.backend.models import Product


def list_equipment(db: Session, *, tenant_id: str) -> list[LogisticsEquipment]:
    return list(
        db.scalars(
            select(LogisticsEquipment)
            .where(LogisticsEquipment.tenant_id == tenant_id)
            .order_by(LogisticsEquipment.is_active.desc(), LogisticsEquipment.name.asc())
        ).all()
    )


def create_equipment(
    db: Session,
    *,
    tenant_id: str,
    payload: EquipmentCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsEquipment:
    equipment = LogisticsEquipment(
        tenant_id=tenant_id,
        name=payload.name.strip(),
        equipment_type=payload.equipment_type,
        is_active=payload.is_active,
    )
    db.add(equipment)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="equipment.create",
        entity_type="equipment",
        entity_id=equipment.id,
        details={"name": equipment.name, "equipment_type": equipment.equipment_type},
    )
    return equipment


def list_movement_equipment(db: Session, *, movement_id: str) -> list[LogisticsMovementEquipment]:
    return list(
        db.scalars(
            select(LogisticsMovementEquipment)
            .where(LogisticsMovementEquipment.movement_id == movement_id)
            .order_by(LogisticsMovementEquipment.assigned_at.asc())
        ).all()
    )


def assign_equipment_to_movement(
    db: Session,
    *,
    movement: LogisticsMovement,
    payload: MovementEquipmentAssignRequest,
    action_context: LogisticsActionContext,
) -> LogisticsMovementEquipment:
    equipment = db.scalar(
        select(LogisticsEquipment).where(
            LogisticsEquipment.id == payload.equipment_id,
            LogisticsEquipment.tenant_id == movement.tenant_id,
        )
    )
    if equipment is None:
        raise LookupError("Equipment not found")
    assignment = LogisticsMovementEquipment(
        tenant_id=movement.tenant_id,
        movement_id=movement.id,
        equipment_id=payload.equipment_id,
        notes=payload.notes,
    )
    db.add(assignment)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="movement_equipment.assign",
        entity_type="movement_equipment",
        entity_id=assignment.id,
        details={"movement_id": movement.id, "equipment_id": equipment.id},
    )
    return assignment


def return_movement_equipment(
    db: Session,
    *,
    assignment: LogisticsMovementEquipment,
    payload: MovementEquipmentReturnRequest,
    action_context: LogisticsActionContext,
) -> LogisticsMovementEquipment:
    assignment.returned_at = assignment.returned_at or func.now()
    if payload.notes is not None:
        assignment.notes = payload.notes
    db.add(assignment)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="movement_equipment.return",
        entity_type="movement_equipment",
        entity_id=assignment.id,
        details={"movement_id": assignment.movement_id},
    )
    return assignment


def _vehicle_allows_route(
    db: Session, *, tenant_id: str, vehicle_id: str, route_id: str
) -> tuple[bool, str | None]:
    restrictions = list(
        db.scalars(
            select(LogisticsVehicleRouteRestriction).where(
                LogisticsVehicleRouteRestriction.tenant_id == tenant_id,
                LogisticsVehicleRouteRestriction.vehicle_id == vehicle_id,
            )
        ).all()
    )
    if not restrictions:
        return True, None
    allow_routes = {item.route_id for item in restrictions if item.restriction_type == "ALLOW"}
    deny_routes = {item.route_id for item in restrictions if item.restriction_type == "DENY"}
    if allow_routes:
        if route_id in allow_routes:
            return True, None
        return False, "Vehicle is restricted to a different route set"
    if route_id in deny_routes:
        return False, "Vehicle is denied for this route"
    return True, None


def validate_vehicle_for_route(
    db: Session,
    *,
    tenant_id: str,
    vehicle_id: str | None,
    route_id: str,
) -> None:
    if vehicle_id is None:
        return
    allowed, reason = _vehicle_allows_route(
        db, tenant_id=tenant_id, vehicle_id=vehicle_id, route_id=route_id
    )
    if not allowed:
        raise ValueError(reason or "El vehículo no es elegible para esta ruta")


def list_vehicle_route_restrictions(
    db: Session,
    *,
    tenant_id: str,
    vehicle_id: str,
) -> list[LogisticsVehicleRouteRestriction]:
    return list(
        db.scalars(
            select(LogisticsVehicleRouteRestriction)
            .where(
                LogisticsVehicleRouteRestriction.tenant_id == tenant_id,
                LogisticsVehicleRouteRestriction.vehicle_id == vehicle_id,
            )
            .order_by(LogisticsVehicleRouteRestriction.created_at.asc())
        ).all()
    )


def replace_vehicle_route_restrictions(
    db: Session,
    *,
    tenant_id: str,
    vehicle_id: str,
    payload: VehicleRouteRestrictionUpsertRequest,
    action_context: LogisticsActionContext,
) -> list[LogisticsVehicleRouteRestriction]:
    db.execute(
        delete(LogisticsVehicleRouteRestriction).where(
            LogisticsVehicleRouteRestriction.tenant_id == tenant_id,
            LogisticsVehicleRouteRestriction.vehicle_id == vehicle_id,
        )
    )
    for restriction in payload.restrictions:
        db.add(
            LogisticsVehicleRouteRestriction(
                tenant_id=tenant_id,
                vehicle_id=vehicle_id,
                route_id=restriction["route_id"],
                restriction_type=restriction.get("restriction_type", "ALLOW"),
            )
        )
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_route_restriction.replace",
        entity_type="vehicle",
        entity_id=vehicle_id,
        details={"count": len(payload.restrictions)},
    )
    return list_vehicle_route_restrictions(db, tenant_id=tenant_id, vehicle_id=vehicle_id)


def list_eligible_vehicles_for_route(
    db: Session,
    *,
    tenant_id: str,
    route_id: str,
) -> list[VehicleEligibilityRead]:
    vehicles = list(
        db.scalars(
            select(LogisticsVehicle)
            .where(LogisticsVehicle.tenant_id == tenant_id)
            .order_by(LogisticsVehicle.plate.asc())
        ).all()
    )
    result: list[VehicleEligibilityRead] = []
    for vehicle in vehicles:
        allowed, reason = _vehicle_allows_route(
            db, tenant_id=tenant_id, vehicle_id=vehicle.id, route_id=route_id
        )
        result.append(
            VehicleEligibilityRead(
                vehicle_id=vehicle.id,
                plate=vehicle.plate,
                adr_class=vehicle.adr_class,
                capacity_weight=float(vehicle.capacity_weight)
                if vehicle.capacity_weight is not None
                else None,
                eligible=allowed,
                reason=reason,
            )
        )
    return result


def list_driver_parameters(
    db: Session, *, tenant_id: str, driver_id: str
) -> list[DriverParameterRead]:
    return [
        DriverParameterRead.model_validate(item)
        for item in db.scalars(
            select(LogisticsDriverParameter)
            .where(
                LogisticsDriverParameter.tenant_id == tenant_id,
                LogisticsDriverParameter.driver_id == driver_id,
            )
            .order_by(LogisticsDriverParameter.param_key.asc())
        ).all()
    ]


def upsert_driver_parameters(
    db: Session,
    *,
    tenant_id: str,
    driver_id: str,
    payload: DriverParametersUpsertRequest,
    action_context: LogisticsActionContext,
) -> list[DriverParameterRead]:
    existing = {
        item.param_key: item
        for item in db.scalars(
            select(LogisticsDriverParameter).where(
                LogisticsDriverParameter.tenant_id == tenant_id,
                LogisticsDriverParameter.driver_id == driver_id,
            )
        ).all()
    }
    for key, value in payload.parameters.items():
        param = existing.get(key)
        if param is None:
            param = LogisticsDriverParameter(
                tenant_id=tenant_id,
                driver_id=driver_id,
                param_key=key,
                param_value=value,
            )
        else:
            param.param_value = value
        db.add(param)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="driver_parameters.upsert",
        entity_type="driver",
        entity_id=driver_id,
        details={"keys": sorted(payload.parameters.keys())},
    )
    return list_driver_parameters(db, tenant_id=tenant_id, driver_id=driver_id)


def list_vehicle_delivery_points(
    db: Session,
    *,
    tenant_id: str,
    vehicle_id: str,
) -> list[VehicleDeliveryPointRead]:
    return [
        VehicleDeliveryPointRead.model_validate(item)
        for item in db.scalars(
            select(LogisticsVehicleDeliveryPoint).where(
                LogisticsVehicleDeliveryPoint.tenant_id == tenant_id,
                LogisticsVehicleDeliveryPoint.vehicle_id == vehicle_id,
            )
        ).all()
    ]


def link_vehicle_delivery_point(
    db: Session,
    *,
    tenant_id: str,
    vehicle_id: str,
    payload: VehicleDeliveryPointCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsVehicleDeliveryPoint:
    link = LogisticsVehicleDeliveryPoint(
        tenant_id=tenant_id,
        vehicle_id=vehicle_id,
        delivery_point_id=payload.delivery_point_id,
    )
    db.add(link)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_delivery_point.link",
        entity_type="vehicle_delivery_point",
        entity_id=link.id,
        details={"vehicle_id": vehicle_id, "delivery_point_id": payload.delivery_point_id},
    )
    return link


def unlink_vehicle_delivery_point(
    db: Session,
    *,
    tenant_id: str,
    vehicle_id: str,
    delivery_point_id: str,
    action_context: LogisticsActionContext,
) -> None:
    link = db.scalar(
        select(LogisticsVehicleDeliveryPoint).where(
            LogisticsVehicleDeliveryPoint.tenant_id == tenant_id,
            LogisticsVehicleDeliveryPoint.vehicle_id == vehicle_id,
            LogisticsVehicleDeliveryPoint.delivery_point_id == delivery_point_id,
        )
    )
    if link is None:
        raise LookupError("Vehicle delivery point link not found")
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_delivery_point.unlink",
        entity_type="vehicle_delivery_point",
        entity_id=link.id,
        details={"vehicle_id": vehicle_id, "delivery_point_id": delivery_point_id},
    )
    db.delete(link)


def get_agenda_daily_summary(
    db: Session,
    *,
    tenant_id: str,
    scheduled_date: date,
) -> list[AgendaDailySummaryBucket]:
    rows = db.execute(
        select(
            LogisticsAgendaTask.driver_id,
            LogisticsAgendaTask.status,
            func.count(LogisticsAgendaTask.id),
        )
        .where(
            LogisticsAgendaTask.tenant_id == tenant_id,
            LogisticsAgendaTask.scheduled_date == scheduled_date,
        )
        .group_by(LogisticsAgendaTask.driver_id, LogisticsAgendaTask.status)
    ).all()
    return [
        AgendaDailySummaryBucket(driver_id=row[0], status=row[1], total=int(row[2])) for row in rows
    ]


def list_route_weekdays(db: Session, *, route_id: str) -> list[LogisticsRouteWeekday]:
    return list(
        db.scalars(
            select(LogisticsRouteWeekday)
            .where(LogisticsRouteWeekday.route_id == route_id)
            .order_by(LogisticsRouteWeekday.weekday.asc())
        ).all()
    )


def replace_route_weekdays(
    db: Session,
    *,
    route: LogisticsRoute,
    payload: RouteWeekdayUpdateRequest,
    action_context: LogisticsActionContext,
) -> list[RouteWeekdayRead]:
    weekdays = sorted(set(payload.weekdays))
    if any(day < 1 or day > 7 for day in weekdays):
        raise ValueError("Los días de semana deben estar entre 1 y 7")
    db.execute(delete(LogisticsRouteWeekday).where(LogisticsRouteWeekday.route_id == route.id))
    for weekday in weekdays:
        db.add(LogisticsRouteWeekday(tenant_id=route.tenant_id, route_id=route.id, weekday=weekday))
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="route.weekdays.update",
        entity_type="route",
        entity_id=route.id,
        details={"weekdays": weekdays},
    )
    return [
        RouteWeekdayRead.model_validate(item) for item in list_route_weekdays(db, route_id=route.id)
    ]


def _cylinder_weight(cylinder: LogisticsCylinder | None) -> float:
    if cylinder is None:
        return 0.0
    return float(cylinder.weight_current or cylinder.weight_origin or 0)


def build_load_weight_summary(db: Session, *, route: LogisticsRoute) -> LoadWeightSummaryRead:
    total_weight = 0.0
    for load in db.scalars(select(LogisticsLoad).where(LogisticsLoad.route_id == route.id)).all():
        cylinder = db.scalar(
            select(LogisticsCylinder).where(LogisticsCylinder.id == load.cylinder_id)
        )
        total_weight += _cylinder_weight(cylinder)
    vehicle = (
        db.scalar(select(LogisticsVehicle).where(LogisticsVehicle.id == route.vehicle_id))
        if route.vehicle_id
        else None
    )
    limit = 5000.0
    if vehicle is not None:
        limit = float(vehicle.useful_load or vehicle.capacity_weight or 5000)
    return LoadWeightSummaryRead(
        route_id=route.id,
        weight_limit_kg=limit,
        total_weight_kg=total_weight,
        exceeds_limit=total_weight > limit,
    )


def validate_route_weight_limit(
    db: Session,
    *,
    route: LogisticsRoute,
    cylinder_id: str,
) -> None:
    summary = build_load_weight_summary(db, route=route)
    cylinder = db.scalar(select(LogisticsCylinder).where(LogisticsCylinder.id == cylinder_id))
    if summary.total_weight_kg + _cylinder_weight(cylinder) > summary.weight_limit_kg:
        raise ValueError("La carga de la ruta excede el límite de peso configurado")


def get_adr_product_config(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
) -> LogisticsAdrProductConfig | None:
    return db.scalar(
        select(LogisticsAdrProductConfig)
        .where(
            LogisticsAdrProductConfig.tenant_id == tenant_id,
            LogisticsAdrProductConfig.product_id == product_id,
        )
        .order_by(LogisticsAdrProductConfig.valid_from.desc())
    )


def upsert_adr_product_config(
    db: Session,
    *,
    tenant_id: str,
    product_id: str,
    payload: AdrProductConfigUpsertRequest,
    action_context: LogisticsActionContext,
) -> LogisticsAdrProductConfig:
    config = LogisticsAdrProductConfig(
        tenant_id=tenant_id,
        product_id=product_id,
        adr_class=payload.adr_class,
        adr_points=payload.adr_points,
        adr_tunnel=payload.adr_tunnel,
        max_quantity=payload.max_quantity,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
    )
    db.add(config)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="adr.product_config.upsert",
        entity_type="adr_product_config",
        entity_id=config.id,
        details={"product_id": product_id},
    )
    return config


def list_adr_incompatibilities(db: Session, *, tenant_id: str) -> list[LogisticsAdrIncompatibility]:
    return list(
        db.scalars(
            select(LogisticsAdrIncompatibility)
            .where(LogisticsAdrIncompatibility.tenant_id == tenant_id)
            .order_by(LogisticsAdrIncompatibility.created_at.desc())
        ).all()
    )


def create_adr_incompatibility(
    db: Session,
    *,
    tenant_id: str,
    payload: AdrIncompatibilityCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsAdrIncompatibility:
    if payload.product_id_1 == payload.product_id_2:
        raise ValueError("Los productos deben ser diferentes")
    item = LogisticsAdrIncompatibility(
        tenant_id=tenant_id,
        product_id_1=payload.product_id_1,
        product_id_2=payload.product_id_2,
    )
    db.add(item)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="adr.incompatibility.create",
        entity_type="adr_incompatibility",
        entity_id=item.id,
        details={"product_id_1": item.product_id_1, "product_id_2": item.product_id_2},
    )
    return item


def delete_adr_incompatibility(
    db: Session,
    *,
    item: LogisticsAdrIncompatibility,
    action_context: LogisticsActionContext,
) -> None:
    audit_logistics_action(
        db,
        context=action_context,
        action="adr.incompatibility.delete",
        entity_type="adr_incompatibility",
        entity_id=item.id,
        details={"product_id_1": item.product_id_1, "product_id_2": item.product_id_2},
    )
    db.delete(item)


def list_eligible_vehicles_for_movement(
    db: Session,
    *,
    movement: LogisticsMovement,
    total_adr_points: float,
) -> list[VehicleEligibilityRead]:
    vehicles = list(
        db.scalars(
            select(LogisticsVehicle).where(LogisticsVehicle.tenant_id == movement.tenant_id)
        ).all()
    )
    result: list[VehicleEligibilityRead] = []
    for vehicle in vehicles:
        eligible = True
        reason = None
        if vehicle.capacity_weight is not None and float(vehicle.capacity_weight) <= 0:
            eligible = False
            reason = "Vehicle has no usable ADR capacity"
        result.append(
            VehicleEligibilityRead(
                vehicle_id=vehicle.id,
                plate=vehicle.plate,
                adr_class=vehicle.adr_class,
                capacity_weight=float(vehicle.capacity_weight)
                if vehicle.capacity_weight is not None
                else None,
                eligible=eligible,
                reason=reason,
            )
        )
    return result


def update_route_gps_start(
    db: Session,
    *,
    route: LogisticsRoute,
    gps_coordinates: dict[str, object],
    action_context: LogisticsActionContext,
) -> LogisticsRoute:
    route.gps_start_coordinates = gps_coordinates
    db.add(route)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="route.gps_start",
        entity_type="route",
        entity_id=route.id,
        details={"gps_coordinates": gps_coordinates},
    )
    return route


def update_route_stop_gps(
    db: Session,
    *,
    stop: LogisticsRouteStop,
    gps_coordinates: dict[str, object],
    action_context: LogisticsActionContext,
) -> LogisticsRouteStop:
    stop.gps_coordinates = gps_coordinates
    db.add(stop)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="route_stop.gps",
        entity_type="route_stop",
        entity_id=stop.id,
        details={"gps_coordinates": gps_coordinates},
    )
    return stop


def update_agenda_task_gps(
    db: Session,
    *,
    task: LogisticsAgendaTask,
    gps_coordinates: dict[str, object],
    action_context: LogisticsActionContext,
) -> LogisticsAgendaTask:
    task.gps_coordinates = gps_coordinates
    db.add(task)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="agenda_task.gps",
        entity_type="agenda_task",
        entity_id=task.id,
        details={"gps_coordinates": gps_coordinates},
    )
    return task


def list_available_cylinders_with_weight(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str | None,
) -> list[CylinderWeightRead]:
    stmt = select(LogisticsCylinder).where(
        LogisticsCylinder.tenant_id == tenant_id,
        LogisticsCylinder.current_state.in_(("EN_ALMACEN_VACIO", "LLENADO_OK")),
        LogisticsCylinder.is_active.is_(True),
    )
    if warehouse_id is not None:
        warehouse = db.scalar(
            select(LogisticsWarehouse).where(
                LogisticsWarehouse.id == warehouse_id,
                LogisticsWarehouse.tenant_id == tenant_id,
            )
        )
        if warehouse is not None:
            stmt = stmt.where(
                or_(
                    LogisticsCylinder.location.ilike(f"%{warehouse.code}%"),
                    LogisticsCylinder.location.ilike(f"%{warehouse.name}%"),
                )
            )
    cylinders = list(db.scalars(stmt.order_by(LogisticsCylinder.serial.asc())).all())
    result: list[CylinderWeightRead] = []
    for cylinder in cylinders:
        result.append(
            CylinderWeightRead(
                cylinder_id=cylinder.id,
                serial=cylinder.serial,
                product_id=None,
                product_name=None,
                tara_weight_kg=float(cylinder.weight_origin)
                if cylinder.weight_origin is not None
                else None,
                current_weight_kg=float(cylinder.weight_current)
                if cylinder.weight_current is not None
                else None,
                content_kg=float(cylinder.content_kg) if cylinder.content_kg is not None else None,
                total_weight_kg=float(cylinder.weight_current)
                if cylinder.weight_current is not None
                else None,
            )
        )
    return result


def get_cylinder_weight(db: Session, *, tenant_id: str, cylinder_id: str) -> CylinderWeightRead:
    cylinder = db.scalar(
        select(LogisticsCylinder).where(
            LogisticsCylinder.tenant_id == tenant_id,
            LogisticsCylinder.id == cylinder_id,
        )
    )
    if cylinder is None:
        raise LookupError("Cylinder not found")
    return CylinderWeightRead(
        cylinder_id=cylinder.id,
        serial=cylinder.serial,
        product_id=None,
        product_name=None,
        tara_weight_kg=float(cylinder.weight_origin)
        if cylinder.weight_origin is not None
        else None,
        current_weight_kg=float(cylinder.weight_current)
        if cylinder.weight_current is not None
        else None,
        content_kg=float(cylinder.content_kg) if cylinder.content_kg is not None else None,
        total_weight_kg=float(cylinder.weight_current)
        if cylinder.weight_current is not None
        else None,
    )


def get_product_content(db: Session, *, tenant_id: str, product_id: str) -> ProductContentRead:
    product = db.scalar(
        select(Product).where(Product.tenant_id == tenant_id, Product.id == product_id)
    )
    if product is None:
        raise LookupError("Product not found")
    return ProductContentRead(
        product_id=product.id,
        product_name=product.name,
        content_kg=float(product.weight_kg) if product.weight_kg is not None else None,
    )
