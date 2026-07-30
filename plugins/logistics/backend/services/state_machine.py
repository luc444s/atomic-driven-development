from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import LogisticsCylinder, LogisticsStateTransition
from plugins.logistics.backend.services.product_bridge import resolve_product_adr

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
            f"El cilindro {cylinder.serial} está en estado final "
            f"({cylinder.current_state}) y no admite transiciones"
        )
    if cylinder.current_state == to_state:
        raise StateTransitionError("No se puede transicionar al mismo estado")

    transition = db.scalar(
        select(LogisticsStateTransition).where(
            LogisticsStateTransition.from_state == cylinder.current_state,
            LogisticsStateTransition.to_state == to_state,
        )
    )
    if transition is None:
        raise StateTransitionError(
            f"Transición no permitida: {cylinder.current_state} → {to_state}. "
            f"Revise el flujo de estados del cilindro {cylinder.serial}."
        )

    if transition.requires_adr and not has_valid_adr(db, cylinder):
        raise StateTransitionError(
            "Esta transición requiere datos ADR del producto asociado"
        )
    if transition.requires_hydrotest and not has_valid_hydrotest(cylinder):
        raise StateTransitionError("Esta transición requiere prueba hidrostática vigente")

    return transition


def has_valid_adr(db: Session, cylinder: LogisticsCylinder) -> bool:
    product_id = cylinder.product_id or cylinder.gas_group_id
    if not product_id:
        return False
    adr = resolve_product_adr(db, product_id)
    return bool(adr and adr.category and adr.un_number and adr.label)


def has_valid_hydrotest(cylinder: LogisticsCylinder) -> bool:
    if cylinder.next_hydrotest_date is None:
        return False
    return cylinder.next_hydrotest_date >= datetime.now(UTC).date()
