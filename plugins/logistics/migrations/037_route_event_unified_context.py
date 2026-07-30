from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0037"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_route_operations" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("lg_route_operations")}

    if "context_type" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_operations "
                "ADD COLUMN context_type VARCHAR(30) NULL"
            )
        )
    if "customer_id" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_operations "
                "ADD COLUMN customer_id VARCHAR(36) NULL REFERENCES crm_customers(id)"
            )
        )
    if "customer_name_snapshot" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_operations "
                "ADD COLUMN customer_name_snapshot VARCHAR(120) NULL"
            )
        )
    if "warehouse_id" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_operations "
                "ADD COLUMN warehouse_id VARCHAR(36) NULL REFERENCES lg_warehouses(id)"
            )
        )
    if "warehouse_name_snapshot" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_operations "
                "ADD COLUMN warehouse_name_snapshot VARCHAR(100) NULL"
            )
        )

    bind.execute(
        text(
            "UPDATE lg_route_operations "
            "SET context_type = 'STOP' "
            "WHERE context_type IS NULL AND route_stop_id IS NOT NULL"
        )
    )

    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_operations_context_type "
            "ON lg_route_operations (context_type)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_operations_customer "
            "ON lg_route_operations (customer_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_operations_warehouse "
            "ON lg_route_operations (warehouse_id)"
        )
    )
    bind.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_route_operation_session_idempotency "
            "ON lg_route_operations (session_id, idempotency_key)"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_route_operations" not in tables:
        return

    bind.execute(
        text(
            "DROP INDEX IF EXISTS uq_lg_route_operation_session_idempotency"
        )
    )
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_route_operations_warehouse"))
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_route_operations_customer"))
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_route_operations_context_type"))
