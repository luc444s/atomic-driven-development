from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0044"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    tables = set(inspector.get_table_names())
    if "lg_zones" in tables:
        # Quitar FK de delivery points antes de dropear la tabla
        bind.execute(text(
            "ALTER TABLE lg_delivery_points DROP CONSTRAINT IF EXISTS fk_lg_delivery_point_zone"
        ))
        bind.execute(text(
            "ALTER TABLE lg_delivery_points DROP COLUMN IF EXISTS zone_id"
        ))
        bind.execute(text("DROP TABLE IF EXISTS lg_zones"))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text(
        "CREATE TABLE lg_zones ("
        "  id VARCHAR(36) NOT NULL PRIMARY KEY,"
        "  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants (id),"
        "  name VARCHAR(100) NOT NULL,"
        "  code VARCHAR(20) NOT NULL,"
        "  is_active BOOLEAN NOT NULL DEFAULT TRUE,"
        "  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()"
        ")"
    ))
    bind.execute(text(
        "ALTER TABLE lg_delivery_points ADD COLUMN IF NOT EXISTS zone_id VARCHAR(36)"
    ))
