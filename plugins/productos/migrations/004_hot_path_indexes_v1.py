from __future__ import annotations

from sqlalchemy import text

revision = "0004"


INDEX_STATEMENTS = [
    (
        "ix_prod_products_tenant_active_name",
        "CREATE INDEX IF NOT EXISTS ix_prod_products_tenant_active_name "
        "ON prod_products (tenant_id, is_active, name)",
    ),
    (
        "ix_prod_prices_prod_list_valid",
        "CREATE INDEX IF NOT EXISTS ix_prod_prices_prod_list_valid "
        "ON prod_prices (product_id, price_list, valid_from DESC)",
    ),
    (
        "ix_prod_costs_prod_type_valid",
        "CREATE INDEX IF NOT EXISTS ix_prod_costs_prod_type_valid "
        "ON prod_costs (product_id, cost_type, valid_from DESC)",
    ),
    (
        "ix_prod_tax_prod_type_valid",
        "CREATE INDEX IF NOT EXISTS ix_prod_tax_prod_type_valid "
        "ON prod_tax_config (product_id, tax_type, valid_from DESC)",
    ),
    (
        "ix_prod_adr_prod_valid",
        "CREATE INDEX IF NOT EXISTS ix_prod_adr_prod_valid "
        "ON prod_adr (product_id, valid_from DESC)",
    ),
    (
        "ix_prod_barcodes_prod_primary_cr",
        "CREATE INDEX IF NOT EXISTS ix_prod_barcodes_prod_primary_cr "
        "ON prod_barcodes (product_id, is_primary DESC, created_at ASC)",
    ),
    (
        "ix_prod_media_prod_primary_cr",
        "CREATE INDEX IF NOT EXISTS ix_prod_media_prod_primary_cr "
        "ON prod_media (product_id, is_primary DESC, created_at ASC)",
    ),
    (
        "ix_prod_promotions_prod_valid_cr",
        "CREATE INDEX IF NOT EXISTS ix_prod_promotions_prod_valid_cr "
        "ON prod_promotions (product_id, valid_from DESC, created_at DESC)",
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
