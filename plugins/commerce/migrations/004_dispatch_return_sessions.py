from sqlalchemy import inspect, text

revision = "0004"


def upgrade(db) -> None:
    bind = db.connection()
    columns = {c["name"] for c in inspect(bind).get_columns("com_dispatches")}

    if "session_id" not in columns:
        bind.execute(text(
            "ALTER TABLE com_dispatches "
            "ADD COLUMN session_id VARCHAR(36) "
            "REFERENCES lg_vehicle_sessions (id)"
        ))
    if "return_session_id" not in columns:
        bind.execute(text(
            "ALTER TABLE com_dispatches "
            "ADD COLUMN return_session_id VARCHAR(36) "
            "REFERENCES lg_vehicle_sessions (id)"
        ))

    indexes = {i["name"] for i in inspect(bind).get_indexes("com_dispatches")}
    if "ix_com_dispatches_session_id" not in indexes:
        bind.execute(text(
            "CREATE INDEX ix_com_dispatches_session_id "
            "ON com_dispatches (session_id)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_com_dispatches_session_id"))
    bind.execute(text("ALTER TABLE com_dispatches DROP COLUMN return_session_id"))
    bind.execute(text("ALTER TABLE com_dispatches DROP COLUMN session_id"))
