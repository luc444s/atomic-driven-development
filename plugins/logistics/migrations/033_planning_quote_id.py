from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0033"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("lg_planning_reservations")}
    if "quote_id" not in existing:
        bind.execute(text(
            "ALTER TABLE lg_planning_reservations ADD COLUMN quote_id VARCHAR(36)"
        ))
        bind.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_lg_planning_quote "
            "ON lg_planning_reservations(tenant_id, quote_id)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing = {col["name"] for col in inspector.get_columns("lg_planning_reservations")}
    if "quote_id" in existing:
        bind.execute(text(
            "DROP INDEX IF EXISTS ix_lg_planning_quote"
        ))
        bind.execute(text(
            "ALTER TABLE lg_planning_reservations DROP COLUMN quote_id"
        ))
