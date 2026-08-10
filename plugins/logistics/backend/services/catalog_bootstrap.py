from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import (
    LogisticsCylinderState,
    LogisticsMovementType,
    LogisticsStateTransition,
)
from plugins.logistics.backend.services.catalog import (
    MOVEMENT_TYPE_DEFINITIONS,
    STATE_DEFINITIONS,
    TRANSITION_DEFINITIONS,
)


def ensure_logistics_catalogs(db: Session) -> None:
    """Re-populate static logistics catalogs if they were emptied."""
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

    existing_transitions = {
        (item.from_state, item.to_state)
        for item in db.scalars(select(LogisticsStateTransition)).all()
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
