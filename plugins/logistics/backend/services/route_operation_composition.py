from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.dto.route_operations import (
    CompositionLineRead,
    CompositionTotalsRead,
    CurrentCompositionRead,
)
from plugins.logistics.backend.models import (
    LogisticsAdrProductConfig,
    LogisticsCylinder,
    LogisticsLoadSerialAssignment,
    LogisticsMovement,
    LogisticsRouteOperation,
    LogisticsRouteOperationItem,
    LogisticsVehicleSession,
)
from plugins.productos.backend.models import Product, ProductAdr

ACTIVE_SESSION_COMPOSITION_STATES = {"CARGA_EN_VEHICULO", "EN_RUTA"}


@dataclass
class SerializedCompositionRow:
    quantity: float
    weight_kg: float | None
    adr_points: float | None


@dataclass
class AggregateDeltaRow:
    product_name: str
    quantity: float


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


def _product_weight(db: Session, *, product_id: str) -> float | None:
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None or product.weight_kg is None:
        return None
    return float(product.weight_kg)


def _product_name(db: Session, *, product_id: str) -> str:
    product = db.scalar(select(Product).where(Product.id == product_id))
    if product is None:
        raise LookupError("Producto no encontrado para composición")
    return product.name


def _load_serialized_composition(
    db: Session, *, session_id: str
) -> dict[str, SerializedCompositionRow]:
    rows = db.execute(
        select(
            LogisticsLoadSerialAssignment.product_id,
            func.count(LogisticsLoadSerialAssignment.cylinder_id),
            func.sum(LogisticsCylinder.weight_current),
            func.sum(LogisticsCylinder.adr_points),
        )
        .join(
            LogisticsCylinder,
            LogisticsCylinder.id == LogisticsLoadSerialAssignment.cylinder_id,
        )
        .where(
            LogisticsLoadSerialAssignment.session_id == session_id,
            # Incluye DELIVERY_SELECTED además de CONFIRMED: los seriales que el chofer
            # seleccionó para entrega temporalmente siguen físicamente en el vehículo
            # y deben reflejarse en la composición vigente.
            LogisticsLoadSerialAssignment.assignment_status.in_(
                {"CONFIRMED", "DELIVERY_SELECTED"}
            ),
            LogisticsCylinder.current_state.in_(ACTIVE_SESSION_COMPOSITION_STATES),
        )
        .group_by(LogisticsLoadSerialAssignment.product_id)
    ).all()
    return {
        product_id: SerializedCompositionRow(
            quantity=float(count or 0),
            weight_kg=float(weight_kg) if weight_kg is not None else None,
            adr_points=float(adr_points) if adr_points is not None else None,
        )
        for product_id, count, weight_kg, adr_points in rows
    }


def _load_physical_only_deltas(
    db: Session, *, session_id: str
) -> dict[str, AggregateDeltaRow]:
    operations = list(
        db.scalars(
            select(LogisticsRouteOperation).where(
                LogisticsRouteOperation.session_id == session_id,
                LogisticsRouteOperation.status == "CONFIRMED",
            )
        ).all()
    )
    if not operations:
        return {}

    movement_ids: set[str] = set()
    movement_types_by_operation: dict[str, set[str]] = {}
    for operation in operations:
        op_movement_ids = json.loads(operation.movement_ids_json)
        movement_ids.update(op_movement_ids)
        movement_types_by_operation[operation.id] = set()

    movement_type_by_id: dict[str, str] = {}
    if movement_ids:
        for movement_id, movement_type in db.execute(
            select(LogisticsMovement.id, LogisticsMovement.movement_type).where(
                LogisticsMovement.id.in_(movement_ids)
            )
        ).all():
            movement_type_by_id[movement_id] = movement_type

    for operation in operations:
        op_movement_ids = json.loads(operation.movement_ids_json)
        movement_types_by_operation[operation.id] = {
            movement_type_by_id[movement_id]
            for movement_id in op_movement_ids
            if movement_id in movement_type_by_id
        }

    deltas: dict[str, AggregateDeltaRow] = {}
    items = list(
        db.scalars(
            select(LogisticsRouteOperationItem)
            .join(
                LogisticsRouteOperation,
                LogisticsRouteOperation.id == LogisticsRouteOperationItem.route_operation_id,
            )
            .where(
                LogisticsRouteOperation.session_id == session_id,
                LogisticsRouteOperation.status == "CONFIRMED",
            )
        ).all()
    )
    for item in items:
        movement_types = movement_types_by_operation.get(item.route_operation_id, set())
        delta = 0.0
        if item.direction == "IN" and "IC" not in movement_types:
            delta = float(item.quantity)
        elif item.direction == "OUT" and "SC" not in movement_types:
            delta = -float(item.quantity)
        if delta == 0:
            continue
        current = deltas.get(item.product_id)
        if current is None:
            deltas[item.product_id] = AggregateDeltaRow(
                product_name=item.product_name,
                quantity=delta,
            )
            continue
        current.quantity += delta
    return deltas


