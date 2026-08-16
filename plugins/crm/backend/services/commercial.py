from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from systutor.kernel.auth.models import User

from plugins.crm.backend.common import CrmActionContext, audit_crm_action, emit_crm_event
from plugins.crm.backend.models import (
    CrmCustomer,
    CrmCustomerCommercialAssignment,
)
from plugins.crm.backend.schemas import (
    CommercialUserOptionRead,
    CustomerCommercialAssignmentCreateRequest,
    CustomerCommercialAssignmentRead,
    CustomerCommercialAssignmentUpdateRequest,
)
from plugins.crm.backend.services.addresses import get_address


def list_commercial_users(db: Session, *, tenant_id: str) -> list[CommercialUserOptionRead]:
    users = list(
        db.scalars(
            select(User)
            .where(User.tenant_id == tenant_id, User.is_active.is_(True))
            .order_by(User.full_name.asc())
        ).all()
    )
    return [
        CommercialUserOptionRead(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            is_active=user.is_active,
        )
        for user in users
    ]


def list_commercial_assignments(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    address_id: str | None = None,
    assignment_role: str | None = None,
    active_only: bool = True,
) -> list[CustomerCommercialAssignmentRead]:
    stmt = (
        select(CrmCustomerCommercialAssignment, User)
        .join(User, User.id == CrmCustomerCommercialAssignment.user_id)
        .where(
            CrmCustomerCommercialAssignment.tenant_id == tenant_id,
            CrmCustomerCommercialAssignment.customer_id == customer_id,
            User.tenant_id == tenant_id,
        )
    )
    if active_only:
        stmt = stmt.where(CrmCustomerCommercialAssignment.is_active.is_(True))
    if address_id is not None:
        stmt = stmt.where(CrmCustomerCommercialAssignment.address_id == address_id)
    if assignment_role is not None:
        stmt = stmt.where(CrmCustomerCommercialAssignment.assignment_role == assignment_role)
    stmt = stmt.order_by(
        CrmCustomerCommercialAssignment.is_primary.desc(),
        CrmCustomerCommercialAssignment.created_at.asc(),
    )
    rows = db.execute(stmt).all()
    return [_serialize_assignment(assignment, user) for assignment, user in rows]


def get_commercial_assignment(
    db: Session, *, tenant_id: str, assignment_id: str
) -> CrmCustomerCommercialAssignment | None:
    return db.scalar(
        select(CrmCustomerCommercialAssignment).where(
            CrmCustomerCommercialAssignment.id == assignment_id,
            CrmCustomerCommercialAssignment.tenant_id == tenant_id,
        )
    )


def create_commercial_assignment(
    db: Session,
    *,
    tenant_id: str,
    customer: CrmCustomer,
    payload: CustomerCommercialAssignmentCreateRequest,
    action_context: CrmActionContext,
) -> CustomerCommercialAssignmentRead:
    user = _require_assignment_user(db, tenant_id=tenant_id, user_id=payload.user_id)
    _validate_assignment_address(
        db,
        tenant_id=tenant_id,
        customer=customer,
        address_id=payload.address_id,
    )
    if payload.is_primary:
        _clear_primary_assignments(
            db,
            tenant_id=tenant_id,
            customer_id=customer.id,
            address_id=payload.address_id,
            assignment_role=payload.assignment_role,
        )
    assignment = CrmCustomerCommercialAssignment(
        tenant_id=tenant_id,
        customer_id=customer.id,
        address_id=payload.address_id,
        user_id=user.id,
        assignment_role=payload.assignment_role,
        notes=payload.notes,
        is_primary=payload.is_primary,
    )
    db.add(assignment)
    db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.commercial_assignment.create",
        entity_type="customer_commercial_assignment",
        entity_id=assignment.id,
        details={
            "customer_id": customer.id,
            "address_id": assignment.address_id,
            "user_id": assignment.user_id,
            "assignment_role": assignment.assignment_role,
        },
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.commercial_assignment_added",
        entity_type="customer_commercial_assignment",
        entity_id=assignment.id,
        payload={
            "customer_id": customer.id,
            "address_id": assignment.address_id,
            "assignment_id": assignment.id,
            "user_id": assignment.user_id,
            "assignment_role": assignment.assignment_role,
        },
    )
    return _serialize_assignment(assignment, user)


