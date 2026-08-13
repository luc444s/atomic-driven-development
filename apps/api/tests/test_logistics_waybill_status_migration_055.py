from __future__ import annotations

from importlib import import_module

from sqlalchemy import text

migration = import_module("plugins.logistics.migrations.055_waybill_statuses_v1")


def test_waybill_status_migration_055_updates_legacy_preview_statuses(db_session) -> None:
    db_session.execute(text("DELETE FROM lg_session_waybill_versions"))
    db_session.execute(
        text(
            "INSERT INTO lg_session_waybill_versions ("
            "id, tenant_id, session_id, version, status, regulatory_context, "
            "operational_hash, snapshot_schema_version, movement_ids_json, snapshot_json, "
            "change_event, change_reason, generated_at, created_at, updated_at"
            ") VALUES "
            "('a', 'tenant-1', 'session-1', 1, 'ACTIVE', 'ES_HACIENDA', 'h1', 1, '[]', '{}', "
            "'INITIAL_GENERATION', 'r1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), "
            "('b', 'tenant-1', 'session-1', 2, 'SUPERSEDED', 'ES_HACIENDA', 'h2', 1, '[]', '{}', "
            "'MOVEMENT_CHANGED', 'r2', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), "
            "('c', 'tenant-1', 'session-1', 3, 'ISSUED', 'ES_HACIENDA', 'h3', 1, '[]', '{}', "
            "'OFFICIAL_ISSUE', 'r3', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
    )
    db_session.commit()

    migration.upgrade(db_session)
    db_session.commit()

    rows = db_session.execute(
        text("SELECT id, status FROM lg_session_waybill_versions ORDER BY id")
    ).all()
    assert rows == [
        ("a", "ACTIVE_PREVIEW"),
        ("b", "SUPERSEDED_PREVIEW"),
        ("c", "ISSUED"),
    ]


def test_waybill_status_migration_055_downgrade_restores_legacy_names(db_session) -> None:
    db_session.execute(text("DELETE FROM lg_session_waybill_versions"))
    db_session.execute(
        text(
            "INSERT INTO lg_session_waybill_versions ("
            "id, tenant_id, session_id, version, status, regulatory_context, "
            "operational_hash, snapshot_schema_version, movement_ids_json, snapshot_json, "
            "change_event, change_reason, generated_at, created_at, updated_at"
            ") VALUES "
            "('a', 'tenant-1', 'session-1', 1, "
            "'ACTIVE_PREVIEW', 'ES_HACIENDA', 'h1', 1, '[]', '{}', "
            "'INITIAL_GENERATION', 'r1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), "
            "('b', 'tenant-1', 'session-1', 2, "
            "'SUPERSEDED_PREVIEW', 'ES_HACIENDA', 'h2', 1, '[]', '{}', "
            "'MOVEMENT_CHANGED', 'r2', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP), "
            "('c', 'tenant-1', 'session-1', 3, 'ISSUED', 'ES_HACIENDA', 'h3', 1, '[]', '{}', "
            "'OFFICIAL_ISSUE', 'r3', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )
    )
    db_session.commit()

    migration.downgrade(db_session)
    db_session.commit()

    rows = db_session.execute(
        text("SELECT id, status FROM lg_session_waybill_versions ORDER BY id")
    ).all()
    assert rows == [
        ("a", "ACTIVE"),
        ("b", "SUPERSEDED"),
        ("c", "ISSUED"),
    ]
