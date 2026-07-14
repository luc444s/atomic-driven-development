from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0020"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "lg_cylinder_contract_items" in existing_tables:
        bind.execute(text("DROP TABLE lg_cylinder_contract_items"))

    if bind.dialect.name == "sqlite":
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_mov_assigned "
                "ON lg_movements (tenant_id, customer_id, movement_type, status) "
                "WHERE status = 'COMPLETADO' AND customer_id IS NOT NULL"
            )
        )
    else:
        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_mov_assigned "
                "ON lg_movements (tenant_id, customer_id, movement_type, status) "
                "INCLUDE (id) "
                "WHERE status = 'COMPLETADO' AND customer_id IS NOT NULL"
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_mov_assigned"))
