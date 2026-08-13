from __future__ import annotations

from sqlalchemy import inspect, text

revision = "055"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "lg_session_waybill_versions" not in tables:
        return None

    # Legacy preview rows used ACTIVE/SUPERSEDED before official document states existed.
    bind.execute(
        text(
            "UPDATE lg_session_waybill_versions "
            "SET status = 'ACTIVE_PREVIEW' "
            "WHERE status = 'ACTIVE'"
        )
    )
    bind.execute(
        text(
            "UPDATE lg_session_waybill_versions "
            "SET status = 'SUPERSEDED_PREVIEW' "
            "WHERE status = 'SUPERSEDED'"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "lg_session_waybill_versions" not in tables:
        return None

    bind.execute(
        text(
            "UPDATE lg_session_waybill_versions "
            "SET status = 'ACTIVE' "
            "WHERE status = 'ACTIVE_PREVIEW'"
        )
    )
    bind.execute(
        text(
            "UPDATE lg_session_waybill_versions "
            "SET status = 'SUPERSEDED' "
            "WHERE status = 'SUPERSEDED_PREVIEW'"
        )
    )
