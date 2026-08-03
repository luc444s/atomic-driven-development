from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.crm.backend.common import CrmActionContext, audit_crm_action, emit_crm_event
from plugins.crm.backend.models import CrmCustomer, CrmCustomerAddress, CrmCustomerContact
from plugins.crm.backend.schemas import (
    CustomerAddressCreateRequest,
    CustomerAddressUpdateRequest,
    CustomerContactCreateRequest,
    CustomerContactUpdateRequest,
)
from plugins.crm.backend.services.geography import get_geography


def list_addresses(db: Session, *, tenant_id: str, customer_id: str) -> list[CrmCustomerAddress]:
    return list(
        db.scalars(
            select(CrmCustomerAddress)
            .where(
                CrmCustomerAddress.tenant_id == tenant_id,
                CrmCustomerAddress.customer_id == customer_id,
            )
            .order_by(CrmCustomerAddress.created_at.asc())
        ).all()
    )


def list_addresses_with_gps(
    db: Session,
    *,
    tenant_id: str,
    customer_ids: list[str] | None = None,
) -> list[CrmCustomerAddress]:
    stmt = select(CrmCustomerAddress).where(
        CrmCustomerAddress.tenant_id == tenant_id,
        CrmCustomerAddress.latitude.is_not(None),
        CrmCustomerAddress.longitude.is_not(None),
        CrmCustomerAddress.is_active.is_(True),
    )
    if customer_ids:
        stmt = stmt.where(CrmCustomerAddress.customer_id.in_(customer_ids))
    return list(
        db.scalars(stmt.order_by(CrmCustomerAddress.created_at.asc())
        ).all()
    )


def get_address(db: Session, *, tenant_id: str, address_id: str) -> CrmCustomerAddress | None:
    return db.scalar(
        select(CrmCustomerAddress).where(
            CrmCustomerAddress.id == address_id,
            CrmCustomerAddress.tenant_id == tenant_id,
        )
    )


def create_address(
    db: Session,
    *,
    tenant_id: str,
    customer: CrmCustomer,
    payload: CustomerAddressCreateRequest,
    action_context: CrmActionContext,
) -> CrmCustomerAddress:
    _validate_address_payload(db, payload=payload)
    address = CrmCustomerAddress(
        tenant_id=tenant_id,
        customer_id=customer.id,
        address_type=payload.address_type,
        label=payload.label,
        geography_id=payload.geography_id,
        line1=payload.line1.strip(),
        line2=payload.line2,
        city=payload.city,
        state=payload.state,
        district=payload.district,
        postal_code=payload.postal_code,
        country_code=payload.country_code,
        latitude=payload.latitude,
        longitude=payload.longitude,
        place_id=payload.place_id,
        formatted_address=payload.formatted_address,
        street_name=payload.street_name,
        street_number=payload.street_number,
        geocode_source=payload.geocode_source,
        precision_meters=payload.precision_meters,
        gps_link=payload.gps_link,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
        contact_email=payload.contact_email,
        is_operational_site=payload.is_operational_site,
        notes=payload.notes,
        captured_by=action_context.actor_user_id,
        captured_at=None,
        ubigeo_code=payload.ubigeo_code,
    )
    db.add(address)
    db.flush()
    if payload.address_type == "FISCAL" and customer.fiscal_address_id is None:
        customer.fiscal_address_id = address.id
        db.add(customer)
        db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.address.create",
        entity_type="customer_address",
        entity_id=address.id,
        details={"customer_id": customer.id, "address_type": address.address_type},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.address_added",
        entity_type="customer_address",
        entity_id=address.id,
        payload={"customer_id": customer.id, "address_id": address.id},
    )
    return address


def update_address(
    db: Session,
    *,
    address: CrmCustomerAddress,
    payload: CustomerAddressUpdateRequest,
    action_context: CrmActionContext,
) -> CrmCustomerAddress:
    _validate_address_payload(db, payload=payload)
    for field in [
        "address_type",
        "label",
        "geography_id",
        "line1",
        "line2",
        "city",
        "state",
        "district",
        "postal_code",
        "country_code",
        "latitude",
        "longitude",
        "place_id",
        "formatted_address",
        "street_name",
        "street_number",
        "geocode_source",
        "precision_meters",
        "gps_link",
        "contact_name",
        "contact_phone",
        "contact_email",
        "is_operational_site",
        "notes",
        "ubigeo_code",
    ]:
        value = getattr(payload, field)
        if value is not None:
            setattr(address, field, value.strip() if isinstance(value, str) else value)
    if payload.is_active is not None:
        address.is_active = payload.is_active
    db.add(address)
    db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.address.update",
        entity_type="customer_address",
        entity_id=address.id,
        details={"customer_id": address.customer_id, "address_type": address.address_type},
    )
    return address


