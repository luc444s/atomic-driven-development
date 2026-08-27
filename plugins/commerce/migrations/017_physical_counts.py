from sqlalchemy import inspect, text

from plugins.commerce.purchase.backend.models import (
    ComPhysicalCount,
    ComPhysicalCountEvent,
    ComPhysicalCountExpectedSerial,
    ComPhysicalCountItem,
)

revision = "0017"

_INDEXES = {
    "com_physical_counts": (
        "ix_com_physical_counts_supplier_id",
        "supplier_id",
    ),
    "com_physical_count_expected_serials": (
        "ix_com_physical_count_expected_serials_count_id",
        "count_id",
    ),
    "com_physical_count_items": (
        "ix_com_physical_count_items_count_id",
        "count_id",
    ),
    "com_physical_count_events": (
        "ix_com_physical_count_events_count_id",
        "count_id",
    ),
}


def upgrade(db) -> None:
    bind = db.connection()
    ComPhysicalCount.__table__.create(bind=bind, checkfirst=True)
    ComPhysicalCountExpectedSerial.__table__.create(bind=bind, checkfirst=True)
    ComPhysicalCountItem.__table__.create(bind=bind, checkfirst=True)
    ComPhysicalCountEvent.__table__.create(bind=bind, checkfirst=True)

    for table, (index_name, column) in _INDEXES.items():
        indexes = {i["name"] for i in inspect(bind).get_indexes(table)}
        if index_name not in indexes:
            bind.execute(text(
                f"CREATE INDEX {index_name} ON {table} ({column})"
            ))


def downgrade(db) -> None:
    bind = db.connection()
    for index_name in (
        "ix_com_physical_count_events_count_id",
        "ix_com_physical_count_items_count_id",
        "ix_com_physical_count_expected_serials_count_id",
        "ix_com_physical_counts_supplier_id",
    ):
        bind.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
    ComPhysicalCountEvent.__table__.drop(bind=bind, checkfirst=True)
    ComPhysicalCountItem.__table__.drop(bind=bind, checkfirst=True)
    ComPhysicalCountExpectedSerial.__table__.drop(bind=bind, checkfirst=True)
    ComPhysicalCount.__table__.drop(bind=bind, checkfirst=True)
