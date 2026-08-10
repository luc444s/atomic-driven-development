from __future__ import annotations

from sqlalchemy import select

from plugins.logistics.backend.models.cylinder import LogisticsCylinder

revision = "052"


def upgrade(db) -> None:
    tanks = list(
        db.scalars(
            select(LogisticsCylinder).where(
                LogisticsCylinder.container_type == "CRYOGENIC_TANK"
            )
        ).all()
    )
    for tank in tanks:
        location = (tank.location or "").strip()
        if not location or location.startswith("TANK_WH:"):
            continue
        if len(location) == 36 and location.count("-") == 4:
            tank.location = f"TANK_WH:{location}"
            db.add(tank)
    db.flush()
