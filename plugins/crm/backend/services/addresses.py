from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.crm.backend.common import CrmActionContext, audit_crm_action, emit_crm_event
from plugins.crm.backend.models import CrmCustomer, CrmCustomerAddress, CrmCustomerContact
from plugins.crm.backend.schemas import (
    CustomerAddressCreateRequest,
    CustomerAddressUpdateRequest,
    CustomerContactCreateRequest,
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
        raise ValueError("Address does not belong to customer")
    if not address.is_active:
        raise ValueError("Inactive address cannot be the fiscal address")
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
        raise ValueError("Cannot delete the active fiscal address")
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


def list_contacts(db: Session, *, tenant_id: str, customer_id: str) -> list[CrmCustomerContact]:
    return list(
        db.scalars(
            select(CrmCustomerContact)
            .where(
                CrmCustomerContact.tenant_id == tenant_id,
                CrmCustomerContact.customer_id == customer_id,
                CrmCustomerContact.is_active.is_(True),
            )
            .order_by(CrmCustomerContact.is_primary.desc(), CrmCustomerContact.created_at.asc())
        ).all()
    )


def create_contact(
    db: Session,
    *,
    tenant_id: str,
    customer: CrmCustomer,
    payload: CustomerContactCreateRequest,
) -> CrmCustomerContact:
    if payload.is_primary:
        for contact in list_contacts(db, tenant_id=tenant_id, customer_id=customer.id):
            if contact.contact_type == payload.contact_type:
                contact.is_primary = False
                db.add(contact)
    contact = CrmCustomerContact(
        tenant_id=tenant_id,
        customer_id=customer.id,
        contact_type=payload.contact_type,
        value=payload.value.strip(),
        label=payload.label,
        is_primary=payload.is_primary,
    )
    db.add(contact)
    db.flush()
    return contact


def get_contact(db: Session, *, tenant_id: str, contact_id: str) -> CrmCustomerContact | None:
    return db.scalar(
        select(CrmCustomerContact).where(
            CrmCustomerContact.id == contact_id,
            CrmCustomerContact.tenant_id == tenant_id,
        )
    )


def delete_contact(db: Session, *, contact: CrmCustomerContact) -> None:
    db.delete(contact)


def _validate_address_payload(
    db: Session,
    *,
    payload: CustomerAddressCreateRequest | CustomerAddressUpdateRequest,
) -> None:
    if payload.geocode_source == "GOOGLE" and not payload.place_id:
        raise ValueError("GOOGLE geocode source requires place_id")
    if payload.geography_id:
        geography = get_geography(db, geography_id=payload.geography_id)
        if geography is None:
            raise ValueError("Geography not found")
        if geography.country_code != payload.country_code:
            raise ValueError("Geography country does not match address country")
