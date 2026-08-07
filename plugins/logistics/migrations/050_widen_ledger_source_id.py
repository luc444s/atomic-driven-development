from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def _is_postgresql(db: Session) -> bool:
    return db.bind.dialect.name == "postgresql"


def upgrade(db: Session) -> None:
    # SQLite no aplica longitud en VARCHAR, por lo que ALTER TYPE es un no-op
    # y además no es sintaxis soportada. Solo se ejecuta en PostgreSQL.
    if not _is_postgresql(db):
        return
    db.execute(
        text(
            "ALTER TABLE lg_customer_cylinder_ledger "
            "ALTER COLUMN source_id TYPE character varying(255)"
        )
    )


def downgrade(db: Session) -> None:
    if not _is_postgresql(db):
        return
    db.execute(
        text(
            "ALTER TABLE lg_customer_cylinder_ledger "
            "ALTER COLUMN source_id TYPE character varying(36)"
        )
    )
