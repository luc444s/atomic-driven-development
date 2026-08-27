from sqlalchemy import inspect, text

revision = "0009"


def upgrade(db) -> None:
    bind = db.connection()
    columns = {c["name"] for c in inspect(bind).get_columns("com_purchase_receipts")}

    if "qty_accepted" not in columns:
        bind.execute(text(
            "ALTER TABLE com_purchase_receipts ADD COLUMN qty_accepted INTEGER"
        ))
    if "qty_rejected" not in columns:
        bind.execute(text(
            "ALTER TABLE com_purchase_receipts ADD COLUMN qty_rejected INTEGER"
        ))
    if "difference_type" not in columns:
        bind.execute(text(
            "ALTER TABLE com_purchase_receipts ADD COLUMN difference_type VARCHAR(20)"
        ))
    if "incidence_notes" not in columns:
        bind.execute(text(
            "ALTER TABLE com_purchase_receipts ADD COLUMN incidence_notes TEXT"
        ))
    if "commercial_closed_at" not in columns:
        bind.execute(text(
            "ALTER TABLE com_purchase_receipts "
            "ADD COLUMN commercial_closed_at TIMESTAMP WITH TIME ZONE"
        ))
    if "commercial_closed_by" not in columns:
        bind.execute(text(
            "ALTER TABLE com_purchase_receipts ADD COLUMN commercial_closed_by VARCHAR(36)"
        ))

    indexes = {i["name"] for i in inspect(bind).get_indexes("com_purchase_receipts")}
    if "ix_com_purchase_receipts_commercial_closed" not in indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_purchase_receipts_commercial_closed "
            "ON com_purchase_receipts (commercial_closed_at)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_com_purchase_receipts_commercial_closed"))
    for col in (
        "commercial_closed_by",
        "commercial_closed_at",
        "incidence_notes",
        "difference_type",
        "qty_rejected",
        "qty_accepted",
    ):
        bind.execute(text(f"ALTER TABLE com_purchase_receipts DROP COLUMN {col}"))
