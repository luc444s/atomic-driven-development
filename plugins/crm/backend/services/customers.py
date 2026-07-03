from __future__ import annotations

from sqlalchemy import inspect, or_, select, text
from sqlalchemy.orm import Session, selectinload

from plugins.crm.backend.common import CrmActionContext, audit_crm_action, emit_crm_event
from plugins.crm.backend.models import CrmCustomer, CrmCustomerAddress
from plugins.crm.backend.schemas import (
    CustomerCreateRequest,
    CustomerSearchItemRead,
    CustomerUpdateRequest,
)
from plugins.crm.backend.services.fiscal_validator import validate
from plugins.crm.backend.services.search import build_customer_filters, count_customers


def get_customer(db: Session, *, tenant_id: str, customer_id: str) -> CrmCustomer | None:
    return db.scalar(
        select(CrmCustomer)
        .options(selectinload(CrmCustomer.addresses), selectinload(CrmCustomer.contacts))
        .where(CrmCustomer.id == customer_id, CrmCustomer.tenant_id == tenant_id)
    )


def require_customer(db: Session, *, tenant_id: str, customer_id: str) -> CrmCustomer:
    customer = get_customer(db, tenant_id=tenant_id, customer_id=customer_id)
    if customer is None:
        raise ValueError("Cliente no encontrado")
    return customer


def create_customer(
    db: Session,
    *,
    tenant_id: str,
    actor_user_id: str,
    payload: CustomerCreateRequest,
    action_context: CrmActionContext,
) -> CrmCustomer:
    _validate_customer_payload(db, tenant_id=tenant_id, payload=payload)
    customer = CrmCustomer(
        tenant_id=tenant_id,
        external_code=payload.external_code,
        legal_name=payload.legal_name.strip(),
        commercial_name=payload.commercial_name,
        document_type_code=payload.document_type_code,
        document_number=payload.document_number,
        country_code=payload.country_code,
        email=payload.email,
        phone=payload.phone,
        mobile=payload.mobile,
        economic_activity_code=payload.economic_activity_code,
        economic_activity_description=payload.economic_activity_description,
        payment_term_code=payload.payment_term_code,
        billing_type=payload.billing_type,
        is_exempt=payload.is_exempt,
        first_name=payload.first_name,
        last_name=payload.last_name,
        birth_date=payload.birth_date,
        gender=payload.gender,
        notes=payload.notes,
        created_by=actor_user_id,
    )
    db.add(customer)
    db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.create",
        entity_type="customer",
        entity_id=customer.id,
        details={"legal_name": customer.legal_name, "document_number": customer.document_number},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.created",
        entity_type="customer",
        entity_id=customer.id,
        payload={
            "customer_id": customer.id,
            "legal_name": customer.legal_name,
            "document_number": customer.document_number,
            "country_code": customer.country_code,
        },
    )
    return customer


