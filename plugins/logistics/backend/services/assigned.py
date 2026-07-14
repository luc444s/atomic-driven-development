from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import LogisticsMovement, LogisticsMovementItem
from plugins.productos.backend.models import Product

MOVEMENT_SIGN: dict[str, int] = {
    "SC": 1,
    "IC": -1,
}


@dataclass(frozen=True)
class AssignedByCustomerRow:
    product_id: str
    product_name: str
    quantity: int
    raw_quantity: int


def get_assigned_by_customer(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    as_of: datetime | None = None,
) -> list[AssignedByCustomerRow]:
    signed_quantity = func.sum(
        case(
            (
                LogisticsMovement.movement_type == "SC",
                func.coalesce(LogisticsMovementItem.quantity_out, 0),
            ),
            (
                LogisticsMovement.movement_type == "IC",
                -func.coalesce(LogisticsMovementItem.quantity_in, 0),
            ),
            else_=0,
        )
    ).label("raw_assigned")
    product_name = func.coalesce(
        Product.name, LogisticsMovementItem.product_name, "Sin tipo de envase"
    )

    stmt = (
        select(
            LogisticsMovementItem.product_id,
            product_name.label("product_name"),
            signed_quantity,
        )
        .join(LogisticsMovement, LogisticsMovement.id == LogisticsMovementItem.movement_id)
        .outerjoin(Product, Product.id == LogisticsMovementItem.product_id)
        .where(
            LogisticsMovement.tenant_id == tenant_id,
            LogisticsMovement.customer_id == customer_id,
            LogisticsMovement.movement_type.in_(tuple(MOVEMENT_SIGN)),
            LogisticsMovement.status == "COMPLETADO",
            LogisticsMovementItem.product_id.is_not(None),
        )
        .group_by(LogisticsMovementItem.product_id, product_name)
    )
    if as_of is not None:
        stmt = stmt.where(LogisticsMovement.created_at <= as_of)

    rows: list[AssignedByCustomerRow] = []
    for product_id, name, raw_assigned in db.execute(stmt).all():
        raw_quantity = int(raw_assigned or 0)
        if raw_quantity <= 0:
            continue
        rows.append(
            AssignedByCustomerRow(
                product_id=product_id,
                product_name=name,
                quantity=raw_quantity,
                raw_quantity=raw_quantity,
            )
        )
    return rows


def has_any_assignment_movement(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str,
    as_of: datetime | None = None,
) -> bool:
    stmt = select(LogisticsMovement.id).where(
        LogisticsMovement.tenant_id == tenant_id,
        LogisticsMovement.customer_id == customer_id,
        LogisticsMovement.movement_type.in_(tuple(MOVEMENT_SIGN)),
        LogisticsMovement.status == "COMPLETADO",
    )
    if as_of is not None:
        stmt = stmt.where(LogisticsMovement.created_at <= as_of)
    return db.scalar(stmt.limit(1)) is not None
