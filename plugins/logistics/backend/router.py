# ruff: noqa: E501
from __future__ import annotations

from datetime import datetime
from typing import Never

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import audit_logistics_action, build_action_context
from plugins.logistics.backend.models import LogisticsAdrIncompatibility, LogisticsMovementEquipment
from plugins.logistics.backend.schemas import (
    AdrIncompatibilityCreateRequest,
    AdrIncompatibilityRead,
    AdrPointsSummaryRead,
    AdrProductConfigRead,
    AdrProductConfigUpsertRequest,
    AgendaDailySummaryBucket,
    AgendaTaskCreateRequest,
    AgendaTaskGpsRequest,
    AgendaTaskRead,
    AgendaTaskTypeRead,
    AgendaTaskUpdateRequest,
    CylinderCreateRequest,
    CylinderLabelDataRead,
    CylinderLabelHistoryRead,
    CylinderOwnershipRead,
    CylinderPageRead,
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
    CylinderWeightRead,
    DeliveryPointCreateRequest,
    DeliveryPointRead,
    DeliveryPointUpdateRequest,
    DispatchGuideAssignRequest,
    DispatchTicketRead,
    DispatchVehicleReturnRequest,
    DriverParameterRead,
    DriverParametersUpsertRequest,
    EquipmentCreateRequest,
    EquipmentRead,
    HydrostaticTestCreateRequest,
    HydrostaticTestRead,
    IncidentReasonRead,
    LoadBulkCreateRequest,
    LoadConfirmRequest,
    LoadCreateRequest,
    LoadRead,
    LoadSummaryReportRead,
    LoadWeightSummaryRead,
    MovementCancelRequest,
    MovementCreateRequest,
    MovementEquipmentAssignRequest,
    MovementEquipmentRead,
    MovementEquipmentReturnRequest,
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
    PlanningGeneratePreloadRequest,
    PlanningPendingOrderRead,
    PlanningPlanOrderRequest,
    PlanningPlanOrderResult,
    PlanningPreloadActionResult,
    PlanningPreloadRead,
    PlanningStockSummaryItem,
    PlanningStockSummaryRequest,
    PrintLabelRequest,
    ProductContentRead,
    ReceptionIncidentCreateRequest,
    ReceptionIncidentRead,
    ReceptionReceiveRequest,
    ReceptionReceiveResult,
    RouteAgendaReportRead,
    RouteCreateRequest,
    RouteGpsStartRequest,
    RouteRead,
    RouteStopCreateRequest,
    RouteStopGpsRequest,
    RouteStopRead,
    RouteStopUpdateRequest,
    RouteUpdateRequest,
    RouteWeekdayRead,
    RouteWeekdayUpdateRequest,
    ScanLogRead,
    ScanRequest,
    ServiceTypeRead,
    StockBridgeLogRead,
    TraceabilityPagination,
    TransferAlbaranRead,
    VehicleCreateRequest,
    VehicleDeliveryPointCreateRequest,
    VehicleDeliveryPointRead,
    VehicleEligibilityRead,
    VehicleRead,
    VehicleRouteRestrictionRead,
    VehicleRouteRestrictionUpsertRequest,
    VehicleUpdateRequest,
    WarehouseCreateRequest,
    WarehouseRead,
    WarehouseSerializedCylinderSummaryItem,
    WarehouseUpdateRequest,
    WarrantyCreateRequest,
    WarrantyRead,
    WaybillRead,
    WaybillSummaryRead,
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
    list_cylinder_states,
    list_delivery_points_catalog,
    list_movement_types,
    list_service_types_catalog,
    list_vehicles_catalog,
    list_warehouses_catalog,
)
from plugins.logistics.backend.services.cylinders import (
    create_cylinder,
    get_allowed_transitions,
    get_cylinder,
    get_cylinder_by_serial,
    list_cylinder_trace,
    list_cylinders,
    list_cylinders_page,
    summarize_cylinders,
    summarize_serialized_cylinders_by_warehouse,
    transition_cylinder,
    update_cylinder,
)
from plugins.logistics.backend.services.dispatch import (
    assign_dispatch_guide,
    close_dispatch,
    vehicle_return,
)
from plugins.logistics.backend.services.documents import (
    build_adr_points_summary,
    build_dispatch_ticket,
    build_load_summary,
    build_route_agenda_report,
    build_transfer_albaran,
    build_waybill,
    build_waybill_summary,
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
from plugins.logistics.backend.services.extensions import (
    assign_equipment_to_movement,
    build_load_weight_summary,
    create_adr_incompatibility,
    create_equipment,
    cylinder_to_read,
    delete_adr_incompatibility,
    get_adr_product_config,
    get_agenda_daily_summary,
    get_cylinder_weight,
    get_product_content,
    link_vehicle_delivery_point,
    list_adr_incompatibilities,
    list_available_cylinders_with_weight,
    list_driver_parameters,
    list_eligible_vehicles_for_movement,
    list_eligible_vehicles_for_route,
    list_equipment,
    list_movement_equipment,
    list_vehicle_delivery_points,
    list_vehicle_route_restrictions,
    replace_route_weekdays,
    replace_vehicle_route_restrictions,
    return_movement_equipment,
    unlink_vehicle_delivery_point,
    update_agenda_task_gps,
    update_route_gps_start,
    update_route_stop_gps,
    upsert_adr_product_config,
    upsert_driver_parameters,
)
from plugins.logistics.backend.services.extras import (
    create_hydrotest,
    create_warranty,
    list_hydrotests,
    list_warranties,
)
from plugins.logistics.backend.services.movements import (
    cancel_movement,
    compute_stock_sync_status,
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
from plugins.logistics.backend.services.planning import (
    accept_preload,
    build_preload_read,
    cancel_preload,
    generate_preload,
    get_preload,
    list_preloads,
    list_stock_summary,
    plan_order,
)
from plugins.logistics.backend.services.planning import (
    list_pending_orders as list_planning_pending_orders,
)
from plugins.logistics.backend.services.reception import (
    create_reception_incident,
    get_reception_detail,
    list_incident_reasons,
    list_pending_receptions,
    receive_movement,
)
from plugins.logistics.backend.services.resources import (
    create_delivery_point,
    create_vehicle,
    create_warehouse,
    get_delivery_point,
    get_vehicle,
    get_warehouse,
    list_delivery_points,
    list_vehicles,
    list_warehouses,
    set_primary_warehouse,
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


def _conflict(exc: IntegrityError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc.orig or exc))


def _not_found(entity_name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found")


def _ensure_warehouse_access(
    db: Session,
    *,
    tenant_context: TenantContext,
    request: Request,
    warehouse_id: str,
    action: str,
) -> None:
    if tenant_context.has_warehouse_access(warehouse_id):
        return
    audit_logistics_action(
        db,
        context=build_action_context(request, tenant_context),
        action=action,
        entity_type="warehouse",
        entity_id=warehouse_id,
        result="denied",
        details={"warehouse_id": warehouse_id, "reason": "warehouse scope denied"},
    )
    db.commit()
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Warehouse access denied")


def _raise_service_error(exc: Exception) -> Never:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise exc


def _resolve_active_warehouse_id(tenant_context: TenantContext) -> str:
    warehouse_ids = tenant_context.current_warehouse_ids
    if warehouse_ids is None or len(warehouse_ids) != 1:
        raise ValueError(
            "No se pudo resolver un almacen activo unico para el usuario. Ajusta el contexto operativo antes de crear el envase."
        )
    return warehouse_ids[0]


def _resolve_entry_warehouse_id(
    db: Session,
    tenant_context: TenantContext,
    warehouse_id: str | None,
) -> str:
    if warehouse_id:
        if not tenant_context.has_warehouse_access(warehouse_id):
            raise ValueError("No tienes acceso al almacen seleccionado para el alta operativa")
        warehouse = get_warehouse(
            db,
            tenant_id=tenant_context.current_tenant_id,
            warehouse_id=warehouse_id,
        )
        if warehouse is None:
            raise LookupError("Warehouse not found")
        return warehouse.id
    return _resolve_active_warehouse_id(tenant_context)


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


@router.get("/catalog/service-types", response_model=list[ServiceTypeRead])
def get_service_type_catalog(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SERVICE_READ,
) -> list[ServiceTypeRead]:
    items = [
        ServiceTypeRead.model_validate(item)
        for item in list_service_types_catalog(db, tenant_id=tenant_context.current_tenant_id)
    ]
    db.commit()
    return items


@router.get("/cylinders", response_model=list[CylinderRead])
def get_cylinders(
    search: str | None = Query(default=None),
    state: str | None = Query(default=None),
    active: bool | None = Query(default=True),
    is_medical: bool | None = Query(default=None),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> list[CylinderRead]:
    return [
        cylinder_to_read(db, cylinder)
        for cylinder in list_cylinders(
            db,
            tenant_id=tenant_context.current_tenant_id,
            search=search,
            state=state,
            active=active,
            is_medical=is_medical,
        )
    ]


@router.get("/cylinders/page", response_model=CylinderPageRead)
def get_cylinders_page(
    search: str | None = Query(default=None),
    state: str | None = Query(default=None),
    active: bool | None = Query(default=True),
    is_medical: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=200),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> CylinderPageRead:
    items, total = list_cylinders_page(
        db,
        tenant_id=tenant_context.current_tenant_id,
        page=page,
        per_page=per_page,
        search=search,
        state=state,
        active=active,
        is_medical=is_medical,
    )
    total_pages = max(1, (total + per_page - 1) // per_page)
    return CylinderPageRead(
        items=[cylinder_to_read(db, cylinder) for cylinder in items],
        pagination=TraceabilityPagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
        ),
    )


@router.get("/cylinders/summary", response_model=list[CylinderSummaryItem])
def get_cylinder_summary(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> list[CylinderSummaryItem]:
    return summarize_cylinders(db, tenant_id=tenant_context.current_tenant_id)


@router.get(
    "/cylinders/serialized-summary",
    response_model=list[WarehouseSerializedCylinderSummaryItem],
)
def get_serialized_cylinder_summary_by_warehouse(
    warehouse_id: str = Query(...),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> list[WarehouseSerializedCylinderSummaryItem]:
    try:
        return summarize_serialized_cylinders_by_warehouse(
            db,
            tenant_id=tenant_context.current_tenant_id,
            warehouse_id=warehouse_id,
        )
    except LookupError as exc:
        raise _not_found("Warehouse") from exc


@router.get("/cylinders/available-with-weight", response_model=list[CylinderWeightRead])
def get_available_cylinders_with_weight_endpoint(
    warehouse_id: str | None = Query(default=None),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> list[CylinderWeightRead]:
    return list_available_cylinders_with_weight(
        db,
        tenant_id=tenant_context.current_tenant_id,
        warehouse_id=warehouse_id,
    )


@router.get(
    "/cylinders/allowed-transitions/{cylinder_id}", response_model=list[CylinderTransitionRead]
)
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
    return cylinder_to_read(db, cylinder)


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
    return cylinder_to_read(db, cylinder)


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
    return cylinder_to_read(db, cylinder)


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
    return [
        CylinderRetimbradoRead.model_validate(item)
        for item in list_retimbrados(db, cylinder_id=cylinder_id)
    ]


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


@router.delete(
    "/cylinders/{cylinder_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT
)
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
    return [
        HydrostaticTestRead.model_validate(item)
        for item in list_hydrotests(db, cylinder_id=cylinder_id)
    ]


@router.post(
    "/cylinders/{cylinder_id}/hydrotests",
    response_model=HydrostaticTestRead,
    status_code=status.HTTP_201_CREATED,
)
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
        for item in list_warranties(
            db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id
        )
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
        resolved_warehouse_id = (
            _resolve_entry_warehouse_id(db, tenant_context, payload.warehouse_id)
            if payload.entry_mode is not None
            else None
        )
        cylinder = create_cylinder(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            warehouse_id=resolved_warehouse_id,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return cylinder_to_read(db, cylinder)


@router.post(
    "/cylinders/{cylinder_id}/warranties",
    response_model=WarrantyRead,
    status_code=status.HTTP_201_CREATED,
)
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
    return cylinder_to_read(db, cylinder)


@router.get("/warehouses", response_model=list[WarehouseRead])
def get_warehouses(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_WAREHOUSE_READ,
) -> list[WarehouseRead]:
    return [
        WarehouseRead.model_validate(item)
        for item in list_warehouses(db, tenant_id=tenant_context.current_tenant_id)
    ]


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
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
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
    warehouse = get_warehouse(
        db, tenant_id=tenant_context.current_tenant_id, warehouse_id=warehouse_id
    )
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
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return WarehouseRead.model_validate(warehouse)


@router.get("/vehicles", response_model=list[VehicleRead])
def get_vehicles(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_VEHICLE_READ,
) -> list[VehicleRead]:
    return [
        VehicleRead.model_validate(item)
        for item in list_vehicles(db, tenant_id=tenant_context.current_tenant_id)
    ]


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


@router.post(
    "/delivery-points", response_model=DeliveryPointRead, status_code=status.HTTP_201_CREATED
)
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


@router.post(
    "/orders/{order_id}/items", response_model=OrderItemRead, status_code=status.HTTP_201_CREATED
)
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
    weekday: int | None = Query(default=None, ge=1, le=7),
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
            weekday=weekday,
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
    try:
        route = create_route(
            db,
            tenant_id=tenant_context.current_tenant_id,
            created_by=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return RouteRead.model_validate(route)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


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
    try:
        route = update_route(
            db,
            route=route,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return RouteRead.model_validate(route)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


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
    route = complete_route(
        db, route=route, action_context=build_action_context(request, tenant_context)
    )
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
    route = cancel_route(
        db, route=route, action_context=build_action_context(request, tenant_context)
    )
    db.commit()
    return RouteRead.model_validate(route)


@router.post(
    "/routes/{route_id}/stops", response_model=RouteStopRead, status_code=status.HTTP_201_CREATED
)
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
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
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
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
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
    movements = list_movements(
        db,
        tenant_id=tenant_context.current_tenant_id,
        movement_type=movement_type,
        status=status_filter,
        customer=customer,
    )
    return [
        MovementRead.model_validate({
            **movement.__dict__,
            "stock_sync_status": compute_stock_sync_status(db, movement=movement),
        })
        for movement in movements
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
    return MovementRead.model_validate({
        **movement.__dict__,
        "stock_sync_status": compute_stock_sync_status(db, movement=movement),
    })


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
    return [
        MovementItemRead.model_validate(item)
        for item in list_movement_items(db, movement_id=movement_id)
    ]


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


@router.get(
    "/movements/{movement_id}/stock-bridge-log",
    response_model=list[StockBridgeLogRead],
)
def get_movement_stock_bridge_log(
    movement_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> list[StockBridgeLogRead]:
    from plugins.logistics.backend.models import LogisticsStockBridgeLog

    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    entries = list(
        db.scalars(
            select(LogisticsStockBridgeLog)
            .where(
                LogisticsStockBridgeLog.tenant_id == movement.tenant_id,
                LogisticsStockBridgeLog.movement_id == movement.id,
            )
            .order_by(LogisticsStockBridgeLog.created_at.desc())
        ).all()
    )
    return [StockBridgeLogRead.model_validate(entry) for entry in entries]


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
    task = complete_agenda_task(
        db, task=task, action_context=build_action_context(request, tenant_context)
    )
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
    task = cancel_agenda_task(
        db, task=task, action_context=build_action_context(request, tenant_context)
    )
    db.commit()
    return AgendaTaskRead.model_validate(task)


@router.get("/planning/stock", response_model=list[PlanningStockSummaryItem])
def get_planning_stock_summary(
    request: Request,
    warehouse_id: str = Query(...),
    product_ids: str | None = Query(default=None),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[PlanningStockSummaryItem]:
    _ensure_warehouse_access(
        db,
        tenant_context=tenant_context,
        request=request,
        warehouse_id=warehouse_id,
        action="planning.stock.read",
    )
    return list_stock_summary(
        db,
        tenant_id=tenant_context.current_tenant_id,
        warehouse_id=warehouse_id,
        product_ids=set(product_ids.split(",")) if product_ids else set(),
    )


@router.post("/planning/stock/summary", response_model=list[PlanningStockSummaryItem])
def post_planning_stock_summary(
    payload: PlanningStockSummaryRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[PlanningStockSummaryItem]:
    _ensure_warehouse_access(
        db,
        tenant_context=tenant_context,
        request=request,
        warehouse_id=payload.warehouse_id,
        action="planning.stock.read",
    )
    orders = list_planning_pending_orders(
        db,
        tenant_id=tenant_context.current_tenant_id,
        allowed_warehouse_ids=tenant_context.current_warehouse_ids,
        warehouse_id=payload.warehouse_id,
    )
    product_ids = {
        item.product_id for order in orders for item in order.items if item.product_id is not None
    }
    return list_stock_summary(
        db,
        tenant_id=tenant_context.current_tenant_id,
        warehouse_id=payload.warehouse_id,
        product_ids=product_ids,
    )


@router.get("/planning/pending-orders", response_model=list[PlanningPendingOrderRead])
def get_planning_pending_orders(
    request: Request,
    warehouse_id: str | None = Query(default=None),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[PlanningPendingOrderRead]:
    if warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=warehouse_id,
            action="planning.pending_orders.read",
        )
    return list_planning_pending_orders(
        db,
        tenant_id=tenant_context.current_tenant_id,
        allowed_warehouse_ids=tenant_context.current_warehouse_ids,
        warehouse_id=warehouse_id,
    )


@router.post("/planning/plan-order/{order_id}", response_model=PlanningPlanOrderResult)
def post_plan_order(
    order_id: str,
    payload: PlanningPlanOrderRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> PlanningPlanOrderResult:
    order = get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if order is None:
        raise _not_found("Order")
    if order.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=order.warehouse_id,
            action="planning.plan_order",
        )
    try:
        result = plan_order(
            db,
            order=order,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post(
    "/planning/generate-preload",
    response_model=PlanningPreloadRead,
    status_code=status.HTTP_201_CREATED,
)
def post_generate_preload(
    payload: PlanningGeneratePreloadRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> PlanningPreloadRead:
    _ensure_warehouse_access(
        db,
        tenant_context=tenant_context,
        request=request,
        warehouse_id=payload.warehouse_id,
        action="planning.generate_preload",
    )
    try:
        preload = generate_preload(
            db,
            tenant_id=tenant_context.current_tenant_id,
            created_by=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return preload
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.get("/planning/preloads", response_model=list[PlanningPreloadRead])
def get_planning_preloads(
    request: Request,
    warehouse_id: str | None = Query(default=None),
    preload_date: str | None = Query(default=None, alias="date"),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> list[PlanningPreloadRead]:
    if warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=warehouse_id,
            action="planning.preload.read",
        )
    parsed_date = datetime.fromisoformat(preload_date).date() if preload_date else None
    return list_preloads(
        db,
        tenant_id=tenant_context.current_tenant_id,
        allowed_warehouse_ids=tenant_context.current_warehouse_ids,
        warehouse_id=warehouse_id,
        preload_date=parsed_date,
        status=status_filter,
    )


@router.get("/planning/preloads/{preload_id}", response_model=PlanningPreloadRead)
def get_planning_preload_detail(
    preload_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> PlanningPreloadRead:
    preload = get_preload(db, tenant_id=tenant_context.current_tenant_id, preload_id=preload_id)
    if preload is None:
        raise _not_found("Preload")
    _ensure_warehouse_access(
        db,
        tenant_context=tenant_context,
        request=request,
        warehouse_id=preload.warehouse_id,
        action="planning.preload.read",
    )
    return build_preload_read(db, preload)


@router.post("/planning/preloads/{preload_id}/accept", response_model=PlanningPreloadActionResult)
def post_accept_preload(
    preload_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> PlanningPreloadActionResult:
    preload = get_preload(db, tenant_id=tenant_context.current_tenant_id, preload_id=preload_id)
    if preload is None:
        raise _not_found("Preload")
    _ensure_warehouse_access(
        db,
        tenant_context=tenant_context,
        request=request,
        warehouse_id=preload.warehouse_id,
        action="planning.preload.accept",
    )
    try:
        result = accept_preload(
            db,
            preload=preload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/planning/preloads/{preload_id}/cancel", response_model=PlanningPreloadRead)
def post_cancel_preload(
    preload_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_MANAGE,
) -> PlanningPreloadRead:
    preload = get_preload(db, tenant_id=tenant_context.current_tenant_id, preload_id=preload_id)
    if preload is None:
        raise _not_found("Preload")
    _ensure_warehouse_access(
        db,
        tenant_context=tenant_context,
        request=request,
        warehouse_id=preload.warehouse_id,
        action="planning.preload.cancel",
    )
    try:
        result = cancel_preload(
            db,
            preload=preload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.get("/reception/pending", response_model=list[MovementRead])
def get_pending_receptions_endpoint(
    request: Request,
    warehouse_id: str = Query(...),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> list[MovementRead]:
    _ensure_warehouse_access(
        db,
        tenant_context=tenant_context,
        request=request,
        warehouse_id=warehouse_id,
        action="reception.pending.read",
    )
    return [
        MovementRead.model_validate(item)
        for item in list_pending_receptions(
            db,
            tenant_id=tenant_context.current_tenant_id,
            warehouse_id=warehouse_id,
        )
    ]


@router.get("/reception/incident-reasons", response_model=list[IncidentReasonRead])
def get_reception_incident_reasons(_: User = REQUIRE_MOVEMENT_READ) -> list[IncidentReasonRead]:
    return list_incident_reasons()


@router.get("/reception/{movement_id}", response_model=MovementRead)
def get_reception_detail_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> MovementRead:
    movement = get_reception_detail(
        db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id
    )
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="reception.read",
        )
    return MovementRead.model_validate(movement)


@router.post("/reception/{movement_id}/receive", response_model=ReceptionReceiveResult)
def post_receive_movement(
    movement_id: str,
    payload: ReceptionReceiveRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CONFIRM,
) -> ReceptionReceiveResult:
    movement = get_reception_detail(
        db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id
    )
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="reception.receive",
        )
    try:
        result = receive_movement(
            db,
            movement=movement,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post(
    "/reception/{movement_id}/incident",
    response_model=ReceptionIncidentRead,
    status_code=status.HTTP_201_CREATED,
)
def post_reception_incident(
    movement_id: str,
    payload: ReceptionIncidentCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CONFIRM,
) -> ReceptionIncidentRead:
    movement = get_reception_detail(
        db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id
    )
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="reception.incident.create",
        )
    try:
        incident = create_reception_incident(
            db,
            movement=movement,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return ReceptionIncidentRead.model_validate(incident)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.get("/waybill/{movement_id}", response_model=WaybillRead)
def get_waybill_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> WaybillRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="waybill.read",
        )
    return build_waybill(db, movement=movement)


@router.get("/waybill/{movement_id}/summary", response_model=WaybillSummaryRead)
def get_waybill_summary_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> WaybillSummaryRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="waybill.summary.read",
        )
    return build_waybill_summary(db, movement=movement)


@router.get("/reports/route-agenda/{route_id}", response_model=RouteAgendaReportRead)
def get_route_agenda_report_endpoint(
    route_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> RouteAgendaReportRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    return build_route_agenda_report(db, route=route)


@router.get("/reports/dispatch-ticket/{movement_id}", response_model=DispatchTicketRead)
def get_dispatch_ticket_report_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> DispatchTicketRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="dispatch.ticket.read",
        )
    return build_dispatch_ticket(db, movement=movement)


@router.get("/reports/transfer-albaran/{movement_id}", response_model=TransferAlbaranRead)
def get_transfer_albaran_report_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> TransferAlbaranRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="transfer.albaran.read",
        )
    return build_transfer_albaran(db, movement=movement)


@router.get("/reports/load-summary/{route_id}", response_model=LoadSummaryReportRead)
def get_load_summary_report_endpoint(
    route_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> LoadSummaryReportRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    return build_load_summary(db, route=route)


@router.get("/reports/adr-summary/{movement_id}", response_model=AdrPointsSummaryRead)
def get_adr_summary_report_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> AdrPointsSummaryRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="adr.summary.read",
        )
    return build_adr_points_summary(db, movement=movement)


@router.patch("/movements/{movement_id}/guide", response_model=MovementRead)
def patch_dispatch_guide_endpoint(
    movement_id: str,
    payload: DispatchGuideAssignRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CONFIRM,
) -> MovementRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    try:
        movement = assign_dispatch_guide(
            db,
            movement=movement,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return MovementRead.model_validate(movement)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.post("/movements/{movement_id}/close-dispatch", response_model=MovementRead)
def post_close_dispatch_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CONFIRM,
) -> MovementRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="dispatch.close",
        )
    try:
        movement = close_dispatch(
            db,
            movement=movement,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return MovementRead.model_validate(movement)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.get("/movements/{movement_id}/dispatch-receipt", response_model=DispatchTicketRead)
def get_dispatch_receipt_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> DispatchTicketRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="dispatch.receipt.read",
        )
    return build_dispatch_ticket(db, movement=movement)


@router.post("/movements/{movement_id}/vehicle-return", response_model=MovementRead)
def post_vehicle_return_endpoint(
    movement_id: str,
    payload: DispatchVehicleReturnRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CONFIRM,
) -> MovementRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="dispatch.vehicle_return",
        )
    try:
        movement = vehicle_return(
            db,
            movement=movement,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return MovementRead.model_validate(movement)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.get("/equipment", response_model=list[EquipmentRead])
def get_equipment_endpoint(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> list[EquipmentRead]:
    return [
        EquipmentRead.model_validate(item)
        for item in list_equipment(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.post("/equipment", response_model=EquipmentRead, status_code=status.HTTP_201_CREATED)
def post_equipment_endpoint(
    payload: EquipmentCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CREATE,
) -> EquipmentRead:
    try:
        equipment = create_equipment(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return EquipmentRead.model_validate(equipment)
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc


@router.get("/movements/{movement_id}/equipment", response_model=list[MovementEquipmentRead])
def get_movement_equipment_endpoint(
    movement_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> list[MovementEquipmentRead]:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    return [
        MovementEquipmentRead.model_validate(item)
        for item in list_movement_equipment(db, movement_id=movement_id)
    ]


@router.post(
    "/movements/{movement_id}/equipment",
    response_model=MovementEquipmentRead,
    status_code=status.HTTP_201_CREATED,
)
def post_movement_equipment_endpoint(
    movement_id: str,
    payload: MovementEquipmentAssignRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CONFIRM,
) -> MovementEquipmentRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    assignment = assign_equipment_to_movement(
        db,
        movement=movement,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return MovementEquipmentRead.model_validate(assignment)


@router.patch(
    "/movements/{movement_id}/equipment/{assignment_id}/return",
    response_model=MovementEquipmentRead,
)
def patch_movement_equipment_return_endpoint(
    movement_id: str,
    assignment_id: str,
    payload: MovementEquipmentReturnRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_CONFIRM,
) -> MovementEquipmentRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    assignment = db.scalar(
        select(LogisticsMovementEquipment).where(
            LogisticsMovementEquipment.id == assignment_id,
            LogisticsMovementEquipment.movement_id == movement_id,
        )
    )
    if assignment is None:
        raise _not_found("Movement equipment")
    assignment = return_movement_equipment(
        db,
        assignment=assignment,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return MovementEquipmentRead.model_validate(assignment)


@router.get(
    "/vehicles/{vehicle_id}/route-restrictions", response_model=list[VehicleRouteRestrictionRead]
)
def get_vehicle_route_restrictions_endpoint(
    vehicle_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[VehicleRouteRestrictionRead]:
    return [
        VehicleRouteRestrictionRead.model_validate(item)
        for item in list_vehicle_route_restrictions(
            db, tenant_id=tenant_context.current_tenant_id, vehicle_id=vehicle_id
        )
    ]


@router.post(
    "/vehicles/{vehicle_id}/route-restrictions", response_model=list[VehicleRouteRestrictionRead]
)
def post_vehicle_route_restrictions_endpoint(
    vehicle_id: str,
    payload: VehicleRouteRestrictionUpsertRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> list[VehicleRouteRestrictionRead]:
    try:
        items = replace_vehicle_route_restrictions(
            db,
            tenant_id=tenant_context.current_tenant_id,
            vehicle_id=vehicle_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return [VehicleRouteRestrictionRead.model_validate(item) for item in items]
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc


@router.get("/routes/{route_id}/eligible-vehicles", response_model=list[VehicleEligibilityRead])
def get_route_eligible_vehicles_endpoint(
    route_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[VehicleEligibilityRead]:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    return list_eligible_vehicles_for_route(
        db, tenant_id=tenant_context.current_tenant_id, route_id=route_id
    )


@router.get("/drivers/{driver_id}/parameters", response_model=list[DriverParameterRead])
def get_driver_parameters_endpoint(
    driver_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[DriverParameterRead]:
    return list_driver_parameters(
        db, tenant_id=tenant_context.current_tenant_id, driver_id=driver_id
    )


@router.put("/drivers/{driver_id}/parameters", response_model=list[DriverParameterRead])
def put_driver_parameters_endpoint(
    driver_id: str,
    payload: DriverParametersUpsertRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> list[DriverParameterRead]:
    items = upsert_driver_parameters(
        db,
        tenant_id=tenant_context.current_tenant_id,
        driver_id=driver_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return items


@router.get("/vehicles/{vehicle_id}/delivery-points", response_model=list[VehicleDeliveryPointRead])
def get_vehicle_delivery_points_endpoint(
    vehicle_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[VehicleDeliveryPointRead]:
    return list_vehicle_delivery_points(
        db, tenant_id=tenant_context.current_tenant_id, vehicle_id=vehicle_id
    )


@router.post(
    "/vehicles/{vehicle_id}/delivery-points",
    response_model=VehicleDeliveryPointRead,
    status_code=status.HTTP_201_CREATED,
)
def post_vehicle_delivery_point_endpoint(
    vehicle_id: str,
    payload: VehicleDeliveryPointCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> VehicleDeliveryPointRead:
    link = link_vehicle_delivery_point(
        db,
        tenant_id=tenant_context.current_tenant_id,
        vehicle_id=vehicle_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return VehicleDeliveryPointRead.model_validate(link)


@router.delete(
    "/vehicles/{vehicle_id}/delivery-points/{delivery_point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_vehicle_delivery_point_endpoint(
    vehicle_id: str,
    delivery_point_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> None:
    unlink_vehicle_delivery_point(
        db,
        tenant_id=tenant_context.current_tenant_id,
        vehicle_id=vehicle_id,
        delivery_point_id=delivery_point_id,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()


@router.get("/agenda/daily-summary", response_model=list[AgendaDailySummaryBucket])
def get_agenda_daily_summary_endpoint(
    summary_date: str | None = Query(default=None, alias="date"),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_READ,
) -> list[AgendaDailySummaryBucket]:
    parsed_date = (
        datetime.fromisoformat(summary_date).date() if summary_date else datetime.now().date()
    )
    return get_agenda_daily_summary(
        db, tenant_id=tenant_context.current_tenant_id, scheduled_date=parsed_date
    )


@router.patch("/routes/{route_id}/weekly-schedule", response_model=list[RouteWeekdayRead])
def patch_route_weekly_schedule_endpoint(
    route_id: str,
    payload: RouteWeekdayUpdateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> list[RouteWeekdayRead]:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    try:
        items = replace_route_weekdays(
            db,
            route=route,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return items
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.get("/loads/weight-summary", response_model=LoadWeightSummaryRead)
def get_load_weight_summary_endpoint(
    route_id: str = Query(...),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_LOAD_MANAGE,
) -> LoadWeightSummaryRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    return build_load_weight_summary(db, route=route)


@router.get("/adr/product-config/{product_id}", response_model=AdrProductConfigRead | None)
def get_adr_product_config_endpoint(
    product_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> AdrProductConfigRead | None:
    item = get_adr_product_config(
        db, tenant_id=tenant_context.current_tenant_id, product_id=product_id
    )
    return AdrProductConfigRead.model_validate(item) if item is not None else None


@router.put("/adr/product-config/{product_id}", response_model=AdrProductConfigRead)
def put_adr_product_config_endpoint(
    product_id: str,
    payload: AdrProductConfigUpsertRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> AdrProductConfigRead:
    item = upsert_adr_product_config(
        db,
        tenant_id=tenant_context.current_tenant_id,
        product_id=product_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return AdrProductConfigRead.model_validate(item)


@router.get("/adr/points/{movement_id}", response_model=AdrPointsSummaryRead)
def get_adr_points_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_MOVEMENT_READ,
) -> AdrPointsSummaryRead:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="adr.points.read",
        )
    return build_adr_points_summary(db, movement=movement)


@router.get("/adr/incompatibilities", response_model=list[AdrIncompatibilityRead])
def get_adr_incompatibilities_endpoint(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[AdrIncompatibilityRead]:
    return [
        AdrIncompatibilityRead.model_validate(item)
        for item in list_adr_incompatibilities(db, tenant_id=tenant_context.current_tenant_id)
    ]


@router.post(
    "/adr/incompatibilities",
    response_model=AdrIncompatibilityRead,
    status_code=status.HTTP_201_CREATED,
)
def post_adr_incompatibility_endpoint(
    payload: AdrIncompatibilityCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> AdrIncompatibilityRead:
    try:
        item = create_adr_incompatibility(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
        return AdrIncompatibilityRead.model_validate(item)
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)


@router.delete(
    "/adr/incompatibilities/{incompatibility_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_adr_incompatibility_endpoint(
    incompatibility_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> None:
    item = db.scalar(
        select(LogisticsAdrIncompatibility).where(
            LogisticsAdrIncompatibility.id == incompatibility_id,
            LogisticsAdrIncompatibility.tenant_id == tenant_context.current_tenant_id,
        )
    )
    if item is None:
        raise _not_found("ADR incompatibility")
    delete_adr_incompatibility(
        db, item=item, action_context=build_action_context(request, tenant_context)
    )
    db.commit()


@router.get("/adr/eligible-vehicles/{movement_id}", response_model=list[VehicleEligibilityRead])
def get_adr_eligible_vehicles_endpoint(
    movement_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_READ,
) -> list[VehicleEligibilityRead]:
    movement = get_movement(db, tenant_id=tenant_context.current_tenant_id, movement_id=movement_id)
    if movement is None:
        raise _not_found("Movement")
    if movement.warehouse_id is not None:
        _ensure_warehouse_access(
            db,
            tenant_context=tenant_context,
            request=request,
            warehouse_id=movement.warehouse_id,
            action="adr.eligible_vehicles.read",
        )
    summary = build_adr_points_summary(db, movement=movement)
    return list_eligible_vehicles_for_movement(
        db, movement=movement, total_adr_points=summary.total_adr_points
    )


@router.patch("/routes/{route_id}/gps-start", response_model=RouteRead)
def patch_route_gps_start_endpoint(
    route_id: str,
    payload: RouteGpsStartRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ROUTE_MANAGE,
) -> RouteRead:
    route = get_route(db, tenant_id=tenant_context.current_tenant_id, route_id=route_id)
    if route is None:
        raise _not_found("Route")
    route = update_route_gps_start(
        db,
        route=route,
        gps_coordinates=payload.gps_coordinates,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return RouteRead.model_validate(route)


@router.patch("/routes/{route_id}/stops/{stop_id}/gps", response_model=RouteStopRead)
def patch_route_stop_gps_endpoint(
    route_id: str,
    stop_id: str,
    payload: RouteStopGpsRequest,
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
    stop = update_route_stop_gps(
        db,
        stop=stop,
        gps_coordinates=payload.gps_coordinates,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return RouteStopRead.model_validate(stop)


@router.patch("/agenda/tasks/{task_id}/gps", response_model=AgendaTaskRead)
def patch_agenda_task_gps_endpoint(
    task_id: str,
    payload: AgendaTaskGpsRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_AGENDA_MANAGE,
) -> AgendaTaskRead:
    task = get_agenda_task(db, tenant_id=tenant_context.current_tenant_id, task_id=task_id)
    if task is None:
        raise _not_found("Agenda task")
    task = update_agenda_task_gps(
        db,
        task=task,
        gps_coordinates=payload.gps_coordinates,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return AgendaTaskRead.model_validate(task)


@router.get("/cylinders/{cylinder_id}/weight", response_model=CylinderWeightRead)
def get_cylinder_weight_endpoint(
    cylinder_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_READ,
) -> CylinderWeightRead:
    try:
        return get_cylinder_weight(
            db,
            tenant_id=tenant_context.current_tenant_id,
            cylinder_id=cylinder_id,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.get("/products/{product_id}/content", response_model=ProductContentRead)
def get_product_content_endpoint(
    product_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_ORDER_READ,
) -> ProductContentRead:
    try:
        return get_product_content(
            db,
            tenant_id=tenant_context.current_tenant_id,
            product_id=product_id,
        )
    except Exception as exc:
        _raise_service_error(exc)


@router.patch("/warehouses/{warehouse_id}/primary", response_model=WarehouseRead)
def set_primary_warehouse_endpoint(
    warehouse_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_WAREHOUSE_MANAGE,
) -> WarehouseRead:
    warehouse = get_warehouse(
        db, tenant_id=tenant_context.current_tenant_id, warehouse_id=warehouse_id
    )
    if warehouse is None:
        raise _not_found("Warehouse")
    try:
        warehouse = set_primary_warehouse(
            db,
            warehouse=warehouse,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return WarehouseRead.model_validate(warehouse)
