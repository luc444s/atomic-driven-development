from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0003"


def upgrade(db) -> None:
    bind = db.connection()
    existing_columns = {c["name"] for c in inspect(bind).get_columns("prod_products")}
    if "delivery_time" in existing_columns:
        bind.execute(text("ALTER TABLE prod_products DROP COLUMN delivery_time"))
