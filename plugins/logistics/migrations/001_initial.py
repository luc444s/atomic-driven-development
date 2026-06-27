from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.sql.schema import Table

from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderState,
    LogisticsCylinderStateLog,
    LogisticsStateTransition,
)
from plugins.logistics.backend.services.catalog import STATE_DEFINITIONS, TRANSITION_DEFINITIONS

revision = "0001"


def _create_table(table: Table | Any, bind) -> None:
    table.create(bind=bind, checkfirst=True)


def _drop_table(table: Table | Any, bind) -> None:
    table.drop(bind=bind, checkfirst=True)


def upgrade(db) -> None:
    bind = db.get_bind()
    for table in [
        LogisticsCylinderState.__table__,
        LogisticsStateTransition.__table__,
        LogisticsCylinder.__table__,
        LogisticsCylinderStateLog.__table__,
    ]:
        _create_table(table, bind)

    existing_states = set(db.scalars(select(LogisticsCylinderState.code)).all())
    for code, is_final, description in STATE_DEFINITIONS:
        if code in existing_states:
            continue
        db.add(
            LogisticsCylinderState(
                code=code,
                is_final=is_final,
                description=description,
            )
        )
    db.flush()

    existing_transitions = {
        (row.from_state, row.to_state) for row in db.scalars(select(LogisticsStateTransition)).all()
    }
    for (
        from_state,
        to_state,
        requires_adr,
        requires_hydrotest,
        description,
    ) in TRANSITION_DEFINITIONS:
        if (from_state, to_state) in existing_transitions:
            continue
        db.add(
            LogisticsStateTransition(
                from_state=from_state,
                to_state=to_state,
                requires_adr=requires_adr,
                requires_hydrotest=requires_hydrotest,
                description=description,
            )
        )
    db.flush()


def downgrade(db) -> None:
    bind = db.get_bind()
    for table in [
        LogisticsCylinderStateLog.__table__,
        LogisticsCylinder.__table__,
        LogisticsStateTransition.__table__,
        LogisticsCylinderState.__table__,
    ]:
        _drop_table(table, bind)
