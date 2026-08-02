"""Motor de exceso de contratos (SPEC 0023AD.4).

Medición global por cliente con fuente única `at_customer`, tracking vivo por
(customer, cylinder_type_id), auto-creación de contrato tras `excess_wait_days`
y protección contra ejecución concurrente del worker (lock optimista).

El contrato auto-creado se construye desde el SNAPSHOT del tracking
(base_unit_price / base_contract_type / excess_wait_days / auto_renew_on_excess),
nunca del contrato base en vivo.
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models.contracts import (
    LogisticsContractExcessTracking,
    LogisticsCylinderContract,
)
from plugins.logistics.backend.schemas import (
    ContractExcessResolveRequest,
    ContractExcessTrackingRead,
    CylinderContractCreate,
    SoftLimitConfirmRequest,
)
from plugins.logistics.backend.services.contracts import (
    _append_history,
    activate_contract,
    create_contract,
)
from plugins.logistics.backend.services.customer_cylinder_summary import (
    get_customer_cylinder_summary,
)

SYSTEM_CONTEXT_BRANCH = None
EXCESS_RESOLVED_REASON = "posesion normalizada"


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _system_user_id(db: Session, tenant_id: str) -> str:
    # Usuario de sistema: primer usuario del tenant (configurable en el futuro).
    from sqlalchemy import text

    return str(
        db.execute(
            text("SELECT id FROM users ORDER BY created_at LIMIT 1")
        ).scalar_one()
    )


def _active_contracts(
    db: Session, *, tenant_id: str, customer_id: str
) -> list[LogisticsCylinderContract]:
    return list(
        db.scalars(
            select(LogisticsCylinderContract)
            .where(
                LogisticsCylinderContract.tenant_id == tenant_id,
                LogisticsCylinderContract.customer_id == customer_id,
                LogisticsCylinderContract.status == "ACTIVE",
            )
            .order_by(  # noqa: E501
                LogisticsCylinderContract.quantity.desc(),
                LogisticsCylinderContract.created_at.desc()
            )
        ).all()
    )


def _contract_base(contracts: list[LogisticsCylinderContract]) -> LogisticsCylinderContract | None:
    # Determinista: mayor quantity; desempate created_at DESC (spec 2b).
    return contracts[0] if contracts else None


def _contract_for_type(
    contracts: list[LogisticsCylinderContract], cylinder_type_id: str | None
) -> LogisticsCylinderContract | None:
    if not cylinder_type_id:
        return None
    return next((c for c in contracts if c.cylinder_type_id == cylinder_type_id), None)


def _active_tracking(
    db: Session, *, tenant_id: str, customer_id: str, cylinder_type_id: str
) -> LogisticsContractExcessTracking | None:
    return db.scalar(
        select(LogisticsContractExcessTracking).where(
            LogisticsContractExcessTracking.tenant_id == tenant_id,
            LogisticsContractExcessTracking.customer_id == customer_id,
            LogisticsContractExcessTracking.cylinder_type_id == cylinder_type_id,
            LogisticsContractExcessTracking.status == "ACTIVE",
        )
    )


def _create_tracking(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    cylinder_type_id: str,
    excess_qty: int,
    source: LogisticsCylinderContract,
    now: datetime,
) -> LogisticsContractExcessTracking:
    tracking = LogisticsContractExcessTracking(
        tenant_id=tenant_id,
        customer_id=customer_id,
        cylinder_type_id=cylinder_type_id,
        excess_qty=excess_qty,
        first_detected_at=now,
        last_seen_at=now,
        excess_wait_days=source.excess_wait_days,
        auto_renew_on_excess=source.auto_renew_on_excess,
        base_unit_price=float(source.unit_price),
        base_contract_type=source.contract_type,
        status="ACTIVE",
    )
    db.add(tracking)
    db.flush()
    return tracking


def _emit_tracking_event(
    db: Session,
    *,
    context: LogisticsActionContext,
    event_name: str,
    tracking: LogisticsContractExcessTracking,
    payload: dict[str, object],
) -> None:
    emit_logistics_event(
        db,
        context=context,
        event_name=event_name,
        entity_type="contract_excess_tracking",
        entity_id=tracking.id,
        payload=payload,
    )


def _auto_create_contract(
    db: Session,
    *,
    tracking: LogisticsContractExcessTracking,
    source: LogisticsCylinderContract,
    system_user_id: str,
    context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    if source.warehouse_id is None:
        raise ValueError(
            "El contrato fuente no tiene almacén; no se puede auto-crear el contrato"
        )
    payload = CylinderContractCreate(
        contract_type=tracking.base_contract_type,
        customer_id=tracking.customer_id,
        warehouse_id=source.warehouse_id,
        start_date=datetime.now(UTC).date(),
        cylinder_type_id=tracking.cylinder_type_id,
        quantity=tracking.excess_qty,
        unit_price=tracking.base_unit_price,
        excess_wait_days=tracking.excess_wait_days,
        auto_renew_on_excess=tracking.auto_renew_on_excess,
        source_contract_id=source.id,
    )
    contract = create_contract(
        db,
        tenant_id=tracking.tenant_id,
        created_by=system_user_id,
        payload=payload,
        action_context=context,
    )
    contract = activate_contract(db, contract=contract, action_context=context)
    # Auto-emitido por el sistema: sin firma automática, pasa a ACTIVE.
    contract.status = "ACTIVE"
    contract.signed_flag = False
    _append_history(
        db,
        contract=contract,
        event_type="AUTO_ACTIVATED",
        description=f"Contrato auto-creado por exceso (tracking {tracking.id})",
        created_by=system_user_id,
    )
    db.add(contract)
    db.flush()
    return contract


def sweep_contract_excess(
    db: Session,
    *,
    tenant_id: str,
    now: datetime | None = None,
    system_user_id: str | None = None,
) -> dict[str, int]:
    """Corrida del worker: evalúa exceso global por cliente y auto-crea contratos."""
    now = _as_aware(now or datetime.now(UTC))
    customers = db.execute(
        select(LogisticsCylinderContract.customer_id)
        .where(
            LogisticsCylinderContract.tenant_id == tenant_id,
            LogisticsCylinderContract.status == "ACTIVE",
        )
        .distinct()
    ).scalars().all()
    system_user_id = system_user_id or _system_user_id(db, tenant_id)

    context = LogisticsActionContext(
        tenant_id=tenant_id,
        branch_id=None,
        actor_user_id=system_user_id,
        correlation_id=None,
        request_id=None,
    )

    result = {
        "customers": 0,
        "trackings_created": 0,
        "trackings_resolved": 0,
        "contracts_created": 0,
        "excess_blocked": 0,
    }
    for customer_id in customers:
        result["customers"] += 1
        contracts = _active_contracts(db, tenant_id=tenant_id, customer_id=customer_id)
        if not contracts:
            continue
        summary = get_customer_cylinder_summary(
            db, tenant_id=tenant_id, customer_id=customer_id
        )
        limit = sum(c.quantity for c in contracts)
        at_customer_total = summary.summary.at_customer
        excess_global = at_customer_total - limit

        # Resolver trackings vivos cuando la posesión se normaliza.
        if excess_global <= 0:
            active = list(
                db.scalars(
                    select(LogisticsContractExcessTracking).where(
                        LogisticsContractExcessTracking.tenant_id == tenant_id,
                        LogisticsContractExcessTracking.customer_id == customer_id,
                        LogisticsContractExcessTracking.status == "ACTIVE",
                    )
                ).all()
            )
            for tracking in active:
                tracking.status = "RESOLVED"
                tracking.resolved_reason = EXCESS_RESOLVED_REASON
                tracking.last_seen_at = now
                db.add(tracking)
                _emit_tracking_event(
                    db,
                    context=context,
                    event_name="logistics.cylinder_contract.excess_resolved",
                    tracking=tracking,
                    payload={
                        "customer_id": tracking.customer_id,
                        "cylinder_type_id": tracking.cylinder_type_id,
                        "reason": EXCESS_RESOLVED_REASON,
                    },
                )
                result["trackings_resolved"] += 1
            db.flush()
            continue

        base_contract = _contract_base(contracts)
        contracted_by_type = {
            c.cylinder_type_id: c.quantity for c in contracts if c.cylinder_type_id
        }

        # Tipos con at_customer > 0: sin contrato primero, luego por exceso mayor.
        types = [
            (
                item.product_id,
                item.product_name,
                item.at_customer,
                max(0, item.at_customer - contracted_by_type.get(item.product_id, 0)),
            )
            for item in summary.by_product
            if item.product_id and item.at_customer > 0
        ]
        types.sort(
            key=lambda t: (
                0 if contracted_by_type.get(t[0]) is None else 1,  # sin contrato primero
                -t[3],  # luego por exceso mayor
                t[0] or "",
            )
        )

        remaining = excess_global
        for product_id, _product_name, _at_customer, raw_excess in types:
            if remaining <= 0:
                break
            if raw_excess <= 0:
                continue
            excess_tipo = min(raw_excess, remaining)
            source = _contract_for_type(contracts, product_id) or base_contract
            if source is None:
                continue

            tracking = _active_tracking(
                db, tenant_id=tenant_id, customer_id=customer_id, cylinder_type_id=product_id
            )
            if tracking is None:
                tracking = _create_tracking(
                    db,
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    cylinder_type_id=product_id,
                    excess_qty=excess_tipo,
                    source=source,
                    now=now,
                )
                result["trackings_created"] += 1
                _emit_tracking_event(
                    db,
                    context=context,
                    event_name="logistics.cylinder_contract.excess_detected",
                    tracking=tracking,
                    payload={
                        "customer_id": tracking.customer_id,
                        "cylinder_type_id": tracking.cylinder_type_id,
                        "excess_qty": excess_tipo,
                        "first_detected_at": tracking.first_detected_at.isoformat(),
                    },
                )
            else:
                tracking.excess_qty = excess_tipo
                tracking.last_seen_at = now
                db.add(tracking)
                db.flush()

                if tracking.status != "ACTIVE":
                    continue
                elapsed_days = (now - _as_aware(tracking.first_detected_at)).total_seconds() / 86400
                if elapsed_days < tracking.excess_wait_days:
                    continue
                if not tracking.auto_renew_on_excess:
                    result["excess_blocked"] += 1
                    continue

                # Lock optimista: el tracking decide una sola vez (SPEC 6).
                claimed = db.execute(
                    update(LogisticsContractExcessTracking)
                    .where(
                        LogisticsContractExcessTracking.id == tracking.id,
                        LogisticsContractExcessTracking.status == "ACTIVE",
                    )
                    .values(status="CONTRACT_CREATED")
                )
                if claimed.rowcount == 0:  # type: ignore[union-attr]
                    continue  # otro worker ganó

                contract = _auto_create_contract(
                    db,
                    tracking=tracking,
                    source=source,
                    system_user_id=system_user_id,
                    context=context,
                )
                tracking.created_contract_id = contract.id
                db.add(tracking)
                result["contracts_created"] += 1
                _emit_tracking_event(
                    db,
                    context=context,
                    event_name="logistics.cylinder_contract.auto_created",
                    tracking=tracking,
                    payload={
                        "source_contract_id": source.id,
                        "new_contract_id": contract.id,
                        "contract_number": contract.contract_number,
                        "customer_id": tracking.customer_id,
                        "cylinder_type_id": tracking.cylinder_type_id,
                        "quantity": tracking.excess_qty,
                    },
                )
            remaining -= excess_tipo
        db.commit()
    return result


def list_customer_excess_tracking(
    db: Session, *, tenant_id: str, customer_id: str
) -> list[ContractExcessTrackingRead]:
    rows = list(
        db.scalars(
            select(LogisticsContractExcessTracking)
            .where(
                LogisticsContractExcessTracking.tenant_id == tenant_id,
                LogisticsContractExcessTracking.customer_id == customer_id,
            )
            .order_by(  # noqa: E501
                LogisticsContractExcessTracking.status.asc(),
                LogisticsContractExcessTracking.first_detected_at.desc()
            )
        ).all()
    )
    contract_numbers = {}
    for r in rows:
        if r.created_contract_id:
            c = db.get(LogisticsCylinderContract, r.created_contract_id)
            contract_numbers[r.created_contract_id] = c.contract_number if c else None
    now = datetime.now(UTC)
    return [
        ContractExcessTrackingRead(
            id=r.id,
            customer_id=r.customer_id,
            cylinder_type_id=r.cylinder_type_id,
            product_name=None,
            excess_qty=r.excess_qty,
            first_detected_at=r.first_detected_at,
            last_seen_at=r.last_seen_at,
            excess_wait_days=r.excess_wait_days,
            auto_renew_on_excess=r.auto_renew_on_excess,
            base_unit_price=float(r.base_unit_price),
            base_contract_type=r.base_contract_type,
            status=r.status,
            resolved_reason=r.resolved_reason,
            created_contract_id=r.created_contract_id,
            contract_number=contract_numbers.get(r.created_contract_id),
            days_pending=max(
                0,
                int(r.excess_wait_days - (now - r.first_detected_at).total_seconds() / 86400)
                if r.status == "ACTIVE" else 0,
            ),
        )
        for r in rows
    ]


def update_excess_policy(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    excess_wait_days: int | None,
    auto_renew_on_excess: bool | None,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    if excess_wait_days is not None:
        if excess_wait_days < 0:
            raise ValueError("excess_wait_days no puede ser negativo")
        contract.excess_wait_days = excess_wait_days
    if auto_renew_on_excess is not None:
        contract.auto_renew_on_excess = auto_renew_on_excess
    db.add(contract)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.excess_policy_updated",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        details={
            "excess_wait_days": contract.excess_wait_days,
            "auto_renew_on_excess": contract.auto_renew_on_excess,
        },
    )
    return contract


def resolve_excess_tracking(
    db: Session,
    *,
    tracking: LogisticsContractExcessTracking,
    payload: ContractExcessResolveRequest,
    action_context: LogisticsActionContext,
) -> LogisticsContractExcessTracking:
    if tracking.status != "ACTIVE":
        raise ValueError("Solo se pueden resolver trackings en estado ACTIVE")
    tracking.status = "RESOLVED"
    tracking.resolved_reason = payload.reason
    tracking.last_seen_at = datetime.now(UTC)
    db.add(tracking)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.excess_resolved_manual",
        entity_type="contract_excess_tracking",
        entity_id=tracking.id,
        details={"reason": payload.reason, "excess_qty": tracking.excess_qty},
    )
    return tracking


def confirm_soft_limit(
    db: Session,
    *,
    payload: SoftLimitConfirmRequest,
    action_context: LogisticsActionContext,
) -> None:
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder_contract.soft_limit_confirm",
        entity_type="customer",
        entity_id=payload.customer_id,
        payload={
            "customer_id": payload.customer_id,
            "contract_id": payload.contract_id,
            "source": payload.source,
        },
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.soft_limit_confirm",
        entity_type="customer",
        entity_id=payload.customer_id,
        details={"contract_id": payload.contract_id, "source": payload.source},
    )
