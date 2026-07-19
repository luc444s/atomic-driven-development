from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0025"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    table_name = "lg_movement_items"
    if table_name not in existing_tables:
        return

    columns = {col["name"]: col for col in inspector.get_columns(table_name)}
    cylinder_id = columns.get("cylinder_id")
    if cylinder_id is not None and cylinder_id.get("nullable") is False:
        bind.execute(
            text(f"ALTER TABLE {table_name} ALTER COLUMN cylinder_id DROP NOT NULL")
        )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    table_name = "lg_movement_items"
    if table_name not in existing_tables:
        return

    rows_with_null = bind.execute(
        text(f"SELECT COUNT(*) FROM {table_name} WHERE cylinder_id IS NULL")
    ).scalar_one()
    if rows_with_null == 0:
        bind.execute(
            text(f"ALTER TABLE {table_name} ALTER COLUMN cylinder_id SET NOT NULL")
        )
