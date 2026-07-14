from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from plugins.crm.backend.services.customers import require_customer
from plugins.logistics.backend.customer_cylinder_summary_schemas import (
    CustomerCylinderAlertRead,
    CustomerCylinderConditionSummaryRead,
    CustomerCylinderContractSnapshotRead,
    CustomerCylinderPipelineRead,
    CustomerCylinderProductSummaryRead,
    CustomerCylinderSummaryRead,
    CustomerCylinderTotalsRead,
)
from plugins.logistics.backend.models import (
    LogisticsCustomerCylinderLedger,
    LogisticsCylinder,
    LogisticsCylinderContract,
    LogisticsCylinderOwnership,
    LogisticsCylinderStateLog,
    LogisticsMovement,
    LogisticsMovementItem,
)
from plugins.logistics.backend.services.assigned import (
    get_assigned_by_customer,
    has_any_assignment_movement,
)
from plugins.productos.backend.models import Product

AT_CUSTOMER_STATES = {"EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO"}
LOSS_INACTIVITY_DAYS_DEFAULT = 90
MISSING_PRODUCT_NAME = "Sin tipo de envase"
UNSPECIFIED_CONDITION = "UNSPECIFIED"


@dataclass
class OwnershipSnapshot:
    customer_id: str | None
    condition: str | None


@dataclass
class ContractRow:
    contract_id: str
    product_id: str | None
    product_name: str
    cylinder_condition: str | None
    quantity: int


@dataclass
class ConditionAccumulator:
    assigned: int = 0
    at_customer: int = 0
    pipeline: int = 0
    lost: int = 0


@dataclass
class ProductAccumulator:
    product_id: str | None
    product_name: str
    contracted: int = 0
    assigned: int = 0
    at_customer: int = 0
    at_customer_unknown: int = 0
    pipeline_total: int = 0
    in_vehicle: int = 0
    in_transit: int = 0
    in_warehouse: int = 0
    unknown_pipeline: int = 0
    lost: int = 0
    deviation: int = 0
    by_condition: dict[str, ConditionAccumulator] = field(default_factory=dict)
    contract_conditions: set[str] = field(default_factory=set)
    extra_at_customer: int = 0
    ledger_at_customer: int = 0

    def condition_bucket(self, condition: str | None) -> ConditionAccumulator:
        code = condition or UNSPECIFIED_CONDITION
        if code not in self.by_condition:
            self.by_condition[code] = ConditionAccumulator()
        return self.by_condition[code]


def _product_key(product_id: str | None, product_name: str) -> str:
    return product_id or f"missing:{product_name}"


def _pipeline_bucket(state: str | None) -> str:
    if state == "CARGA_EN_VEHICULO":
        return "in_vehicle"
    if state == "EN_RUTA":
        return "in_transit"
    if state is None:
        return "unknown"
    if state.startswith("EN_ALMACEN") or state in {"CREADO_VACIO", "EN_LLENADO", "LLENADO_OK"}:
        return "in_warehouse"
    return "unknown"


def _latest_ownership_map(
    db: Session,
    *,
    cylinder_ids: set[str],
    as_of: datetime | None,
) -> dict[str, OwnershipSnapshot]:
    if not cylinder_ids:
        return {}
    stmt = select(LogisticsCylinderOwnership).where(
        LogisticsCylinderOwnership.cylinder_id.in_(cylinder_ids)
    )
    if as_of is not None:
        stmt = stmt.where(LogisticsCylinderOwnership.change_date <= as_of)
    rows = db.scalars(
        stmt.order_by(
            LogisticsCylinderOwnership.cylinder_id.asc(),
            LogisticsCylinderOwnership.change_date.desc(),
            LogisticsCylinderOwnership.created_at.desc(),
        )
    ).all()
    latest: dict[str, OwnershipSnapshot] = {}
    for row in rows:
        if row.cylinder_id in latest:
            continue
        latest[row.cylinder_id] = OwnershipSnapshot(
            customer_id=row.customer_id,
            condition=row.condition,
        )
    return latest


