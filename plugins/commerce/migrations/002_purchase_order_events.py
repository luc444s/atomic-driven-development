from plugins.commerce.purchase.backend.models import ComPurchaseOrderEvent

revision = "0002"


def upgrade(db) -> None:
    bind = db.connection()
    ComPurchaseOrderEvent.__table__.create(bind=bind, checkfirst=True)


def downgrade(db) -> None:
    bind = db.connection()
    ComPurchaseOrderEvent.__table__.drop(bind=bind, checkfirst=True)
