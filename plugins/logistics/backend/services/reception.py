from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsReceptionIncident,
    LogisticsWarehouse,
)
from plugins.logistics.backend.schemas import (
    CylinderTransitionRequest,
    IncidentReasonRead,
    MovementItemRead,
    MovementRead,
    ReceptionIncidentCreateRequest,
    ReceptionIncidentRead,
    ReceptionReceiveRequest,
    ReceptionReceiveResult,
)
from plugins.logistics.backend.services.cylinders import get_cylinder, transition_cylinder
from plugins.logistics.backend.services.movements import record_movement_status_change
from plugins.logistics.backend.services.stock_bridge import adjust_products_stock

INCIDENT_REASONS = (
    ("OBSERVADO", "Cilindro observado", "OBSERVADO"),
    ("PARA_REPARACION", "Enviar a reparacion", "PARA_REPARACION"),
    ("FALTANTE", "Faltante detectado en recepcion", None),
)


def list_incident_reasons() -> list[IncidentReasonRead]:
    return [
        IncidentReasonRead(code=code, description=description, target_state=target_state)
        for code, description, target_state in INCIDENT_REASONS
    ]


def list_pending_receptions(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str,
) -> list[LogisticsMovement]:
    return list(
        db.scalars(
            select(LogisticsMovement)
            .where(
                LogisticsMovement.tenant_id == tenant_id,
                LogisticsMovement.warehouse_id == warehouse_id,
                LogisticsMovement.status == "DESCARGADO_POR_RECEPCIONAR",
            )
            .order_by(LogisticsMovement.updated_at.desc())
        ).all()
    )


def get_reception_detail(
    db: Session,
    *,
    tenant_id: str,
    movement_id: str,
) -> LogisticsMovement | None:
    return db.scalar(
        select(LogisticsMovement).where(
            LogisticsMovement.id == movement_id,
            LogisticsMovement.tenant_id == tenant_id,
        )
    )


def list_reception_incidents(db: Session, *, movement_id: str) -> list[LogisticsReceptionIncident]:
    return list(
        db.scalars(
            select(LogisticsReceptionIncident)
            .where(LogisticsReceptionIncident.movement_id == movement_id)
            .order_by(LogisticsReceptionIncident.created_at.desc())
        ).all()
    )


def create_reception_incident(
    db: Session,
    *,
    movement: LogisticsMovement,
    payload: ReceptionIncidentCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsReceptionIncident:
    incident = LogisticsReceptionIncident(
        tenant_id=movement.tenant_id,
        movement_id=movement.id,
        cylinder_id=payload.cylinder_id,
        reason_code=payload.reason_code,
        description=payload.description,
        created_by=action_context.actor_user_id,
    )
    db.add(incident)
    if payload.cylinder_id is not None:
        target_state = next(
            (target for code, _, target in INCIDENT_REASONS if code == payload.reason_code),
            None,
        )
        if target_state is not None:
            transition_cylinder(
                db,
                tenant_id=movement.tenant_id,
                cylinder_id=payload.cylinder_id,
                payload=CylinderTransitionRequest(
                    to_state=target_state,
                    movement_id=movement.id,
                    origin="RECEPTION_INCIDENT",
                    reason_code=payload.reason_code,
                    notes=payload.description,
                ),
                action_context=action_context,
            )
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=movement.branch_id,
        action="reception.incident.create",
        entity_type="reception_incident",
        entity_id=incident.id,
        details={"movement_id": movement.id, "reason_code": incident.reason_code},
    )
    return incident