def update_customer(
    db: Session,
    *,
    customer: CrmCustomer,
    payload: CustomerUpdateRequest,
    action_context: CrmActionContext,
) -> CrmCustomer:
    effective = CustomerCreateRequest(
        external_code=payload.external_code
        if payload.external_code is not None
        else customer.external_code,
        legal_name=payload.legal_name if payload.legal_name is not None else customer.legal_name,
        commercial_name=(
            payload.commercial_name
            if payload.commercial_name is not None
            else customer.commercial_name
        ),
        document_type_code=(
            payload.document_type_code
            if payload.document_type_code is not None
            else customer.document_type_code
        ),
        document_number=(
            payload.document_number
            if payload.document_number is not None
            else customer.document_number
        ),
        country_code=payload.country_code
        if payload.country_code is not None
        else customer.country_code,
        email=payload.email if payload.email is not None else customer.email,
        phone=payload.phone if payload.phone is not None else customer.phone,
        mobile=payload.mobile if payload.mobile is not None else customer.mobile,
        economic_activity_code=(
            payload.economic_activity_code
            if payload.economic_activity_code is not None
            else customer.economic_activity_code
        ),
        economic_activity_description=(
            payload.economic_activity_description
            if payload.economic_activity_description is not None
            else customer.economic_activity_description
        ),
        payment_term_code=(
            payload.payment_term_code
            if payload.payment_term_code is not None
            else customer.payment_term_code
        ),
        billing_type=payload.billing_type
        if payload.billing_type is not None
        else customer.billing_type,
        is_exempt=payload.is_exempt if payload.is_exempt is not None else customer.is_exempt,
        first_name=payload.first_name if payload.first_name is not None else customer.first_name,
        last_name=payload.last_name if payload.last_name is not None else customer.last_name,
        birth_date=payload.birth_date if payload.birth_date is not None else customer.birth_date,
        gender=payload.gender if payload.gender is not None else customer.gender,
        notes=payload.notes if payload.notes is not None else customer.notes,
    )
    _validate_customer_payload(
        db, tenant_id=customer.tenant_id, payload=effective, exclude_customer_id=customer.id
    )
    changed_fields: list[str] = []
    for field in [
        "external_code",
        "legal_name",
        "commercial_name",
        "document_type_code",
        "document_number",
        "country_code",
        "email",
        "phone",
        "mobile",
        "economic_activity_code",
        "economic_activity_description",
        "payment_term_code",
        "billing_type",
        "first_name",
        "last_name",
        "birth_date",
        "gender",
        "notes",
    ]:
        value = getattr(payload, field)
        if value is not None and getattr(customer, field) != value:
            setattr(customer, field, value)
            changed_fields.append(field)
    if payload.is_exempt is not None and customer.is_exempt != payload.is_exempt:
        customer.is_exempt = payload.is_exempt
        changed_fields.append("is_exempt")
    db.add(customer)
    db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.update",
        entity_type="customer",
        entity_id=customer.id,
        details={"changed_fields": changed_fields},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.updated",
        entity_type="customer",
        entity_id=customer.id,
        payload={"customer_id": customer.id, "changed_fields": changed_fields},
    )
    return customer


def list_customers(
    db: Session,
    *,
    tenant_id: str,
    search: str | None = None,
    document_type_code: str | None = None,
    country_code: str | None = None,
    is_active: bool | None = None,
    payment_term_code: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[CrmCustomer], int]:
    filters = build_customer_filters(
        search=search,
        document_type_code=document_type_code,
        country_code=country_code,
        is_active=is_active,
        payment_term_code=payment_term_code,
    )
    stmt = (
        select(CrmCustomer)
        .options(selectinload(CrmCustomer.addresses), selectinload(CrmCustomer.contacts))
        .where(CrmCustomer.tenant_id == tenant_id, *filters)
        .order_by(CrmCustomer.legal_name.asc())
        .limit(limit)
        .offset(offset)
    )
    items = list(db.scalars(stmt).all())
    total = count_customers(db, tenant_id=tenant_id, filters=filters)
    return items, total


def search_customers(
    db: Session, *, tenant_id: str, query: str, limit: int = 20
) -> list[CustomerSearchItemRead]:
    term = f"%{query.strip()}%"
    stmt = (
        select(CrmCustomer)
        .options(selectinload(CrmCustomer.addresses))
        .where(
            CrmCustomer.tenant_id == tenant_id,
            CrmCustomer.is_active.is_(True),
            or_(
                CrmCustomer.legal_name.ilike(term),
                CrmCustomer.commercial_name.ilike(term),
                CrmCustomer.document_number.ilike(term),
                CrmCustomer.email.ilike(term),
                CrmCustomer.phone.ilike(term),
                CrmCustomer.external_code.ilike(term),
                CrmCustomer.addresses.any(
                    or_(
                        CrmCustomerAddress.city.ilike(term),
                        CrmCustomerAddress.district.ilike(term),
                        CrmCustomerAddress.state.ilike(term),
                        CrmCustomerAddress.line1.ilike(term),
                        CrmCustomerAddress.contact_phone.ilike(term),
                        CrmCustomerAddress.contact_email.ilike(term),
                    )
                ),
            ),
        )
        .order_by(CrmCustomer.legal_name.asc())
        .limit(limit)
    )
    customers = list(db.scalars(stmt).all())
    return [
        CustomerSearchItemRead(
            id=item.id,
            legal_name=item.legal_name,
            commercial_name=item.commercial_name,
            display_name=item.commercial_name or item.legal_name,
            document_type_code=item.document_type_code,
            document_number=item.document_number,
            external_code=item.external_code,
            email=item.email,
            phone=item.phone,
            country_code=item.country_code,
            fiscal_address_summary=_build_fiscal_address_summary(item),
            locality_summary=_build_locality_summary(item),
        )
        for item in customers
    ]


