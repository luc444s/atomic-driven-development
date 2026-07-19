from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0022"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    table_name = "lg_logistics_operations"
    if table_name not in existing_tables:
        return

    columns = {col["name"]: col for col in inspector.get_columns(table_name)}
    col = columns.get("external_movement_id")
    if col and str(col["type"]).startswith("VARCHAR(100)"):
        bind.execute(
            text(f"ALTER TABLE {table_name} ALTER COLUMN external_movement_id TYPE VARCHAR(255)")
        )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    table_name = "lg_logistics_operations"
    if table_name not in existing_tables:
        return

    columns = {col["name"]: col for col in inspector.get_columns(table_name)}
    col = columns.get("external_movement_id")
    if col and str(col["type"]).startswith("VARCHAR"):
        bind.execute(
            text(f"ALTER TABLE {table_name} ALTER COLUMN external_movement_id TYPE VARCHAR(100)")
        )
