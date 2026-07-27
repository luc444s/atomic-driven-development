from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0005"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    existing = {col["name"] for col in inspector.get_columns("stk_balance")}
    if "reserved_quantity" not in existing:
        bind.execute(text(
            "ALTER TABLE stk_balance ADD COLUMN reserved_quantity NUMERIC(12,3) NOT NULL DEFAULT 0"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("stk_balance")}
    if "reserved_quantity" in existing:
        bind.execute(text("ALTER TABLE stk_balance DROP COLUMN reserved_quantity"))
