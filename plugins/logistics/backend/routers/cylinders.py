from __future__ import annotations

from typing import Never

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.schemas import (
    CylinderCreateRequest,
    CylinderFillRequest,
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
    CylinderSummaryItem,
    CylinderTransitionRead,
    CylinderTransitionRequest,
    CylinderUpdateRequest,
    CylinderVacateRequest,
    CylinderWeightRead,
    HydrostaticTestCreateRequest,
    HydrostaticTestRead,
    PrintLabelRequest,
    TraceabilityPagination,
    WarehouseSerializedCylinderSummaryItem,
    WarrantyCreateRequest,
    WarrantyRead,
)
from plugins.logistics.backend.services.cylinders import (
    create_cylinder,
    fill_cylinder,
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
    vacate_cylinder,
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
    cylinder_to_read,
    get_cylinder_weight,
    list_available_cylinders_with_weight,
)
from plugins.logistics.backend.services.extras import (
    create_hydrotest,
    create_warranty,
    list_hydrotests,
    list_warranties,
)
from plugins.logistics.backend.services.resources import get_warehouse
from plugins.logistics.backend.services.state_machine import StateTransitionError

router = APIRouter(tags=["logistics-cylinders"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)

REQUIRE_CYLINDER_READ = Depends(require_permission("logistics.cylinder.read"))
REQUIRE_CYLINDER_CREATE = Depends(require_permission("logistics.cylinder.create"))
REQUIRE_CYLINDER_UPDATE = Depends(require_permission("logistics.cylinder.update"))
REQUIRE_CYLINDER_TRANSITION = Depends(require_permission("logistics.cylinder.transition"))
REQUIRE_CYLINDER_TRACE = Depends(require_permission("logistics.cylinder.trace"))
REQUIRE_MAINTENANCE_READ = Depends(require_permission("logistics.maintenance.read"))
REQUIRE_MAINTENANCE_MANAGE = Depends(require_permission("logistics.maintenance.manage"))
REQUIRE_RETIMBRADO_READ = Depends(require_permission("logistics.retimbrado.read"))
REQUIRE_RETIMBRADO_MANAGE = Depends(require_permission("logistics.retimbrado.manage"))
REQUIRE_LABEL_PRINT = Depends(require_permission("logistics.label.print"))
REQUIRE_LABEL_READ = Depends(require_permission("logistics.label.read"))
REQUIRE_OWNERSHIP_READ = Depends(require_permission("logistics.ownership.read"))
REQUIRE_SERVICE_READ = Depends(require_permission("logistics.service.read"))
REQUIRE_SERVICE_MANAGE = Depends(require_permission("logistics.service.manage"))


def _conflict(exc: IntegrityError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc.orig or exc))


def _not_found(entity_name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found")


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
            "No se pudo resolver un almacen activo unico para el usuario. "
            "Ajusta el contexto operativo antes de crear el envase."
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


@router.get("/cylinders", response_model=list[CylinderRead])
def get_cylinders(
    search: str | None = Query(default=None),
    state: str | None = Query(default=None),
    active: bool | None = Query(default=True),
    is_medical: bool | None = Query(default=None),
    container_type: str | None = Query(default=None),
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
            container_type=container_type,
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
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
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


@router.post("/cylinders/{cylinder_id}/fill", response_model=CylinderRead)
def fill_cylinder_endpoint(
    cylinder_id: str,
    payload: CylinderFillRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_UPDATE,
) -> CylinderRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    try:
        resolved_warehouse_id = _resolve_entry_warehouse_id(
            db,
            tenant_context,
            payload.warehouse_id,
        )
        cylinder = fill_cylinder(
            db,
            tenant_id=tenant_context.current_tenant_id,
            cylinder=cylinder,
            warehouse_id=resolved_warehouse_id,
            source_product_id=payload.source_product_id,
            content_kg=payload.content_kg,
            volume_m3=payload.volume_m3,
            weight_current=payload.weight_current,
            fill_operation_id=payload.fill_operation_id,
            notes=payload.notes,
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


@router.post("/cylinders/{cylinder_id}/vacate", response_model=CylinderRead)
def vacate_cylinder_endpoint(
    cylinder_id: str,
    payload: CylinderVacateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CYLINDER_UPDATE,
) -> CylinderRead:
    cylinder = get_cylinder(db, tenant_id=tenant_context.current_tenant_id, cylinder_id=cylinder_id)
    if cylinder is None:
        raise _not_found("Cylinder")
    try:
        resolved_warehouse_id = _resolve_entry_warehouse_id(
            db,
            tenant_context,
            payload.warehouse_id,
        )
        cylinder = vacate_cylinder(
            db,
            tenant_id=tenant_context.current_tenant_id,
            cylinder=cylinder,
            warehouse_id=resolved_warehouse_id,
            weight_current=payload.weight_current,
            notes=payload.notes,
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
