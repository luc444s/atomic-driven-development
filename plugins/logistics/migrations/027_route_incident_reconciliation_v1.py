from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0027"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_route_incidents" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("lg_route_incidents")}

    if "related_route_operation_id" in columns and "related_operation_id" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_incidents "
                "RENAME COLUMN related_route_operation_id TO related_operation_id"
            )
        )
    if "incident_type" in columns and "type" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_incidents "
                "RENAME COLUMN incident_type TO type"
            )
        )
    if "resolved_by" in columns and "closed_by" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_incidents "
                "RENAME COLUMN resolved_by TO closed_by"
            )
        )
    if "resolved_at" in columns and "closed_at" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_incidents "
                "RENAME COLUMN resolved_at TO closed_at"
            )
        )

    columns = {column["name"] for column in inspector.get_columns("lg_route_incidents")}
    if "corrective_operation_id" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_route_incidents "
                "ADD COLUMN corrective_operation_id VARCHAR(36) NULL REFERENCES lg_route_operations(id)"
            )
        )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_route_incidents_corrective_operation "
            "ON lg_route_incidents (corrective_operation_id)"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_route_incidents" not in tables:
        return

    bind.execute(text("DROP INDEX IF EXISTS ix_lg_route_incidents_corrective_operation"))
