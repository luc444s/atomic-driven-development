from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.kernel.auth.models import User
from plugins.logistics.backend.common import LogisticsActionContext, audit_logistics_action
from plugins.logistics.backend.dto.sessions import (
    SessionWaybillDestinationRead,
    SessionWaybillDriverRead,
    SessionWaybillItemRead,
    SessionWaybillSnapshotRead,
    SessionWaybillStateRead,
    SessionWaybillTotalsRead,
    SessionWaybillVehicleRead,
    SessionWaybillVersionRead,
)
from plugins.logistics.backend.models import (
    LogisticsAdrProductConfig,
    LogisticsDeliveryPoint,
    LogisticsOperation,
    LogisticsRouteOperation,
    LogisticsRouteStop,
    LogisticsSessionWaybillVersion,
    LogisticsVehicle,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.services.route_operations import build_current_composition
from plugins.productos.backend.models import Product, ProductAdr

REGULATORY_CONTEXT = "ES_HACIENDA"
SNAPSHOT_SCHEMA_VERSION = 1
REGENERABLE_STATUSES = {"OUTBOUND", "RETURNING"}


@dataclass
class CurrentSessionWaybill:
    movement_ids: list[str]
    operational_hash: str
    snapshot: SessionWaybillSnapshotRead


def _normalize_movement_ids(movement_ids: list[str | None]) -> list[str]:
    return sorted({movement_id for movement_id in movement_ids if movement_id})


def _latest_adr_config(
    db: Session, *, tenant_id: str, product_id: str, today: date
) -> LogisticsAdrProductConfig | None:
    return db.scalar(
        select(LogisticsAdrProductConfig)
        .where(
            LogisticsAdrProductConfig.tenant_id == tenant_id,
            LogisticsAdrProductConfig.product_id == product_id,
            LogisticsAdrProductConfig.valid_from <= today,
            (LogisticsAdrProductConfig.valid_to.is_(None))
            | (LogisticsAdrProductConfig.valid_to >= today),
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
            (ProductAdr.valid_to.is_(None)) | (ProductAdr.valid_to >= today),
        )
        .order_by(ProductAdr.valid_from.desc())
    )


def _product_weight(db: Session, *, tenant_id: str, product_id: str) -> float | None:
    product = db.scalar(
        select(Product).where(Product.tenant_id == tenant_id, Product.id == product_id)
    )
    if product is None or product.weight_kg is None:
        return None
    return float(product.weight_kg)


def _get_confirmed_transfer_out_operation(
    db: Session, *, session_id: str
) -> LogisticsOperation | None:
    return db.scalar(
        select(LogisticsOperation)
        .where(
            LogisticsOperation.session_id == session_id,
            LogisticsOperation.movement_type == "TRANSFER_OUT",
            LogisticsOperation.status == "CONFIRMED",
        )
        .order_by(LogisticsOperation.created_at.desc())
    )


def _build_destination(
    db: Session, *, route_id: str | None
) -> SessionWaybillDestinationRead:
    def _compose_destination_label(
        customer_name: str | None, address: str | None
    ) -> str | None:
        normalized_customer = customer_name.strip() if customer_name else None
        normalized_address = address.strip() if address else None
        if normalized_customer and normalized_address and normalized_customer != normalized_address:
            return f"{normalized_customer} - {normalized_address}"
        return normalized_customer or normalized_address

    if route_id is None:
        return SessionWaybillDestinationRead()
    first_stop = db.scalar(
        select(LogisticsRouteStop)
        .where(LogisticsRouteStop.route_id == route_id)
        .order_by(LogisticsRouteStop.stop_order.asc())
    )
    if first_stop is None:
        return SessionWaybillDestinationRead()
    delivery_point = db.scalar(
        select(LogisticsDeliveryPoint).where(
            LogisticsDeliveryPoint.id == first_stop.delivery_point_id
        )
    )
    if delivery_point is None:
        destination_label = _compose_destination_label(
            first_stop.customer_name_snapshot,
            first_stop.notes,
        )
        return SessionWaybillDestinationRead(
            id=first_stop.customer_id or first_stop.delivery_point_id,
            name=destination_label,
            address=destination_label,
        )
    return SessionWaybillDestinationRead(
        id=delivery_point.id,
        name=delivery_point.customer_name,
        address=delivery_point.address,
    )


def build_current_session_waybill(
    db: Session, *, session: LogisticsVehicleSession
) -> CurrentSessionWaybill:
    operation = _get_confirmed_transfer_out_operation(db, session_id=session.id)
    vehicle = db.scalar(select(LogisticsVehicle).where(LogisticsVehicle.id == session.vehicle_id))
    if vehicle is None:
        raise LookupError("Vehiculo no encontrado")
    driver = db.scalar(select(User).where(User.id == session.driver_id))
    if driver is None:
        raise LookupError("Conductor no encontrado")
    composition = build_current_composition(db, session=session)
    snapshot = SessionWaybillSnapshotRead(
        vehicle=SessionWaybillVehicleRead(
            id=vehicle.id,
            plate=vehicle.plate,
            kind=vehicle.vehicle_type,
        ),
        driver=SessionWaybillDriverRead(
            id=driver.id,
            name=driver.full_name,
        ),
        destination=_build_destination(db, route_id=session.route_id),
        transported_items=[
            SessionWaybillItemRead(
                product_id=line.product_id,
                product_name=line.product_name,
                quantity=line.quantity,
                weight_kg=line.weight_kg,
                adr_points=line.adr_points,
            )
            for line in composition.product_lines
        ],
        totals=SessionWaybillTotalsRead(
            total_packages=composition.totals.total_packages,
            total_weight_kg=composition.totals.total_weight_kg,
            total_adr_points=composition.totals.total_adr_points,
        ),
    )
    route_operation_movement_ids = []
    for row in db.scalars(
        select(LogisticsRouteOperation.movement_ids_json).where(
            LogisticsRouteOperation.session_id == session.id,
            LogisticsRouteOperation.status == "CONFIRMED",
        )
    ).all():
        route_operation_movement_ids.extend(json.loads(row))
    movement_ids = _normalize_movement_ids([
        *([operation.external_movement_id or operation.id] if operation else []),
        *route_operation_movement_ids,
    ])
    hash_payload = {
        "vehicle_session_id": session.id,
        "movement_ids": movement_ids,
        "vehicle": snapshot.vehicle.model_dump(),
        "driver": snapshot.driver.model_dump(),
        "destination": snapshot.destination.model_dump(),
        "transported_items": [item.model_dump() for item in snapshot.transported_items],
        "totals": snapshot.totals.model_dump(),
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
    }
    operational_hash = hashlib.sha256(
        json.dumps(hash_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return CurrentSessionWaybill(
        movement_ids=movement_ids,
        operational_hash=operational_hash,
        snapshot=snapshot,
    )


def _get_active_version(
    db: Session, *, session_id: str
) -> LogisticsSessionWaybillVersion | None:
    return db.scalar(
        select(LogisticsSessionWaybillVersion)
        .where(
            LogisticsSessionWaybillVersion.session_id == session_id,
            LogisticsSessionWaybillVersion.status == "ACTIVE",
        )
        .order_by(LogisticsSessionWaybillVersion.version.desc())
    )


def _list_versions(
    db: Session, *, session_id: str
) -> list[LogisticsSessionWaybillVersion]:
    return list(
        db.scalars(
            select(LogisticsSessionWaybillVersion)
            .where(LogisticsSessionWaybillVersion.session_id == session_id)
            .order_by(LogisticsSessionWaybillVersion.version.desc())
        ).all()
    )


def _version_to_read(version: LogisticsSessionWaybillVersion) -> SessionWaybillVersionRead:
    return SessionWaybillVersionRead(
        id=version.id,
        vehicle_session_id=version.session_id,
        movement_ids=json.loads(version.movement_ids_json),
        version=version.version,
        previous_version_id=version.previous_version_id,
        status=version.status,
        regulatory_context=version.regulatory_context,
        generated_at=version.generated_at,
        generated_by=version.generated_by,
        snapshot_schema_version=version.snapshot_schema_version,
        change_event=version.change_event,
        change_reason=version.change_reason,
        snapshot=SessionWaybillSnapshotRead.model_validate(json.loads(version.snapshot_json)),
    )


def get_session_waybill_state(
    db: Session, *, session: LogisticsVehicleSession
) -> SessionWaybillStateRead:
    active = _get_active_version(db, session_id=session.id)
    if active is None:
        return SessionWaybillStateRead(
            active=None,
            sync_status=None,
            can_regenerate=session.status in REGENERABLE_STATUSES,
        )
    current = build_current_session_waybill(db, session=session)
    return SessionWaybillStateRead(
        active=_version_to_read(active),
        sync_status=(
            "SYNCED"
            if active.operational_hash == current.operational_hash
            else "OUTDATED"
        ),
        can_regenerate=session.status in REGENERABLE_STATUSES,
    )


def list_session_waybill_history(
    db: Session, *, session: LogisticsVehicleSession
) -> list[SessionWaybillVersionRead]:
    return [_version_to_read(version) for version in _list_versions(db, session_id=session.id)]


def regenerate_session_waybill(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    event: str,
    reason: str,
    idempotency_key: str | None,
    action_context: LogisticsActionContext,
) -> SessionWaybillStateRead:
    if session.status not in REGENERABLE_STATUSES:
        raise ValueError("La carta porte solo puede regenerarse cuando la jornada está en ruta")
    if idempotency_key:
        existing = db.scalar(
            select(LogisticsSessionWaybillVersion).where(
                LogisticsSessionWaybillVersion.session_id == session.id,
                LogisticsSessionWaybillVersion.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return get_session_waybill_state(db, session=session)

    current = build_current_session_waybill(db, session=session)
    active = _get_active_version(db, session_id=session.id)
    if active is not None and active.operational_hash == current.operational_hash:
        return get_session_waybill_state(db, session=session)

    next_version = 1 if active is None else active.version + 1
    if active is not None:
        active.status = "SUPERSEDED"
        db.add(active)

    snapshot_json = json.dumps(current.snapshot.model_dump(), sort_keys=True, separators=(",", ":"))
    version = LogisticsSessionWaybillVersion(
        tenant_id=session.tenant_id,
        session_id=session.id,
        previous_version_id=active.id if active is not None else None,
        version=next_version,
        status="ACTIVE",
        regulatory_context=REGULATORY_CONTEXT,
        generated_by=action_context.actor_user_id,
        operational_hash=current.operational_hash,
        snapshot_schema_version=SNAPSHOT_SCHEMA_VERSION,
        movement_ids_json=json.dumps(current.movement_ids),
        snapshot_json=snapshot_json,
        change_event=event,
        change_reason=reason,
        idempotency_key=idempotency_key,
    )
    db.add(version)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.waybill.regenerate",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "version_id": version.id,
            "version": next_version,
            "change_event": event,
            "change_reason": reason,
        },
    )
    return get_session_waybill_state(db, session=session)
