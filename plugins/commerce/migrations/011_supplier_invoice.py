from sqlalchemy import inspect, text

from plugins.commerce.purchase.backend.models import (
    ComSupplierInvoice,
    ComSupplierInvoiceLine,
)

revision = "0011"


def upgrade(db) -> None:
    bind = db.connection()
    ComSupplierInvoice.__table__.create(bind=bind, checkfirst=True)
    ComSupplierInvoiceLine.__table__.create(bind=bind, checkfirst=True)

    indexes = {i["name"] for i in inspect(bind).get_indexes("com_supplier_invoices")}
    if "ix_com_supplier_invoices_order_id" not in indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_supplier_invoices_order_id "
            "ON com_supplier_invoices (order_id)"
        ))
    if "ix_com_supplier_invoices_supplier_id" not in indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_supplier_invoices_supplier_id "
            "ON com_supplier_invoices (supplier_id)"
        ))

    line_indexes = {
        i["name"] for i in inspect(bind).get_indexes("com_supplier_invoice_lines")
    }
    if "ix_com_supplier_invoice_lines_invoice_id" not in line_indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_supplier_invoice_lines_invoice_id "
            "ON com_supplier_invoice_lines (invoice_id)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_com_supplier_invoice_lines_invoice_id"))
    bind.execute(text("DROP INDEX IF EXISTS ix_com_supplier_invoices_supplier_id"))
    bind.execute(text("DROP INDEX IF EXISTS ix_com_supplier_invoices_order_id"))
    ComSupplierInvoiceLine.__table__.drop(bind=bind, checkfirst=True)
    ComSupplierInvoice.__table__.drop(bind=bind, checkfirst=True)
