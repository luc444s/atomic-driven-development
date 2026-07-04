from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.crm.backend.common import CrmActionContext, audit_crm_action, emit_crm_event
from plugins.crm.backend.models import CrmCustomer, CrmCustomerBankAccount
from plugins.crm.backend.schemas import (
    CustomerBankAccountCreateRequest,
    CustomerBankAccountUpdateRequest,
)


def get_bank_account(
    db: Session, *, tenant_id: str, bank_account_id: str
) -> CrmCustomerBankAccount | None:
    return db.scalar(
        select(CrmCustomerBankAccount).where(
            CrmCustomerBankAccount.id == bank_account_id,
            CrmCustomerBankAccount.tenant_id == tenant_id,
        )
    )


def list_bank_accounts(
    db: Session, *, tenant_id: str, customer_id: str
) -> list[CrmCustomerBankAccount]:
    return list(
        db.scalars(
            select(CrmCustomerBankAccount)
            .where(
                CrmCustomerBankAccount.tenant_id == tenant_id,
                CrmCustomerBankAccount.customer_id == customer_id,
            )
            .order_by(CrmCustomerBankAccount.created_at.desc())
        ).all()
    )


def create_bank_account(
    db: Session,
    *,
    tenant_id: str,
    customer: CrmCustomer,
    payload: CustomerBankAccountCreateRequest,
    action_context: CrmActionContext,
) -> CrmCustomerBankAccount:
    _enforce_single_primary_for_new(db, tenant_id, customer.id, payload.is_primary)

    account = CrmCustomerBankAccount(
        tenant_id=tenant_id,
        customer_id=customer.id,
        bank_name=payload.bank_name.strip(),
        account_holder=payload.account_holder.strip(),
        iban=payload.iban,
        bic_swift=payload.bic_swift,
        is_primary=payload.is_primary,
        notes=payload.notes,
    )
    db.add(account)
    db.flush()

    audit_crm_action(
        db,
        context=action_context,
        action="customer.bank_account.add",
        entity_type="bank_account",
        entity_id=account.id,
        details={"customer_id": customer.id, "bank_name": account.bank_name},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.bank_account_added",
        entity_type="bank_account",
        entity_id=account.id,
        payload={
            "customer_id": customer.id,
            "bank_account_id": account.id,
            "bank_name": account.bank_name,
        },
    )
    return account


def update_bank_account(
    db: Session,
    *,
    tenant_id: str,
    account: CrmCustomerBankAccount,
    payload: CustomerBankAccountUpdateRequest,
    action_context: CrmActionContext,
) -> CrmCustomerBankAccount:
    changed: list[str] = []

    if payload.bank_name is not None and account.bank_name != payload.bank_name.strip():
        account.bank_name = payload.bank_name.strip()
        changed.append("bank_name")

    if (
        payload.account_holder is not None
        and account.account_holder != payload.account_holder.strip()
    ):
        account.account_holder = payload.account_holder.strip()
        changed.append("account_holder")

    if payload.iban is not None and account.iban != payload.iban:
        account.iban = payload.iban
        changed.append("iban")

    if payload.bic_swift is not None and account.bic_swift != payload.bic_swift:
        account.bic_swift = payload.bic_swift
        changed.append("bic_swift")

    if payload.is_primary is not None and account.is_primary != payload.is_primary:
        if payload.is_primary:
            _enforce_single_primary(db, tenant_id, account.customer_id, account.id)
        account.is_primary = payload.is_primary
        changed.append("is_primary")

    if payload.is_active is not None and account.is_active != payload.is_active:
        account.is_active = payload.is_active
        changed.append("is_active")

    if payload.notes is not None and account.notes != payload.notes:
        account.notes = payload.notes
        changed.append("notes")

    db.add(account)
    db.flush()

    audit_crm_action(
        db,
        context=action_context,
        action="customer.bank_account.update",
        entity_type="bank_account",
        entity_id=account.id,
        details={"changed_fields": changed},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.bank_account_updated",
        entity_type="bank_account",
        entity_id=account.id,
        payload={
            "customer_id": account.customer_id,
            "bank_account_id": account.id,
            "changed_fields": changed,
        },
    )
    return account


def delete_bank_account(
    db: Session,
    *,
    account: CrmCustomerBankAccount,
    action_context: CrmActionContext,
) -> None:
    customer_id = account.customer_id
    bank_account_id = account.id
    bank_name = account.bank_name

    db.delete(account)
    db.flush()

    audit_crm_action(
        db,
        context=action_context,
        action="customer.bank_account.remove",
        entity_type="bank_account",
        entity_id=bank_account_id,
        details={"customer_id": customer_id, "bank_name": bank_name},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.bank_account_removed",
        entity_type="bank_account",
        entity_id=bank_account_id,
        payload={
            "customer_id": customer_id,
            "bank_account_id": bank_account_id,
        },
    )


def _enforce_single_primary_for_new(
    db: Session, tenant_id: str, customer_id: str, is_primary: bool
) -> None:
    if not is_primary:
        return
    db.execute(
        select(CrmCustomerBankAccount).where(
            CrmCustomerBankAccount.tenant_id == tenant_id,
            CrmCustomerBankAccount.customer_id == customer_id,
            CrmCustomerBankAccount.is_primary.is_(True),
        )
    ).first()
    existing = db.scalar(
        select(CrmCustomerBankAccount).where(
            CrmCustomerBankAccount.tenant_id == tenant_id,
            CrmCustomerBankAccount.customer_id == customer_id,
            CrmCustomerBankAccount.is_primary.is_(True),
        )
    )
    if existing is not None:
        existing.is_primary = False
        db.add(existing)


def _enforce_single_primary(
    db: Session, tenant_id: str, customer_id: str, exclude_id: str
) -> None:
    existing = db.scalar(
        select(CrmCustomerBankAccount).where(
            CrmCustomerBankAccount.tenant_id == tenant_id,
            CrmCustomerBankAccount.customer_id == customer_id,
            CrmCustomerBankAccount.is_primary.is_(True),
            CrmCustomerBankAccount.id != exclude_id,
        )
    )
    if existing is not None:
        existing.is_primary = False
        db.add(existing)
