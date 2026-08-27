from sqlalchemy import inspect, text

revision = "0013"


def upgrade(db) -> None:
    bind = db.connection()
    columns = {c["name"] for c in inspect(bind).get_columns("com_supplier_claims")}
    if "source" not in columns:
        bind.execute(text(
            "ALTER TABLE com_supplier_claims "
            "ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'MANUAL'"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    columns = {c["name"] for c in inspect(bind).get_columns("com_supplier_claims")}
    if "source" in columns:
        bind.execute(text("ALTER TABLE com_supplier_claims DROP COLUMN source"))
