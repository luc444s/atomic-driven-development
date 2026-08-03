from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0044"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    dialect = bind.dialect.name

    tables = set(inspector.get_table_names())
    if "lg_zones" in tables:
        columns = {col["name"] for col in inspector.get_columns("lg_delivery_points")}
        if "zone_id" in columns:
            # SQLite no soporta DROP CONSTRAINT nombrado; el FK desaparece al quitar la columna.
            if dialect != "sqlite":
                bind.execute(
                    text(
                        "ALTER TABLE lg_delivery_points "
                        "DROP CONSTRAINT IF EXISTS fk_lg_delivery_point_zone"
                    )
                )
            bind.execute(text("ALTER TABLE lg_delivery_points DROP COLUMN zone_id"))
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
