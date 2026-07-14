from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import (
    LogisticsCustomerCylinderLedger,
    LogisticsCylinder,
    LogisticsCylinderContract,
)
from plugins.productos.backend.models import Product

EVENT_IN_TO_CUSTOMER = "IN_TO_CUSTOMER"
EVENT_OUT_FROM_CUSTOMER = "OUT_FROM_CUSTOMER"
SOURCE_MOBILE_DELIVERY = "MOBILE_DELIVERY"
SOURCE_MOBILE_PICKUP = "MOBILE_PICKUP"
TRACE_MODE_AGGREGATE = "AGGREGATE"
TRACE_MODE_SERIALIZED = "SERIALIZED"


@dataclass
class CustomerPossessionSnapshot:
    contract_id: str | None
    condition: str | None
    product_name: str | None


def _resolve_product_name(db: Session, *, tenant_id: str, product_id: str | None) -> str | None:
    if not product_id:
        return None
    return db.scalar(
        select(Product.name).where(
            Product.id == product_id,
            Product.tenant_id == tenant_id,
        )
    )


def _resolve_cylinder_condition(
    db: Session,
    *,
    tenant_id: str,
    cylinder_id: str | None,
) -> str | None:
    if not cylinder_id:
        return None
    return db.scalar(
        select(LogisticsCylinder.condition).where(
            LogisticsCylinder.id == cylinder_id,
            LogisticsCylinder.tenant_id == tenant_id,
        )
    )


def resolve_active_customer_contract_snapshot(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    product_id: str | None,
) -> CustomerPossessionSnapshot:
    stmt = select(LogisticsCylinderContract).where(
        LogisticsCylinderContract.tenant_id == tenant_id,
        LogisticsCylinderContract.customer_id == customer_id,
        LogisticsCylinderContract.status == "ACTIVE",
    )
    if product_id is not None:
        stmt = stmt.where(LogisticsCylinderContract.cylinder_type_id == product_id)
    contracts = list(db.scalars(stmt.order_by(LogisticsCylinderContract.created_at.asc())).all())
    if len(contracts) != 1:
        return CustomerPossessionSnapshot(
            contract_id=None,
            condition=None,
            product_name=_resolve_product_name(db, tenant_id=tenant_id, product_id=product_id),
        )
    contract = contracts[0]
    return CustomerPossessionSnapshot(
        contract_id=contract.id,
        condition=contract.cylinder_condition,
        product_name=_resolve_product_name(db, tenant_id=tenant_id, product_id=product_id),
    )


def append_customer_possession_event(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    source_type: str,
    source_id: str,
    event_type: str,
    product_id: str | None,
    product_name: str | None,
    quantity: float,
    created_by: str,
    occurred_at: datetime | None,
    notes: str | None,
    contract_id: str | None = None,
    condition: str | None = None,
    cylinder_id: str | None = None,
    trace_mode: str | None = None,
) -> LogisticsCustomerCylinderLedger:
    existing = db.scalar(
        select(LogisticsCustomerCylinderLedger).where(
            LogisticsCustomerCylinderLedger.tenant_id == tenant_id,
            LogisticsCustomerCylinderLedger.source_type == source_type,
            LogisticsCustomerCylinderLedger.source_id == source_id,
            LogisticsCustomerCylinderLedger.event_type == event_type,
        )
    )
    if existing is not None:
        return existing

    snapshot = resolve_active_customer_contract_snapshot(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        product_id=product_id,
    )
    resolved_product_name = product_name or snapshot.product_name
    resolved_condition = (
        condition
        or _resolve_cylinder_condition(
            db,
            tenant_id=tenant_id,
            cylinder_id=cylinder_id,
        )
        or snapshot.condition
    )

    ledger = LogisticsCustomerCylinderLedger(
        tenant_id=tenant_id,
        customer_id=customer_id,
        contract_id=contract_id or snapshot.contract_id,
        source_type=source_type,
        source_id=source_id,
        event_type=event_type,
        product_id=product_id,
        product_name=resolved_product_name,
        condition=resolved_condition,
        quantity=quantity,
        cylinder_id=cylinder_id,
        trace_mode=trace_mode or (TRACE_MODE_SERIALIZED if cylinder_id else TRACE_MODE_AGGREGATE),
        occurred_at=occurred_at or datetime.now(UTC),
        created_by=created_by,
        notes=notes,
    )
    db.add(ledger)
    db.flush()
    return ledger
