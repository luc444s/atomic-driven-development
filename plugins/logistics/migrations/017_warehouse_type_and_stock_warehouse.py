from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0017"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "lg_warehouses" in existing_tables:
        existing_columns = {col["name"] for col in inspector.get_columns("lg_warehouses")}
        if "warehouse_type" not in existing_columns:
            bind.execute(
                text(
                    "ALTER TABLE lg_warehouses "
                    "ADD COLUMN warehouse_type VARCHAR(20) NOT NULL DEFAULT 'FIXED'"
                )
            )

    if "lg_mobile_warehouse_items" in existing_tables:
        item_columns = {
            col["name"] for col in inspector.get_columns("lg_mobile_warehouse_items")
        }
        if "customer_id" not in item_columns:
            bind.execute(
                text(
                    "ALTER TABLE lg_mobile_warehouse_items "
                    "ADD COLUMN customer_id VARCHAR(36)"
                )
            )
            bind.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_lg_mobile_warehouse_items_customer "
                    "ON lg_mobile_warehouse_items (tenant_id, customer_id)"
                )
            )

    if "lg_mobile_warehouses" in existing_tables:
        existing_columns = {
            col["name"] for col in inspector.get_columns("lg_mobile_warehouses")
        }
        if "stock_warehouse_id" not in existing_columns:
            bind.execute(
                text(
                    "ALTER TABLE lg_mobile_warehouses "
                    "ADD COLUMN stock_warehouse_id VARCHAR(36)"
                )
            )
            bind.execute(
                text(
                    "CREATE INDEX ix_lg_mobile_warehouses_stock_warehouse "
                    "ON lg_mobile_warehouses (tenant_id, stock_warehouse_id)"
                )
            )


    if "lg_mobile_warehouse_snapshots" not in existing_tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_mobile_warehouse_snapshots (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    mobile_warehouse_id VARCHAR(36) NOT NULL,
                    snapshot_type VARCHAR(30) NOT NULL,
                    captured_at TIMESTAMP NOT NULL,
                    captured_by VARCHAR(36),
                    total_units NUMERIC(18, 4) NOT NULL DEFAULT 0,
                    total_weight_kg NUMERIC(18, 4) NOT NULL DEFAULT 0,
                    metadata JSONB
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_mw_snapshots_warehouse "
                "ON lg_mobile_warehouse_snapshots (tenant_id, mobile_warehouse_id)"
            )
        )

    if "lg_mobile_warehouse_snapshot_items" not in existing_tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_mobile_warehouse_snapshot_items (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    snapshot_id VARCHAR(36) NOT NULL,
                    product_id VARCHAR(36) NOT NULL,
                    condition VARCHAR(20),
                    quantity NUMERIC(18, 4) NOT NULL,
                    weight_kg NUMERIC(18, 4) NOT NULL DEFAULT 0,
                    FOREIGN KEY (snapshot_id)
                        REFERENCES lg_mobile_warehouse_snapshots(id)
                )
                """
            )
        )

    if "lg_mobile_warehouse_item_events" not in existing_tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_mobile_warehouse_item_events (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    mobile_warehouse_item_id VARCHAR(36) NOT NULL,
                    event_type VARCHAR(30) NOT NULL,
                    ledger_entry_id VARCHAR(36),
                    movement_id VARCHAR(36),
                    customer_id VARCHAR(36),
                    occurred_at TIMESTAMP NOT NULL,
                    created_by VARCHAR(36),
                    metadata JSONB,
                    FOREIGN KEY (mobile_warehouse_item_id)
                        REFERENCES lg_mobile_warehouse_items(id)
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_mw_item_events_item "
                "ON lg_mobile_warehouse_item_events (tenant_id, mobile_warehouse_item_id)"
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "lg_mobile_warehouses" in existing_tables:
        existing_columns = {
            col["name"] for col in inspector.get_columns("lg_mobile_warehouses")
        }
        if "stock_warehouse_id" in existing_columns:
            bind.execute(
                text("DROP INDEX IF EXISTS ix_lg_mobile_warehouses_stock_warehouse")
            )
            bind.execute(
                text("ALTER TABLE lg_mobile_warehouses DROP COLUMN stock_warehouse_id")
            )

    if "lg_warehouses" in existing_tables:
        existing_columns = {col["name"] for col in inspector.get_columns("lg_warehouses")}
        if "warehouse_type" in existing_columns:
            bind.execute(
                text("ALTER TABLE lg_warehouses DROP COLUMN warehouse_type")
            )
