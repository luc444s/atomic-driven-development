from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0007"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "lg_warehouses" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("lg_warehouses")}
    if "branch_id" not in columns:
        bind.execute(text("ALTER TABLE lg_warehouses ADD COLUMN branch_id VARCHAR(36)"))


def downgrade(db) -> None:
    return None
