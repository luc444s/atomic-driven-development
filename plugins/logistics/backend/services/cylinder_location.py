from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsWarehouse,
)


@dataclass(slots=True)
class CylinderCurrentWarehouse:
    warehouse_id: str | None
    warehouse_code: str | None
    warehouse_name: str | None
    source: str


def _match_location_text_to_warehouse(
    db: Session, *, tenant_id: str, location_text: str | None
) -> CylinderCurrentWarehouse:
    normalized_location = (location_text or "").strip().upper()
    if not normalized_location:
        return CylinderCurrentWarehouse(None, None, None, "none")

    warehouses = db.scalars(
        select(LogisticsWarehouse).where(LogisticsWarehouse.tenant_id == tenant_id)
    ).all()

    for warehouse in warehouses:
        if warehouse.code and warehouse.code.upper() in normalized_location:
            return CylinderCurrentWarehouse(
                warehouse.id,
                warehouse.code,
                warehouse.name,
                "location",
            )
    for warehouse in warehouses:
        if warehouse.name and warehouse.name.upper() in normalized_location:
            return CylinderCurrentWarehouse(
                warehouse.id,
                warehouse.code,
                warehouse.name,
                "location",
            )

    return CylinderCurrentWarehouse(None, None, None, "location")


def resolve_cylinder_current_warehouse(
    db: Session, *, tenant_id: str, cylinder: LogisticsCylinder
) -> CylinderCurrentWarehouse:
    row = db.execute(
        select(
            LogisticsMovement.warehouse_id,
            LogisticsWarehouse.code.label("warehouse_code"),
            LogisticsWarehouse.name.label("warehouse_name"),
        )
        .join(
            LogisticsMovementItem,
            LogisticsMovementItem.movement_id == LogisticsMovement.id,
        )
        .outerjoin(
            LogisticsWarehouse,
            LogisticsWarehouse.id == LogisticsMovement.warehouse_id,
        )
        .where(
            LogisticsMovementItem.cylinder_id == cylinder.id,
            LogisticsMovement.warehouse_id.is_not(None),
        )
        .order_by(LogisticsMovement.created_at.desc(), LogisticsMovementItem.created_at.desc())
        .limit(1)
    ).first()
    if row is not None:
        return CylinderCurrentWarehouse(
            row.warehouse_id,
            row.warehouse_code,
            row.warehouse_name,
            "movement",
        )

    return _match_location_text_to_warehouse(
        db,
        tenant_id=tenant_id,
        location_text=cylinder.location,
    )


def cylinder_is_at_warehouse(
    db: Session, *, tenant_id: str, warehouse_id: str | None, cylinder: LogisticsCylinder
) -> bool:
    if warehouse_id is None:
        return True
    current_warehouse = resolve_cylinder_current_warehouse(
        db,
        tenant_id=tenant_id,
        cylinder=cylinder,
    )
    return current_warehouse.warehouse_id == warehouse_id
