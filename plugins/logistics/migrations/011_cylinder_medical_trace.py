from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0011"


def _add_column_if_missing(bind, table_name: str, column_def: str) -> None:
    existing = {c["name"] for c in inspect(bind).get_columns(table_name)}
    col_name = column_def.split()[0]
    if col_name in existing:
        return
    bind.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}"))


def upgrade(db) -> None:
    bind = db.connection()
    _add_column_if_missing(bind, "lg_cylinders", "is_medical BOOLEAN NOT NULL DEFAULT FALSE")
    _add_column_if_missing(bind, "lg_cylinders", "medical_notes TEXT")
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_cylinders_is_medical "
            "ON lg_cylinders (is_medical) WHERE is_medical = TRUE"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cylinders_is_medical"))
    bind.execute(text("ALTER TABLE lg_cylinders DROP COLUMN IF EXISTS medical_notes"))
    bind.execute(text("ALTER TABLE lg_cylinders DROP COLUMN IF EXISTS is_medical"))
