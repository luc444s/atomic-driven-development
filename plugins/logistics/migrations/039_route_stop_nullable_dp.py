from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0039"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    columns = {col["name"] for col in inspector.get_columns("lg_route_stops")}

    if "delivery_point_id" in columns:
        bind.execute(text(
            "ALTER TABLE lg_route_stops ALTER COLUMN delivery_point_id DROP NOT NULL"
        ))
