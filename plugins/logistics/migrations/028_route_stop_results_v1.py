from __future__ import annotations

from sqlalchemy import text

revision = "0028"


def upgrade(db) -> None:
    bind = db.connection()
    bind.execute(
        text(
            "CREATE TABLE IF NOT EXISTS lg_route_stop_results ("
            "id VARCHAR(36) PRIMARY KEY, "
            "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
            "session_id VARCHAR(36) NOT NULL REFERENCES lg_vehicle_sessions(id), "
            "route_stop_id VARCHAR(36) NOT NULL REFERENCES lg_route_stops(id), "
            "status VARCHAR(20) NOT NULL, "
            "completion_percent NUMERIC(5,2) NOT NULL DEFAULT 0, "
            "outcome_type VARCHAR(40) NOT NULL, "
            "driver_note TEXT NULL, "
            "created_by VARCHAR(36) NOT NULL REFERENCES users(id), "
            "updated_by VARCHAR(36) NOT NULL REFERENCES users(id), "
            "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
            "updated_at TIMESTAMP WITH TIME ZONE NOT NULL, "
            "UNIQUE (session_id, route_stop_id)"
            ")"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_stop_results_session_id "
            "ON lg_route_stop_results (session_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_stop_results_route_stop_id "
            "ON lg_route_stop_results (route_stop_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_stop_results_status "
            "ON lg_route_stop_results (status)"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP TABLE IF EXISTS lg_route_stop_results"))
