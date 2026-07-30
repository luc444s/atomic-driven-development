from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0038"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_vehicle_location_events" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_vehicle_location_events ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "branch_id VARCHAR(36) NULL REFERENCES branches(id), "
                "session_id VARCHAR(36) NOT NULL REFERENCES lg_vehicle_sessions(id), "
                "route_id VARCHAR(36) NULL REFERENCES lg_routes(id), "
                "vehicle_id VARCHAR(36) NOT NULL REFERENCES lg_vehicles(id), "
                "driver_id VARCHAR(36) NOT NULL REFERENCES users(id), "
                "lat NUMERIC(10,7) NOT NULL, "
                "lng NUMERIC(10,7) NOT NULL, "
                "speed NUMERIC(10,2) NULL, "
                "heading NUMERIC(10,2) NULL, "
                "accuracy_meters NUMERIC(10,2) NULL, "
                "source VARCHAR(20) NOT NULL, "
                "recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "received_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
    bind.execute(text("CREATE INDEX IF NOT EXISTS ix_lg_vehicle_location_events_session_recorded_at ON lg_vehicle_location_events (tenant_id, session_id, recorded_at DESC)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS ix_lg_vehicle_location_events_vehicle_recorded_at ON lg_vehicle_location_events (tenant_id, vehicle_id, recorded_at DESC)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS ix_lg_vehicle_location_events_route_recorded_at ON lg_vehicle_location_events (tenant_id, route_id, recorded_at DESC)"))

    if "lg_route_control_states" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_route_control_states ("
                "session_id VARCHAR(36) PRIMARY KEY REFERENCES lg_vehicle_sessions(id), "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "route_id VARCHAR(36) NULL REFERENCES lg_routes(id), "
                "vehicle_id VARCHAR(36) NOT NULL REFERENCES lg_vehicles(id), "
                "active_stop_id VARCHAR(36) NULL REFERENCES lg_route_stops(id), "
                "active_stop_started_at TIMESTAMP WITH TIME ZONE NULL, "
                "current_stop_id VARCHAR(36) NULL REFERENCES lg_route_stops(id), "
                "current_stop_index INTEGER NULL, "
                "status VARCHAR(30) NOT NULL, "
                "last_lat NUMERIC(10,7) NULL, "
                "last_lng NUMERIC(10,7) NULL, "
                "last_speed NUMERIC(10,2) NULL, "
                "last_heading NUMERIC(10,2) NULL, "
                "last_recorded_at TIMESTAMP WITH TIME ZONE NULL, "
                "completed_stops INTEGER NOT NULL DEFAULT 0, "
                "total_stops INTEGER NOT NULL DEFAULT 0, "
                "progress_percent NUMERIC(5,2) NOT NULL DEFAULT 0, "
                "off_route BOOLEAN NOT NULL DEFAULT FALSE, "
                "next_stop_eta_minutes INTEGER NULL, "
                "geofence_state VARCHAR(20) NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
    bind.execute(text("CREATE INDEX IF NOT EXISTS ix_lg_route_control_states_route_id ON lg_route_control_states (route_id)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS ix_lg_route_control_states_vehicle_id ON lg_route_control_states (vehicle_id)"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS ix_lg_route_control_states_status ON lg_route_control_states (status)"))

    delivery_point_columns = {column["name"] for column in inspector.get_columns("lg_delivery_points")}
    if "gps_coordinates" not in delivery_point_columns:
        bind.execute(text("ALTER TABLE lg_delivery_points ADD COLUMN gps_coordinates JSON NULL"))

    route_operation_columns = {column["name"] for column in inspector.get_columns("lg_route_operations")}
    if "location_event_id" not in route_operation_columns:
        bind.execute(text("ALTER TABLE lg_route_operations ADD COLUMN location_event_id VARCHAR(36) NULL REFERENCES lg_vehicle_location_events(id)"))
    if "location_lat" not in route_operation_columns:
        bind.execute(text("ALTER TABLE lg_route_operations ADD COLUMN location_lat NUMERIC(10,7) NULL"))
    if "location_lng" not in route_operation_columns:
        bind.execute(text("ALTER TABLE lg_route_operations ADD COLUMN location_lng NUMERIC(10,7) NULL"))
    bind.execute(text("CREATE INDEX IF NOT EXISTS ix_lg_route_operations_location_event_id ON lg_route_operations (location_event_id)"))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_route_operations_location_event_id"))
    bind.execute(text("DROP TABLE IF EXISTS lg_route_control_states"))
    bind.execute(text("DROP TABLE IF EXISTS lg_vehicle_location_events"))
