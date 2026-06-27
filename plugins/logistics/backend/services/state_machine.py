from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import LogisticsCylinder, LogisticsStateTransition

FINAL_STATES = {"BLOQUEADO", "OBSERVADO", "DE_BAJA", "PERDIDO"}


class StateTransitionError(ValueError):
    pass


def list_allowed_transitions(
    db: Session,
    *,
    from_state: str,
) -> list[LogisticsStateTransition]:
    return list(
        db.scalars(
            select(LogisticsStateTransition)
            .where(LogisticsStateTransition.from_state == from_state)
            .order_by(LogisticsStateTransition.to_state)
        ).all()
    )


def ensure_transition_allowed(
    db: Session,
    *,
    cylinder: LogisticsCylinder,
    to_state: str,
) -> LogisticsStateTransition:
    if cylinder.current_state in FINAL_STATES:
        raise StateTransitionError(
            f"Cylinder {cylinder.serial} is in final state {cylinder.current_state}"
        )
    if cylinder.current_state == to_state:
        raise StateTransitionError("Transition to the same state is not allowed")

    transition = db.scalar(
        select(LogisticsStateTransition).where(
            LogisticsStateTransition.from_state == cylinder.current_state,
            LogisticsStateTransition.to_state == to_state,
        )
    )
    if transition is None:
        raise StateTransitionError(
            f"Transition {cylinder.current_state} -> {to_state} is not allowed"
        )

    if transition.requires_adr and not has_valid_adr(cylinder):
        raise StateTransitionError(
            "Transition requires ADR data (`adr_category`, `adr_un_number`, `adr_label`)"
        )
    if transition.requires_hydrotest and not has_valid_hydrotest(cylinder):
        raise StateTransitionError("Transition requires a valid `next_hydrotest_date`")

    return transition


def has_valid_adr(cylinder: LogisticsCylinder) -> bool:
    return bool(cylinder.adr_category and cylinder.adr_un_number and cylinder.adr_label)


def has_valid_hydrotest(cylinder: LogisticsCylinder) -> bool:
    if cylinder.next_hydrotest_date is None:
        return False
    return cylinder.next_hydrotest_date >= datetime.now(UTC).date()
