from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0032"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_planning_reservations" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_planning_reservations ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "branch_id VARCHAR(36) NULL REFERENCES branches(id), "
                "vehicle_id VARCHAR(36) NOT NULL REFERENCES lg_vehicles(id), "
                "origin_warehouse_id VARCHAR(36) NOT NULL REFERENCES lg_warehouses(id), "
                "planned_start_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "planned_end_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "expected_load_summary JSON NOT NULL, "
                "expected_weight_total NUMERIC(19,4) NULL, "
                "expected_volume_total NUMERIC(19,4) NULL, "
                "service_type VARCHAR(50) NULL, "
                "route_id VARCHAR(36) NULL REFERENCES lg_routes(id), "
                "driver_id VARCHAR(36) NULL REFERENCES users(id), "
                "adr_required BOOLEAN NOT NULL DEFAULT FALSE, "
                "notes TEXT NULL, "
                "status VARCHAR(30) NOT NULL DEFAULT 'PLANNED', "
                "conflict_reason VARCHAR(40) NULL, "
                "permit_override BOOLEAN NOT NULL DEFAULT FALSE, "
                "override_reason TEXT NULL, "
                "linked_session_id VARCHAR(36) NULL REFERENCES lg_vehicle_sessions(id), "
                "actual_start_at TIMESTAMP WITH TIME ZONE NULL, "
                "actual_end_at TIMESTAMP WITH TIME ZONE NULL, "
                "actual_load_summary JSON NULL, "
                "created_by VARCHAR(36) NOT NULL REFERENCES users(id), "
                "updated_by VARCHAR(36) NOT NULL REFERENCES users(id), "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_planning_reservations_vehicle "
                "ON lg_planning_reservations (vehicle_id)"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_planning_reservations_window "
                "ON lg_planning_reservations (planned_start_at, planned_end_at)"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_planning_reservations_status "
                "ON lg_planning_reservations (status)"
            )
        )

    if bind.dialect.name == "postgresql":
        bind.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gist"))
        bind.execute(
            text(
                "ALTER TABLE lg_planning_reservations "
                "DROP CONSTRAINT IF EXISTS ex_lg_planning_vehicle_window_active"
            )
        )
        bind.execute(
            text(
                "ALTER TABLE lg_planning_reservations "
                "ADD CONSTRAINT ex_lg_planning_vehicle_window_active "
                "EXCLUDE USING gist ("
                "vehicle_id WITH =, "
                "tstzrange(planned_start_at, planned_end_at) WITH &&"
                ") "
                "WHERE (status IN ('PLANNED', 'READY', 'IN_PROGRESS'))"
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    if bind.dialect.name == "postgresql":
        bind.execute(
            text(
                "ALTER TABLE lg_planning_reservations "
                "DROP CONSTRAINT IF EXISTS ex_lg_planning_vehicle_window_active"
            )
        )
    bind.execute(text("DROP TABLE IF EXISTS lg_planning_reservations"))
