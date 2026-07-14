from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0002"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "stk_ledger" not in existing_tables:
        return

    existing_columns = {col["name"] for col in inspector.get_columns("stk_ledger")}
    new_columns = [
        ("movement_type", "VARCHAR(30)"),
        ("operation_type", "VARCHAR(30)"),
        ("document_type", "VARCHAR(50)"),
        ("document_id", "VARCHAR(36)"),
        ("related_party_type", "VARCHAR(20)"),
        ("related_party_id", "VARCHAR(36)"),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            bind.execute(
                text(
                    f"ALTER TABLE stk_ledger ADD COLUMN {col_name} {col_type}"
                )
            )

    if "movement_type" in existing_columns:
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_stk_ledger_movement_type "
                "ON stk_ledger (tenant_id, movement_type)"
            )
        )
    if "operation_type" in existing_columns:
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_stk_ledger_operation_type "
                "ON stk_ledger (tenant_id, operation_type)"
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "stk_ledger" not in existing_tables:
        return

    existing_columns = {col["name"] for col in inspector.get_columns("stk_ledger")}
    for col_name in [
        "movement_type",
        "operation_type",
        "document_type",
        "document_id",
        "related_party_type",
        "related_party_id",
    ]:
        if col_name in existing_columns:
            bind.execute(text(f"ALTER TABLE stk_ledger DROP COLUMN {col_name}"))
