from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0024"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_route_operations" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_route_operations ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "session_id VARCHAR(36) NOT NULL REFERENCES lg_vehicle_sessions(id), "
                "route_stop_id VARCHAR(36) NULL REFERENCES lg_route_stops(id), "
                "operation_type VARCHAR(30) NOT NULL, "
                "status VARCHAR(30) NOT NULL DEFAULT 'DRAFT', "
                "movement_ids_json TEXT NOT NULL DEFAULT '[]', "
                "idempotency_key VARCHAR(120) NOT NULL, "
                "notes TEXT NULL, "
                "performed_by VARCHAR(36) NULL REFERENCES users(id), "
                "performed_at TIMESTAMP WITH TIME ZONE NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(text("CREATE INDEX ix_lg_route_operations_session ON lg_route_operations (session_id)"))
        bind.execute(text("CREATE INDEX ix_lg_route_operations_status ON lg_route_operations (status)"))
        bind.execute(text("CREATE INDEX ix_lg_route_operations_type ON lg_route_operations (operation_type)"))

    if "lg_route_operation_items" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_route_operation_items ("
                "id VARCHAR(36) PRIMARY KEY, "
                "route_operation_id VARCHAR(36) NOT NULL REFERENCES lg_route_operations(id), "
                "product_id VARCHAR(36) NOT NULL REFERENCES prod_products(id), "
                "product_name VARCHAR(200) NOT NULL, "
                "quantity NUMERIC(19,4) NOT NULL, "
                "direction VARCHAR(10) NOT NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_route_operation_items_operation "
                "ON lg_route_operation_items (route_operation_id)"
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP TABLE IF EXISTS lg_route_operation_items"))
    bind.execute(text("DROP TABLE IF EXISTS lg_route_operations"))
