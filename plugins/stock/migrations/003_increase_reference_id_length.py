from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0003"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "stk_ledger" not in existing_tables:
        return

    columns = {col["name"]: col for col in inspector.get_columns("stk_ledger")}
    col = columns.get("reference_id")
    if col and col.get("type") and str(col["type"]).startswith("VARCHAR(100)"):
        bind.execute(text("ALTER TABLE stk_ledger ALTER COLUMN reference_id TYPE VARCHAR(255)"))


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "stk_ledger" not in existing_tables:
        return

    columns = {col["name"]: col for col in inspector.get_columns("stk_ledger")}
    col = columns.get("reference_id")
    if col and str(col["type"]).startswith("VARCHAR"):
        bind.execute(text("ALTER TABLE stk_ledger ALTER COLUMN reference_id TYPE VARCHAR(100)"))
