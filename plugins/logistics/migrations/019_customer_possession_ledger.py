from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0019"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "lg_customer_cylinder_ledger" not in existing_tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_customer_cylinder_ledger (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    customer_id VARCHAR(36) NOT NULL,
                    contract_id VARCHAR(36),
                    source_type VARCHAR(30) NOT NULL,
                    source_id VARCHAR(36) NOT NULL,
                    event_type VARCHAR(30) NOT NULL,
                    product_id VARCHAR(36),
                    product_name VARCHAR(200),
                    condition VARCHAR(20),
                    quantity NUMERIC(19, 4) NOT NULL,
                    cylinder_id VARCHAR(36),
                    trace_mode VARCHAR(20) NOT NULL DEFAULT 'AGGREGATE',
                    occurred_at TIMESTAMP NOT NULL,
                    created_by VARCHAR(36) NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL,
                    CONSTRAINT uq_lg_customer_cylinder_ledger_source_event
                        UNIQUE (tenant_id, source_type, source_id, event_type)
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_lg_customer_cylinder_ledger_customer "
                "ON lg_customer_cylinder_ledger (tenant_id, customer_id)"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_lg_customer_cylinder_ledger_product "
                "ON lg_customer_cylinder_ledger (tenant_id, product_id)"
            )
        )

    if "lg_mobile_warehouse_items" in existing_tables:
        if bind.dialect.name == "sqlite":
            bind.execute(
                text(
                    """
                    INSERT OR IGNORE INTO lg_customer_cylinder_ledger (
                        id,
                        tenant_id,
                        customer_id,
                        contract_id,
                        source_type,
                        source_id,
                        event_type,
                        product_id,
                        product_name,
                        condition,
                        quantity,
                        cylinder_id,
                        trace_mode,
                        occurred_at,
                        created_by,
                        notes,
                        created_at
                    )
                    SELECT
                        item.id,
                        item.tenant_id,
                        item.customer_id,
                        NULL,
                        CASE
                            WHEN item.status = 'DELIVERED' THEN 'MOBILE_DELIVERY'
                            WHEN item.status = 'PICKED_UP' THEN 'MOBILE_PICKUP'
                            ELSE 'MOBILE_EVENT'
                        END,
                        item.id,
                        CASE
                            WHEN item.status = 'DELIVERED' THEN 'IN_TO_CUSTOMER'
                            WHEN item.status = 'PICKED_UP' THEN 'OUT_FROM_CUSTOMER'
                            ELSE 'UNKNOWN'
                        END,
                        item.product_id,
                        item.product_name,
                        NULL,
                        item.quantity,
                        item.cylinder_id,
                        CASE
                            WHEN item.cylinder_id IS NOT NULL THEN 'SERIALIZED'
                            ELSE 'AGGREGATE'
                        END,
                        COALESCE(item.unloaded_at, item.loaded_at, item.created_at),
                        COALESCE(item.unloaded_by, item.loaded_by),
                        item.notes,
                        COALESCE(item.unloaded_at, item.loaded_at, item.created_at)
                    FROM lg_mobile_warehouse_items item
                    WHERE item.customer_id IS NOT NULL
                      AND item.status IN ('DELIVERED', 'PICKED_UP')
                    """
                )
            )
        else:
            bind.execute(
                text(
                    """
                    INSERT INTO lg_customer_cylinder_ledger (
                        id,
                        tenant_id,
                        customer_id,
                        contract_id,
                        source_type,
                        source_id,
                        event_type,
                        product_id,
                        product_name,
                        condition,
                        quantity,
                        cylinder_id,
                        trace_mode,
                        occurred_at,
                        created_by,
                        notes,
                        created_at
                    )
                    SELECT
                        item.id,
                        item.tenant_id,
                        item.customer_id,
                        NULL,
                        CASE
                            WHEN item.status = 'DELIVERED' THEN 'MOBILE_DELIVERY'
                            WHEN item.status = 'PICKED_UP' THEN 'MOBILE_PICKUP'
                            ELSE 'MOBILE_EVENT'
                        END,
                        item.id,
                        CASE
                            WHEN item.status = 'DELIVERED' THEN 'IN_TO_CUSTOMER'
                            WHEN item.status = 'PICKED_UP' THEN 'OUT_FROM_CUSTOMER'
                            ELSE 'UNKNOWN'
                        END,
                        item.product_id,
                        item.product_name,
                        NULL,
                        item.quantity,
                        item.cylinder_id,
                        CASE
                            WHEN item.cylinder_id IS NOT NULL THEN 'SERIALIZED'
                            ELSE 'AGGREGATE'
                        END,
                        COALESCE(item.unloaded_at, item.loaded_at, item.created_at),
                        COALESCE(item.unloaded_by, item.loaded_by),
                        item.notes,
                        COALESCE(item.unloaded_at, item.loaded_at, item.created_at)
                    FROM lg_mobile_warehouse_items item
                    WHERE item.customer_id IS NOT NULL
                      AND item.status IN ('DELIVERED', 'PICKED_UP')
                    ON CONFLICT ON CONSTRAINT uq_lg_customer_cylinder_ledger_source_event DO NOTHING
                    """
                )
            )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    if "lg_customer_cylinder_ledger" in existing_tables:
        bind.execute(text("DROP TABLE lg_customer_cylinder_ledger"))
