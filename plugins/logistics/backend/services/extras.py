from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.crm.backend.services.customers import require_customer
from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderWarranty,
    LogisticsHydrostaticTest,
)
from plugins.logistics.backend.schemas import HydrostaticTestCreateRequest, WarrantyCreateRequest


def list_hydrotests(db: Session, *, cylinder_id: str) -> list[LogisticsHydrostaticTest]:
    return list(
        db.scalars(
            select(LogisticsHydrostaticTest)
            .where(LogisticsHydrostaticTest.cylinder_id == cylinder_id)
            .order_by(LogisticsHydrostaticTest.test_date.desc())
        ).all()
    )


def create_hydrotest(
    db: Session,
    *,
    cylinder: LogisticsCylinder,
    payload: HydrostaticTestCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsHydrostaticTest:
    hydrotest = LogisticsHydrostaticTest(
        cylinder_id=cylinder.id,
        test_date=payload.test_date,
        previous_test_date=payload.previous_test_date,
        status=payload.status,
        movement_id=payload.movement_id,
        modified_by=payload.modified_by,
        notes=payload.notes,
    )
    cylinder.last_hydrotest_date = payload.test_date
    cylinder.next_hydrotest_date = payload.test_date + timedelta(days=365 * 5)
    db.add(cylinder)
    db.add(hydrotest)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="hydrotest.create",
        entity_type="cylinder",
        entity_id=cylinder.id,
        details={"serial": cylinder.serial, "test_date": payload.test_date.isoformat()},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder.hydrotest_registered",
        entity_type="cylinder",
        entity_id=cylinder.id,
        payload={"serial": cylinder.serial, "test_date": payload.test_date.isoformat()},
    )
    return hydrotest


def list_warranties(
    db: Session,
    *,
    tenant_id: str,
    cylinder_id: str,
) -> list[LogisticsCylinderWarranty]:
    return list(
        db.scalars(
            select(LogisticsCylinderWarranty)
            .where(
                LogisticsCylinderWarranty.tenant_id == tenant_id,
                LogisticsCylinderWarranty.cylinder_id == cylinder_id,
            )
            .order_by(LogisticsCylinderWarranty.created_at.desc())
        ).all()
    )


def create_warranty(
    db: Session,
    *,
    tenant_id: str,
    cylinder: LogisticsCylinder,
    payload: WarrantyCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderWarranty:
    customer = require_customer(db, tenant_id=tenant_id, customer_id=payload.customer_id)
    warranty = LogisticsCylinderWarranty(
        tenant_id=tenant_id,
        cylinder_id=cylinder.id,
        customer_id=customer.id,
        customer_name=customer.legal_name,
        warranty_type=payload.warranty_type,
        status=payload.status or "INGRESO",
        description=payload.description,
        return_date=payload.return_date,
        created_by=action_context.actor_user_id,
    )
    db.add(warranty)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="warranty.create",
        entity_type="warranty",
        entity_id=warranty.id,
        details={"serial": cylinder.serial, "type": warranty.warranty_type},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.warranty.created",
        entity_type="warranty",
        entity_id=warranty.id,
        payload={"serial": cylinder.serial, "type": warranty.warranty_type},
    )
    return warranty
