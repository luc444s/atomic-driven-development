from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def upgrade(db: Session) -> None:
    db.execute(
        text(
            "ALTER TABLE lg_planning_reservations "
            "ADD COLUMN IF NOT EXISTS customer_ids_json JSON"
        )
    )
    db.execute(
        text(
            "ALTER TABLE lg_planning_reservations "
            "ADD COLUMN IF NOT EXISTS address_ids_json JSON"
        )
    )


def downgrade(db: Session) -> None:
    db.execute(
        text(
            "ALTER TABLE lg_planning_reservations "
            "DROP COLUMN IF EXISTS address_ids_json"
        )
    )
    db.execute(
        text(
            "ALTER TABLE lg_planning_reservations "
            "DROP COLUMN IF EXISTS customer_ids_json"
        )
    )