def update_commercial_assignment(
    db: Session,
    *,
    tenant_id: str,
    customer: CrmCustomer,
    assignment: CrmCustomerCommercialAssignment,
    payload: CustomerCommercialAssignmentUpdateRequest,
    action_context: CrmActionContext,
) -> CustomerCommercialAssignmentRead:
    address_was_provided = "address_id" in payload.model_fields_set
    next_address_id = payload.address_id if address_was_provided else assignment.address_id
    next_role = (
        payload.assignment_role
        if payload.assignment_role is not None
        else assignment.assignment_role
    )
    next_primary = payload.is_primary if payload.is_primary is not None else assignment.is_primary
    next_user_id = payload.user_id if payload.user_id is not None else assignment.user_id
    user = _require_assignment_user(db, tenant_id=tenant_id, user_id=next_user_id)
    _validate_assignment_address(
        db,
        tenant_id=tenant_id,
        customer=customer,
        address_id=next_address_id,
    )
    if next_primary:
        _clear_primary_assignments(
            db,
            tenant_id=tenant_id,
            customer_id=customer.id,
            address_id=next_address_id,
            assignment_role=next_role,
            exclude_assignment_id=assignment.id,
    )
    for field in ["address_id", "user_id", "assignment_role", "notes"]:
        if field not in payload.model_fields_set:
            continue
        value = getattr(payload, field)
        setattr(assignment, field, value.strip() if isinstance(value, str) else value)
    if payload.is_primary is not None:
        assignment.is_primary = payload.is_primary
    if payload.is_active is not None:
        assignment.is_active = payload.is_active
    db.add(assignment)
    db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.commercial_assignment.update",
        entity_type="customer_commercial_assignment",
        entity_id=assignment.id,
        details={
            "customer_id": customer.id,
            "address_id": assignment.address_id,
            "user_id": assignment.user_id,
            "assignment_role": assignment.assignment_role,
        },
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.commercial_assignment_updated",
        entity_type="customer_commercial_assignment",
        entity_id=assignment.id,
        payload={
            "customer_id": customer.id,
            "address_id": assignment.address_id,
            "assignment_id": assignment.id,
            "user_id": assignment.user_id,
            "assignment_role": assignment.assignment_role,
        },
    )
    return _serialize_assignment(assignment, user)


def delete_commercial_assignment(
    db: Session,
    *,
    assignment: CrmCustomerCommercialAssignment,
    action_context: CrmActionContext,
) -> None:
    audit_crm_action(
        db,
        context=action_context,
        action="customer.commercial_assignment.delete",
        entity_type="customer_commercial_assignment",
        entity_id=assignment.id,
        details={
            "customer_id": assignment.customer_id,
            "address_id": assignment.address_id,
            "user_id": assignment.user_id,
            "assignment_role": assignment.assignment_role,
        },
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.commercial_assignment_removed",
        entity_type="customer_commercial_assignment",
        entity_id=assignment.id,
        payload={
            "customer_id": assignment.customer_id,
            "address_id": assignment.address_id,
            "assignment_id": assignment.id,
            "user_id": assignment.user_id,
            "assignment_role": assignment.assignment_role,
        },
    )
    db.delete(assignment)


def _serialize_assignment(
    assignment: CrmCustomerCommercialAssignment, user: User
) -> CustomerCommercialAssignmentRead:
    return CustomerCommercialAssignmentRead(
        id=assignment.id,
        customer_id=assignment.customer_id,
        address_id=assignment.address_id,
        user_id=assignment.user_id,
        user_display_name=user.full_name,
        user_email=user.email,
        assignment_role=assignment.assignment_role,
        notes=assignment.notes,
        is_primary=assignment.is_primary,
        is_active=assignment.is_active,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


def _require_assignment_user(db: Session, *, tenant_id: str, user_id: str) -> User:
    user = db.scalar(select(User).where(User.id == user_id, User.tenant_id == tenant_id))
    if user is None:
        raise ValueError("El usuario comercial no pertenece al tenant")
    return user


def _validate_assignment_address(
    db: Session,
    *,
    tenant_id: str,
    customer: CrmCustomer,
    address_id: str | None,
) -> None:
    if address_id is None:
        return
    address = get_address(db, tenant_id=tenant_id, address_id=address_id)
    if address is None or address.customer_id != customer.id:
        raise ValueError("La sede vinculada no pertenece al cliente")


def _clear_primary_assignments(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    address_id: str | None,
    assignment_role: str,
    exclude_assignment_id: str | None = None,
) -> None:
    assignments = list(
        db.scalars(
            select(CrmCustomerCommercialAssignment).where(
                CrmCustomerCommercialAssignment.tenant_id == tenant_id,
                CrmCustomerCommercialAssignment.customer_id == customer_id,
            )
        ).all()
    )
    for existing in assignments:
        if exclude_assignment_id is not None and existing.id == exclude_assignment_id:
            continue
        if existing.assignment_role != assignment_role:
            continue
        if existing.address_id != address_id:
            continue
        if existing.is_primary:
            existing.is_primary = False
            db.add(existing)
