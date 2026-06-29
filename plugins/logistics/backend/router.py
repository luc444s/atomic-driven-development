# ruff: noqa: E501
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.schemas import (
    AgendaTaskCreateRequest,
    AgendaTaskRead,
    AgendaTaskTypeRead,
    AgendaTaskUpdateRequest,
    BrandRead,
    CylinderConditionRead,
    CylinderCreateRequest,
    CylinderLabelDataRead,
    CylinderLabelHistoryRead,
    CylinderOwnershipRead,
    CylinderRead,
    CylinderRetimbradoCreateRequest,
    CylinderRetimbradoRead,
    CylinderServiceCreateRequest,
    CylinderServiceRead,
    CylinderServiceUpdateRequest,
    CylinderStateLogRead,
    CylinderStateRead,
    CylinderSummaryItem,
    CylinderTransitionRead,
    CylinderTransitionRequest,
    CylinderUpdateRequest,
    DeliveryPointCreateRequest,
    DeliveryPointRead,
    DeliveryPointUpdateRequest,
    GasProductRead,
    HydrostaticTestCreateRequest,
    HydrostaticTestRead,
    LoadBulkCreateRequest,
    LoadConfirmRequest,
    LoadCreateRequest,
    LoadRead,
    MovementCancelRequest,
    MovementCreateRequest,
    MovementItemRead,
    MovementRead,
    MovementStatusHistoryRead,
    MovementTypeRead,
    MovementUpdateRequest,
    OrderCreateRequest,
    OrderItemCreateRequest,
    OrderItemRead,
    OrderItemUpdateRequest,
    OrderRead,
    OrderUpdateRequest,
    PrintLabelRequest,
    RouteCreateRequest,
    RouteRead,
    RouteStopCreateRequest,
    RouteStopRead,
    RouteStopUpdateRequest,
    RouteUpdateRequest,
    ScanLogRead,
    ScanRequest,
    ServiceTypeRead,
    VehicleCreateRequest,
    VehicleRead,
    VehicleUpdateRequest,
    WarehouseCreateRequest,
    WarehouseRead,
    WarehouseUpdateRequest,
    WarrantyCreateRequest,
    WarrantyRead,
    ZoneCreateRequest,
    ZoneRead,
)
from plugins.logistics.backend.services.agenda import (
    cancel_agenda_task,
    complete_agenda_task,
    create_agenda_task,
    get_agenda_task,
    list_agenda_tasks,
    update_agenda_task,
)
from plugins.logistics.backend.services.catalog import (
    list_agenda_task_types,
    list_brands_catalog,
    list_conditions_catalog,
    list_cylinder_states,
    list_delivery_points_catalog,
    list_gas_products_catalog,
    list_movement_types,
    list_service_types_catalog,
    list_vehicles_catalog,
    list_warehouses_catalog,
    list_zones_catalog,
)
from plugins.logistics.backend.services.cylinders import (
    create_cylinder,
    get_allowed_transitions,
    get_cylinder,
    get_cylinder_by_serial,
    list_cylinder_trace,
    list_cylinders,
    summarize_cylinders,
    transition_cylinder,
    update_cylinder,
)
from plugins.logistics.backend.services.envase import (
    build_label_data,
    create_cylinder_service,
    create_retimbrado,
    delete_cylinder_service,
    get_cylinder_service,
    list_cylinder_services,
    list_label_history,
    list_ownership_history,
    list_retimbrados,
    print_label,
    update_cylinder_service,
)
from plugins.logistics.backend.services.extras import (
    create_hydrotest,
    create_warranty,
    list_hydrotests,
    list_warranties,
)
from plugins.logistics.backend.services.movements import (
    cancel_movement,
    confirm_movement,
    create_movement,
    get_movement,
    list_movement_history,
    list_movement_items,
    list_movements,
    update_movement,
)
from plugins.logistics.backend.services.orders import (
    create_order,
    create_order_item,
    delete_order_item,
    get_order,
    get_order_item,
    list_order_items,
    list_orders,
    update_order,
    update_order_item,
)
from plugins.logistics.backend.services.resources import (
    create_delivery_point,
    create_vehicle,
    create_warehouse,
    create_zone,
    get_delivery_point,
    get_vehicle,
    get_warehouse,
    list_delivery_points,
    list_vehicles,
    list_warehouses,
    list_zones,
    update_delivery_point,
    update_vehicle,
    update_warehouse,
)
from plugins.logistics.backend.services.routes import (
    bulk_create_loads,
    cancel_route,
    complete_route,
    confirm_loads,
    create_agenda_tasks_from_route,
    create_load,
    create_route,
    create_route_stop,
    delete_load,
    delete_route_stop,
    deliver_route_stop,
    get_load_by_id,
    get_route,
    get_route_stop,
    list_loads,
    list_route_stops,
    list_routes,
    start_route,
    update_route,
    update_route_stop,
)
from plugins.logistics.backend.services.scan import list_scan_logs, process_scan
from plugins.logistics.backend.services.state_machine import StateTransitionError

