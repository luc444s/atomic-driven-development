from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0023"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "lg_session_waybill_versions" not in tables:
        bind.execute(
            text(
                "CREATE TABLE lg_session_waybill_versions ("
                "id VARCHAR(36) PRIMARY KEY, "
                "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
                "session_id VARCHAR(36) NOT NULL REFERENCES lg_vehicle_sessions(id), "
                "previous_version_id VARCHAR(36) NULL REFERENCES lg_session_waybill_versions(id), "
                "version INTEGER NOT NULL, "
                "status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE', "
                "regulatory_context VARCHAR(40) NOT NULL DEFAULT 'ES_HACIENDA', "
                "generated_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "generated_by VARCHAR(36) NULL REFERENCES users(id), "
                "operational_hash VARCHAR(128) NOT NULL, "
                "snapshot_schema_version INTEGER NOT NULL DEFAULT 1, "
                "movement_ids_json TEXT NOT NULL DEFAULT '[]', "
                "snapshot_json TEXT NOT NULL, "
                "change_event VARCHAR(40) NOT NULL, "
                "change_reason TEXT NOT NULL, "
                "idempotency_key VARCHAR(120) NULL, "
                "created_at TIMESTAMP WITH TIME ZONE NOT NULL, "
                "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
                ")"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_session_waybill_versions_session "
                "ON lg_session_waybill_versions (session_id)"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_session_waybill_versions_status "
                "ON lg_session_waybill_versions (status)"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_session_waybill_versions_previous "
                "ON lg_session_waybill_versions (previous_version_id)"
            )
        )
        bind.execute(
            text(
                "CREATE INDEX ix_lg_session_waybill_versions_idempotency "
                "ON lg_session_waybill_versions (idempotency_key)"
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP TABLE IF EXISTS lg_session_waybill_versions"))
