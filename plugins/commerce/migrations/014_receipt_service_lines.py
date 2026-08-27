from sqlalchemy import inspect, text

from plugins.commerce.purchase.backend.models import ComReceiptServiceLine

revision = "0014"


def upgrade(db) -> None:
    bind = db.connection()
    ComReceiptServiceLine.__table__.create(bind=bind, checkfirst=True)

    indexes = {i["name"] for i in inspect(bind).get_indexes("com_receipt_service_lines")}
    for index_name, column in (
        ("ix_com_receipt_service_lines_receipt_id", "receipt_id"),
        ("ix_com_receipt_service_lines_cylinder_id", "cylinder_id"),
    ):
        if index_name not in indexes:
            bind.execute(text(
                f"CREATE INDEX {index_name} "
                f"ON com_receipt_service_lines ({column})"
            ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_com_receipt_service_lines_receipt_id"))
    bind.execute(text("DROP INDEX IF EXISTS ix_com_receipt_service_lines_cylinder_id"))
    ComReceiptServiceLine.__table__.drop(bind=bind, checkfirst=True)
