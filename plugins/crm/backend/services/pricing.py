from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.crm.backend.common import CrmActionContext, audit_crm_action, emit_crm_event
from plugins.crm.backend.models import CrmCustomer, CrmCustomerPricingTerm
from plugins.crm.backend.schemas import (
    CustomerPricingTermCreateRequest,
    CustomerPricingTermUpdateRequest,
)


def get_pricing_term(
    db: Session, *, tenant_id: str, pricing_term_id: str
) -> CrmCustomerPricingTerm | None:
    return db.scalar(
        select(CrmCustomerPricingTerm).where(
            CrmCustomerPricingTerm.id == pricing_term_id,
            CrmCustomerPricingTerm.tenant_id == tenant_id,
        )
    )


def list_pricing_terms(
    db: Session, *, tenant_id: str, customer_id: str
) -> list[CrmCustomerPricingTerm]:
    return list(
        db.scalars(
            select(CrmCustomerPricingTerm)
            .where(
                CrmCustomerPricingTerm.tenant_id == tenant_id,
                CrmCustomerPricingTerm.customer_id == customer_id,
            )
            .order_by(CrmCustomerPricingTerm.created_at.desc())
        ).all()
    )


def _validate_pricing_term_payload(payload: CustomerPricingTermCreateRequest) -> None:
    if payload.scope_type == "PRODUCT" and payload.product_id is None:
        raise ValueError("product_id es obligatorio cuando scope_type es PRODUCT")

    if payload.scope_type == "GLOBAL" and payload.product_id is not None:
        raise ValueError("product_id no debe enviarse cuando scope_type es GLOBAL")

    if payload.pricing_mode == "FIXED_PRICE" and payload.fixed_amount is None:
        raise ValueError("fixed_amount es obligatorio cuando pricing_mode es FIXED_PRICE")

    if payload.pricing_mode == "PERCENT_DISCOUNT" and payload.discount_percent is None:
        raise ValueError(
            "discount_percent es obligatorio cuando pricing_mode es PERCENT_DISCOUNT"
        )


def create_pricing_term(
    db: Session,
    *,
    tenant_id: str,
    customer: CrmCustomer,
    payload: CustomerPricingTermCreateRequest,
    action_context: CrmActionContext,
) -> CrmCustomerPricingTerm:
    _validate_pricing_term_payload(payload)

    term = CrmCustomerPricingTerm(
        tenant_id=tenant_id,
        customer_id=customer.id,
        product_id=payload.product_id if payload.scope_type == "PRODUCT" else None,
        scope_type=payload.scope_type,
        pricing_mode=payload.pricing_mode,
        fixed_amount=payload.fixed_amount,
        discount_percent=payload.discount_percent,
        currency=payload.currency,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        source_quote_ref=payload.source_quote_ref,
        approved_by=action_context.actor_user_id,
        notes=payload.notes,
    )
    db.add(term)
    db.flush()

    audit_crm_action(
        db,
        context=action_context,
        action="customer.pricing_term.add",
        entity_type="pricing_term",
        entity_id=term.id,
        details={
            "customer_id": customer.id,
            "scope_type": term.scope_type,
            "pricing_mode": term.pricing_mode,
        },
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.pricing_term_added",
        entity_type="pricing_term",
        entity_id=term.id,
        payload={
            "customer_id": customer.id,
            "pricing_term_id": term.id,
            "scope_type": term.scope_type,
        },
    )
    return term


def update_pricing_term(
    db: Session,
    *,
    tenant_id: str,
    term: CrmCustomerPricingTerm,
    payload: CustomerPricingTermUpdateRequest,
    action_context: CrmActionContext,
) -> CrmCustomerPricingTerm:
    changed: list[str] = []

    if payload.product_id is not None and term.product_id != payload.product_id:
        term.product_id = payload.product_id
        changed.append("product_id")

    if payload.scope_type is not None and term.scope_type != payload.scope_type:
        term.scope_type = payload.scope_type
        changed.append("scope_type")

    if payload.pricing_mode is not None and term.pricing_mode != payload.pricing_mode:
        term.pricing_mode = payload.pricing_mode
        changed.append("pricing_mode")

    if payload.fixed_amount is not None and term.fixed_amount != payload.fixed_amount:
        term.fixed_amount = payload.fixed_amount
        changed.append("fixed_amount")

    if (
        payload.discount_percent is not None
        and term.discount_percent != payload.discount_percent
    ):
        term.discount_percent = payload.discount_percent
        changed.append("discount_percent")

    if payload.currency is not None and term.currency != payload.currency:
        term.currency = payload.currency
        changed.append("currency")

    if payload.valid_from is not None and term.valid_from != payload.valid_from:
        term.valid_from = payload.valid_from
        changed.append("valid_from")

    if payload.valid_to is not None and term.valid_to != payload.valid_to:
        term.valid_to = payload.valid_to
        changed.append("valid_to")

    if (
        payload.source_quote_ref is not None
        and term.source_quote_ref != payload.source_quote_ref
    ):
        term.source_quote_ref = payload.source_quote_ref
        changed.append("source_quote_ref")

    if payload.is_active is not None and term.is_active != payload.is_active:
        term.is_active = payload.is_active
        changed.append("is_active")

    if payload.notes is not None and term.notes != payload.notes:
        term.notes = payload.notes
        changed.append("notes")

    db.add(term)
    db.flush()

    audit_crm_action(
        db,
        context=action_context,
        action="customer.pricing_term.update",
        entity_type="pricing_term",
        entity_id=term.id,
        details={"changed_fields": changed},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.pricing_term_updated",
        entity_type="pricing_term",
        entity_id=term.id,
        payload={
            "customer_id": term.customer_id,
            "pricing_term_id": term.id,
            "changed_fields": changed,
        },
    )
    return term


def delete_pricing_term(
    db: Session,
    *,
    term: CrmCustomerPricingTerm,
    action_context: CrmActionContext,
) -> None:
    customer_id = term.customer_id
    pricing_term_id = term.id

    db.delete(term)
    db.flush()

    audit_crm_action(
        db,
        context=action_context,
        action="customer.pricing_term.remove",
        entity_type="pricing_term",
        entity_id=pricing_term_id,
        details={"customer_id": customer_id},
    )
    emit_crm_event(
        db,
        context=action_context,
        event_name="crm.customer.pricing_term_removed",
        entity_type="pricing_term",
        entity_id=pricing_term_id,
        payload={
            "customer_id": customer_id,
            "pricing_term_id": pricing_term_id,
        },
    )
