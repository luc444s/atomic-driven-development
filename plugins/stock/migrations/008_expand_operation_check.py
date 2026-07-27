from __future__ import annotations

from sqlalchemy import text

revision = "0008"


def _is_sqlite(bind) -> bool:
    return "sqlite" in str(bind.engine.url)


def upgrade(db) -> None:
    bind = db.connection()

    if _is_sqlite(bind):
        return

    bind.execute(text(
        "ALTER TABLE stk_ledger DROP CONSTRAINT IF EXISTS ck_stk_ledger_operation"
    ))
    bind.execute(text("""
        ALTER TABLE stk_ledger ADD CONSTRAINT ck_stk_ledger_operation CHECK (
            operation IN ('initial','adjust','transfer_in','transfer_out',
                          'reserve','release','sale_out','purchase_in','return_in','damage_out',
                          'production_in','production_out')
        )
    """))


def downgrade(db) -> None:
    bind = db.connection()

    if _is_sqlite(bind):
        return

    bind.execute(text(
        "ALTER TABLE stk_ledger DROP CONSTRAINT IF EXISTS ck_stk_ledger_operation"
    ))
    bind.execute(text("""
        ALTER TABLE stk_ledger ADD CONSTRAINT ck_stk_ledger_operation CHECK (
            operation IN ('initial','adjust','transfer_in','transfer_out')
        )
    """))
