from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0026"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_route_incidents" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_route_incidents ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "session_id VARCHAR(36) NOT NULL REFERENCES lg_vehicle_sessions(id), "
                "route_stop_id VARCHAR(36) NULL REFERENCES lg_route_stops(id), "
                "related_operation_id VARCHAR(36) NULL REFERENCES lg_route_operations(id), "
                "type VARCHAR(40) NOT NULL, "
                "status VARCHAR(20) NOT NULL DEFAULT 'OPEN', "
                "corrective_operation_id VARCHAR(36) NULL REFERENCES lg_route_operations(id), "
                "notes TEXT NULL, "
                "created_by VARCHAR(36) NOT NULL REFERENCES users(id), "
                "closed_by VARCHAR(36) NULL REFERENCES users(id), "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "closed_at TIMESTAMP WITH TIME ZONE NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_route_incidents_session "
                "ON lg_route_incidents (session_id)"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_route_incidents_stop "
                "ON lg_route_incidents (route_stop_id)"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_route_incidents_status "
                "ON lg_route_incidents (status)"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_route_incidents_corrective_operation "
                "ON lg_route_incidents (corrective_operation_id)"
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP TABLE IF EXISTS lg_route_incidents"))
