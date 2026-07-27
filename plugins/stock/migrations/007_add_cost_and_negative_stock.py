from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0007"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    balance_cols = {col["name"] for col in inspector.get_columns("stk_balance")}
    if "total_cost" not in balance_cols:
        bind.execute(text(
            "ALTER TABLE stk_balance ADD COLUMN total_cost NUMERIC(14,4) NOT NULL DEFAULT 0"
        ))
    if "allow_negative_stock" not in balance_cols:
        bind.execute(text(
            "ALTER TABLE stk_balance ADD COLUMN allow_negative_stock BOOLEAN NOT NULL DEFAULT FALSE"
        ))

    config_cols = {col["name"] for col in inspector.get_columns("stk_config")}
    if "allow_negative_stock" not in config_cols:
        bind.execute(text(
            "ALTER TABLE stk_config ADD COLUMN allow_negative_stock BOOLEAN NOT NULL DEFAULT FALSE"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    balance_cols = {col["name"] for col in inspector.get_columns("stk_balance")}
    if "allow_negative_stock" in balance_cols:
        bind.execute(text("ALTER TABLE stk_balance DROP COLUMN allow_negative_stock"))
    if "total_cost" in balance_cols:
        bind.execute(text("ALTER TABLE stk_balance DROP COLUMN total_cost"))

    config_cols = {col["name"] for col in inspector.get_columns("stk_config")}
    if "allow_negative_stock" in config_cols:
        bind.execute(text("ALTER TABLE stk_config DROP COLUMN allow_negative_stock"))
