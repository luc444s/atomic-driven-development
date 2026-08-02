from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0045"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    columns = {col["name"] for col in inspector.get_columns("lg_warehouses")}
    for column, ddl in [
        ("latitude", "DOUBLE PRECISION"),
        ("longitude", "DOUBLE PRECISION"),
        ("formatted_address", "VARCHAR(255)"),
        ("place_id", "VARCHAR(64)"),
        ("geocode_source", "VARCHAR(20)"),
    ]:
        if column not in columns:
            bind.execute(text(f"ALTER TABLE lg_warehouses ADD COLUMN {column} {ddl}"))


def downgrade(db) -> None:
    bind = db.connection()
    for column in ["latitude", "longitude", "formatted_address", "place_id", "geocode_source"]:
        bind.execute(text(f"ALTER TABLE lg_warehouses DROP COLUMN IF EXISTS {column}"))
