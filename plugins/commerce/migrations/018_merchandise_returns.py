from sqlalchemy import inspect, text

from plugins.commerce.purchase.backend.models import (
    ComMerchandiseReturn,
    ComMerchandiseReturnEvent,
    ComMerchandiseReturnLine,
)

revision = "0018"

_INDEXES = {
    "com_merchandise_returns": (
        ("ix_com_merchandise_returns_order_id", "order_id"),
        ("ix_com_merchandise_returns_receipt_id", "receipt_id"),
    ),
    "com_merchandise_return_lines": (
        ("ix_com_merchandise_return_lines_return_id", "return_id"),
    ),
    "com_merchandise_return_events": (
        ("ix_com_merchandise_return_events_return_id", "return_id"),
    ),
}


def upgrade(db) -> None:
    bind = db.connection()
    ComMerchandiseReturn.__table__.create(bind=bind, checkfirst=True)
    ComMerchandiseReturnLine.__table__.create(bind=bind, checkfirst=True)
    ComMerchandiseReturnEvent.__table__.create(bind=bind, checkfirst=True)

    inspector = inspect(bind)
    for table, specs in _INDEXES.items():
        indexes = {item["name"] for item in inspector.get_indexes(table)}
        for index_name, column in specs:
            if index_name not in indexes:
                bind.execute(text(f"CREATE INDEX {index_name} ON {table} ({column})"))


def downgrade(db) -> None:
    bind = db.connection()
    for index_name in (
        "ix_com_merchandise_return_events_return_id",
        "ix_com_merchandise_return_lines_return_id",
        "ix_com_merchandise_returns_receipt_id",
        "ix_com_merchandise_returns_order_id",
    ):
        bind.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
    ComMerchandiseReturnEvent.__table__.drop(bind=bind, checkfirst=True)
    ComMerchandiseReturnLine.__table__.drop(bind=bind, checkfirst=True)
    ComMerchandiseReturn.__table__.drop(bind=bind, checkfirst=True)
