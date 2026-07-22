from __future__ import annotations

from sqlalchemy import text

revision = "0031"


STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    "CREATE INDEX IF NOT EXISTS ix_lg_cyl_serial_trgm "
    "ON lg_cylinders USING gin (serial gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS ix_lg_cyl_desc_trgm "
    "ON lg_cylinders USING gin (description gin_trgm_ops) "
    "WHERE description IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_lg_cyl_barcode1_trgm "
    "ON lg_cylinders USING gin (barcode1 gin_trgm_ops) "
    "WHERE barcode1 IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_lg_cyl_barcode2_trgm "
    "ON lg_cylinders USING gin (barcode2 gin_trgm_ops) "
    "WHERE barcode2 IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_lg_cyl_location_trgm "
    "ON lg_cylinders USING gin (location gin_trgm_ops) "
    "WHERE location IS NOT NULL",
]


def upgrade(db) -> None:
    bind = db.connection()
    if bind.dialect.name != "postgresql":
        return
    for statement in STATEMENTS:
        bind.execute(text(statement))


def downgrade(db) -> None:
    bind = db.connection()
    if bind.dialect.name != "postgresql":
        return
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cyl_location_trgm"))
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cyl_barcode2_trgm"))
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cyl_barcode1_trgm"))
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cyl_desc_trgm"))
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cyl_serial_trgm"))
