from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0009"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("stk_ledger")}

    if "unit_cost" not in existing:
        bind.execute(text("ALTER TABLE stk_ledger ADD COLUMN unit_cost NUMERIC(14,4)"))
    if "total_cost" not in existing:
        bind.execute(text("ALTER TABLE stk_ledger ADD COLUMN total_cost NUMERIC(14,4)"))
    if "cost_after" not in existing:
        bind.execute(text("ALTER TABLE stk_ledger ADD COLUMN cost_after NUMERIC(14,4)"))
    if "source" not in existing:
        bind.execute(text("ALTER TABLE stk_ledger ADD COLUMN source VARCHAR(20)"))


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("stk_ledger")}

    for col in ("source", "cost_after", "total_cost", "unit_cost"):
        if col in existing:
            bind.execute(text(f"ALTER TABLE stk_ledger DROP COLUMN {col}"))
