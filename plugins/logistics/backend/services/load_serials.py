from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.dto.load_serials import (
    LoadSerialAssignmentRead,
    LoadSerialSearchResultRead,
)
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsLoadSerialAssignment,
    LogisticsOperation,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import CylinderTransitionRequest
from plugins.logistics.backend.services.cylinders import transition_cylinder
from plugins.logistics.backend.services.state_machine import StateTransitionError

ACTIVE_ASSIGNMENT_STATUSES = {"SELECTED", "CONFIRMED"}
COMPATIBLE_CYLINDER_STATES = {"LLENADO_OK", "EN_ALMACEN_VACIO"}
ROUTE_PICKUP_COMPATIBLE_CYLINDER_STATES = {"EN_CLIENTE_VACIO"}
VALID_RELEASE_REASONS = {"MANUAL", "TIMEOUT", "OPERATION_CANCELLED"}
SELECTION_CONTEXT_LOAD_PLAN = "LOAD_PLAN"
SELECTION_CONTEXT_ROUTE_PICKUP = "ROUTE_PICKUP"


def _normalize_selection_context(value: str | None) -> str:
    if not value:
        return SELECTION_CONTEXT_LOAD_PLAN
    normalized = value.strip().upper()
    if normalized not in {SELECTION_CONTEXT_LOAD_PLAN, SELECTION_CONTEXT_ROUTE_PICKUP}:
        raise ValueError("Contexto de selección serial no soportado")
    return normalized


def _build_assignment_read(assignment: LogisticsLoadSerialAssignment) -> LoadSerialAssignmentRead:
    return LoadSerialAssignmentRead(
        id=assignment.id,
        session_id=assignment.session_id,
        product_id=assignment.product_id,
        cylinder_id=assignment.cylinder_id,
        cylinder_serial=assignment.cylinder_serial,
        assignment_status=assignment.assignment_status,
        selected_by=assignment.selected_by,
        selected_at=assignment.selected_at,
        confirmed_by_operation_id=assignment.confirmed_by_operation_id,
        confirmed_at=assignment.confirmed_at,
        released_at=assignment.released_at,
        release_reason=assignment.release_reason,
        notes=assignment.notes,
        updated_at=assignment.updated_at,
    )


def _product_matches_cylinder(cylinder: LogisticsCylinder, *, product_id: str) -> bool:
    return cylinder.product_id == product_id or cylinder.gas_group_id == product_id


def _warehouse_matches_cylinder(
    db: Session, *, tenant_id: str, warehouse_id: str | None, cylinder: LogisticsCylinder
) -> bool:
    if warehouse_id is None:
        return True
    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == warehouse_id,
            LogisticsWarehouse.tenant_id == tenant_id,
        )
    )
    if warehouse is None:
        raise LookupError("Almacén origen no encontrado")
    location = (cylinder.location or "").upper()
    return warehouse.code.upper() in location or warehouse.name.upper() in location


def _active_assignment_for_cylinder(
    db: Session, *, cylinder_id: str
) -> LogisticsLoadSerialAssignment | None:
    return db.scalar(
        select(LogisticsLoadSerialAssignment)
        .where(
            LogisticsLoadSerialAssignment.cylinder_id == cylinder_id,
            LogisticsLoadSerialAssignment.assignment_status.in_(ACTIVE_ASSIGNMENT_STATUSES),
        )
        .with_for_update()
    )


def _resolve_cylinder_for_selection(
    db: Session, *, tenant_id: str, raw_serial: str
) -> LogisticsCylinder | None:
    normalized_serial = raw_serial.strip().upper()
    cylinder = db.scalar(
        select(LogisticsCylinder)
        .where(
            LogisticsCylinder.tenant_id == tenant_id,
            or_(
                LogisticsCylinder.serial == normalized_serial,
                LogisticsCylinder.barcode1 == normalized_serial,
                LogisticsCylinder.barcode2 == normalized_serial,
            ),
        )
        .with_for_update()
    )
    if cylinder is not None:
        return cylinder

    if not normalized_serial.isdigit() or len(normalized_serial) < 4:
        return None

    matches = list(
        db.scalars(
            select(LogisticsCylinder)
            .where(
                LogisticsCylinder.tenant_id == tenant_id,
                or_(
                    LogisticsCylinder.serial.ilike(f"%{normalized_serial}"),
                    LogisticsCylinder.barcode1.ilike(f"%{normalized_serial}"),
                    LogisticsCylinder.barcode2.ilike(f"%{normalized_serial}"),
                ),
            )
            .order_by(LogisticsCylinder.serial.asc())
            .limit(2)
            .with_for_update()
        ).all()
    )
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(
            "El código numérico coincide con más de un serial. Selecciona manualmente."
        )
    return None


