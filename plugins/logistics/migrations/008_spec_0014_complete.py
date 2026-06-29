from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0008"


def _table_names(bind) -> set[str]:
    return set(inspect(bind).get_table_names())


def _column_names(bind, table_name: str) -> set[str]:
    return {column["name"] for column in inspect(bind).get_columns(table_name)}


def upgrade(db) -> None:
    bind = db.connection()
    tables = _table_names(bind)

    if "lg_routes" in tables:
        columns = _column_names(bind, "lg_routes")
        if "gps_start_coordinates" not in columns:
            bind.execute(text("ALTER TABLE lg_routes ADD COLUMN gps_start_coordinates JSON"))

    if "lg_route_stops" in tables:
        columns = _column_names(bind, "lg_route_stops")
        if "gps_coordinates" not in columns:
            bind.execute(text("ALTER TABLE lg_route_stops ADD COLUMN gps_coordinates JSON"))

    if "lg_movements" in tables:
        columns = _column_names(bind, "lg_movements")
        if "dispatched_at" not in columns:
            bind.execute(text("ALTER TABLE lg_movements ADD COLUMN dispatched_at TIMESTAMP"))

    if "lg_movement_items" in tables:
        columns = _column_names(bind, "lg_movement_items")
        if "product_id" not in columns:
            bind.execute(text("ALTER TABLE lg_movement_items ADD COLUMN product_id VARCHAR(36)"))
        if "product_name" not in columns:
            bind.execute(text("ALTER TABLE lg_movement_items ADD COLUMN product_name VARCHAR(200)"))

    if "lg_plan_preloads" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_plan_preloads (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    warehouse_id VARCHAR(36) NOT NULL,
                    branch_id VARCHAR(36),
                    preload_date DATE NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    notes TEXT,
                    created_by VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_plan_preloads_active ON lg_plan_preloads(tenant_id, warehouse_id, preload_date) WHERE status IN ('PENDIENTE', 'ACEPTADA')"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_lg_plan_preloads_status ON lg_plan_preloads(warehouse_id, status, preload_date)"
            )
        )

    if "lg_plan_preload_items" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_plan_preload_items (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    preload_id VARCHAR(36) NOT NULL,
                    order_item_id VARCHAR(36) NOT NULL,
                    product_id VARCHAR(36) NOT NULL,
                    product_name VARCHAR(200),
                    quantity_planned NUMERIC(19, 4) NOT NULL DEFAULT 0,
                    quantity_loaded NUMERIC(19, 4) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_lg_plan_preload_items_product ON lg_plan_preload_items(product_id, preload_id)"
            )
        )

    if "lg_reception_incidents" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_reception_incidents (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    movement_id VARCHAR(36) NOT NULL,
                    cylinder_id VARCHAR(36),
                    reason_code VARCHAR(50) NOT NULL,
                    description TEXT,
                    created_by VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP
                )
                """
            )
        )

    if "lg_equipment" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_equipment (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    name VARCHAR(120) NOT NULL,
                    equipment_type VARCHAR(50),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_equipment_tenant_name ON lg_equipment(tenant_id, name)"
            )
        )

    if "lg_movement_equipment" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_movement_equipment (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    movement_id VARCHAR(36) NOT NULL,
                    equipment_id VARCHAR(36) NOT NULL,
                    assigned_at TIMESTAMP,
                    returned_at TIMESTAMP,
                    notes TEXT
                )
                """
            )
        )

    if "lg_vehicle_route_restrictions" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_vehicle_route_restrictions (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    vehicle_id VARCHAR(36) NOT NULL,
                    route_id VARCHAR(36) NOT NULL,
                    restriction_type VARCHAR(10) NOT NULL DEFAULT 'ALLOW',
                    created_at TIMESTAMP
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_vehicle_route_restriction ON lg_vehicle_route_restrictions(tenant_id, vehicle_id, route_id)"
            )
        )

    if "lg_driver_parameters" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_driver_parameters (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    driver_id VARCHAR(36) NOT NULL,
                    param_key VARCHAR(100) NOT NULL,
                    param_value TEXT,
                    updated_at TIMESTAMP
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_driver_parameter_key ON lg_driver_parameters(tenant_id, driver_id, param_key)"
            )
        )

    if "lg_vehicle_delivery_points" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_vehicle_delivery_points (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    vehicle_id VARCHAR(36) NOT NULL,
                    delivery_point_id VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_vehicle_delivery_point ON lg_vehicle_delivery_points(tenant_id, vehicle_id, delivery_point_id)"
            )
        )

    if "lg_route_weekdays" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_route_weekdays (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    route_id VARCHAR(36) NOT NULL,
                    weekday INTEGER NOT NULL,
                    created_at TIMESTAMP
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_route_weekday ON lg_route_weekdays(route_id, weekday)"
            )
        )

    if "lg_adr_product_config" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_adr_product_config (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    product_id VARCHAR(36) NOT NULL,
                    adr_class VARCHAR(50),
                    adr_points NUMERIC(19, 4),
                    adr_tunnel VARCHAR(10),
                    max_quantity NUMERIC(19, 4),
                    valid_from DATE NOT NULL,
                    valid_to DATE,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_adr_product_config_from ON lg_adr_product_config(tenant_id, product_id, valid_from)"
            )
        )

    if "lg_adr_incompatibilities" not in tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_adr_incompatibilities (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL,
                    product_id_1 VARCHAR(36) NOT NULL,
                    product_id_2 VARCHAR(36) NOT NULL,
                    created_at TIMESTAMP
                )
                """
            )
        )
        bind.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_adr_incompatibility_pair ON lg_adr_incompatibilities(tenant_id, product_id_1, product_id_2)"
            )
        )


def downgrade(db) -> None:
    return None
