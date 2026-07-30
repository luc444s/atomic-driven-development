from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0036"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    fks = inspector.get_foreign_keys("lg_planning_reservations")
    has_quote_fk = any(
        fk.get("constrained_columns") == ["quote_id"]
        for fk in fks
    )
    if not has_quote_fk:
        bind.execute(text(
            "ALTER TABLE lg_planning_reservations "
            "ADD CONSTRAINT fk_planning_reservation_quote "
            "FOREIGN KEY (quote_id) REFERENCES ventas_quote_drafts(id)"
        ))

    quote_cols = {col["name"] for col in inspector.get_columns("ventas_quote_drafts")}
    if "updated_by" not in quote_cols:
        bind.execute(text(
            "ALTER TABLE ventas_quote_drafts "
            "ADD COLUMN updated_by VARCHAR(36) REFERENCES users(id)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    fks = inspector.get_foreign_keys("lg_planning_reservations")
    for fk in fks:
        if fk.get("constrained_columns") == ["quote_id"]:
            bind.execute(text(
                "ALTER TABLE lg_planning_reservations "
                f"DROP CONSTRAINT {fk['name']}"
            ))

    quote_cols = {col["name"] for col in inspector.get_columns("ventas_quote_drafts")}
    if "updated_by" in quote_cols:
        bind.execute(text(
            "ALTER TABLE ventas_quote_drafts DROP COLUMN updated_by"
        ))