def list_selected_load_serial_assignments(
    db: Session,
    *,
    session_id: str,
    product_id: str | None = None,
    selection_context: str | None = None,
) -> list[LoadSerialAssignmentRead]:
    context = _normalize_selection_context(selection_context)
    stmt = select(LogisticsLoadSerialAssignment).where(
        LogisticsLoadSerialAssignment.session_id == session_id,
        LogisticsLoadSerialAssignment.assignment_status.in_(ACTIVE_ASSIGNMENT_STATUSES),
    )
    if product_id is not None:
        stmt = stmt.where(LogisticsLoadSerialAssignment.product_id == product_id)
    assignments = list(
        db.scalars(stmt.order_by(LogisticsLoadSerialAssignment.selected_at.asc())).all()
    )
    if context == SELECTION_CONTEXT_ROUTE_PICKUP:
        filtered: list[LogisticsLoadSerialAssignment] = []
        for assignment in assignments:
            cylinder = db.scalar(
                select(LogisticsCylinder).where(LogisticsCylinder.id == assignment.cylinder_id)
            )
            if (
                cylinder is not None
                and cylinder.current_state in ROUTE_PICKUP_COMPATIBLE_CYLINDER_STATES
            ):
                filtered.append(assignment)
        assignments = filtered
    return [_build_assignment_read(item) for item in assignments]


def search_load_serial_candidates(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    product_id: str,
    source_warehouse_id: str | None,
    selection_context: str | None,
    query: str,
) -> list[LoadSerialSearchResultRead]:
    context = _normalize_selection_context(selection_context)
    normalized_query = query.strip().upper()
    if len(normalized_query) < 2:
        return []
    numeric_only_query = normalized_query.isdigit()
    search_pattern = (
        f"%{normalized_query}%" if numeric_only_query else f"{normalized_query}%"
    )

    cylinders = list(
        db.scalars(
            select(LogisticsCylinder)
            .where(
                LogisticsCylinder.tenant_id == session.tenant_id,
                or_(
                    LogisticsCylinder.serial.ilike(search_pattern),
                    LogisticsCylinder.barcode1.ilike(search_pattern),
                    LogisticsCylinder.barcode2.ilike(search_pattern),
                ),
            )
            .order_by(LogisticsCylinder.serial.asc())
            .limit(20)
        ).all()
    )

    results: list[LoadSerialSearchResultRead] = []
    for cylinder in cylinders:
        active_assignment = db.scalar(
            select(LogisticsLoadSerialAssignment)
            .where(
                LogisticsLoadSerialAssignment.cylinder_id == cylinder.id,
                LogisticsLoadSerialAssignment.assignment_status.in_(ACTIVE_ASSIGNMENT_STATUSES),
            )
        )
        if not _product_matches_cylinder(cylinder, product_id=product_id):
            availability_status = "UNAVAILABLE"
            context_label = "Corresponde a otro producto"
        elif active_assignment is not None:
            availability_status = "OCCUPIED"
            context_label = (
                "Seleccionado en esta jornada"
                if active_assignment.session_id == session.id
                else "Ocupado en otra jornada"
            )
        elif cylinder.current_state not in (
            ROUTE_PICKUP_COMPATIBLE_CYLINDER_STATES
            if context == SELECTION_CONTEXT_ROUTE_PICKUP
            else COMPATIBLE_CYLINDER_STATES
        ):
            availability_status = "UNAVAILABLE"
            context_label = cylinder.current_state
        elif context != SELECTION_CONTEXT_ROUTE_PICKUP and not _warehouse_matches_cylinder(
            db,
            tenant_id=session.tenant_id,
            warehouse_id=source_warehouse_id,
            cylinder=cylinder,
        ):
            availability_status = "UNAVAILABLE"
            context_label = "Fuera de almacén origen"
        else:
            availability_status = "AVAILABLE"
            context_label = "Disponible"
        results.append(
            LoadSerialSearchResultRead(
                cylinder_id=cylinder.id,
                serial=cylinder.serial,
                availability_status=availability_status,
                context_label=context_label,
            )
        )
    return results


def count_active_assignments(
    db: Session, *, session_id: str, product_id: str
) -> int:
    return len(
        list_selected_load_serial_assignments(
            db,
            session_id=session_id,
            product_id=product_id,
        )
    )