def _latest_state_map(
    db: Session,
    *,
    cylinder_ids: set[str],
    as_of: datetime | None,
    fallback_states: dict[str, str],
) -> dict[str, str | None]:
    if not cylinder_ids:
        return {}
    if as_of is None:
        return {cylinder_id: fallback_states.get(cylinder_id) for cylinder_id in cylinder_ids}
    stmt = select(LogisticsCylinderStateLog).where(
        LogisticsCylinderStateLog.cylinder_id.in_(cylinder_ids)
    )
    stmt = stmt.where(LogisticsCylinderStateLog.created_at <= as_of)
    rows = db.scalars(
        stmt.order_by(
            LogisticsCylinderStateLog.cylinder_id.asc(),
            LogisticsCylinderStateLog.created_at.desc(),
            LogisticsCylinderStateLog.id.desc(),
        )
    ).all()
    latest: dict[str, str | None] = {}
    for row in rows:
        if row.cylinder_id in latest:
            continue
        latest[row.cylinder_id] = row.to_state
    for cylinder_id in cylinder_ids:
        latest.setdefault(cylinder_id, fallback_states.get(cylinder_id))
    return latest


def _active_contracts(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
) -> list[ContractRow]:
    stmt = (
        select(LogisticsCylinderContract, Product.name)
        .outerjoin(Product, Product.id == LogisticsCylinderContract.cylinder_type_id)
        .where(
            LogisticsCylinderContract.tenant_id == tenant_id,
            LogisticsCylinderContract.customer_id == customer_id,
            LogisticsCylinderContract.status == "ACTIVE",
        )
        .order_by(LogisticsCylinderContract.created_at.asc())
    )
    return [
        ContractRow(
            contract_id=contract.id,
            product_id=contract.cylinder_type_id,
            product_name=product_name or MISSING_PRODUCT_NAME,
            cylinder_condition=contract.cylinder_condition,
            quantity=contract.quantity,
        )
        for contract, product_name in db.execute(stmt).all()
    ]


def _customer_related_cylinder_ids(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    as_of: datetime | None,
) -> set[str]:
    ownership_stmt = select(distinct(LogisticsCylinderOwnership.cylinder_id)).where(
        LogisticsCylinderOwnership.customer_id == customer_id
    )
    if as_of is not None:
        ownership_stmt = ownership_stmt.where(LogisticsCylinderOwnership.change_date <= as_of)

    movement_stmt = (
        select(distinct(LogisticsMovementItem.cylinder_id))
        .join(LogisticsMovement, LogisticsMovement.id == LogisticsMovementItem.movement_id)
        .where(
            LogisticsMovement.tenant_id == tenant_id,
            LogisticsMovement.customer_id == customer_id,
            LogisticsMovement.movement_type.in_(["SC", "IC"]),
            LogisticsMovement.status == "COMPLETADO",
            LogisticsMovementItem.cylinder_id.is_not(None),
        )
    )
    if as_of is not None:
        movement_stmt = movement_stmt.where(LogisticsMovement.created_at <= as_of)

    ledger_stmt = select(distinct(LogisticsCustomerCylinderLedger.cylinder_id)).where(
        LogisticsCustomerCylinderLedger.tenant_id == tenant_id,
        LogisticsCustomerCylinderLedger.customer_id == customer_id,
        LogisticsCustomerCylinderLedger.cylinder_id.is_not(None),
    )
    if as_of is not None:
        ledger_stmt = ledger_stmt.where(LogisticsCustomerCylinderLedger.occurred_at <= as_of)

    ownership_ids = {row for row in db.scalars(ownership_stmt).all() if row is not None}
    movement_ids = {row for row in db.scalars(movement_stmt).all() if row is not None}
    ledger_ids = {row for row in db.scalars(ledger_stmt).all() if row is not None}
    return ownership_ids | movement_ids | ledger_ids


