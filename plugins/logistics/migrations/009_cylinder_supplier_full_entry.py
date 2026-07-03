from __future__ import annotations

from sqlalchemy import select

from plugins.logistics.backend.models import LogisticsMovementType

revision = "0009"


def upgrade(db) -> None:
    existing = set(db.scalars(select(LogisticsMovementType.code)).all())
    if "IFP" not in existing:
        db.add(
            LogisticsMovementType(
                code="IFP",
                name="Ingreso lleno desde proveedor",
                category="INGRESO",
                moves_cylinders=True,
                origin_state=None,
                target_state="LLENADO_OK",
            )
        )
    db.flush()


def downgrade(db) -> None:
    item = db.scalar(select(LogisticsMovementType).where(LogisticsMovementType.code == "IFP"))
    if item is not None:
        db.delete(item)
        db.flush()
