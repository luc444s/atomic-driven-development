from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0002"


def upgrade(db) -> None:
    bind = db.connection()
    existing_columns = {c["name"] for c in inspect(bind).get_columns("prod_products")}
    if "default_weight_kg" not in existing_columns:
        bind.execute(text("ALTER TABLE prod_products ADD COLUMN default_weight_kg NUMERIC(10, 2) NULL"))
