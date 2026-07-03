from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.crm.backend.common import build_action_context
from plugins.crm.backend.models import CrmCustomer
from plugins.crm.backend.schemas import (
    CustomerAddressCreateRequest,
    CustomerAddressRead,
    CustomerAddressUpdateRequest,
    CustomerContactCreateRequest,
    CustomerContactRead,
    CustomerCreateRequest,
    CustomerListItemRead,
    CustomerPageRead,
    CustomerRead,
    CustomerSearchItemRead,
    CustomerToggleActiveRequest,
    CustomerUpdateRequest,
    DocumentTypeRead,
    FiscalAddressSetResponse,
    GeographyRead,
    GeographySeedRequest,
    GeographySeedResponse,
    PaymentTermRead,
)
from plugins.crm.backend.services.addresses import (
    create_address,
    create_contact,
    delete_address,
    delete_contact,
    get_address,
    get_contact,
    list_addresses,
    list_contacts,
    set_fiscal_address,
    update_address,
)
from plugins.crm.backend.services.catalog import list_document_types, list_payment_terms
from plugins.crm.backend.services.customers import (
    create_customer,
    get_customer,
    list_customers,
    search_customers,
    toggle_active,
    update_customer,
)
from plugins.crm.backend.services.geography import (
    list_countries,
    list_departments,
    list_districts,
    list_provinces,
    seed_geography,
)

router = APIRouter(tags=["crm"])
DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)

REQUIRE_CUSTOMER_READ = Depends(require_permission("crm.customer.read"))
REQUIRE_CUSTOMER_CREATE = Depends(require_permission("crm.customer.create"))
REQUIRE_CUSTOMER_UPDATE = Depends(require_permission("crm.customer.update"))
REQUIRE_CATALOG_READ = Depends(require_permission("crm.catalog.read"))
REQUIRE_GEOGRAPHY_READ = Depends(require_permission("crm.geography.read"))
REQUIRE_GEOGRAPHY_MANAGE = Depends(require_permission("crm.geography.manage"))


