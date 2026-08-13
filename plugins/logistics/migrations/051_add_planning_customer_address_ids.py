from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session


def _add_column_if_missing(
    db: Session,
    *,
    table_name: str,
    column_name: str,
    column_sql: str,
) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in existing_columns:
        return
    db.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))


def upgrade(db: Session) -> None:
    # SQLite test DB does not support IF NOT EXISTS here, so inspect first and add only when absent.
    _add_column_if_missing(
        db,
        table_name="lg_planning_reservations",
        column_name="customer_ids_json",
        column_sql="JSON",
    )
    _add_column_if_missing(
        db,
        table_name="lg_planning_reservations",
        column_name="address_ids_json",
        column_sql="JSON",
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
