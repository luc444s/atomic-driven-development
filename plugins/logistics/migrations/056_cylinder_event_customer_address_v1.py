from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0056"

_COLUMN = "customer_address_id"
_INDEX = "ix_lg_cylinder_events_customer_address"
_FK = "fk_lg_cylinder_events_customer_address"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "lg_cylinder_events" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("lg_cylinder_events")}
    if _COLUMN not in columns:
        bind.execute(
            text("ALTER TABLE lg_cylinder_events ADD COLUMN customer_address_id VARCHAR(36)")
        )

    index_names = {idx["name"] for idx in inspector.get_indexes("lg_cylinder_events")}
    if _INDEX not in index_names:
        bind.execute(
            text(
                "CREATE INDEX ix_lg_cylinder_events_customer_address "
                "ON lg_cylinder_events (customer_address_id, occurred_at)"
            )
        )

    if bind.dialect.name == "sqlite":
        return

    fk_columns = {
        fk["constrained_columns"][0] for fk in inspector.get_foreign_keys("lg_cylinder_events")
    }
    if _COLUMN not in fk_columns:
        bind.execute(
            text(
                "ALTER TABLE lg_cylinder_events "
                "ADD CONSTRAINT fk_lg_cylinder_events_customer_address "
                "FOREIGN KEY (customer_address_id) REFERENCES crm_customer_addresses(id)"
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "lg_cylinder_events" not in tables:
        return

    if bind.dialect.name != "sqlite":
        fk_columns = {
            fk["constrained_columns"][0]
            for fk in inspector.get_foreign_keys("lg_cylinder_events")
        }
        if _COLUMN in fk_columns:
            bind.execute(
                text(
                    "ALTER TABLE lg_cylinder_events "
                    "DROP CONSTRAINT fk_lg_cylinder_events_customer_address"
                )
            )

    index_names = {idx["name"] for idx in inspector.get_indexes("lg_cylinder_events")}
    if _INDEX in index_names:
        bind.execute(
            text("DROP INDEX ix_lg_cylinder_events_customer_address")
        )

    columns = {col["name"] for col in inspector.get_columns("lg_cylinder_events")}
    if _COLUMN in columns:
        bind.execute(
            text("ALTER TABLE lg_cylinder_events DROP COLUMN customer_address_id")
        )
