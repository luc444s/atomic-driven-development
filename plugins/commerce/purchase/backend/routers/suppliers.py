from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from systutor.kernel.auth.models import User  # noqa: F401 - mantiene parity con router previo
from systutor.kernel.tenants.context import TenantContext

from plugins.commerce.purchase.backend.models import (
    ComSupplierBankAccount,
    ComSupplierContact,
)
from plugins.commerce.purchase.backend.schemas import (
    SupplierAddressCreateRequest,
    SupplierBankAccountCreateRequest,
    SupplierContactCreateRequest,
    SupplierCreateRequest,
    SupplierRead,
    SupplierUpdateRequest,
)
from plugins.commerce.purchase.backend.routers.common import (
    DB_SESSION,
    REQUIRE_SUPPLIER_MANAGE,
    REQUIRE_SUPPLIER_READ,
    TENANT_CONTEXT,
)
from plugins.commerce.purchase.backend.services import addresses, suppliers

router = APIRouter()


@router.get("", response_model=list[SupplierRead], dependencies=[REQUIRE_SUPPLIER_READ])
def list_suppliers_endpoint(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    search: str | None = None,
) -> list[SupplierRead]:
    return [
        SupplierRead.model_validate(item)
        for item in suppliers.list_suppliers(
            db, tenant_id=tenant_context.current_tenant_id, search=search
        )
    ]


@router.post(
    "",
    response_model=SupplierRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def create_supplier(
    payload: SupplierCreateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.create_supplier(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    return SupplierRead.model_validate(item)


@router.patch(
    "/{supplier_id}",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def update_supplier(
    supplier_id: str,
    payload: SupplierUpdateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(
        db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    item = suppliers.update_supplier(
        db, supplier=item, payload=payload.model_dump(exclude_unset=True)
    )
    db.commit()
    return SupplierRead.model_validate(item)


@router.post(
    "/{supplier_id}/disable",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def disable_supplier(
    supplier_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(
        db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    item = suppliers.disable_supplier(db, supplier=item)
    db.commit()
    return SupplierRead.model_validate(item)


@router.post(
    "/{supplier_id}/addresses",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def add_supplier_address(
    supplier_id: str,
    payload: SupplierAddressCreateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(
        db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    addresses.add_supplier_address(
        db,
        supplier=item,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    return SupplierRead.model_validate(item)


@router.delete(
    "/{supplier_id}/addresses/{address_id}",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def remove_supplier_address(
    supplier_id: str,
    address_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(
        db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    try:
        addresses.delete_supplier_address(db, supplier=item, address_id=address_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return SupplierRead.model_validate(item)


@router.post(
    "/{supplier_id}/contacts",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def add_supplier_contact(
    supplier_id: str,
    payload: SupplierContactCreateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    contact = ComSupplierContact(
        tenant_id=tenant_context.current_tenant_id,
        supplier_id=supplier_id,
        **payload.model_dump(exclude_unset=True),
    )
    db.add(contact)
    db.commit()
    return SupplierRead.model_validate(item)


@router.delete(
    "/{supplier_id}/contacts/{contact_id}",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def remove_supplier_contact(
    supplier_id: str,
    contact_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    contact = db.scalar(select(ComSupplierContact).where(
        ComSupplierContact.id == contact_id, ComSupplierContact.supplier_id == supplier_id
    ))
    if contact is None:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    db.delete(contact)
    db.commit()
    item = suppliers.get_supplier(db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id)
    return SupplierRead.model_validate(item) if item else SupplierRead.model_validate({})


@router.post(
    "/{supplier_id}/bank-accounts",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def add_supplier_bank_account(
    supplier_id: str,
    payload: SupplierBankAccountCreateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    account = ComSupplierBankAccount(
        tenant_id=tenant_context.current_tenant_id,
        supplier_id=supplier_id,
        **payload.model_dump(exclude_unset=True),
    )
    db.add(account)
    db.commit()
    return SupplierRead.model_validate(item)


@router.delete(
    "/{supplier_id}/bank-accounts/{account_id}",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def remove_supplier_bank_account(
    supplier_id: str,
    account_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    account = db.scalar(select(ComSupplierBankAccount).where(
        ComSupplierBankAccount.id == account_id, ComSupplierBankAccount.supplier_id == supplier_id
    ))
    if account is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    db.delete(account)
    db.commit()
    item = suppliers.get_supplier(db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id)
    return SupplierRead.model_validate(item) if item else SupplierRead.model_validate({})
