from sqlalchemy import inspect, text

from plugins.commerce.purchase.backend.models import (
    ComSupplierClaim,
    ComSupplierClaimEvent,
)

revision = "0012"


def upgrade(db) -> None:
    bind = db.connection()
    ComSupplierClaim.__table__.create(bind=bind, checkfirst=True)
    ComSupplierClaimEvent.__table__.create(bind=bind, checkfirst=True)

    indexes = {i["name"] for i in inspect(bind).get_indexes("com_supplier_claims")}
    if "ix_com_supplier_claims_order_id" not in indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_supplier_claims_order_id "
            "ON com_supplier_claims (order_id)"
        ))
    if "ix_com_supplier_claims_supplier_id" not in indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_supplier_claims_supplier_id "
            "ON com_supplier_claims (supplier_id)"
        ))

    event_indexes = {
        i["name"] for i in inspect(bind).get_indexes("com_supplier_claim_events")
    }
    if "ix_com_supplier_claim_events_claim_id" not in event_indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_supplier_claim_events_claim_id "
            "ON com_supplier_claim_events (claim_id)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_com_supplier_claim_events_claim_id"))
    bind.execute(text("DROP INDEX IF EXISTS ix_com_supplier_claims_supplier_id"))
    bind.execute(text("DROP INDEX IF EXISTS ix_com_supplier_claims_order_id"))
    ComSupplierClaimEvent.__table__.drop(bind=bind, checkfirst=True)
    ComSupplierClaim.__table__.drop(bind=bind, checkfirst=True)