def _bad_request(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


def _conflict(message: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)


def _not_found(entity_name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found")


def _serialize_contact(contact) -> CustomerContactRead:
    return CustomerContactRead.model_validate(contact)


def _serialize_address(address) -> CustomerAddressRead:
    return CustomerAddressRead.model_validate(address)


def _serialize_customer(customer: CrmCustomer) -> CustomerRead:
    return CustomerRead(
        id=customer.id,
        legal_name=customer.legal_name,
        commercial_name=customer.commercial_name,
        external_code=customer.external_code,
        document_type_code=customer.document_type_code,
        document_number=customer.document_number,
        country_code=customer.country_code,
        email=customer.email,
        phone=customer.phone,
        mobile=customer.mobile,
        payment_term_code=customer.payment_term_code,
        billing_type=customer.billing_type,
        is_exempt=customer.is_exempt,
        is_active=customer.is_active,
        fiscal_address_id=customer.fiscal_address_id,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        economic_activity_code=customer.economic_activity_code,
        economic_activity_description=customer.economic_activity_description,
        activity_validated=customer.activity_validated,
        activity_validation_source=customer.activity_validation_source,
        activity_validation_date=customer.activity_validation_date,
        first_name=customer.first_name,
        last_name=customer.last_name,
        birth_date=customer.birth_date,
        gender=customer.gender,
        notes=customer.notes,
        addresses=[_serialize_address(item) for item in customer.addresses],
        contacts=[_serialize_contact(item) for item in customer.contacts],
    )


@router.get(
    "/catalog/document-types",
    response_model=list[DocumentTypeRead],
    dependencies=[REQUIRE_CATALOG_READ],
)
def get_document_types(
    country_code: str | None = Query(default=None),
    db: Session = DB_SESSION,
) -> list[DocumentTypeRead]:
    return [
        DocumentTypeRead.model_validate(item)
        for item in list_document_types(db, country_code=country_code)
    ]


@router.get(
    "/catalog/payment-terms",
    response_model=list[PaymentTermRead],
    dependencies=[REQUIRE_CATALOG_READ],
)
def get_payment_terms(db: Session = DB_SESSION) -> list[PaymentTermRead]:
    return [PaymentTermRead.model_validate(item) for item in list_payment_terms(db)]


@router.get(
    "/geography/countries",
    response_model=list[GeographyRead],
    dependencies=[REQUIRE_GEOGRAPHY_READ],
)
def get_countries(db: Session = DB_SESSION) -> list[GeographyRead]:
    return [GeographyRead.model_validate(item) for item in list_countries(db)]


@router.get(
    "/geography/departments",
    response_model=list[GeographyRead],
    dependencies=[REQUIRE_GEOGRAPHY_READ],
)
def get_departments(
    country_code: str = Query(...), db: Session = DB_SESSION
) -> list[GeographyRead]:
    return [
        GeographyRead.model_validate(item)
        for item in list_departments(db, country_code=country_code)
    ]


@router.get(
    "/geography/provinces",
    response_model=list[GeographyRead],
    dependencies=[REQUIRE_GEOGRAPHY_READ],
)
def get_provinces(department_id: str = Query(...), db: Session = DB_SESSION) -> list[GeographyRead]:
    return [
        GeographyRead.model_validate(item)
        for item in list_provinces(db, department_id=department_id)
    ]


@router.get(
    "/geography/districts",
    response_model=list[GeographyRead],
    dependencies=[REQUIRE_GEOGRAPHY_READ],
)
def get_districts(province_id: str = Query(...), db: Session = DB_SESSION) -> list[GeographyRead]:
    return [
        GeographyRead.model_validate(item) for item in list_districts(db, province_id=province_id)
    ]


@router.post(
    "/geography/seed", response_model=GeographySeedResponse, dependencies=[REQUIRE_GEOGRAPHY_MANAGE]
)
def post_seed_geography(
    payload: GeographySeedRequest, db: Session = DB_SESSION
) -> GeographySeedResponse:
    inserted = seed_geography(db, country_code=payload.country_code)
    db.commit()
    return GeographySeedResponse(country_code=payload.country_code, inserted=inserted)


@router.get("/customers", response_model=CustomerPageRead, dependencies=[REQUIRE_CUSTOMER_READ])
def get_customers(
    search: str | None = Query(default=None),
    document_type_code: str | None = Query(default=None),
    country_code: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    payment_term_code: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> CustomerPageRead:
    items, total = list_customers(
        db,
        tenant_id=tenant_context.current_tenant_id,
        search=search,
        document_type_code=document_type_code,
        country_code=country_code,
        is_active=is_active,
        payment_term_code=payment_term_code,
        limit=limit,
        offset=offset,
    )
    return CustomerPageRead(
        items=[
            CustomerListItemRead(
                id=item.id,
                legal_name=item.legal_name,
                commercial_name=item.commercial_name,
                external_code=item.external_code,
                document_type_code=item.document_type_code,
                document_number=item.document_number,
                country_code=item.country_code,
                email=item.email,
                phone=item.phone,
                mobile=item.mobile,
                payment_term_code=item.payment_term_code,
                billing_type=item.billing_type,
                is_exempt=item.is_exempt,
                is_active=item.is_active,
                fiscal_address_id=item.fiscal_address_id,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/customers/search",
    response_model=list[CustomerSearchItemRead],
    dependencies=[REQUIRE_CUSTOMER_READ],
)
def get_search_customers(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[CustomerSearchItemRead]:
    return search_customers(
        db, tenant_id=tenant_context.current_tenant_id, query=query, limit=limit
    )


@router.get(
    "/customers/{customer_id}", response_model=CustomerRead, dependencies=[REQUIRE_CUSTOMER_READ]
)
def get_customer_detail(
    customer_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> CustomerRead:
    customer = get_customer(db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id)
    if customer is None:
        raise _not_found("Customer")
    return _serialize_customer(customer)


@router.post(
    "/customers",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CUSTOMER_CREATE],
)
def post_customer(
    request: Request,
    payload: CustomerCreateRequest,
    current_user: User = REQUIRE_CUSTOMER_CREATE,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> CustomerRead:
    action_context = build_action_context(request, tenant_context)
    try:
        customer = create_customer(
            db,
            tenant_id=tenant_context.current_tenant_id,
            actor_user_id=current_user.id,
            payload=payload,
            action_context=action_context,
        )
        db.commit()
        db.refresh(customer)
        customer = get_customer(
            db, tenant_id=tenant_context.current_tenant_id, customer_id=customer.id
        )
        assert customer is not None
        return _serialize_customer(customer)
    except ValueError as exc:
        db.rollback()
        message = str(exc)
        if "already exists" in message or "ya existe" in message:
            raise _conflict(message) from exc
        raise _bad_request(message) from exc


@router.put(
    "/customers/{customer_id}", response_model=CustomerRead, dependencies=[REQUIRE_CUSTOMER_UPDATE]
)
def put_customer(
    request: Request,
    customer_id: str,
    payload: CustomerUpdateRequest,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> CustomerRead:
    customer = get_customer(db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id)
    if customer is None:
        raise _not_found("Customer")
    action_context = build_action_context(request, tenant_context)
    try:
        update_customer(db, customer=customer, payload=payload, action_context=action_context)
        db.commit()
        refreshed = get_customer(
            db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id
        )
        assert refreshed is not None
        return _serialize_customer(refreshed)
    except ValueError as exc:
        db.rollback()
        message = str(exc)
        if "already exists" in message or "ya existe" in message:
            raise _conflict(message) from exc
        raise _bad_request(message) from exc


@router.patch(
    "/customers/{customer_id}/toggle-active",
    response_model=CustomerRead,
    dependencies=[REQUIRE_CUSTOMER_UPDATE],
)
def patch_toggle_customer(
    request: Request,
    customer_id: str,
    payload: CustomerToggleActiveRequest,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> CustomerRead:
    customer = get_customer(db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id)
    if customer is None:
        raise _not_found("Customer")
    action_context = build_action_context(request, tenant_context)
    try:
        toggle_active(
            db,
            customer=customer,
            is_active=payload.is_active,
            reason=payload.reason,
            action_context=action_context,
        )
        db.commit()
        refreshed = get_customer(
            db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id
        )
        assert refreshed is not None
        return _serialize_customer(refreshed)
    except ValueError as exc:
        db.rollback()
        message = str(exc)
        if "cannot be disabled" in message:
            raise _conflict(message) from exc
        raise _bad_request(message) from exc


@router.get(
    "/customers/{customer_id}/addresses",
    response_model=list[CustomerAddressRead],
    dependencies=[REQUIRE_CUSTOMER_READ],
)
def get_customer_addresses(
    customer_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[CustomerAddressRead]:
    customer = get_customer(db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id)
    if customer is None:
        raise _not_found("Customer")
    return [
        _serialize_address(item)
        for item in list_addresses(
            db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id
        )
    ]


@router.post(
    "/customers/{customer_id}/addresses",
    response_model=CustomerAddressRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CUSTOMER_UPDATE],
)
def post_customer_address(
    request: Request,
    customer_id: str,
    payload: CustomerAddressCreateRequest,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> CustomerAddressRead:
    customer = get_customer(db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id)
    if customer is None:
        raise _not_found("Customer")
    action_context = build_action_context(request, tenant_context)
    try:
        address = create_address(
            db,
            tenant_id=tenant_context.current_tenant_id,
            customer=customer,
            payload=payload,
            action_context=action_context,
        )
        db.commit()
        return _serialize_address(address)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.put(
    "/addresses/{address_id}",
    response_model=CustomerAddressRead,
    dependencies=[REQUIRE_CUSTOMER_UPDATE],
)
def put_address(
    request: Request,
    address_id: str,
    payload: CustomerAddressUpdateRequest,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> CustomerAddressRead:
    address = get_address(db, tenant_id=tenant_context.current_tenant_id, address_id=address_id)
    if address is None:
        raise _not_found("Address")
    action_context = build_action_context(request, tenant_context)
    try:
        update_address(db, address=address, payload=payload, action_context=action_context)
        db.commit()
        return _serialize_address(address)
    except ValueError as exc:
        db.rollback()
        raise _bad_request(str(exc)) from exc


@router.put(
    "/customers/{customer_id}/fiscal-address/{address_id}",
    response_model=FiscalAddressSetResponse,
    dependencies=[REQUIRE_CUSTOMER_UPDATE],
)
def put_fiscal_address(
    request: Request,
    customer_id: str,
    address_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> FiscalAddressSetResponse:
    customer = get_customer(db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id)
    if customer is None:
        raise _not_found("Customer")
    address = get_address(db, tenant_id=tenant_context.current_tenant_id, address_id=address_id)
    if address is None:
        raise _not_found("Address")
    action_context = build_action_context(request, tenant_context)
    try:
        set_fiscal_address(db, customer=customer, address=address, action_context=action_context)
        db.commit()
        return FiscalAddressSetResponse(customer_id=customer.id, fiscal_address_id=address.id)
    except ValueError as exc:
        db.rollback()
        message = str(exc)
        if "Inactive address" in message:
            raise _conflict(message) from exc
        raise _bad_request(message) from exc


@router.delete(
    "/addresses/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[REQUIRE_CUSTOMER_UPDATE],
)
def delete_customer_address(
    request: Request,
    address_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> None:
    address = get_address(db, tenant_id=tenant_context.current_tenant_id, address_id=address_id)
    if address is None:
        raise _not_found("Address")
    customer = get_customer(
        db, tenant_id=tenant_context.current_tenant_id, customer_id=address.customer_id
    )
    if customer is None:
        raise _not_found("Customer")
    action_context = build_action_context(request, tenant_context)
    try:
        delete_address(db, customer=customer, address=address, action_context=action_context)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise _conflict(str(exc)) from exc


@router.get(
    "/customers/{customer_id}/contacts",
    response_model=list[CustomerContactRead],
    dependencies=[REQUIRE_CUSTOMER_READ],
)
def get_customer_contacts(
    customer_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[CustomerContactRead]:
    customer = get_customer(db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id)
    if customer is None:
        raise _not_found("Customer")
    return [
        _serialize_contact(item)
        for item in list_contacts(
            db, tenant_id=tenant_context.current_tenant_id, customer_id=customer.id
        )
    ]


@router.post(
    "/customers/{customer_id}/contacts",
    response_model=CustomerContactRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_CUSTOMER_UPDATE],
)
def post_customer_contact(
    customer_id: str,
    payload: CustomerContactCreateRequest,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> CustomerContactRead:
    customer = get_customer(db, tenant_id=tenant_context.current_tenant_id, customer_id=customer_id)
    if customer is None:
        raise _not_found("Customer")
    contact = create_contact(
        db,
        tenant_id=tenant_context.current_tenant_id,
        customer=customer,
        payload=payload,
    )
    db.commit()
    return _serialize_contact(contact)


@router.delete(
    "/contacts/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[REQUIRE_CUSTOMER_UPDATE],
)
def delete_customer_contact(
    contact_id: str,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> None:
    contact = get_contact(db, tenant_id=tenant_context.current_tenant_id, contact_id=contact_id)
    if contact is None:
        raise _not_found("Contact")
    delete_contact(db, contact=contact)
    db.commit()
