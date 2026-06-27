from __future__ import annotations

from sqlalchemy import select

from plugins.logistics.backend.models import LogisticsStateTransition

revision = "0003"


def upgrade(db) -> None:
    existing = db.scalar(
        select(LogisticsStateTransition).where(
            LogisticsStateTransition.from_state == "EN_CLIENTE_VACIO",
            LogisticsStateTransition.to_state == "EN_ALMACEN_VACIO",
        )
    )
    if existing is not None:
        return

    db.add(
        LogisticsStateTransition(
            from_state="EN_CLIENTE_VACIO",
            to_state="EN_ALMACEN_VACIO",
            requires_adr=False,
            requires_hydrotest=False,
            description="Recepcion directa en almacen",
        )
    )
    db.flush()


def downgrade(db) -> None:
    row = db.scalar(
        select(LogisticsStateTransition).where(
            LogisticsStateTransition.from_state == "EN_CLIENTE_VACIO",
            LogisticsStateTransition.to_state == "EN_ALMACEN_VACIO",
        )
    )
    if row is None:
        return
    db.delete(row)
