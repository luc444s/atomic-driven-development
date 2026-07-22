from __future__ import annotations

from sqlalchemy import text

revision = "0004"


INDEX_STATEMENTS = [
    (
        "ix_stk_balance_tenant_wh_prod",
        "CREATE INDEX IF NOT EXISTS ix_stk_balance_tenant_wh_prod "
        "ON stk_balance (tenant_id, warehouse_id, product_id)",
    ),
    (
        "ix_stk_ledger_tenant_prod_wh_cr",
        "CREATE INDEX IF NOT EXISTS ix_stk_ledger_tenant_prod_wh_cr "
        "ON stk_ledger (tenant_id, product_id, warehouse_id, created_at DESC, id DESC)",
    ),
    (
        "ix_stk_ledger_tenant_wh_op_cr",
        "CREATE INDEX IF NOT EXISTS ix_stk_ledger_tenant_wh_op_cr "
        "ON stk_ledger (tenant_id, warehouse_id, operation, created_at DESC, id DESC)",
    ),
]


def upgrade(db) -> None:
    bind = db.connection()
    for _, statement in INDEX_STATEMENTS:
        bind.execute(text(statement))


def downgrade(db) -> None:
    bind = db.connection()
    for index_name, _ in reversed(INDEX_STATEMENTS):
        bind.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
