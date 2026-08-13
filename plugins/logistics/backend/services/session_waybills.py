from __future__ import annotations

import hashlib
import html
import json
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.config import Settings
from apps.api.app.kernel.auth.models import User
from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
)
from plugins.logistics.backend.dto.sessions import (
    SessionWaybillDestinationRead,
    SessionWaybillDriverRead,
    SessionWaybillHistoryVersionRead,
    SessionWaybillItemRead,
    SessionWaybillOfficialVersionRead,
    SessionWaybillPreviewVersionRead,
    SessionWaybillSnapshotRead,
    SessionWaybillStateRead,
    SessionWaybillTotalsRead,
    SessionWaybillVehicleRead,
    WaybillConsigneeRead,
    WaybillIssuerRead,
    WaybillOfficialSnapshotRead,
    WaybillRegulatoryLineRead,
)
from plugins.logistics.backend.models import (
    LogisticsAdrProductConfig,
    LogisticsDeliveryPoint,
    LogisticsLoadPlan,
    LogisticsLoadPlanItem,
    LogisticsMovementItem,
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
ACTIVE_PREVIEW_STATUSES = {"ACTIVE", "ACTIVE_PREVIEW"}


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
            LogisticsSessionWaybillVersion.status.in_(ACTIVE_PREVIEW_STATUSES),
        )
        .order_by(LogisticsSessionWaybillVersion.version.desc())
    )