def product_requires_serial_capture(
    db: Session,
    *,
    tenant_id: str,
    session_id: str,
    product_id: str,
    source_warehouse_id: str | None,
) -> bool:
    existing_assignment = db.scalar(
        select(LogisticsLoadSerialAssignment.id).where(
            LogisticsLoadSerialAssignment.session_id == session_id,
            LogisticsLoadSerialAssignment.product_id == product_id,
        )
    )
    if existing_assignment is not None:
        return True

    cylinders = list(
        db.scalars(
            select(LogisticsCylinder)
            .where(
                LogisticsCylinder.tenant_id == tenant_id,
                LogisticsCylinder.is_active.is_(True),
                LogisticsCylinder.current_state.in_(COMPATIBLE_CYLINDER_STATES),
                or_(
                    LogisticsCylinder.product_id == product_id,
                    LogisticsCylinder.gas_group_id == product_id,
                ),
            )
            .order_by(LogisticsCylinder.serial.asc())
            .limit(20)
        ).all()
    )
    if source_warehouse_id is None:
        return bool(cylinders)
    return any(
        _warehouse_matches_cylinder(
            db,
            tenant_id=tenant_id,
            warehouse_id=source_warehouse_id,
            cylinder=cylinder,
        )
        for cylinder in cylinders
    )


def select_load_serial(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    product_id: str,
    source_warehouse_id: str | None,
    selection_context: str | None,
    serial: str,
    action_context: LogisticsActionContext,
) -> LoadSerialAssignmentRead:
    context = _normalize_selection_context(selection_context)
    cylinder = _resolve_cylinder_for_selection(
        db,
        tenant_id=session.tenant_id,
        raw_serial=serial,
    )
    if cylinder is None:
        raise LookupError("Serial no encontrado")
    if not cylinder.is_active:
        raise ValueError("El cilindro no está activo")
    if not _product_matches_cylinder(cylinder, product_id=product_id):
        raise ValueError("El serial no corresponde al producto seleccionado")
    compatible_states = (
        ROUTE_PICKUP_COMPATIBLE_CYLINDER_STATES
        if context == SELECTION_CONTEXT_ROUTE_PICKUP
        else COMPATIBLE_CYLINDER_STATES
    )
    if cylinder.current_state not in compatible_states:
        raise ValueError("El cilindro no está disponible para carga operativa")
    if context != SELECTION_CONTEXT_ROUTE_PICKUP and not _warehouse_matches_cylinder(
        db,
        tenant_id=session.tenant_id,
        warehouse_id=source_warehouse_id,
        cylinder=cylinder,
    ):
        raise ValueError("El cilindro no pertenece al almacén origen de esta línea")

    active_assignment = _active_assignment_for_cylinder(db, cylinder_id=cylinder.id)
    if active_assignment is not None:
        if (
            active_assignment.session_id == session.id
            and active_assignment.product_id == product_id
        ):
            return _build_assignment_read(active_assignment)
        raise ValueError("El cilindro ya está ocupado por otra jornada")

    assignment = LogisticsLoadSerialAssignment(
        tenant_id=session.tenant_id,
        session_id=session.id,
        product_id=product_id,
        cylinder_id=cylinder.id,
        cylinder_serial=cylinder.serial,
        assignment_status="SELECTED",
        selected_by=action_context.actor_user_id,
        notes=context,
    )
    db.add(assignment)
    try:
        db.flush()
    except IntegrityError as exc:
        raise ValueError("El cilindro ya fue seleccionado en otra jornada") from exc
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.load_serial.select",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "product_id": product_id,
            "cylinder_id": cylinder.id,
            "serial": cylinder.serial,
        },
    )
    return _build_assignment_read(assignment)


def release_load_serial(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    assignment_id: str,
    release_reason: str,
    action_context: LogisticsActionContext,
) -> LoadSerialAssignmentRead:
    if release_reason not in VALID_RELEASE_REASONS:
        raise ValueError("Motivo de liberación no soportado")
    assignment = db.scalar(
        select(LogisticsLoadSerialAssignment)
        .where(
            LogisticsLoadSerialAssignment.id == assignment_id,
            LogisticsLoadSerialAssignment.session_id == session.id,
        )
        .with_for_update()
    )
    if assignment is None:
        raise LookupError("Asignación serial no encontrada")
    if assignment.assignment_status != "SELECTED":
        raise ValueError("Solo se pueden liberar seriales seleccionados antes de confirmar")
    assignment.assignment_status = "RELEASED"
    assignment.released_at = datetime.now(UTC)
    assignment.release_reason = release_reason
    db.add(assignment)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.load_serial.release",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "assignment_id": assignment.id,
            "serial": assignment.cylinder_serial,
            "release_reason": release_reason,
        },
    )
    return _build_assignment_read(assignment)