def _load_cylinders(
    db: Session,
    *,
    tenant_id: str,
    cylinder_ids: set[str],
) -> dict[str, LogisticsCylinder]:
    if not cylinder_ids:
        return {}
    rows = db.scalars(
        select(LogisticsCylinder).where(
            LogisticsCylinder.tenant_id == tenant_id,
            LogisticsCylinder.id.in_(cylinder_ids),
        )
    ).all()
    return {row.id: row for row in rows}


def _product_names(
    db: Session,
    *,
    tenant_id: str,
    product_ids: set[str],
) -> dict[str, str]:
    if not product_ids:
        return {}
    rows = db.execute(
        select(Product.id, Product.name).where(
            Product.tenant_id == tenant_id,
            Product.id.in_(product_ids),
        )
    ).all()
    return {product_id: product_name for product_id, product_name in rows}


def _build_contract_snapshot(contract_ids: list[str]) -> CustomerCylinderContractSnapshotRead:
    if not contract_ids:
        return CustomerCylinderContractSnapshotRead(status="NONE")
    return CustomerCylinderContractSnapshotRead(
        contract_id=contract_ids[0] if len(contract_ids) == 1 else None,
        status="ACTIVE",
        active_contract_count=len(contract_ids),
        contract_ids=contract_ids,
    )


def _product_sort_key(item: ProductAccumulator) -> tuple[str, str]:
    return (item.product_name.lower(), item.product_id or "")


def _apply_customer_possession_ledger(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    as_of: datetime | None,
    get_product,
) -> None:
    stmt = (
        select(LogisticsCustomerCylinderLedger, Product.name)
        .outerjoin(Product, Product.id == LogisticsCustomerCylinderLedger.product_id)
        .where(
            LogisticsCustomerCylinderLedger.tenant_id == tenant_id,
            LogisticsCustomerCylinderLedger.customer_id == customer_id,
            LogisticsCustomerCylinderLedger.cylinder_id.is_(None),
        )
        .order_by(LogisticsCustomerCylinderLedger.occurred_at.asc())
    )
    if as_of is not None:
        stmt = stmt.where(LogisticsCustomerCylinderLedger.occurred_at <= as_of)

    net: dict[tuple[str, str], int] = {}
    meta: dict[tuple[str, str], tuple[str | None, str, str]] = {}
    for row, product_name in db.execute(stmt).all():
        resolved_product_name = row.product_name or product_name or MISSING_PRODUCT_NAME
        product_key = _product_key(row.product_id, resolved_product_name)
        condition_code = row.condition or UNSPECIFIED_CONDITION
        key = (product_key, condition_code)
        sign = 1 if row.event_type == "IN_TO_CUSTOMER" else -1
        net[key] = net.get(key, 0) + int(row.quantity) * sign
        meta[key] = (row.product_id, resolved_product_name, condition_code)

    for key, quantity in net.items():
        if quantity <= 0:
            continue
        product_id, product_name, condition_code = meta[key]
        product = get_product(product_id, product_name)
        product.at_customer += quantity
        product.ledger_at_customer += quantity
        product.condition_bucket(condition_code).at_customer += quantity


