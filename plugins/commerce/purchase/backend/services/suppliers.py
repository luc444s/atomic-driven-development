from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import ComSupplier


def list_suppliers(
    db: Session, *, tenant_id: str, search: str | None = None, active_only: bool = True
) -> list[ComSupplier]:
    stmt = select(ComSupplier).where(ComSupplier.tenant_id == tenant_id)
    if active_only:
        stmt = stmt.where(ComSupplier.is_active.is_(True))
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(ComSupplier.name.ilike(term))
    stmt = stmt.order_by(ComSupplier.name.asc())
    return list(db.scalars(stmt).all())


def get_supplier(db: Session, *, tenant_id: str, supplier_id: str) -> ComSupplier | None:
    return db.scalar(
        select(ComSupplier).where(
            ComSupplier.id == supplier_id, ComSupplier.tenant_id == tenant_id
        )
    )


def create_supplier(db: Session, *, tenant_id: str, payload: dict) -> ComSupplier:
    supplier = ComSupplier(tenant_id=tenant_id, **payload)
    db.add(supplier)
    db.flush()
    return supplier


def update_supplier(db: Session, *, supplier: ComSupplier, payload: dict) -> ComSupplier:
    for field, value in payload.items():
        if value is not None:
            setattr(supplier, field, value)
    db.add(supplier)
    db.flush()
    return supplier


def disable_supplier(db: Session, *, supplier: ComSupplier) -> ComSupplier:
    supplier.is_active = False
    db.add(supplier)
    db.flush()
    return supplier
