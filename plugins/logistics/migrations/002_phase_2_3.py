from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.sql.schema import Table

from plugins.logistics.backend.models import (
    LogisticsAgendaTask,
    LogisticsAgendaTaskType,
    LogisticsCylinderWarranty,
    LogisticsDeliveryPoint,
    LogisticsHydrostaticTest,
    LogisticsLoad,
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsMovementStatusHistory,
    LogisticsMovementType,
    LogisticsOrder,
    LogisticsOrderItem,
    LogisticsRoute,
    LogisticsRouteStop,
    LogisticsVehicle,
    LogisticsWarehouse,
    LogisticsZone,
)
from plugins.logistics.backend.services.catalog import (
    AGENDA_TASK_TYPE_DEFINITIONS,
    MOVEMENT_TYPE_DEFINITIONS,
)

revision = "0002"


def _create_table(table: Table | Any, bind) -> None:
    table.create(bind=bind, checkfirst=True)


def _drop_table(table: Table | Any, bind) -> None:
    table.drop(bind=bind, checkfirst=True)


def upgrade(db) -> None:
    bind = db.get_bind()
    for table in [
        LogisticsWarehouse.__table__,
        LogisticsZone.__table__,
        LogisticsVehicle.__table__,
        LogisticsDeliveryPoint.__table__,
        LogisticsOrder.__table__,
        LogisticsOrderItem.__table__,
        LogisticsRoute.__table__,
        LogisticsRouteStop.__table__,
        LogisticsLoad.__table__,
        LogisticsMovementType.__table__,
        LogisticsMovement.__table__,
        LogisticsMovementItem.__table__,
        LogisticsMovementStatusHistory.__table__,
        LogisticsAgendaTaskType.__table__,
        LogisticsAgendaTask.__table__,
        LogisticsHydrostaticTest.__table__,
        LogisticsCylinderWarranty.__table__,
    ]:
        _create_table(table, bind)

    existing_movement_types = set(db.scalars(select(LogisticsMovementType.code)).all())
    for (
        code,
        name,
        category,
        moves_cylinders,
        origin_state,
        target_state,
    ) in MOVEMENT_TYPE_DEFINITIONS:
        if code in existing_movement_types:
            continue
        db.add(
            LogisticsMovementType(
                code=code,
                name=name,
                category=category,
                moves_cylinders=moves_cylinders,
                origin_state=origin_state,
                target_state=target_state,
            )
        )

    existing_task_types = set(db.scalars(select(LogisticsAgendaTaskType.code)).all())
    for code, description in AGENDA_TASK_TYPE_DEFINITIONS:
        if code in existing_task_types:
            continue
        db.add(LogisticsAgendaTaskType(code=code, description=description))

    db.flush()


def downgrade(db) -> None:
    bind = db.get_bind()
    for table in [
        LogisticsCylinderWarranty.__table__,
        LogisticsHydrostaticTest.__table__,
        LogisticsAgendaTask.__table__,
        LogisticsAgendaTaskType.__table__,
        LogisticsMovementStatusHistory.__table__,
        LogisticsMovementItem.__table__,
        LogisticsMovement.__table__,
        LogisticsMovementType.__table__,
        LogisticsLoad.__table__,
        LogisticsRouteStop.__table__,
        LogisticsRoute.__table__,
        LogisticsOrderItem.__table__,
        LogisticsOrder.__table__,
        LogisticsDeliveryPoint.__table__,
        LogisticsVehicle.__table__,
        LogisticsZone.__table__,
        LogisticsWarehouse.__table__,
    ]:
        _drop_table(table, bind)
