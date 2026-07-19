from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0021"


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_vehicles" in tables:
        vehicle_columns = _column_names(inspector, "lg_vehicles")
        if "mobile_warehouse_id" not in vehicle_columns:
            bind.execute(
                text(
                    "ALTER TABLE lg_vehicles "
                    "ADD COLUMN mobile_warehouse_id VARCHAR(36) NULL REFERENCES lg_warehouses(id)"
                )
            )

    if "lg_vehicle_sessions" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_vehicle_sessions ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "branch_id VARCHAR(36) NULL REFERENCES branches(id), "
                "vehicle_id VARCHAR(36) NOT NULL REFERENCES lg_vehicles(id), "
                "driver_id VARCHAR(36) NOT NULL REFERENCES users(id), "
                "origin_warehouse_id VARCHAR(36) NOT NULL REFERENCES lg_warehouses(id), "
                "mobile_warehouse_id VARCHAR(36) NOT NULL REFERENCES lg_warehouses(id), "
                "route_id VARCHAR(36) NULL REFERENCES lg_routes(id), "
                "status VARCHAR(40) NOT NULL DEFAULT 'DRAFT', "
                "opened_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "ready_at TIMESTAMP WITH TIME ZONE NULL, "
                "departed_at TIMESTAMP WITH TIME ZONE NULL, "
                "returned_at TIMESTAMP WITH TIME ZONE NULL, "
                "closed_at TIMESTAMP WITH TIME ZONE NULL, "
                "planned_weight_kg NUMERIC(19,4) NULL, "
                "loaded_weight_kg NUMERIC(19,4) NULL, "
                "closing_notes TEXT NULL, "
                "created_by VARCHAR(36) NOT NULL REFERENCES users(id), "
                "updated_by VARCHAR(36) NOT NULL REFERENCES users(id), "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(text("CREATE INDEX ix_lg_vehicle_sessions_tenant ON lg_vehicle_sessions (tenant_id)"))
        bind.execute(text("CREATE INDEX ix_lg_vehicle_sessions_vehicle ON lg_vehicle_sessions (vehicle_id)"))
        bind.execute(text("CREATE INDEX ix_lg_vehicle_sessions_status ON lg_vehicle_sessions (status)"))

    if "lg_load_plans" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_load_plans ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "session_id VARCHAR(36) NOT NULL REFERENCES lg_vehicle_sessions(id), "
                "status VARCHAR(30) NOT NULL DEFAULT 'DRAFT', "
                "notes TEXT NULL, "
                "created_by VARCHAR(36) NOT NULL REFERENCES users(id), "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(text("CREATE INDEX ix_lg_load_plans_session ON lg_load_plans (session_id)"))

    if "lg_load_plan_items" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_load_plan_items ("
                "id VARCHAR(36) PRIMARY KEY, "
                "load_plan_id VARCHAR(36) NOT NULL REFERENCES lg_load_plans(id), "
                "product_id VARCHAR(36) NOT NULL REFERENCES prod_products(id), "
                "product_name VARCHAR(200) NOT NULL, "
                "planned_quantity NUMERIC(19,4) NOT NULL, "
                "planned_weight_kg NUMERIC(19,4) NULL, "
                "source_warehouse_id VARCHAR(36) NOT NULL REFERENCES lg_warehouses(id), "
                "notes TEXT NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(text("CREATE INDEX ix_lg_load_plan_items_plan ON lg_load_plan_items (load_plan_id)"))

    if "lg_logistics_operations" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_logistics_operations ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "session_id VARCHAR(36) NOT NULL REFERENCES lg_vehicle_sessions(id), "
                "route_stop_id VARCHAR(36) NULL REFERENCES lg_route_stops(id), "
                "movement_type VARCHAR(30) NOT NULL, "
                "status VARCHAR(30) NOT NULL DEFAULT 'DRAFT', "
                "external_movement_id VARCHAR(100) NULL, "
                "idempotency_key VARCHAR(120) NOT NULL, "
                "performed_by VARCHAR(36) NULL REFERENCES users(id), "
                "performed_at TIMESTAMP WITH TIME ZONE NULL, "
                "notes TEXT NULL, "
                "evidence_json TEXT NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(text("CREATE INDEX ix_lg_logistics_operations_session ON lg_logistics_operations (session_id)"))
        bind.execute(text("CREATE INDEX ix_lg_logistics_operations_status ON lg_logistics_operations (status)"))

    if "lg_logistics_operation_items" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_logistics_operation_items ("
                "id VARCHAR(36) PRIMARY KEY, "
                "operation_id VARCHAR(36) NOT NULL REFERENCES lg_logistics_operations(id), "
                "product_id VARCHAR(36) NOT NULL REFERENCES prod_products(id), "
                "product_name VARCHAR(200) NOT NULL, "
                "quantity NUMERIC(19,4) NOT NULL, "
                "weight_kg NUMERIC(19,4) NULL, "
                "notes TEXT NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(text("CREATE INDEX ix_lg_logistics_operation_items_op ON lg_logistics_operation_items (operation_id)"))

    if "lg_session_reconciliations" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_session_reconciliations ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "session_id VARCHAR(36) NOT NULL REFERENCES lg_vehicle_sessions(id), "
                "status VARCHAR(30) NOT NULL DEFAULT 'MATCHED', "
                "counted_by VARCHAR(36) NULL REFERENCES users(id), "
                "counted_at TIMESTAMP WITH TIME ZONE NULL, "
                "closed_by VARCHAR(36) NULL REFERENCES users(id), "
                "closed_at TIMESTAMP WITH TIME ZONE NULL, "
                "notes TEXT NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(text("CREATE INDEX ix_lg_session_reconciliations_session ON lg_session_reconciliations (session_id)"))

    if "lg_inventory_discrepancies" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_inventory_discrepancies ("
                "id VARCHAR(36) PRIMARY KEY, "
                "reconciliation_id VARCHAR(36) NOT NULL REFERENCES lg_session_reconciliations(id), "
                "product_id VARCHAR(36) NOT NULL REFERENCES prod_products(id), "
                "product_name VARCHAR(200) NOT NULL, "
                "expected_quantity NUMERIC(19,4) NOT NULL, "
                "counted_quantity NUMERIC(19,4) NOT NULL, "
                "difference_quantity NUMERIC(19,4) NOT NULL, "
                "status VARCHAR(40) NOT NULL DEFAULT 'OPEN', "
                "resolution_notes TEXT NULL, "
                "resolved_by VARCHAR(36) NULL REFERENCES users(id), "
                "resolved_at TIMESTAMP WITH TIME ZONE NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(text("CREATE INDEX ix_lg_inventory_discrepancies_reconciliation ON lg_inventory_discrepancies (reconciliation_id)"))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP TABLE IF EXISTS lg_inventory_discrepancies"))
    bind.execute(text("DROP TABLE IF EXISTS lg_session_reconciliations"))
    bind.execute(text("DROP TABLE IF EXISTS lg_logistics_operation_items"))
    bind.execute(text("DROP TABLE IF EXISTS lg_logistics_operations"))
    bind.execute(text("DROP TABLE IF EXISTS lg_load_plan_items"))
    bind.execute(text("DROP TABLE IF EXISTS lg_load_plans"))
    bind.execute(text("DROP TABLE IF EXISTS lg_vehicle_sessions"))
