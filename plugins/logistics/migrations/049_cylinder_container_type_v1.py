from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0049"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("lg_cylinders")}
    if "container_type" not in columns:
        bind.execute(
            text(
                "ALTER TABLE lg_cylinders "
                "ADD COLUMN container_type VARCHAR(20) NOT NULL DEFAULT 'CYLINDER'"
            )
        )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_cylinders_container_type "
            "ON lg_cylinders (container_type)"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cylinders_container_type"))
    bind.execute(text("ALTER TABLE lg_cylinders DROP COLUMN IF EXISTS container_type"))
