from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import ComSupplier, ComSupplierAddress


def add_supplier_address(
    db: Session,
    *,
    supplier: ComSupplier,
    tenant_id: str,
    payload: dict,
) -> ComSupplierAddress:
    addr = ComSupplierAddress(
        tenant_id=tenant_id,
        supplier_id=supplier.id,
        line1=payload["line1"],
        district=payload.get("district"),
        city=payload.get("city"),
        country_code=payload.get("country_code", "PE"),
        latitude=payload.get("latitude"),
        longitude=payload.get("longitude"),
        label=payload.get("label"),
    )
    db.add(addr)
    db.flush()
    return addr


def delete_supplier_address(
    db: Session,
    *,
    supplier: ComSupplier,
    address_id: str,
) -> None:
    addr = db.scalar(
        select(ComSupplierAddress).where(
            ComSupplierAddress.id == address_id,
            ComSupplierAddress.supplier_id == supplier.id,
        )
    )
    if addr is None:
        raise ValueError("Direccion no encontrada")
    db.delete(addr)
    db.flush()
