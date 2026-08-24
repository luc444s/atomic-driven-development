from plugins.commerce.purchase.backend.models import ComDispatch, ComDispatchCylinder

revision = "0003"


def upgrade(db) -> None:
    bind = db.connection()
    ComDispatch.__table__.create(bind=bind, checkfirst=True)
    ComDispatchCylinder.__table__.create(bind=bind, checkfirst=True)


def downgrade(db) -> None:
    bind = db.connection()
    ComDispatchCylinder.__table__.drop(bind=bind, checkfirst=True)
    ComDispatch.__table__.drop(bind=bind, checkfirst=True)
