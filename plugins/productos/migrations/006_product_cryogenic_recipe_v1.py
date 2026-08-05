from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0006"


def upgrade(db) -> None:
    bind = db.connection()
    existing_columns = {c["name"] for c in inspect(bind).get_columns("prod_adr")}
    if "source_product_id" not in existing_columns:
        bind.execute(text("ALTER TABLE prod_adr ADD COLUMN source_product_id VARCHAR(36) NULL"))
    if "source_quantity_liters" not in existing_columns:
        bind.execute(
            text("ALTER TABLE prod_adr ADD COLUMN source_quantity_liters NUMERIC(10, 3) NULL")
        )