def set_fiscal_address(
    db: Session,
    *,
    customer: CrmCustomer,
    address: CrmCustomerAddress,
    action_context: CrmActionContext,
) -> CrmCustomer:
    if address.customer_id != customer.id:
        raise ValueError("La dirección no pertenece al cliente")
    if not address.is_active:
        raise ValueError("Una dirección inactiva no puede ser la dirección fiscal")
    customer.fiscal_address_id = address.id
    db.add(customer)
    db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.fiscal_address.set",
        entity_type="customer",
        entity_id=customer.id,
        details={"fiscal_address_id": address.id},
    )
    return customer


def delete_address(
    db: Session,
    *,
    customer: CrmCustomer,
    address: CrmCustomerAddress,
    action_context: CrmActionContext,
) -> None:
    if customer.fiscal_address_id == address.id:
        raise ValueError("No se puede eliminar la dirección fiscal activa")
    audit_crm_action(
        db,
        context=action_context,
        action="customer.address.delete",
        entity_type="customer_address",
        entity_id=address.id,
        details={"customer_id": customer.id},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.address_removed",
        entity_type="customer_address",
        entity_id=address.id,
        payload={"customer_id": customer.id, "address_id": address.id},
    )
    db.delete(address)


def list_contacts(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    address_id: str | None = None,
    contact_purpose: str | None = None,
    active_only: bool = True,
) -> list[CrmCustomerContact]:
    stmt = select(CrmCustomerContact).where(
        CrmCustomerContact.tenant_id == tenant_id,
        CrmCustomerContact.customer_id == customer_id,
    )
    if active_only:
        stmt = stmt.where(CrmCustomerContact.is_active.is_(True))
    if address_id is not None:
        stmt = stmt.where(CrmCustomerContact.address_id == address_id)
    if contact_purpose is not None:
        stmt = stmt.where(CrmCustomerContact.contact_purpose == contact_purpose)
    stmt = stmt.order_by(CrmCustomerContact.is_primary.desc(), CrmCustomerContact.created_at.asc())
    return list(db.scalars(stmt).all())


def create_contact(
    db: Session,
    *,
    tenant_id: str,
    customer: CrmCustomer,
    payload: CustomerContactCreateRequest,
    action_context: CrmActionContext,
) -> CrmCustomerContact:
    _validate_contact_address(
        db,
        tenant_id=tenant_id,
        customer=customer,
        address_id=payload.address_id,
    )
    if payload.is_primary:
        _clear_primary_contacts(
            db,
            tenant_id=tenant_id,
            customer_id=customer.id,
            address_id=payload.address_id,
            contact_purpose=payload.contact_purpose,
        )
    contact = CrmCustomerContact(
        tenant_id=tenant_id,
        customer_id=customer.id,
        full_name=payload.full_name,
        label=payload.label,
        role=payload.role,
        phone=payload.phone,
        email=payload.email,
        address_id=payload.address_id,
        contact_purpose=payload.contact_purpose,
        contact_type=payload.contact_type,
        notes=payload.notes,
        is_primary=payload.is_primary,
    )
    db.add(contact)
    db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.contact.create",
        entity_type="customer_contact",
        entity_id=contact.id,
        details={
            "customer_id": customer.id,
            "address_id": contact.address_id,
            "contact_purpose": contact.contact_purpose,
        },
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.contact_added",
        entity_type="customer_contact",
        entity_id=contact.id,
        payload={
            "customer_id": customer.id,
            "contact_id": contact.id,
            "address_id": contact.address_id,
            "contact_purpose": contact.contact_purpose,
        },
    )
    return contact