def toggle_active(
    db: Session,
    *,
    customer: CrmCustomer,
    is_active: bool,
    reason: str | None,
    action_context: CrmActionContext,
) -> CrmCustomer:
    if customer.is_active == is_active:
        return customer
    if not is_active:
        _ensure_customer_can_be_disabled(db, customer_id=customer.id)
    previous = customer.is_active
    customer.is_active = is_active
    db.add(customer)
    db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.status_change",
        entity_type="customer",
        entity_id=customer.id,
        details={"previous_status": previous, "is_active": is_active, "reason": reason},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.status_changed",
        entity_type="customer",
        entity_id=customer.id,
        payload={"customer_id": customer.id, "previous_status": previous, "is_active": is_active},
    )
    return customer


def _validate_customer_payload(
    db: Session,
    *,
    tenant_id: str,
    payload: CustomerCreateRequest,
    exclude_customer_id: str | None = None,
) -> None:
    validation = validate(payload.document_type_code, payload.document_number, payload.country_code)
    if not validation.is_valid:
        raise ValueError(validation.error_message or "Invalid document")
    stmt = select(CrmCustomer).where(
        CrmCustomer.tenant_id == tenant_id,
        CrmCustomer.document_type_code == payload.document_type_code,
        CrmCustomer.document_number == (validation.formatted or payload.document_number),
    )
    existing = db.scalar(stmt)
    if existing is not None and existing.id != exclude_customer_id:
        raise ValueError("El documento del cliente ya existe")
    if payload.external_code:
        existing_external = db.scalar(
            select(CrmCustomer).where(
                CrmCustomer.tenant_id == tenant_id,
                CrmCustomer.external_code == payload.external_code,
            )
        )
        if existing_external is not None and existing_external.id != exclude_customer_id:
            raise ValueError("El código externo del cliente ya existe")
    payload.document_number = validation.formatted or payload.document_number


def _build_fiscal_address_summary(customer: CrmCustomer) -> str | None:
    if customer.fiscal_address_id is None:
        return None
    for address in customer.addresses:
        if address.id == customer.fiscal_address_id:
            parts = [address.line1]
            if address.district:
                parts.append(address.district)
            elif address.city:
                parts.append(address.city)
            return ", ".join(parts)
    return None


def _build_locality_summary(customer: CrmCustomer) -> str | None:
    preferred = None
    if customer.fiscal_address_id is not None:
        preferred = next(
            (address for address in customer.addresses if address.id == customer.fiscal_address_id),
            None,
        )
    address = preferred or next(iter(customer.addresses), None)
    if address is None:
        return None
    for value in (address.district, address.city, address.state):
        if value:
            return value
    return None


def _ensure_customer_can_be_disabled(db: Session, *, customer_id: str) -> None:
    bind = db.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "lg_orders" in tables:
        pending_order = db.execute(
            text(
                "SELECT 1 FROM lg_orders "
                "WHERE customer_id = :customer_id AND status NOT IN ('COMPLETADO', 'CANCELADO') "
                "LIMIT 1"
            ),
            {"customer_id": customer_id},
        ).first()
        if pending_order is not None:
            raise ValueError("El cliente tiene pedidos abiertos y no puede desactivarse")

    if "lg_movements" in tables:
        pending_movement = db.execute(
            text(
                "SELECT 1 FROM lg_movements "
                "WHERE customer_id = :customer_id AND status NOT IN ('COMPLETADO', 'CANCELADO') "
                "LIMIT 1"
            ),
            {"customer_id": customer_id},
        ).first()
        if pending_movement is not None:
            raise ValueError("El cliente tiene movimientos abiertos y no puede desactivarse")
