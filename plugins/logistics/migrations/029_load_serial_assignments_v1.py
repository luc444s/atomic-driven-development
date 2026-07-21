from __future__ import annotations

from sqlalchemy import text

revision = "0029"


def upgrade(db) -> None:
    bind = db.connection()
    bind.execute(
        text(
            "CREATE TABLE IF NOT EXISTS lg_load_serial_assignments ("
            "id VARCHAR(36) PRIMARY KEY, "
            "tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id), "
            "session_id VARCHAR(36) NOT NULL REFERENCES lg_vehicle_sessions(id), "
            "product_id VARCHAR(36) NOT NULL REFERENCES prod_products(id), "
            "cylinder_id VARCHAR(36) NOT NULL REFERENCES lg_cylinders(id), "
            "cylinder_serial VARCHAR(50) NOT NULL, "
            "assignment_status VARCHAR(20) NOT NULL, "
            "selected_by VARCHAR(36) NOT NULL REFERENCES users(id), "
            "selected_at TIMESTAMP WITH TIME ZONE NOT NULL, "
            "confirmed_by_operation_id VARCHAR(36) NULL REFERENCES lg_logistics_operations(id), "
            "confirmed_at TIMESTAMP WITH TIME ZONE NULL, "
            "released_at TIMESTAMP WITH TIME ZONE NULL, "
            "release_reason VARCHAR(30) NULL, "
            "notes TEXT NULL, "
            "updated_at TIMESTAMP WITH TIME ZONE NOT NULL"
            ")"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_load_serial_assignments_session_id "
            "ON lg_load_serial_assignments (session_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_load_serial_assignments_product_id "
            "ON lg_load_serial_assignments (product_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_load_serial_assignments_cylinder_id "
            "ON lg_load_serial_assignments (cylinder_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_load_serial_assignments_status "
            "ON lg_load_serial_assignments (assignment_status)"
        )
    )
    bind.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_lg_load_serial_assignments_cylinder_active "
            "ON lg_load_serial_assignments (cylinder_id) "
            "WHERE assignment_status IN ('SELECTED', 'CONFIRMED')"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP TABLE IF EXISTS lg_load_serial_assignments"))
