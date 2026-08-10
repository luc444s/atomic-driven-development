from __future__ import annotations

from plugins.commerce.purchase.backend.models import (
    ComPurchaseItem,
    ComPurchaseOrder,
    ComPurchaseReceipt,
    ComSupplier,
    ComSupplierAddress,
    ComSupplierBankAccount,
    ComSupplierContact,
    ComSupplierPaymentTerm,
)

revision = "0001"


def upgrade(db) -> None:
    bind = db.connection()
    ComSupplier.__table__.create(bind=bind, checkfirst=True)
    ComSupplierAddress.__table__.create(bind=bind, checkfirst=True)
    ComSupplierContact.__table__.create(bind=bind, checkfirst=True)
    ComSupplierBankAccount.__table__.create(bind=bind, checkfirst=True)
    ComSupplierPaymentTerm.__table__.create(bind=bind, checkfirst=True)
    ComPurchaseOrder.__table__.create(bind=bind, checkfirst=True)
    ComPurchaseItem.__table__.create(bind=bind, checkfirst=True)
    ComPurchaseReceipt.__table__.create(bind=bind, checkfirst=True)


def downgrade(db) -> None:
    bind = db.connection()
    ComPurchaseReceipt.__table__.drop(bind=bind, checkfirst=True)
    ComPurchaseItem.__table__.drop(bind=bind, checkfirst=True)
    ComPurchaseOrder.__table__.drop(bind=bind, checkfirst=True)
    ComSupplierPaymentTerm.__table__.drop(bind=bind, checkfirst=True)
    ComSupplierBankAccount.__table__.drop(bind=bind, checkfirst=True)
    ComSupplierContact.__table__.drop(bind=bind, checkfirst=True)
    ComSupplierAddress.__table__.drop(bind=bind, checkfirst=True)
    ComSupplier.__table__.drop(bind=bind, checkfirst=True)
