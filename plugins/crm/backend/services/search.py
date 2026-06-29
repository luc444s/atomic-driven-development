from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from plugins.crm.backend.models import CrmCustomer


def build_customer_filters(
    *,
    search: str | None,
    document_type_code: str | None,
    country_code: str | None,
    is_active: bool | None,
    payment_term_code: str | None,
) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                CrmCustomer.legal_name.ilike(term),
                CrmCustomer.document_number.ilike(term),
                CrmCustomer.email.ilike(term),
                CrmCustomer.phone.ilike(term),
                CrmCustomer.external_code.ilike(term),
            )
        )
    if document_type_code:
        filters.append(CrmCustomer.document_type_code == document_type_code.upper())
    if country_code:
        filters.append(CrmCustomer.country_code == country_code.upper())
    if is_active is not None:
        filters.append(CrmCustomer.is_active.is_(is_active))
    if payment_term_code:
        filters.append(CrmCustomer.payment_term_code == payment_term_code.upper())
    return filters


def count_customers(
    db: Session,
    *,
    tenant_id: str,
    filters: list[ColumnElement[bool]],
) -> int:
    stmt = (
        select(func.count())
        .select_from(CrmCustomer)
        .where(CrmCustomer.tenant_id == tenant_id, *filters)
    )
    return int(db.scalar(stmt) or 0)
