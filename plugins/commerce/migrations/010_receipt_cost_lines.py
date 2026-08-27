from sqlalchemy import inspect, text

from plugins.commerce.purchase.backend.models import ComReceiptCostLine

revision = "0010"


def upgrade(db) -> None:
    bind = db.connection()
    ComReceiptCostLine.__table__.create(bind=bind, checkfirst=True)

    indexes = {i["name"] for i in inspect(bind).get_indexes("com_receipt_cost_lines")}
    if "ix_com_receipt_cost_lines_receipt_id" not in indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_receipt_cost_lines_receipt_id "
            "ON com_receipt_cost_lines (receipt_id)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_com_receipt_cost_lines_receipt_id"))
    ComReceiptCostLine.__table__.drop(bind=bind, checkfirst=True)
