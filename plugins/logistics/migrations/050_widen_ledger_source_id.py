from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def upgrade(db: Session) -> None:
    db.execute(
        text(
            "ALTER TABLE lg_customer_cylinder_ledger "
            "ALTER COLUMN source_id TYPE character varying(255)"
        )
    )


def downgrade(db: Session) -> None:
    db.execute(
        text(
            "ALTER TABLE lg_customer_cylinder_ledger "
            "ALTER COLUMN source_id TYPE character varying(36)"
        )
    )