router = APIRouter(tags=["logistics"])
DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)

REQUIRE_CYLINDER_READ = Depends(require_permission("logistics.cylinder.read"))
REQUIRE_CYLINDER_CREATE = Depends(require_permission("logistics.cylinder.create"))
REQUIRE_CYLINDER_UPDATE = Depends(require_permission("logistics.cylinder.update"))
REQUIRE_CYLINDER_TRANSITION = Depends(require_permission("logistics.cylinder.transition"))
REQUIRE_CYLINDER_TRACE = Depends(require_permission("logistics.cylinder.trace"))
REQUIRE_ORDER_READ = Depends(require_permission("logistics.order.read"))
REQUIRE_ORDER_CREATE = Depends(require_permission("logistics.order.create"))
REQUIRE_ORDER_MANAGE = Depends(require_permission("logistics.order.manage"))
REQUIRE_ROUTE_READ = Depends(require_permission("logistics.route.read"))
REQUIRE_ROUTE_MANAGE = Depends(require_permission("logistics.route.manage"))
REQUIRE_LOAD_MANAGE = Depends(require_permission("logistics.load.manage"))
REQUIRE_MOVEMENT_READ = Depends(require_permission("logistics.movement.read"))
REQUIRE_MOVEMENT_CREATE = Depends(require_permission("logistics.movement.create"))
REQUIRE_MOVEMENT_CONFIRM = Depends(require_permission("logistics.movement.confirm"))
REQUIRE_WAREHOUSE_READ = Depends(require_permission("logistics.warehouse.read"))
REQUIRE_WAREHOUSE_MANAGE = Depends(require_permission("logistics.warehouse.manage"))
REQUIRE_VEHICLE_READ = Depends(require_permission("logistics.vehicle.read"))
REQUIRE_VEHICLE_MANAGE = Depends(require_permission("logistics.vehicle.manage"))
REQUIRE_AGENDA_READ = Depends(require_permission("logistics.agenda.read"))
REQUIRE_AGENDA_MANAGE = Depends(require_permission("logistics.agenda.manage"))
REQUIRE_MAINTENANCE_READ = Depends(require_permission("logistics.maintenance.read"))
REQUIRE_MAINTENANCE_MANAGE = Depends(require_permission("logistics.maintenance.manage"))
REQUIRE_RETIMBRADO_READ = Depends(require_permission("logistics.retimbrado.read"))
REQUIRE_RETIMBRADO_MANAGE = Depends(require_permission("logistics.retimbrado.manage"))
REQUIRE_SCAN_EXECUTE = Depends(require_permission("logistics.scan.execute"))
REQUIRE_SCAN_READ = Depends(require_permission("logistics.scan.read"))
REQUIRE_LABEL_PRINT = Depends(require_permission("logistics.label.print"))
REQUIRE_LABEL_READ = Depends(require_permission("logistics.label.read"))
REQUIRE_OWNERSHIP_READ = Depends(require_permission("logistics.ownership.read"))
REQUIRE_SERVICE_READ = Depends(require_permission("logistics.service.read"))
REQUIRE_SERVICE_MANAGE = Depends(require_permission("logistics.service.manage"))
REQUIRE_GAS_CATALOG_READ = Depends(require_permission("logistics.gas.read"))
REQUIRE_BRAND_CATALOG_READ = Depends(require_permission("logistics.brand.read"))


def _conflict(exc: IntegrityError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc.orig or exc))