def get_customer_cylinder_summary(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    include_serials: bool = False,
    as_of: datetime | None = None,
) -> CustomerCylinderSummaryRead:
    if include_serials:
        raise ValueError("include_serials no esta disponible en el primer slice de 0023AO")

    customer = require_customer(db, tenant_id=tenant_id, customer_id=customer_id)
    active_contracts = _active_contracts(db, tenant_id=tenant_id, customer_id=customer_id)
    assigned_rows = get_assigned_by_customer(
        db, tenant_id=tenant_id, customer_id=customer_id, as_of=as_of
    )
    has_assignment_movements = has_any_assignment_movement(
        db, tenant_id=tenant_id, customer_id=customer_id, as_of=as_of
    )

    by_product: dict[str, ProductAccumulator] = {}
    contract_ids = [row.contract_id for row in active_contracts]

    def get_product(product_id: str | None, product_name: str) -> ProductAccumulator:
        key = _product_key(product_id, product_name)
        if key not in by_product:
            by_product[key] = ProductAccumulator(product_id=product_id, product_name=product_name)
        return by_product[key]

    for contract in active_contracts:
        product = get_product(contract.product_id, contract.product_name)
        product.contracted += contract.quantity
        if contract.product_id and contract.cylinder_condition:
            product.contract_conditions.add(contract.cylinder_condition)

    for row in assigned_rows:
        product = get_product(row.product_id, row.product_name)
        product.assigned += row.quantity

    _apply_customer_possession_ledger(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        as_of=as_of,
        get_product=get_product,
    )

    candidate_ids = _customer_related_cylinder_ids(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        as_of=as_of,
    )
    cylinders = _load_cylinders(db, tenant_id=tenant_id, cylinder_ids=candidate_ids)
    product_names = _product_names(
        db,
        tenant_id=tenant_id,
        product_ids={cylinder.product_id for cylinder in cylinders.values() if cylinder.product_id},
    )
    fallback_states = {
        cylinder_id: cylinder.current_state for cylinder_id, cylinder in cylinders.items()
    }
    latest_states = _latest_state_map(
        db,
        cylinder_ids=candidate_ids,
        as_of=as_of,
        fallback_states=fallback_states,
    )
    latest_ownerships = _latest_ownership_map(db, cylinder_ids=candidate_ids, as_of=as_of)

    for cylinder_id in candidate_ids:
        ownership = latest_ownerships.get(cylinder_id)
        state = latest_states.get(cylinder_id)
        cylinder = cylinders.get(cylinder_id)
        if cylinder is None:
            continue
        product = get_product(
            cylinder.product_id,
            product_names.get(cylinder.product_id or "", MISSING_PRODUCT_NAME),
        )
        condition = (ownership.condition if ownership else None) or cylinder.condition
        condition_bucket = product.condition_bucket(condition)
        if state in AT_CUSTOMER_STATES:
            if ownership is not None and ownership.customer_id == customer_id:
                product.at_customer += 1
                condition_bucket.at_customer += 1
            else:
                product.at_customer_unknown += 1
            continue

        pipeline_bucket = _pipeline_bucket(state)
        product.pipeline_total += 1
        if pipeline_bucket == "in_vehicle":
            product.in_vehicle += 1
        elif pipeline_bucket == "in_transit":
            product.in_transit += 1
        elif pipeline_bucket == "in_warehouse":
            product.in_warehouse += 1
        else:
            product.unknown_pipeline += 1
        condition_bucket.pipeline += 1

    product_rows: list[CustomerCylinderProductSummaryRead] = []
    alerts: list[CustomerCylinderAlertRead] = []

    for product in sorted(by_product.values(), key=_product_sort_key):
        tracked_at_customer = product.at_customer - product.extra_at_customer
        transition_mode = (
            product.assigned == 0 and product.at_customer > 0 and not has_assignment_movements
        )
        product.lost = max(
            product.assigned
            - (tracked_at_customer + product.at_customer_unknown + product.pipeline_total),
            0,
        )
        if transition_mode:
            product.lost = 0
        product.deviation = product.assigned - product.contracted
        if product.lost > 0:
            if len(product.contract_conditions) == 1:
                product.condition_bucket(
                    next(iter(product.contract_conditions))
                ).lost += product.lost
            else:
                product.condition_bucket(None).lost += product.lost

        if product.at_customer_unknown > 0:
            alerts.append(
                CustomerCylinderAlertRead(
                    severity="CRITICAL",
                    category="ownership_inconsistent",
                    message=(
                        f"{product.at_customer_unknown} cilindros de {product.product_name} "
                        "estan en cliente "
                        "sin ownership correcto"
                    ),
                )
            )
        if product.extra_at_customer > 0 and not transition_mode:
            alerts.append(
                CustomerCylinderAlertRead(
                    severity="CRITICAL",
                    category="unassigned_at_customer",
                    message=(
                        f"{product.extra_at_customer} cilindros de {product.product_name} "
                        "estan en cliente "
                        "sin asignacion contractual activa"
                    ),
                )
            )
        if product.ledger_at_customer > 0 and product.assigned == 0 and not transition_mode:
            alerts.append(
                CustomerCylinderAlertRead(
                    severity="CRITICAL",
                    category="unassigned_at_customer",
                    message=(
                        f"{product.ledger_at_customer} envases de {product.product_name} "
                        "estan en cliente sin asignacion contractual activa"
                    ),
                )
            )
        if transition_mode:
            alerts.append(
                CustomerCylinderAlertRead(
                    severity="INFO",
                    category="transition",
                    message=(
                        f"{product.at_customer} cilindros de {product.product_name} en cliente "
                        "sin assigned historico. Se regulara con proximos movimientos."
                    ),
                )
            )
        elif product.assigned > product.contracted:
            alerts.append(
                CustomerCylinderAlertRead(
                    severity="ERROR",
                    category="excess_assignment",
                    message=(
                        f"Hay {product.assigned} cilindros asignados de {product.product_name} "
                        f"para un contrato de {product.contracted}"
                    ),
                )
            )
        elif product.assigned < product.contracted:
            alerts.append(
                CustomerCylinderAlertRead(
                    severity="WARNING",
                    category="shortage",
                    message=(
                        f"Asignados {product.assigned} de {product.contracted} cilindros "
                        "contratados "
                        f"de {product.product_name}"
                    ),
                )
            )
        if product.lost > 0:
            alerts.append(
                CustomerCylinderAlertRead(
                    severity="WARNING",
                    category="loss",
                    message=(
                        f"Hay {product.lost} cilindros de {product.product_name} asignados "
                        "sin ubicacion operativa consistente"
                    ),
                )
            )
        if product.pipeline_total > 0:
            alerts.append(
                CustomerCylinderAlertRead(
                    severity="INFO",
                    category="pipeline",
                    message=(
                        f"{product.pipeline_total} cilindros de {product.product_name} "
                        "estan en pipeline "
                        f"({product.in_vehicle} vehiculo, {product.in_transit} transito, "
                        f"{product.in_warehouse} almacen, {product.unknown_pipeline} unknown)"
                    ),
                )
            )

        product_rows.append(
            CustomerCylinderProductSummaryRead(
                product_id=product.product_id,
                product_name=product.product_name,
                contracted=product.contracted,
                assigned=product.assigned,
                at_customer=product.at_customer,
                at_customer_unknown=product.at_customer_unknown,
                pipeline=CustomerCylinderPipelineRead(
                    total=product.pipeline_total,
                    in_vehicle=product.in_vehicle,
                    in_transit=product.in_transit,
                    in_warehouse=product.in_warehouse,
                    unknown=product.unknown_pipeline,
                ),
                lost=product.lost,
                deviation=product.deviation,
                by_condition={
                    code: CustomerCylinderConditionSummaryRead(
                        assigned=condition.assigned,
                        at_customer=condition.at_customer,
                        pipeline=condition.pipeline,
                        lost=condition.lost,
                    )
                    for code, condition in sorted(product.by_condition.items())
                },
            )
        )

    if not contract_ids and product_rows:
        alerts.append(
            CustomerCylinderAlertRead(
                severity="ERROR",
                category="missing_contract",
                message="El cliente tiene cilindros operativos relacionados sin contrato activo",
            )
        )

    totals = CustomerCylinderTotalsRead(
        contracted=sum(item.contracted for item in product_rows),
        assigned=sum(item.assigned for item in product_rows),
        at_customer=sum(item.at_customer for item in product_rows),
        at_customer_unknown=sum(item.at_customer_unknown for item in product_rows),
        pipeline=sum(item.pipeline.total for item in product_rows),
        lost=sum(item.lost for item in product_rows),
        deviation=sum(item.deviation for item in product_rows),
    )

    return CustomerCylinderSummaryRead(
        customer_id=customer.id,
        customer_name=customer.commercial_name or customer.legal_name,
        contract=_build_contract_snapshot(contract_ids),
        summary=totals,
        by_product=product_rows,
        alerts=alerts,
    )
