from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0015"


def upgrade(db) -> None:
    bind = db.connection()

    if bind.dialect.name != "postgresql":
        return

    inspector = inspect(bind)
    existing_tables = {t for t in inspector.get_table_names()}
    if "lg_scan_log" not in existing_tables:
        return

    col_info = [c for c in inspector.get_columns("lg_scan_log") if c["name"] == "movement_id"]
    if col_info and col_info[0].get("nullable") is False:
        bind.execute(text("ALTER TABLE lg_scan_log ALTER COLUMN movement_id DROP NOT NULL"))