def build_current_composition_v2(
    db: Session, *, session: LogisticsVehicleSession
) -> CurrentCompositionRead:
    from plugins.logistics.backend.integrations.stock import get_warehouse_balances

    balances = get_warehouse_balances(
        db,
        tenant_id=session.tenant_id,
        warehouse_id=session.mobile_warehouse_id,
    )
    balance_map = {balance.product_id: balance for balance in balances.items}
    serialized_map = _load_serialized_composition(db, session_id=session.id)
    physical_deltas = _load_physical_only_deltas(db, session_id=session.id)

    reference_date = (session.departed_at or session.opened_at).date()
    product_lines: list[CompositionLineRead] = []
    total_packages = 0.0
    total_weight = 0.0
    total_adr_points = 0.0
    product_ids = set(balance_map) | set(serialized_map) | set(physical_deltas)

    for product_id in sorted(product_ids):
        balance = balance_map.get(product_id)
        if product_id in serialized_map:
            serialized = serialized_map[product_id]
            quantity = serialized.quantity
            if quantity <= 0:
                continue
            product_name = (
                balance.product_name
                if balance is not None
                else physical_deltas.get(product_id, AggregateDeltaRow("", 0)).product_name
                or _product_name(db, product_id=product_id)
            )
            total_line_weight = serialized.weight_kg
            adr_points = serialized.adr_points
        else:
            quantity = float(balance.quantity) if balance is not None else 0.0
            quantity += physical_deltas.get(product_id, AggregateDeltaRow("", 0)).quantity
            if quantity <= 0:
                continue
            product_name = (
                balance.product_name
                if balance is not None
                else physical_deltas.get(product_id, AggregateDeltaRow("", 0)).product_name
                or _product_name(db, product_id=product_id)
            )
            weight_kg = _product_weight(db, product_id=product_id)
            total_line_weight = weight_kg * quantity if weight_kg is not None else None
            adr_points = None
            adr_cfg = _latest_adr_config(
                db,
                tenant_id=session.tenant_id,
                product_id=product_id,
                today=reference_date,
            )
            if adr_cfg is not None and adr_cfg.adr_points is not None:
                adr_points = float(adr_cfg.adr_points) * quantity
            else:
                fallback = _fallback_prod_adr(
                    db,
                    tenant_id=session.tenant_id,
                    product_id=product_id,
                    today=reference_date,
                )
                if fallback is not None and fallback.points is not None:
                    adr_points = float(fallback.points) * quantity

        product_lines.append(
            CompositionLineRead(
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                weight_kg=total_line_weight,
                adr_points=adr_points,
            )
        )
        total_packages += quantity
        total_weight += total_line_weight or 0
        total_adr_points += adr_points or 0

    confirmed_ops = db.scalar(
        select(func.count(LogisticsRouteOperation.id)).where(
            LogisticsRouteOperation.session_id == session.id,
            LogisticsRouteOperation.status == "CONFIRMED",
        )
    )
    return CurrentCompositionRead(
        session_id=session.id,
        composition_version=int(confirmed_ops or 0) + 1,
        product_lines=product_lines,
        totals=CompositionTotalsRead(
            total_packages=total_packages,
            total_weight_kg=total_weight,
            total_adr_points=total_adr_points,
        ),
    )
