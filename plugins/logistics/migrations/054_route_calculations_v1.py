from __future__ import annotations

from sqlalchemy import inspect, text

revision = "054"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_route_calculations" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_route_calculations ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "route_id VARCHAR(36) NULL REFERENCES lg_routes(id), "
                "session_id VARCHAR(36) NULL REFERENCES lg_vehicle_sessions(id), "
                "planning_reservation_id VARCHAR(36) NULL REFERENCES lg_planning_reservations(id), "
                "provider_stack VARCHAR(50) NOT NULL, "
                "input_hash VARCHAR(64) NOT NULL, "
                "ordered_stop_ids_json JSON NOT NULL, "
                "totals_json JSON NOT NULL, "
                "violations_json JSON NOT NULL, "
                "polyline TEXT NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "created_by VARCHAR(36) NOT NULL REFERENCES users(id)"
                ")"
            )
        )

    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_calculations_route_id "
            "ON lg_route_calculations (route_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_calculations_session_id "
            "ON lg_route_calculations (session_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_calculations_planning_reservation_id "
            "ON lg_route_calculations (planning_reservation_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_calculations_input_hash "
            "ON lg_route_calculations (input_hash)"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP TABLE IF EXISTS lg_route_calculations"))
