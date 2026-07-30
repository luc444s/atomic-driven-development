from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0034"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    dialect = bind.dialect.name

    movement_cols = {col["name"] for col in inspector.get_columns("lg_movements")}
    if "origin_movement_id" not in movement_cols:
        bind.execute(text(
            "ALTER TABLE lg_movements ADD COLUMN origin_movement_id VARCHAR(36)"
        ))
        bind.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_lg_movements_origin "
            "ON lg_movements(tenant_id, origin_movement_id)"
        ))

    if "last_stock_sync_error" not in movement_cols:
        bind.execute(text(
            "ALTER TABLE lg_movements ADD COLUMN last_stock_sync_error TEXT"
        ))

    tables = inspector.get_table_names()
    if "lg_stock_bridge_log" not in tables:
        if dialect == "postgresql":
            bind.execute(text("""
                CREATE TABLE lg_stock_bridge_log (
                    id          VARCHAR(36) PRIMARY KEY,
                    tenant_id   VARCHAR(36) NOT NULL REFERENCES tenants(id),
                    movement_id VARCHAR(36) NOT NULL,
                    operation   VARCHAR(20) NOT NULL,
                    product_id  VARCHAR(36),
                    quantity    NUMERIC(12,3),
                    unit_cost   NUMERIC(14,4),
                    status      VARCHAR(20) NOT NULL,
                    error_msg   TEXT,
                    payload     JSONB,
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))
        else:
            bind.execute(text("""
                CREATE TABLE lg_stock_bridge_log (
                    id          VARCHAR(36) PRIMARY KEY,
                    tenant_id   VARCHAR(36) NOT NULL REFERENCES tenants(id),
                    movement_id VARCHAR(36) NOT NULL,
                    operation   VARCHAR(20) NOT NULL,
                    product_id  VARCHAR(36),
                    quantity    NUMERIC(12,3),
                    unit_cost   NUMERIC(14,4),
                    status      VARCHAR(20) NOT NULL,
                    error_msg   TEXT,
                    payload     TEXT,
                    created_at  DATETIME NOT NULL DEFAULT (datetime('now'))
                )
            """))
        bind.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_stock_bridge_log_movement "
            "ON lg_stock_bridge_log(tenant_id, movement_id)"
        ))
        bind.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_stock_bridge_log_created "
            "ON lg_stock_bridge_log(tenant_id, created_at DESC)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    movement_cols = {col["name"] for col in inspector.get_columns("lg_movements")}
    if "origin_movement_id" in movement_cols:
        bind.execute(text(
            "DROP INDEX IF EXISTS ix_lg_movements_origin"
        ))
        bind.execute(text(
            "ALTER TABLE lg_movements DROP COLUMN origin_movement_id"
        ))

    if "last_stock_sync_error" in movement_cols:
        bind.execute(text(
            "ALTER TABLE lg_movements DROP COLUMN last_stock_sync_error"
        ))

    tables = inspector.get_table_names()
    if "lg_stock_bridge_log" in tables:
        bind.execute(text(
            "DROP INDEX IF EXISTS ix_stock_bridge_log_movement"
        ))
        bind.execute(text(
            "DROP INDEX IF EXISTS ix_stock_bridge_log_created"
        ))
        bind.execute(text(
            "DROP TABLE lg_stock_bridge_log"
        ))
