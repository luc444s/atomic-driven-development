from sqlalchemy import inspect, text

revision = "0015"


def upgrade(db) -> None:
    bind = db.connection()
    columns = {c["name"] for c in inspect(bind).get_columns("com_receipt_service_lines")}

    if "test_date" not in columns:
        bind.execute(text(
            "ALTER TABLE com_receipt_service_lines ADD COLUMN test_date DATE"
        ))
    if "next_test_date" not in columns:
        bind.execute(text(
            "ALTER TABLE com_receipt_service_lines ADD COLUMN next_test_date DATE"
        ))
    if "result" not in columns:
        bind.execute(text(
            "ALTER TABLE com_receipt_service_lines ADD COLUMN result VARCHAR(20)"
        ))
    if "document_ref" not in columns:
        bind.execute(text(
            "ALTER TABLE com_receipt_service_lines ADD COLUMN document_ref VARCHAR(80)"
        ))

    indexes = {i["name"] for i in inspect(bind).get_indexes("com_receipt_service_lines")}
    if "ix_com_receipt_service_lines_next_test_date" not in indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_receipt_service_lines_next_test_date "
            "ON com_receipt_service_lines (next_test_date)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_com_receipt_service_lines_next_test_date"))
    for col in ("document_ref", "result", "next_test_date", "test_date"):
        bind.execute(text(f"ALTER TABLE com_receipt_service_lines DROP COLUMN {col}"))