def receive_movement(
    db: Session,
    *,
    movement: LogisticsMovement,
    payload: ReceptionReceiveRequest,
    action_context: LogisticsActionContext,
) -> ReceptionReceiveResult:
    if movement.status != "DESCARGADO_POR_RECEPCIONAR":
        raise ValueError("Solo los movimientos pendientes de recepción pueden recibirse")
    if movement.warehouse_id is None:
        raise ValueError("El movimiento debe definir el almacén de destino")

    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == movement.warehouse_id,
            LogisticsWarehouse.tenant_id == movement.tenant_id,
        )
    )
    item_rows = list(
        db.scalars(
            select(LogisticsMovementItem)
            .where(LogisticsMovementItem.movement_id == movement.id)
            .order_by(LogisticsMovementItem.created_at.asc())
        ).all()
    )
    received_map = {item.movement_item_id: item.quantity_received for item in payload.items}
    explicit_mode = len(received_map) > 0
    stock_deltas: dict[tuple[str | None, str | None], float] = defaultdict(float)
    shortage_items: list[MovementItemRead] = []

    for item in item_rows:
        expected_quantity = float(item.quantity_in or item.quantity or 0)
        if expected_quantity <= 0:
            continue
        quantity_received = received_map.get(item.id, expected_quantity if not explicit_mode else 0)
        if quantity_received > expected_quantity:
            raise ValueError("La cantidad recibida no puede exceder la cantidad esperada")
        shortage = expected_quantity - quantity_received
        if quantity_received > 0 and item.cylinder_id is not None:
            cylinder = get_cylinder(db, tenant_id=movement.tenant_id, cylinder_id=item.cylinder_id)
            if cylinder is not None and cylinder.current_state != "EN_ALMACEN_VACIO":
                transitioned = transition_cylinder(
                    db,
                    tenant_id=movement.tenant_id,
                    cylinder_id=item.cylinder_id,
                    payload=CylinderTransitionRequest(
                        to_state="EN_ALMACEN_VACIO",
                        movement_id=movement.id,
                        origin="RECEPTION",
                        notes=payload.notes,
                    ),
                    action_context=action_context,
                )
                if transitioned is not None:
                    item.state_after = transitioned.current_state
        if quantity_received > 0:
            stock_deltas[(item.product_id, item.product_name)] += quantity_received
        if shortage > 0:
            shortage_item = LogisticsMovementItem(
                movement_id=movement.id,
                cylinder_id=None,
                product_id=item.product_id,
                product_name=item.product_name,
                quantity_in=shortage,
                quantity_out=0,
                quantity=0,
                quantity_planned=0,
                item_status="SHORTAGE",
                state_before=item.state_before,
                state_after=item.state_after,
                notes="FALTANTE NO TRANSFERIDO",
            )
            db.add(shortage_item)
            db.flush()
            shortage_items.append(MovementItemRead.model_validate(shortage_item))
        db.add(item)

    adjust_products_stock(
        db,
        tenant_id=movement.tenant_id,
        warehouse_id=movement.warehouse_id,
        deltas=[
            (product_id, quantity, product_name)
            for (product_id, product_name), quantity in stock_deltas.items()
        ],
        reason=f"Reception movement {movement.id}",
        idempotency_prefix=f"{movement.id}:reception",
        action_context=action_context,
    )

    previous_status = movement.status
    movement.status = "RECEPCIONADO"
    if payload.notes:
        movement.notes = f"{movement.notes or ''}\nRecepcion: {payload.notes}".strip()
    db.add(movement)
    record_movement_status_change(
        db,
        movement=movement,
        field_name="status",
        from_value=previous_status,
        to_value=movement.status,
        changed_by=action_context.actor_user_id,
        notes=payload.notes,
    )
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        branch_id=warehouse.branch_id if warehouse is not None else movement.branch_id,
        action="reception.complete",
        entity_type="movement",
        entity_id=movement.id,
        details={
            "warehouse_id": movement.warehouse_id,
            "items_received": sum(stock_deltas.values()),
            "shortages": len(shortage_items),
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        branch_id=warehouse.branch_id if warehouse is not None else movement.branch_id,
        event_name="logistics.reception.completed",
        entity_type="movement",
        entity_id=movement.id,
        payload={
            "movement_id": movement.id,
            "warehouse_id": movement.warehouse_id,
            "items_received": sum(stock_deltas.values()),
            "items_short": len(shortage_items),
            "branch_id": warehouse.branch_id if warehouse is not None else movement.branch_id,
        },
    )
    incidents = [
        ReceptionIncidentRead.model_validate(item)
        for item in list_reception_incidents(db, movement_id=movement.id)
    ]
    return ReceptionReceiveResult(
        movement=MovementRead.model_validate(movement),
        incidents=incidents,
        shortage_items=shortage_items,
    )
