from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0043"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    columns = {col["name"] for col in inspector.get_columns("lg_warehouses")}
    if "is_primary" not in columns:
        bind.execute(text(
            "ALTER TABLE lg_warehouses ADD COLUMN is_primary BOOLEAN NOT NULL DEFAULT FALSE"
        ))
    # Almacén principal inicial: FUENTE DE PIEDRA-MALAGA (code '1')
    bind.execute(text(
        "UPDATE lg_warehouses SET is_primary = TRUE WHERE code = '1'"
    ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("ALTER TABLE lg_warehouses DROP COLUMN IF EXISTS is_primary"))
