from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0057"

_COLUMN = "current_warehouse_id"
_INDEX = "ix_lg_cylinders_current_warehouse_id"
_FK = "fk_lg_cylinders_current_warehouse_id"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "lg_cylinders" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("lg_cylinders")}
    if _COLUMN not in columns:
        bind.execute(
            text("ALTER TABLE lg_cylinders ADD COLUMN current_warehouse_id VARCHAR(36)")
        )

    index_names = {idx["name"] for idx in inspector.get_indexes("lg_cylinders")}
    if _INDEX not in index_names:
        bind.execute(
            text(
                "CREATE INDEX ix_lg_cylinders_current_warehouse_id "
                "ON lg_cylinders (current_warehouse_id)"
            )
        )

    if bind.dialect.name != "sqlite":
        fk_columns = {
            fk["constrained_columns"][0] for fk in inspector.get_foreign_keys("lg_cylinders")
        }
        if _COLUMN not in fk_columns:
            bind.execute(
                text(
                    "ALTER TABLE lg_cylinders "
                    "ADD CONSTRAINT fk_lg_cylinders_current_warehouse_id "
                    "FOREIGN KEY (current_warehouse_id) REFERENCES lg_warehouses(id)"
                )
            )

    # Backfill: ultimo evento de ubicacion con warehouse_id por cilindro.
    if "lg_cylinder_events" in tables:
        bind.execute(
            text(
                """
                UPDATE lg_cylinders
                SET current_warehouse_id = (
                    SELECT e.warehouse_id
                    FROM lg_cylinder_events e
                    WHERE e.cylinder_id = lg_cylinders.id
                      AND e.warehouse_id IS NOT NULL
                      AND e.event_type IN (
                        'WAREHOUSE_IN', 'VEHICLE_LOAD',
                        'CUSTOMER_DELIVERY', 'CUSTOMER_PICKUP'
                      )
                    ORDER BY e.occurred_at DESC, e.created_at DESC
                    LIMIT 1
                )
                WHERE lg_cylinders.current_warehouse_id IS NULL
                """
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "lg_cylinders" not in tables:
        return

    if bind.dialect.name != "sqlite":
        fk_columns = {
            fk["constrained_columns"][0] for fk in inspector.get_foreign_keys("lg_cylinders")
        }
        if _COLUMN in fk_columns:
            bind.execute(
                text(
                    "ALTER TABLE lg_cylinders "
                    "DROP CONSTRAINT fk_lg_cylinders_current_warehouse_id"
                )
            )

    index_names = {idx["name"] for idx in inspector.get_indexes("lg_cylinders")}
    if _INDEX in index_names:
        bind.execute(text("DROP INDEX ix_lg_cylinders_current_warehouse_id"))

    columns = {col["name"] for col in inspector.get_columns("lg_cylinders")}
    if _COLUMN in columns:
        bind.execute(text("ALTER TABLE lg_cylinders DROP COLUMN current_warehouse_id"))