def update_contact(
    db: Session,
    *,
    tenant_id: str,
    customer: CrmCustomer,
    contact: CrmCustomerContact,
    payload: CustomerContactUpdateRequest,
    action_context: CrmActionContext,
) -> CrmCustomerContact:
    address_was_provided = "address_id" in payload.model_fields_set
    next_address_id = payload.address_id if address_was_provided else contact.address_id
    next_contact_purpose = (
        payload.contact_purpose if payload.contact_purpose is not None else contact.contact_purpose
    )
    next_is_primary = payload.is_primary if payload.is_primary is not None else contact.is_primary
    _validate_contact_address(
        db,
        tenant_id=tenant_id,
        customer=customer,
        address_id=next_address_id,
    )
    if next_is_primary:
        _clear_primary_contacts(
            db,
            tenant_id=tenant_id,
            customer_id=customer.id,
            address_id=next_address_id,
            contact_purpose=next_contact_purpose,
            exclude_contact_id=contact.id,
        )
    for field in [
        "full_name",
        "label",
        "role",
        "phone",
        "email",
        "address_id",
        "contact_purpose",
        "contact_type",
        "notes",
    ]:
        if field not in payload.model_fields_set:
            continue
        value = getattr(payload, field)
        setattr(contact, field, value.strip() if isinstance(value, str) else value)
    if payload.is_primary is not None:
        contact.is_primary = payload.is_primary
    if payload.is_active is not None:
        contact.is_active = payload.is_active
    db.add(contact)
    db.flush()
    audit_crm_action(
        db,
        context=action_context,
        action="customer.contact.update",
        entity_type="customer_contact",
        entity_id=contact.id,
        details={
            "customer_id": customer.id,
            "address_id": contact.address_id,
            "contact_purpose": contact.contact_purpose,
        },
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.contact_updated",
        entity_type="customer_contact",
        entity_id=contact.id,
        payload={
            "customer_id": customer.id,
            "contact_id": contact.id,
            "address_id": contact.address_id,
            "contact_purpose": contact.contact_purpose,
        },
    )
    return contact


def get_contact(db: Session, *, tenant_id: str, contact_id: str) -> CrmCustomerContact | None:
    return db.scalar(
        select(CrmCustomerContact).where(
            CrmCustomerContact.id == contact_id,
            CrmCustomerContact.tenant_id == tenant_id,
        )
    )


def delete_contact(
    db: Session,
    *,
    contact: CrmCustomerContact,
    action_context: CrmActionContext,
) -> None:
    audit_crm_action(
        db,
        context=action_context,
        action="customer.contact.delete",
        entity_type="customer_contact",
        entity_id=contact.id,
        details={
            "customer_id": contact.customer_id,
            "address_id": contact.address_id,
            "contact_purpose": contact.contact_purpose,
        },
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.contact_removed",
        entity_type="customer_contact",
        entity_id=contact.id,
        payload={
            "customer_id": contact.customer_id,
            "contact_id": contact.id,
            "address_id": contact.address_id,
            "contact_purpose": contact.contact_purpose,
        },
    )
    db.delete(contact)


def _clear_primary_contacts(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    address_id: str | None,
    contact_purpose: str,
    exclude_contact_id: str | None = None,
) -> None:
    contacts = list_contacts(
        db,
        tenant_id=tenant_id,
        customer_id=customer_id,
        active_only=False,
    )
    for existing in contacts:
        if exclude_contact_id is not None and existing.id == exclude_contact_id:
            continue
        if existing.contact_purpose != contact_purpose:
            continue
        if existing.address_id != address_id:
            continue
        if existing.is_primary:
            existing.is_primary = False
            db.add(existing)


def _validate_contact_address(
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
        raise ValueError("La dirección vinculada no pertenece al cliente")


def _validate_address_payload(
    db: Session,
    *,
    payload: CustomerAddressCreateRequest | CustomerAddressUpdateRequest,
) -> None:
    if payload.geocode_source == "GOOGLE" and not payload.place_id:
        raise ValueError("La fuente de geocodificación GOOGLE requiere place_id")
    if payload.geography_id:
        geography = get_geography(db, geography_id=payload.geography_id)
        if geography is None:
            raise ValueError("Geografía no encontrada")
        if geography.country_code != payload.country_code:
            raise ValueError("El país de la geografía no coincide con el país de la dirección")
