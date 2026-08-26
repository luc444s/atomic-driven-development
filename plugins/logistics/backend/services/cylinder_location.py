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

# No se importa get_last_location_event a nivel modulo porque
# cylinders.py importa cylinder_location.py → circular import.
# Se importa dentro de resolve_cylinder_current_warehouse.


def _cylinder_is_in_transit(cylinder: LogisticsCylinder) -> bool:
    # Un cilindro en transito se esta moviendo activamente entre ubicaciones.
    # Solo en estos estados el ultimo movimiento es la fuente de verdad
    # para saber donde esta.
    return cylinder.current_state in {"CARGA_EN_VEHICULO", "EN_RUTA"}


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

    if normalized_location.startswith(prefix := "TANK_WH:"):
        warehouse_id = (location_text or "").strip()[len(prefix):]
        warehouse = db.get(LogisticsWarehouse, warehouse_id)
        if warehouse is not None:
            return CylinderCurrentWarehouse(
                warehouse.id,
                warehouse.code,
                warehouse.name,
                "location",
            )
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
    if cylinder.current_warehouse_id is not None:
        warehouse = db.get(LogisticsWarehouse, cylinder.current_warehouse_id)
        if warehouse is not None:
            return CylinderCurrentWarehouse(
                warehouse.id,
                warehouse.code,
                warehouse.name,
                "denormalized",
            )
        # Columna apunta a warehouse inexistente: degrada al calculo.
    # Si el cilindro ya no esta en transito (CARGA_EN_VEHICULO / EN_RUTA),
    # el ultimo movimiento pierde vigencia. La verdad fisica esta en el
    # ultimo evento de ubicacion (WAREHOUSE_IN, CUSTOMER_DELIVERY, etc.)
    # o, como fallback, en el campo location del cilindro.
    if not _cylinder_is_in_transit(cylinder):
        # Lazy import para evitar circular import con cylinders.py
        from plugins.logistics.backend.services.cylinders import (
            get_last_location_event,
        )

        event = get_last_location_event(db, cylinder_id=cylinder.id)
        if event is not None and event.warehouse_id is not None:
            warehouse = db.get(LogisticsWarehouse, event.warehouse_id)
            if warehouse is not None:
                return CylinderCurrentWarehouse(
                    warehouse.id,
                    warehouse.code,
                    warehouse.name,
                    "event",
                )
        return _match_location_text_to_warehouse(
            db,
            tenant_id=tenant_id,
            location_text=cylinder.location,
        )

    # En transito: la fuente de verdad es el ultimo movimiento con warehouse_id.
    # El movimiento SC/IC registra el warehouse origen o destino del traslado.

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