def ensure_required_serials_for_load_plan(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    load_plan_items,
) -> None:
    for item in load_plan_items:
        if not product_requires_serial_capture(
            db,
            tenant_id=session.tenant_id,
            session_id=session.id,
            product_id=item.product_id,
            source_warehouse_id=item.source_warehouse_id,
        ):
            continue
        quantity = float(item.planned_quantity)
        if not quantity.is_integer():
            raise ValueError("Los productos serializados requieren cantidades enteras")
        selected_count = count_active_assignments(
            db,
            session_id=session.id,
            product_id=item.product_id,
        )
        if selected_count != int(quantity):
            raise ValueError(
                f"El producto {item.product_name} requiere {int(quantity)} seriales "
                f"y tiene {selected_count} seleccionados"
            )


def confirm_selected_serials_for_operation(
    db: Session,
    *,
    tenant_id: str,
    session_id: str,
    product_ids: set[str],
    operation: LogisticsOperation,
    action_context: LogisticsActionContext,
) -> None:
    assignments = list(
        db.scalars(
            select(LogisticsLoadSerialAssignment)
            .where(
                LogisticsLoadSerialAssignment.session_id == session_id,
                LogisticsLoadSerialAssignment.product_id.in_(product_ids),
                LogisticsLoadSerialAssignment.assignment_status == "SELECTED",
            )
            .order_by(LogisticsLoadSerialAssignment.selected_at.asc())
            .with_for_update()
        ).all()
    )
    now = datetime.now(UTC)
    for assignment in assignments:
        assignment.assignment_status = "CONFIRMED"
        assignment.confirmed_by_operation_id = operation.id
        assignment.confirmed_at = now
        db.add(assignment)
        cylinder = db.scalar(
            select(LogisticsCylinder).where(
                LogisticsCylinder.tenant_id == tenant_id,
                LogisticsCylinder.id == assignment.cylinder_id,
            )
        )
        if cylinder is None:
            continue
        if cylinder.current_state != "CARGA_EN_VEHICULO":
            try:
                transition_cylinder(
                    db,
                    tenant_id=tenant_id,
                    cylinder_id=cylinder.id,
                    payload=CylinderTransitionRequest(
                        to_state="CARGA_EN_VEHICULO",
                        session_id=session_id,
                        origin="SESSION_LOAD_CONFIRM",
                        notes=f"VehicleSession {session_id}",
                    ),
                    action_context=action_context,
                )
            except StateTransitionError:
                # Preserve stronger real states if the cylinder already moved beyond loading.
                pass


def mark_confirmed_serials_on_outbound(
    db: Session,
    *,
    tenant_id: str,
    session_id: str,
    action_context: LogisticsActionContext,
) -> None:
    assignments = list(
        db.scalars(
            select(LogisticsLoadSerialAssignment).where(
                LogisticsLoadSerialAssignment.session_id == session_id,
                LogisticsLoadSerialAssignment.assignment_status == "CONFIRMED",
            )
        ).all()
    )
    for assignment in assignments:
        cylinder = db.scalar(
            select(LogisticsCylinder).where(
                LogisticsCylinder.tenant_id == tenant_id,
                LogisticsCylinder.id == assignment.cylinder_id,
            )
        )
        if cylinder is None or cylinder.current_state != "CARGA_EN_VEHICULO":
            continue
        try:
            transition_cylinder(
                db,
                tenant_id=tenant_id,
                cylinder_id=cylinder.id,
                payload=CylinderTransitionRequest(
                    to_state="EN_RUTA",
                    session_id=session_id,
                    origin="SESSION_OUTBOUND",
                    notes=f"VehicleSession {session_id}",
                ),
                action_context=action_context,
            )
        except StateTransitionError:
            continue


def release_active_serial_assignments(
    db: Session,
    *,
    session_id: str,
    product_id: str | None = None,
    release_reason: str,
) -> None:
    if release_reason not in VALID_RELEASE_REASONS:
        raise ValueError("Motivo de liberación no soportado")
    stmt = (
        select(LogisticsLoadSerialAssignment)
        .where(
            LogisticsLoadSerialAssignment.session_id == session_id,
            LogisticsLoadSerialAssignment.assignment_status.in_(ACTIVE_ASSIGNMENT_STATUSES),
        )
        .with_for_update()
    )
    if product_id is not None:
        stmt = stmt.where(LogisticsLoadSerialAssignment.product_id == product_id)
    assignments = list(db.scalars(stmt).all())
    now = datetime.now(UTC)
    for assignment in assignments:
        assignment.assignment_status = "RELEASED"
        assignment.released_at = now
        assignment.release_reason = release_reason
        db.add(assignment)