def _get_latest_issued_version(
    db: Session, *, session_id: str
) -> LogisticsSessionWaybillVersion | None:
    return db.scalar(
        select(LogisticsSessionWaybillVersion)
        .where(
            LogisticsSessionWaybillVersion.session_id == session_id,
            LogisticsSessionWaybillVersion.status == "ISSUED",
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


def _preview_version_to_read(
    version: LogisticsSessionWaybillVersion,
) -> SessionWaybillPreviewVersionRead:
    return SessionWaybillPreviewVersionRead(
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
        document_kind="PREVIEW",
        snapshot=SessionWaybillSnapshotRead.model_validate(json.loads(version.snapshot_json)),
    )


def _official_version_to_read(
    version: LogisticsSessionWaybillVersion,
) -> SessionWaybillOfficialVersionRead:
    return SessionWaybillOfficialVersionRead(
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
        document_kind="OFFICIAL",
        snapshot=WaybillOfficialSnapshotRead.model_validate(json.loads(version.snapshot_json)),
    )


def _history_version_to_read(
    version: LogisticsSessionWaybillVersion,
) -> SessionWaybillHistoryVersionRead:
    snapshot_json = json.loads(version.snapshot_json)
    return SessionWaybillHistoryVersionRead(
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
        document_kind=(
            "OFFICIAL"
            if "issuer" in snapshot_json and "regulatory_lines" in snapshot_json
            else "PREVIEW"
        ),
        snapshot=snapshot_json,
    )


def _resolve_waybill_issuer(settings: Settings) -> WaybillIssuerRead:
    legal_name = (settings.logistics_waybill_issuer_legal_name or "").strip()
    address_line = (settings.logistics_waybill_issuer_address_line or "").strip()
    postal_city_line = (settings.logistics_waybill_issuer_postal_city_line or "").strip()
    if not legal_name or not address_line or not postal_city_line:
        # Fallback keeps operation usable until operator sets the legal issuer explicitly.
        return WaybillIssuerRead(
            legal_name=settings.seed_demo_tenant_name,
            address_line="DIRECCION PENDIENTE CONFIGURACION",
            postal_city_line="LOCALIDAD PENDIENTE CONFIGURACION",
        )
    return WaybillIssuerRead(
        legal_name=legal_name,
        address_line=address_line,
        postal_city_line=postal_city_line,
    )


def _resolve_waybill_consignee(
    db: Session, *, session: LogisticsVehicleSession
) -> WaybillConsigneeRead:
    stops = list(
        db.scalars(
            select(LogisticsRouteStop).where(LogisticsRouteStop.route_id == session.route_id)
        ).all()
    )
    # Multi-stop must stay inside current system scope, not depend on future albaranes.
    if len(stops) > 1:
        return WaybillConsigneeRead(
            mode="ROUTE_DISTRIBUTION",
            legal_name="REPARTO EN RUTA",
            note="Multiples destinos operativos en una misma jornada",
        )
    destination = _build_destination(db, route_id=session.route_id)
    if not destination.name or not destination.address:
        raise ValueError(
            "No se pudo resolver destinatario real para emitir la carta porte oficial"
        )
    return WaybillConsigneeRead(
        mode="SINGLE_DESTINATION",
        legal_name=destination.name,
        address_line=destination.address,
    )


def build_waybill_regulatory_lines(
    db: Session, *, session: LogisticsVehicleSession
) -> list[WaybillRegulatoryLineRead]:
    source_lines = _collect_waybill_source_lines(db, session=session)
    if not source_lines:
        raise ValueError(
            "No hay carga operativa en el vehiculo para emitir la carta porte oficial"
        )

    today = date.today()
    lines: list[WaybillRegulatoryLineRead] = []
    for line in source_lines:
        quantity = float(
            line.quantity if hasattr(line, "quantity") else line.planned_quantity
        )
        if hasattr(line, "quantity_out") and float(line.quantity_out or 0) > 0:
            quantity = float(line.quantity_out)
        elif hasattr(line, "quantity_in") and float(line.quantity_in or 0) > 0:
            quantity = float(line.quantity_in)
        total_weight_kg = getattr(line, "weight_kg", None)
        if total_weight_kg is None:
            total_weight_kg = getattr(line, "planned_weight_kg", None)
        if quantity <= 0:
            continue
        adr_cfg = _latest_adr_config(
            db,
            tenant_id=session.tenant_id,
            product_id=line.product_id,
            today=today,
        )
        fallback = _fallback_prod_adr(
            db,
            tenant_id=session.tenant_id,
            product_id=line.product_id,
            today=today,
        )
        if fallback is None or not fallback.un_number or not fallback.cargo_description:
            raise ValueError(
                "Faltan datos ADR minimos para emitir carta porte oficial del producto "
                f"{line.product_name}"
            )
        net_quantity = float(total_weight_kg) if total_weight_kg is not None else quantity
        net_unit_label = (
            "kg" if total_weight_kg is not None else (fallback.unit_measure or "ud")
        )
        lines.append(
            WaybillRegulatoryLineRead(
                adr_goods_description=f"UN {fallback.un_number} {fallback.cargo_description}",
                product_name=line.product_name,
                adr_category=(adr_cfg.adr_class if adr_cfg is not None else None)
                or fallback.category,
                package_type_label=fallback.packaging_type,
                package_count=int(quantity) if quantity.is_integer() else None,
                net_quantity=net_quantity,
                net_unit_label=net_unit_label,
                adr_total_quantity=net_quantity,
                adr_total_unit_label=net_unit_label,
            )
        )
    return lines


def _collect_waybill_source_lines(
    db: Session, *, session: LogisticsVehicleSession
) -> list[object]:
    composition = build_current_composition(db, session=session)
    source_lines = list(composition.product_lines)
    if not source_lines:
        load_plan = db.scalar(
            select(LogisticsLoadPlan).where(LogisticsLoadPlan.session_id == session.id)
        )
        if load_plan is not None:
            # Fallback preserves legal emit when live stock composition is empty
            # but session still has an explicit confirmed/operational load plan.
            source_lines = list(
                db.scalars(
                    select(LogisticsLoadPlanItem)
                    .where(LogisticsLoadPlanItem.load_plan_id == load_plan.id)
                    .order_by(LogisticsLoadPlanItem.created_at.asc())
                ).all()
            )
    if not source_lines:
        operation = _get_confirmed_transfer_out_operation(db, session_id=session.id)
        if operation is not None:
            movement_id = operation.external_movement_id or operation.id
            # Final fallback uses confirmed transfer-out rows, which are the strongest
            # persisted evidence of what was actually loaded for the session.
            source_lines = list(
                db.scalars(
                    select(LogisticsMovementItem)
                    .where(LogisticsMovementItem.movement_id == movement_id)
                    .order_by(LogisticsMovementItem.created_at.asc())
                ).all()
            )
    return [
        line
        for line in source_lines
        if float(
            (line.quantity_out if hasattr(line, "quantity_out") and line.quantity_out else 0)
            or (line.quantity_in if hasattr(line, "quantity_in") and line.quantity_in else 0)
            or (line.quantity if hasattr(line, "quantity") else line.planned_quantity)
        )
        > 0
    ]


def build_waybill_official_snapshot(
    db: Session, *, session: LogisticsVehicleSession, settings: Settings
) -> WaybillOfficialSnapshotRead:
    current = build_current_session_waybill(db, session=session)
    if not current.snapshot.vehicle.plate.strip():
        raise ValueError("La carta porte oficial necesita matricula de vehiculo")
    if not current.snapshot.driver.name.strip():
        raise ValueError("La carta porte oficial necesita nombre de conductor")
    return WaybillOfficialSnapshotRead(
        issue_date=date.today(),
        vehicle_plate=current.snapshot.vehicle.plate,
        trailer_plate=None,
        driver_name=current.snapshot.driver.name,
        issuer=_resolve_waybill_issuer(settings),
        consignee=_resolve_waybill_consignee(db, session=session),
        regulatory_lines=build_waybill_regulatory_lines(db, session=session),
        totals=current.snapshot.totals,
    )


def get_session_waybill_state(
    db: Session, *, session: LogisticsVehicleSession
) -> SessionWaybillStateRead:
    active = _get_active_version(db, session_id=session.id)
    issued = _get_latest_issued_version(db, session_id=session.id)
    if active is None:
        return SessionWaybillStateRead(
            active=None,
            issued=_official_version_to_read(issued) if issued is not None else None,
            sync_status=None,
            can_regenerate=session.status in REGENERABLE_STATUSES,
            can_emit=False,
            can_reissue=issued is not None,
            emit_block_reason="Genera primero la preview viva de la carta porte",
        )
    current = build_current_session_waybill(db, session=session)
    sync_status = (
        "SYNCED" if active.operational_hash == current.operational_hash else "OUTDATED"
    )
    has_source_lines = bool(_collect_waybill_source_lines(db, session=session))
    emit_block_reason = None
    if sync_status != "SYNCED":
        emit_block_reason = (
            "La preview viva esta desactualizada. Regenera la carta porte antes de emitir."
        )
    elif not has_source_lines:
        emit_block_reason = (
            "El vehiculo no tiene carga operativa. No se puede emitir carta porte oficial vacia."
        )
    return SessionWaybillStateRead(
        active=_preview_version_to_read(active),
        issued=_official_version_to_read(issued) if issued is not None else None,
        sync_status=sync_status,
        can_regenerate=session.status in REGENERABLE_STATUSES,
        can_emit=sync_status == "SYNCED" and has_source_lines,
        can_reissue=issued is not None,
        emit_block_reason=emit_block_reason,
    )


def list_session_waybill_history(
    db: Session, *, session: LogisticsVehicleSession
) -> list[SessionWaybillHistoryVersionRead]:
    versions = _list_versions(db, session_id=session.id)
    return [_history_version_to_read(version) for version in versions]


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
        active.status = "SUPERSEDED_PREVIEW"
        db.add(active)

    snapshot_json = json.dumps(current.snapshot.model_dump(), sort_keys=True, separators=(",", ":"))
    version = LogisticsSessionWaybillVersion(
        tenant_id=session.tenant_id,
        session_id=session.id,
        previous_version_id=active.id if active is not None else None,
        version=next_version,
        status="ACTIVE_PREVIEW",
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


def emit_session_waybill_document(
    db: Session,
    *,
    session: LogisticsVehicleSession,
    settings: Settings,
    reason: str,
    idempotency_key: str | None,
    action_context: LogisticsActionContext,
) -> SessionWaybillStateRead:
    if idempotency_key:
        existing = db.scalar(
            select(LogisticsSessionWaybillVersion).where(
                LogisticsSessionWaybillVersion.session_id == session.id,
                LogisticsSessionWaybillVersion.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return get_session_waybill_state(db, session=session)

    active = _get_active_version(db, session_id=session.id)
    if active is None:
        raise ValueError("Genera la preview viva antes de emitir la carta porte oficial")
    current = build_current_session_waybill(db, session=session)
    if active.operational_hash != current.operational_hash:
        raise ValueError(
            "La preview viva esta desactualizada; regenerala antes de emitir"
        )

    previous_issued = _get_latest_issued_version(db, session_id=session.id)
    next_version = (
        max(
            (item.version for item in _list_versions(db, session_id=session.id)),
            default=0,
        )
        + 1
    )
    if previous_issued is not None:
        previous_issued.status = "SUPERSEDED_ISSUED"
        db.add(previous_issued)

    snapshot = build_waybill_official_snapshot(db, session=session, settings=settings)
    # Official document keeps same operational hash so preview freshness can detect stale emission.
    version = LogisticsSessionWaybillVersion(
        tenant_id=session.tenant_id,
        session_id=session.id,
        previous_version_id=previous_issued.id if previous_issued is not None else active.id,
        version=next_version,
        status="ISSUED",
        regulatory_context=REGULATORY_CONTEXT,
        generated_by=action_context.actor_user_id,
        operational_hash=current.operational_hash,
        snapshot_schema_version=SNAPSHOT_SCHEMA_VERSION,
        movement_ids_json=json.dumps(current.movement_ids),
        # Official snapshot carries `date`, so persist through Pydantic JSON mode.
        snapshot_json=json.dumps(
            snapshot.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        ),
        change_event="OFFICIAL_ISSUE",
        change_reason=reason,
        idempotency_key=idempotency_key,
    )
    db.add(version)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="vehicle_session.waybill.emit",
        entity_type="vehicle_session",
        entity_id=session.id,
        details={
            "version_id": version.id,
            "version": next_version,
            "change_reason": reason,
        },
    )
    return get_session_waybill_state(db, session=session)


def get_session_waybill_document_version(
    db: Session, *, session_id: str, version_id: str | None = None
) -> LogisticsSessionWaybillVersion | None:
    query = select(LogisticsSessionWaybillVersion).where(
        LogisticsSessionWaybillVersion.session_id == session_id,
        LogisticsSessionWaybillVersion.status.in_({"ISSUED", "SUPERSEDED_ISSUED"}),
    )
    if version_id is not None:
        return db.scalar(query.where(LogisticsSessionWaybillVersion.id == version_id))
    return db.scalar(query.order_by(LogisticsSessionWaybillVersion.version.desc()))


def render_waybill_html(version: LogisticsSessionWaybillVersion) -> str:
    snapshot = WaybillOfficialSnapshotRead.model_validate(json.loads(version.snapshot_json))
    rows = "".join(
        (
            "<tr>"
            f"<td>{html.escape(line.adr_goods_description)}</td>"
            f"<td>{html.escape(line.product_name)}</td>"
            f"<td>{html.escape(line.adr_category or '-')}</td>"
            f"<td>{html.escape(line.package_type_label or '-')}</td>"
            f"<td>{line.package_count if line.package_count is not None else '-'}</td>"
            f"<td>{line.net_quantity if line.net_quantity is not None else '-'} "
            f"{html.escape(line.net_unit_label or '')}</td>"
            f"<td>{line.adr_total_quantity if line.adr_total_quantity is not None else '-'} "
            f"{html.escape(line.adr_total_unit_label or '')}</td>"
            "</tr>"
        )
        for line in snapshot.regulatory_lines
    )
    consignee_address = snapshot.consignee.address_line or snapshot.consignee.note or "-"
    meta_line = (
        f"Documento oficial emitido v{version.version} · Fecha {snapshot.issue_date.isoformat()} "
        f"· Conductor {html.escape(snapshot.driver_name)} · Vehiculo "
        f"{html.escape(snapshot.vehicle_plate)}"
    )
    issuer_box = (
        "<div class='box'><h2>Expedidor / Transportista</h2>"
        f"<div>{html.escape(snapshot.issuer.legal_name)}</div>"
        f"<div>{html.escape(snapshot.issuer.address_line)}</div>"
        f"<div>{html.escape(snapshot.issuer.postal_city_line)}</div></div>"
    )
    consignee_box = (
        "<div class='box'><h2>Destinatario</h2>"
        f"<div>{html.escape(snapshot.consignee.legal_name or '-')}</div>"
        f"<div>{html.escape(consignee_address)}</div>"
        f"<div>{html.escape(snapshot.consignee.mode)}</div></div>"
    )
    totals_packages = (
        snapshot.totals.total_packages
        if snapshot.totals.total_packages is not None
        else "-"
    )
    totals_weight = (
        snapshot.totals.total_weight_kg
        if snapshot.totals.total_weight_kg is not None
        else "-"
    )
    totals_adr = (
        snapshot.totals.total_adr_points
        if snapshot.totals.total_adr_points is not None
        else "-"
    )
    return (
        "<!doctype html>"
        "<html lang='es'><head><meta charset='utf-8' />"
        f"<title>Carta de porte v{version.version}</title>"
        "<style>body{font-family:Arial,sans-serif;margin:32px;color:#111;font-size:12px;}"
        "h1{font-size:22px;margin:0 0 8px;}h2{font-size:14px;margin:0 0 8px;}"
        ".grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px;}"
        ".box{border:1px solid #ccc;padding:12px;border-radius:8px;}"
        "table{width:100%;border-collapse:collapse;margin-top:12px;}"
        "th,td{border:1px solid #ccc;padding:8px;text-align:left;vertical-align:top;}"
        "th{background:#f4f4f4;}"
        ".meta{margin-bottom:16px;color:#444;}"
        ".totals{margin-top:16px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}"
        ".totals div{border:1px solid #ccc;padding:10px;border-radius:8px;}</style></head><body>"
        "<h1>Carta de porte</h1>"
        f"<div class='meta'>{meta_line}</div>"
        "<div class='grid'>"
        f"{issuer_box}"
        f"{consignee_box}"
        "</div>"
        "<table><thead><tr>"
        "<th>Mercancia ADR</th><th>Producto</th><th>Categoria</th>"
        "<th>Tipo bulto</th><th>Bultos</th><th>Cantidad neta</th>"
        "<th>Cantidad ADR total</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "<div class='totals'>"
        f"<div>Total bultos: {totals_packages}</div>"
        f"<div>Peso total: {totals_weight} kg</div>"
        f"<div>Puntos ADR: {totals_adr}</div>"
        "</div></body></html>"
    )