def _not_found(entity_name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found")


@router.get("/catalog/cylinder-states", response_model=list[CylinderStateRead])
def get_cylinder_states(
    db: Session = DB_SESSION,
    _: User = REQUIRE_CYLINDER_READ,
) -> list[CylinderStateRead]:
    return [CylinderStateRead.model_validate(state) for state in list_cylinder_states(db)]


@router.get("/catalog/movement-types", response_model=list[MovementTypeRead])
def get_movement_types(
    db: Session = DB_SESSION,
    _: User = REQUIRE_MOVEMENT_READ,
) -> list[MovementTypeRead]:
    return [MovementTypeRead.model_validate(item) for item in list_movement_types(db)]


@router.get("/catalog/task-types", response_model=list[AgendaTaskTypeRead])
def get_task_types(
    db: Session = DB_SESSION,
    _: User = REQUIRE_AGENDA_READ,
) -> list[AgendaTaskTypeRead]:
    return [AgendaTaskTypeRead.model_validate(item) for item in list_agenda_task_types(db)]


@router.get("/catalog/warehouses", response_model=list[WarehouseRead])
def get_warehouse_catalog(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_WAREHOUSE_READ,
) -> list[WarehouseRead]:
    return [
        WarehouseRead.model_validate(item)
        for item in list_warehouses_catalog(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.get("/catalog/vehicles", response_model=list[VehicleRead])
def get_vehicle_catalog(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_VEHICLE_READ,
) -> list[VehicleRead]:
    return [
        VehicleRead.model_validate(item)
        for item in list_vehicles_catalog(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.get("/catalog/delivery-points", response_model=list[DeliveryPointRead])
def get_delivery_point_catalog(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[DeliveryPointRead]:
    return [
        DeliveryPointRead.model_validate(item)
        for item in list_delivery_points_catalog(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.get("/catalog/zones", response_model=list[ZoneRead])
def get_zone_catalog(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_WAREHOUSE_READ,
) -> list[ZoneRead]:
    return [ZoneRead.model_validate(item) for item in list_zones_catalog(db, tenant_id=tenant_context.current_tenant_id)]


@router.get("/catalog/conditions", response_model=list[CylinderConditionRead])
def get_condition_catalog(
    db: Session = DB_SESSION,
    _: User = REQUIRE_CYLINDER_READ,
) -> list[CylinderConditionRead]:
    return [
        CylinderConditionRead.model_validate(item)
        for item in list_conditions_catalog(db)
    ]


@router.get("/catalog/gas-products", response_model=list[GasProductRead])
def get_gas_product_catalog(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_GAS_CATALOG_READ,
) -> list[GasProductRead]:
    return [
        GasProductRead.model_validate(item)
        for item in list_gas_products_catalog(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.get("/catalog/brands", response_model=list[BrandRead])
def get_brand_catalog(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_BRAND_CATALOG_READ,
) -> list[BrandRead]:
    return [BrandRead.model_validate(item) for item in list_brands_catalog(db, tenant_id=tenant_context.current_tenant_id)]


@router.get("/catalog/service-types", response_model=list[ServiceTypeRead])
def get_service_type_catalog(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SERVICE_READ,
) -> list[ServiceTypeRead]:
    return [
        ServiceTypeRead.model_validate(item)
        for item in list_service_types_catalog(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.get("/cylinders", response_model=list[CylinderRead])
def get_cylinders(
    search: str | None = Query(default=None),
    state: str | None = Query(default=None),
    active: bool | None = Query(default=True),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> list[CylinderRead]:
    return [
        CylinderRead.model_validate(cylinder)
        for cylinder in list_cylinders(
            db,
            tenant_id=tenant_context.current_tenant_id,
            search=search,
            state=state,
            active=active,
        )
    ]


@router.get("/cylinders/summary", response_model=list[CylinderSummaryItem])
def get_cylinder_summary(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> list[CylinderSummaryItem]:
    return summarize_cylinders(db, tenant_id=tenant_context.current_tenant_id)


@router.get("/cylinders/allowed-transitions/{cylinder_id}", response_model=list[CylinderTransitionRead])
def get_cylinder_allowed_transitions(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> list[CylinderTransitionRead]:
    transitions = get_allowed_transitions(
        db,
        tenant_id=tenant_context.current_tenant_id,
        cylinder_id=cylinder_id,
    )
    if transitions is None:
        raise _not_found("Cylinder")
    return [CylinderTransitionRead.model_validate(transition) for transition in transitions]


@router.get("/cylinders/by-serial/{serial}", response_model=CylinderRead)
def get_cylinder_by_serial_endpoint(
    serial: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> CylinderRead:
    cylinder = get_cylinder_by_serial(
        db,
        tenant_id=tenant_context.current_tenant_id,
        serial_or_barcode=serial,
    )
    if cylinder is None:
        raise _not_found("Cylinder")
    return CylinderRead.model_validate(cylinder)


@router.get("/cylinders/{cylinder_id}", response_model=CylinderRead)
def get_cylinder_detail(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> CylinderRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    return CylinderRead.model_validate(cylinder)


@router.patch("/cylinders/{cylinder_id}", response_model=CylinderRead)
def update_cylinder_endpoint(
    cylinder_id: str,
    payload: CylinderUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_UPDATE,
) -> CylinderRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    try:
        cylinder = update_cylinder(
            db,
            cylinder=cylinder,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return CylinderRead.model_validate(cylinder)


@router.get("/cylinders/{cylinder_id}/trace", response_model=list[CylinderStateLogRead])
def get_cylinder_trace(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_TRACE,
) -> list[CylinderStateLogRead]:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    return [
        CylinderStateLogRead.model_validate(item)
        for item in list_cylinder_trace(
            db,
            tenant_id=tenant_context.current_tenant_id,
            cylinder_id=cylinder_id,
        )
    ]


@router.get("/cylinders/{cylinder_id}/label-data", response_model=CylinderLabelDataRead)
def get_cylinder_label_data_endpoint(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_LABEL_READ,
) -> CylinderLabelDataRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    return CylinderLabelDataRead.model_validate(build_label_data(db, cylinder=cylinder))


@router.get("/cylinders/{cylinder_id}/retimbrados", response_model=list[CylinderRetimbradoRead])
def get_cylinder_retimbrados(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_RETIMBRADO_READ,
) -> list[CylinderRetimbradoRead]:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    return [CylinderRetimbradoRead.model_validate(item) for item in list_retimbrados(db, cylinder_id=cylinder_id)]


@router.post(
    "/cylinders/{cylinder_id}/retimbrados",
    response_model=CylinderRetimbradoRead,
    status_code=status.HTTP_201_CREATED,
)
def create_cylinder_retimbrado_endpoint(
    cylinder_id: str,
    payload: CylinderRetimbradoCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_RETIMBRADO_MANAGE,
) -> CylinderRetimbradoRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    retimbrado = create_retimbrado(
        db,
        cylinder=cylinder,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return CylinderRetimbradoRead.model_validate(retimbrado)


@router.get("/cylinders/{cylinder_id}/ownership", response_model=list[CylinderOwnershipRead])
def get_cylinder_ownership_endpoint(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_OWNERSHIP_READ,
) -> list[CylinderOwnershipRead]:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    return [
        CylinderOwnershipRead.model_validate(item)
        for item in list_ownership_history(db, cylinder_id=cylinder_id)
    ]


@router.get("/cylinders/{cylinder_id}/label-history", response_model=list[CylinderLabelHistoryRead])
def get_cylinder_label_history_endpoint(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_LABEL_READ,
) -> list[CylinderLabelHistoryRead]:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    return [
        CylinderLabelHistoryRead.model_validate(item)
        for item in list_label_history(db, cylinder_id=cylinder_id)
    ]


@router.post(
    "/cylinders/{cylinder_id}/print-label",
    response_model=CylinderLabelHistoryRead,
    status_code=status.HTTP_201_CREATED,
)
def print_cylinder_label_endpoint(
    cylinder_id: str,
    payload: PrintLabelRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_LABEL_PRINT,
) -> CylinderLabelHistoryRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    try:
        label_history = print_label(
            db,
            cylinder=cylinder,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CylinderLabelHistoryRead.model_validate(label_history)


@router.get("/cylinders/{cylinder_id}/services", response_model=list[CylinderServiceRead])
def get_cylinder_services_endpoint(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SERVICE_READ,
) -> list[CylinderServiceRead]:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    return [
        CylinderServiceRead.model_validate(item)
        for item in list_cylinder_services(db, cylinder_id=cylinder_id)
    ]


@router.post(
    "/cylinders/{cylinder_id}/services",
    response_model=CylinderServiceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_cylinder_service_endpoint(
    cylinder_id: str,
    payload: CylinderServiceCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SERVICE_MANAGE,
) -> CylinderServiceRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    service = create_cylinder_service(
        db,
        cylinder=cylinder,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return CylinderServiceRead.model_validate(service)


@router.patch("/cylinders/{cylinder_id}/services/{service_id}", response_model=CylinderServiceRead)
def update_cylinder_service_endpoint(
    cylinder_id: str,
    service_id: str,
    payload: CylinderServiceUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SERVICE_MANAGE,
) -> CylinderServiceRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    service = get_cylinder_service(db, cylinder_id=cylinder_id, service_id=service_id)
    if service is None:
        raise _not_found("Cylinder service")
    service = update_cylinder_service(
        db,
        service=service,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return CylinderServiceRead.model_validate(service)


@router.delete("/cylinders/{cylinder_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cylinder_service_endpoint(
    cylinder_id: str,
    service_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SERVICE_MANAGE,
) -> None:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    service = get_cylinder_service(db, cylinder_id=cylinder_id, service_id=service_id)
    if service is None:
        raise _not_found("Cylinder service")
    delete_cylinder_service(
        db,
        service=service,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()


@router.get("/cylinders/{cylinder_id}/hydrotests", response_model=list[HydrostaticTestRead])
def get_cylinder_hydrotests(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MAINTENANCE_READ,
) -> list[HydrostaticTestRead]:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    return [HydrostaticTestRead.model_validate(item) for item in list_hydrotests(db, cylinder_id=cylinder_id)]


@router.post("/cylinders/{cylinder_id}/hydrotests", response_model=HydrostaticTestRead, status_code=status.HTTP_201_CREATED)
def create_cylinder_hydrotest(
    cylinder_id: str,
    payload: HydrostaticTestCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MAINTENANCE_MANAGE,
) -> HydrostaticTestRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    hydrotest = create_hydrotest(
        db,
        cylinder=cylinder,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return HydrostaticTestRead.model_validate(hydrotest)


@router.get("/cylinders/{cylinder_id}/warranties", response_model=list[WarrantyRead])
def get_cylinder_warranties(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MAINTENANCE_READ,
) -> list[WarrantyRead]:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    return [
        WarrantyRead.model_validate(item)
        for item in list_warranties(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    ]


@router.post("/cylinders", response_model=CylinderRead, status_code=status.HTTP_201_CREATED)
def create_cylinder_endpoint(
    payload: CylinderCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_CREATE,
) -> CylinderRead:
    try:
        cylinder = create_cylinder(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return CylinderRead.model_validate(cylinder)


@router.post("/cylinders/{cylinder_id}/warranties", response_model=WarrantyRead, status_code=status.HTTP_201_CREATED)
def create_cylinder_warranty(
    cylinder_id: str,
    payload: WarrantyCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MAINTENANCE_MANAGE,
) -> WarrantyRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    warranty = create_warranty(
        db,
        tenant_id=tenant_context.current_tenant_id,
        cylinder=cylinder,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return WarrantyRead.model_validate(warranty)


@router.post("/cylinders/{cylinder_id}/transition", response_model=CylinderRead)
def transition_cylinder_endpoint(
    cylinder_id: str,
    payload: CylinderTransitionRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_TRANSITION,
) -> CylinderRead:
    try:
        cylinder = transition_cylinder(
            db,
            tenant_id=tenant_context.current_tenant_id,
            cylinder_id=cylinder_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        if cylinder is None:
            raise _not_found("Cylinder")
        db.commit()
    except StateTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CylinderRead.model_validate(cylinder)


@router.get("/warehouses", response_model=list[WarehouseRead])
def get_warehouses(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_WAREHOUSE_READ,
) -> list[WarehouseRead]:
    return [WarehouseRead.model_validate(item) for item in list_warehouses(db, tenant_id=tenant_context.current_tenant_id)]


@router.post("/warehouses", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
def create_warehouse_endpoint(
    payload: WarehouseCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_WAREHOUSE_MANAGE,
) -> WarehouseRead:
    try:
        warehouse = create_warehouse(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return WarehouseRead.model_validate(warehouse)


@router.patch("/warehouses/{warehouse_id}", response_model=WarehouseRead)
def update_warehouse_endpoint(
    warehouse_id: str,
    payload: WarehouseUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_WAREHOUSE_MANAGE,
) -> WarehouseRead:
    warehouse = get_warehouse(db, tenant_id=tenant_context.current_tenant_id, warehouse_id=warehouse_id)
    if warehouse is None:
        raise _not_found("Warehouse")
    try:
        warehouse = update_warehouse(
            db,
            warehouse=warehouse,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return WarehouseRead.model_validate(warehouse)


@router.get("/zones", response_model=list[ZoneRead])
def get_zones(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_WAREHOUSE_READ,
) -> list[ZoneRead]:
    return [ZoneRead.model_validate(item) for item in list_zones(db, tenant_id=tenant_context.current_tenant_id)]


@router.post("/zones", response_model=ZoneRead, status_code=status.HTTP_201_CREATED)
def create_zone_endpoint(
    payload: ZoneCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_WAREHOUSE_MANAGE,
) -> ZoneRead:
    try:
        zone = create_zone(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return ZoneRead.model_validate(zone)


@router.get("/vehicles", response_model=list[VehicleRead])
def get_vehicles(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_VEHICLE_READ,
) -> list[VehicleRead]:
    return [VehicleRead.model_validate(item) for item in list_vehicles(db, tenant_id=tenant_context.current_tenant_id)]


@router.post("/vehicles", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
def create_vehicle_endpoint(
    payload: VehicleCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_VEHICLE_MANAGE,
) -> VehicleRead:
    try:
        vehicle = create_vehicle(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return VehicleRead.model_validate(vehicle)


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleRead)
def update_vehicle_endpoint(
    vehicle_id: str,
    payload: VehicleUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_VEHICLE_MANAGE,
) -> VehicleRead:
    vehicle = get_vehicle(db, tenant_id=tenant_context.current_tenant_id, vehicle_id=vehicle_id)
    if vehicle is None:
        raise _not_found("Vehicle")
    try:
        vehicle = update_vehicle(
            db,
            vehicle=vehicle,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return VehicleRead.model_validate(vehicle)


@router.get("/delivery-points", response_model=list[DeliveryPointRead])
def get_delivery_points(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[DeliveryPointRead]:
    return [
        DeliveryPointRead.model_validate(item)
        for item in list_delivery_points(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.post("/delivery-points", response_model=DeliveryPointRead, status_code=status.HTTP_201_CREATED)
def create_delivery_point_endpoint(
    payload: DeliveryPointCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> DeliveryPointRead:
    delivery_point = create_delivery_point(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return DeliveryPointRead.model_validate(delivery_point)


@router.patch("/delivery-points/{delivery_point_id}", response_model=DeliveryPointRead)
def update_delivery_point_endpoint(
    delivery_point_id: str,
    payload: DeliveryPointUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> DeliveryPointRead:
    delivery_point = get_delivery_point(
        db,
        tenant_id=tenant_context.current_tenant_id,
        delivery_point_id=delivery_point_id,
    )
    if delivery_point is None:
        raise _not_found("Delivery point")
    delivery_point = update_delivery_point(
        db,
        delivery_point=delivery_point,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return DeliveryPointRead.model_validate(delivery_point)


@router.get("/orders", response_model=list[OrderRead])
def get_orders(
    customer: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[OrderRead]:
    return [
        OrderRead.model_validate(item)
        for item in list_orders(
            db,
            tenant_id=tenant_context.current_tenant_id,
            customer=customer,
            status=status_filter,
        )
    ]


@router.get("/orders/pending", response_model=list[OrderRead])
def get_pending_orders(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[OrderRead]:
    return [
        OrderRead.model_validate(item)
        for item in list_orders(db, tenant_id=tenant_context.current_tenant_id, status="PENDIENTE")
    ]


@router.get("/orders/{order_id}", response_model=OrderRead)
def get_order_detail(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> OrderRead:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    return OrderRead.model_validate(order)


@router.get("/orders/{order_id}/items", response_model=list[OrderItemRead])
def get_order_items(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[OrderItemRead]:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    return [OrderItemRead.model_validate(item) for item in list_order_items(db, order_id=order_id)]


@router.post("/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order_endpoint(
    payload: OrderCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_CREATE,
) -> OrderRead:
    try:
        order = create_order(
            db,
            tenant_id=tenant_context.current_tenant_id,
            created_by=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return OrderRead.model_validate(order)


@router.patch("/orders/{order_id}", response_model=OrderRead)
def update_order_endpoint(
    order_id: str,
    payload: OrderUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> OrderRead:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    order = update_order(
        db,
        order=order,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return OrderRead.model_validate(order)


@router.post("/orders/{order_id}/items", response_model=OrderItemRead, status_code=status.HTTP_201_CREATED)
def create_order_item_endpoint(
    order_id: str,
    payload: OrderItemCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> OrderItemRead:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    item = create_order_item(
        db,
        order=order,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return OrderItemRead.model_validate(item)


@router.patch("/orders/{order_id}/items/{item_id}", response_model=OrderItemRead)
def update_order_item_endpoint(
    order_id: str,
    item_id: str,
    payload: OrderItemUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> OrderItemRead:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    item = get_order_item(db, order_id=order_id, item_id=item_id)
    if item is None:
        raise _not_found("Order item")
    item = update_order_item(
        db,
        item=item,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return OrderItemRead.model_validate(item)


@router.delete("/orders/{order_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_item_endpoint(
    order_id: str,
    item_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> None:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    item = get_order_item(db, order_id=order_id, item_id=item_id)
    if item is None:
        raise _not_found("Order item")
    delete_order_item(db, item=item, action_context=build_action_context(request, tenant_context))
    db.commit()


@router.get("/routes", response_model=list[RouteRead])
def get_routes(
    route_date: str | None = Query(default=None, alias="date"),
    driver: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[RouteRead]:
    parsed_date = None
    if route_date:
        parsed_date = datetime.fromisoformat(route_date).date()
    return [
        RouteRead.model_validate(item)
        for item in list_routes(
            db,
            tenant_id=tenant_context.current_tenant_id,
            status=status_filter,
            driver_id=driver,
            route_date=parsed_date,
        )
    ]


@router.get("/routes/{route_id}", response_model=RouteRead)
def get_route_detail(
    route_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> RouteRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    return RouteRead.model_validate(route)


@router.get("/routes/{route_id}/stops", response_model=list[RouteStopRead])
def get_route_stop_list(
    route_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[RouteStopRead]:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    return [RouteStopRead.model_validate(item) for item in list_route_stops(db, route_id=route_id)]


@router.post("/routes", response_model=RouteRead, status_code=status.HTTP_201_CREATED)
def create_route_endpoint(
    payload: RouteCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RouteRead:
    route = create_route(
        db,
        tenant_id=tenant_context.current_tenant_id,
        created_by=tenant_context.current_user_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return RouteRead.model_validate(route)


@router.patch("/routes/{route_id}", response_model=RouteRead)
def update_route_endpoint(
    route_id: str,
    payload: RouteUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RouteRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    route = update_route(
        db,
        route=route,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return RouteRead.model_validate(route)


@router.post("/routes/{route_id}/start", response_model=RouteRead)
def start_route_endpoint(
    route_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RouteRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    try:
        route = start_route(
            db,
            tenant_id=tenant_context.current_tenant_id,
            route=route,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except StateTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RouteRead.model_validate(route)


@router.post("/routes/{route_id}/complete", response_model=RouteRead)
def complete_route_endpoint(
    route_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RouteRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    route = complete_route(db, route=route, action_context=build_action_context(request, tenant_context))
    db.commit()
    return RouteRead.model_validate(route)


@router.post("/routes/{route_id}/cancel", response_model=RouteRead)
def cancel_route_endpoint(
    route_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RouteRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    route = cancel_route(db, route=route, action_context=build_action_context(request, tenant_context))
    db.commit()
    return RouteRead.model_validate(route)


@router.post("/routes/{route_id}/stops", response_model=RouteStopRead, status_code=status.HTTP_201_CREATED)
def create_route_stop_endpoint(
    route_id: str,
    payload: RouteStopCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RouteStopRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    try:
        stop = create_route_stop(
            db,
            route=route,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return RouteStopRead.model_validate(stop)


@router.patch("/routes/{route_id}/stops/{stop_id}", response_model=RouteStopRead)
def update_route_stop_endpoint(
    route_id: str,
    stop_id: str,
    payload: RouteStopUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RouteStopRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    stop = get_route_stop(db, route_id=route_id, stop_id=stop_id)
    if stop is None:
        raise _not_found("Route stop")
    try:
        stop = update_route_stop(
            db,
            stop=stop,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return RouteStopRead.model_validate(stop)


@router.delete("/routes/{route_id}/stops/{stop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route_stop_endpoint(
    route_id: str,
    stop_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> None:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    stop = get_route_stop(db, route_id=route_id, stop_id=stop_id)
    if stop is None:
        raise _not_found("Route stop")
    delete_route_stop(db, stop=stop, action_context=build_action_context(request, tenant_context))
    db.commit()


@router.post("/routes/{route_id}/stops/{stop_id}/deliver", response_model=RouteStopRead)
def deliver_route_stop_endpoint(
    route_id: str,
    stop_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RouteStopRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    stop = get_route_stop(db, route_id=route_id, stop_id=stop_id)
    if stop is None:
        raise _not_found("Route stop")
    try:
        stop = deliver_route_stop(
            db,
            tenant_id=tenant_context.current_tenant_id,
            route=route,
            stop=stop,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except StateTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RouteStopRead.model_validate(stop)


@router.post("/routes/{route_id}/agenda-tasks", response_model=list[AgendaTaskRead])
def create_route_agenda_tasks_endpoint(
    route_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_MANAGE,
) -> list[AgendaTaskRead]:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    tasks = create_agenda_tasks_from_route(
        db,
        tenant_id=tenant_context.current_tenant_id,
        route=route,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return [AgendaTaskRead.model_validate(item) for item in tasks]


@router.get("/loads", response_model=list[LoadRead])
def get_loads(
    route_id: str = Query(...),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_LOAD_MANAGE,
) -> list[LoadRead]:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    return [LoadRead.model_validate(item) for item in list_loads(db, route_id=route_id)]


@router.post("/loads", response_model=LoadRead, status_code=status.HTTP_201_CREATED)
def create_load_endpoint(
    payload: LoadCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_LOAD_MANAGE,
) -> LoadRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=payload.route_id)
    if route is None:
        raise _not_found("Route")
    try:
        load = create_load(
            db,
            route=route,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return LoadRead.model_validate(load)


@router.post("/loads/bulk", response_model=list[LoadRead], status_code=status.HTTP_201_CREATED)
def bulk_create_load_endpoint(
    payload: LoadBulkCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_LOAD_MANAGE,
) -> list[LoadRead]:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=payload.route_id)
    if route is None:
        raise _not_found("Route")
    try:
        loads = bulk_create_loads(
            db,
            route=route,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return [LoadRead.model_validate(item) for item in loads]


@router.delete("/loads/{load_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_load_endpoint(
    load_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_LOAD_MANAGE,
) -> None:
    load = get_load_by_id(db, load_id=load_id)
    if load is None:
        raise _not_found("Load")
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=load.route_id)
    if route is None:
        raise _not_found("Route")
    delete_load(db, load=load, action_context=build_action_context(request, tenant_context))
    db.commit()


@router.post("/loads/confirm", response_model=list[LoadRead])
def confirm_loads_endpoint(
    payload: LoadConfirmRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_LOAD_MANAGE,
) -> list[LoadRead]:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=payload.route_id)
    if route is None:
        raise _not_found("Route")
    try:
        loads = confirm_loads(
            db,
            tenant_id=tenant_context.current_tenant_id,
            route=route,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except (IntegrityError, StateTransitionError) as exc:
        db.rollback()
        if isinstance(exc, IntegrityError):
            raise _conflict(exc) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return [LoadRead.model_validate(item) for item in loads]


@router.get("/movements", response_model=list[MovementRead])
def get_movements(
    movement_type: str | None = Query(default=None, alias="type"),
    status_filter: str | None = Query(default=None, alias="status"),
    customer: str | None = Query(default=None),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> list[MovementRead]:
    return [
        MovementRead.model_validate(item)
        for item in list_movements(
            db,
            tenant_id=tenant_context.current_tenant_id,
            movement_type=movement_type,
            status=status_filter,
            customer=customer,
        )
    ]


@router.get("/movements/{movement_id}", response_model=MovementRead)
def get_movement_detail(
    movement_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> MovementRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    return MovementRead.model_validate(movement)


@router.get("/movements/{movement_id}/items", response_model=list[MovementItemRead])
def get_movement_item_list(
    movement_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> list[MovementItemRead]:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    return [MovementItemRead.model_validate(item) for item in list_movement_items(db, movement_id=movement_id)]


@router.get("/movements/{movement_id}/history", response_model=list[MovementStatusHistoryRead])
def get_movement_history(
    movement_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> list[MovementStatusHistoryRead]:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    return [
        MovementStatusHistoryRead.model_validate(item)
        for item in list_movement_history(db, movement_id=movement_id)
    ]


@router.post("/movements", response_model=MovementRead, status_code=status.HTTP_201_CREATED)
def create_movement_endpoint(
    payload: MovementCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CREATE,
) -> MovementRead:
    try:
        movement = create_movement(
            db,
            tenant_id=tenant_context.current_tenant_id,
            created_by=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    return MovementRead.model_validate(movement)


@router.patch("/movements/{movement_id}", response_model=MovementRead)
def update_movement_endpoint(
    movement_id: str,
    payload: MovementUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CREATE,
) -> MovementRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    movement = update_movement(
        db,
        movement=movement,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return MovementRead.model_validate(movement)


@router.post("/movements/{movement_id}/confirm", response_model=MovementRead)
def confirm_movement_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CONFIRM,
) -> MovementRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    try:
        movement = confirm_movement(
            db,
            tenant_id=tenant_context.current_tenant_id,
            movement=movement,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except StateTransitionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MovementRead.model_validate(movement)


@router.post("/movements/{movement_id}/cancel", response_model=MovementRead)
def cancel_movement_endpoint(
    movement_id: str,
    payload: MovementCancelRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CONFIRM,
) -> MovementRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    movement = cancel_movement(
        db,
        movement=movement,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return MovementRead.model_validate(movement)


@router.post("/scan", response_model=ScanLogRead, status_code=status.HTTP_201_CREATED)
def process_scan_endpoint(
    payload: ScanRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SCAN_EXECUTE,
) -> ScanLogRead:
    try:
        scan_log = process_scan(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except ValueError as exc:
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ScanLogRead.model_validate(scan_log)


@router.get("/scan/log", response_model=list[ScanLogRead])
def get_scan_log_list(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SCAN_READ,
) -> list[ScanLogRead]:
    return [
        ScanLogRead.model_validate(item)
        for item in list_scan_logs(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.get("/scan/log/{movement_id}", response_model=list[ScanLogRead])
def get_scan_log_by_movement(
    movement_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SCAN_READ,
) -> list[ScanLogRead]:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    return [
        ScanLogRead.model_validate(item)
        for item in list_scan_logs(
            db,
            tenant_id=tenant_context.current_tenant_id,
            movement_id=movement_id,
        )
    ]


@router.get("/agenda/tasks", response_model=list[AgendaTaskRead])
def get_agenda_task_list(
    driver: str | None = Query(default=None),
    task_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    scheduled_date: str | None = Query(default=None, alias="date"),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_READ,
) -> list[AgendaTaskRead]:
    parsed_date = None
    if scheduled_date:
        parsed_date = datetime.fromisoformat(scheduled_date).date()
    return [
        AgendaTaskRead.model_validate(item)
        for item in list_agenda_tasks(
            db,
            tenant_id=tenant_context.current_tenant_id,
            driver_id=driver,
            status=status_filter,
            task_type=task_type,
            scheduled_date=parsed_date,
        )
    ]


@router.get("/agenda/tasks/by-driver/{driver_id}", response_model=list[AgendaTaskRead])
def get_agenda_tasks_by_driver(
    driver_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_READ,
) -> list[AgendaTaskRead]:
    return [
        AgendaTaskRead.model_validate(item)
        for item in list_agenda_tasks(
            db,
            tenant_id=tenant_context.current_tenant_id,
            driver_id=driver_id,
        )
    ]


@router.get("/agenda/tasks/{task_id}", response_model=AgendaTaskRead)
def get_agenda_task_detail(
    task_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_READ,
) -> AgendaTaskRead:
    task = get_agenda_task(db, tenant_id=tenant_context.current_tenant_id, task_id=task_id)
    if task is None:
        raise _not_found("Agenda task")
    return AgendaTaskRead.model_validate(task)


@router.post("/agenda/tasks", response_model=AgendaTaskRead, status_code=status.HTTP_201_CREATED)
def create_agenda_task_endpoint(
    payload: AgendaTaskCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_MANAGE,
) -> AgendaTaskRead:
    task = create_agenda_task(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return AgendaTaskRead.model_validate(task)


@router.patch("/agenda/tasks/{task_id}", response_model=AgendaTaskRead)
def update_agenda_task_endpoint(
    task_id: str,
    payload: AgendaTaskUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_MANAGE,
) -> AgendaTaskRead:
    task = get_agenda_task(db, tenant_id=tenant_context.current_tenant_id, task_id=task_id)
    if task is None:
        raise _not_found("Agenda task")
    task = update_agenda_task(
        db,
        task=task,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return AgendaTaskRead.model_validate(task)


@router.post("/agenda/tasks/{task_id}/complete", response_model=AgendaTaskRead)
def complete_agenda_task_endpoint(
    task_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_MANAGE,
) -> AgendaTaskRead:
    task = get_agenda_task(db, tenant_id=tenant_context.current_tenant_id, task_id=task_id)
    if task is None:
        raise _not_found("Agenda task")
    task = complete_agenda_task(db, task=task, action_context=build_action_context(request, tenant_context))
    db.commit()
    return AgendaTaskRead.model_validate(task)


@router.post("/agenda/tasks/{task_id}/cancel", response_model=AgendaTaskRead)
def cancel_agenda_task_endpoint(
    task_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_MANAGE,
) -> AgendaTaskRead:
    task = get_agenda_task(db, tenant_id=tenant_context.current_tenant_id, task_id=task_id)
    if task is None:
        raise _not_found("Agenda task")
    task = cancel_agenda_task(db, task=task, action_context=build_action_context(request, tenant_context))
    db.commit()
    return AgendaTaskRead.model_validate(task)
