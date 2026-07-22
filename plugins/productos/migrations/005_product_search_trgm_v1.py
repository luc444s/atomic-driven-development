from __future__ import annotations

from sqlalchemy import text

revision = "0005"


STATEMENTS = [
    "CREATE EXTENSION IF NOT EXISTS pg_trgm",
    "CREATE INDEX IF NOT EXISTS ix_prod_products_sku_trgm "
    "ON prod_products USING gin (sku gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS ix_prod_products_name_trgm "
    "ON prod_products USING gin (name gin_trgm_ops)",
    "CREATE INDEX IF NOT EXISTS ix_prod_barcodes_barcode_trgm "
    "ON prod_barcodes USING gin (barcode gin_trgm_ops)",
]


def upgrade(db) -> None:
    bind = db.connection()
    for statement in STATEMENTS:
        bind.execute(text(statement))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_prod_barcodes_barcode_trgm"))
    bind.execute(text("DROP INDEX IF EXISTS ix_prod_products_name_trgm"))
    bind.execute(text("DROP INDEX IF EXISTS ix_prod_products_sku_trgm"))
