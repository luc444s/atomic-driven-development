from sqlalchemy import inspect, text

revision = "0005"


def upgrade(db) -> None:
    bind = db.connection()
    columns = {c["name"] for c in inspect(bind).get_columns("com_purchase_receipts")}

    if "dispatch_id" not in columns:
        bind.execute(text(
            "ALTER TABLE com_purchase_receipts "
            "ADD COLUMN dispatch_id VARCHAR(36) "
            "REFERENCES com_dispatches (id)"
        ))

    indexes = {i["name"] for i in inspect(bind).get_indexes("com_purchase_receipts")}
    if "ix_com_purchase_receipts_dispatch_id" not in indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_purchase_receipts_dispatch_id "
            "ON com_purchase_receipts (dispatch_id)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_com_purchase_receipts_dispatch_id"))
    bind.execute(text("ALTER TABLE com_purchase_receipts DROP COLUMN dispatch_id"))
