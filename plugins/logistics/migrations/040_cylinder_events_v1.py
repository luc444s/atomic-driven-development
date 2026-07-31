from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0040"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    tables = inspector.get_table_names()
    if "lg_cylinder_events" in tables:
        return

    bind.execute(text("""
        CREATE TABLE lg_cylinder_events (
            id VARCHAR(36) PRIMARY KEY,
            tenant_id VARCHAR(36) NOT NULL,
            cylinder_id VARCHAR(36) NOT NULL,
            event_type VARCHAR(30) NOT NULL,
            location_type VARCHAR(20) NOT NULL,
            location_id VARCHAR(36) NOT NULL,
            warehouse_id VARCHAR(36),
            session_id VARCHAR(36),
            customer_id VARCHAR(36),
            source_type VARCHAR(30) NOT NULL,
            source_id VARCHAR(36),
            occurred_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_by VARCHAR(36) NOT NULL
        )
    """))

    bind.execute(text(
        "CREATE INDEX ix_lg_cylinder_events_cylinder_time "
        "ON lg_cylinder_events (cylinder_id, occurred_at DESC, created_at DESC)"
    ))
    bind.execute(text(
        "CREATE INDEX ix_lg_cylinder_events_warehouse "
        "ON lg_cylinder_events (warehouse_id, occurred_at)"
    ))
    bind.execute(text(
        "CREATE INDEX ix_lg_cylinder_events_customer "
        "ON lg_cylinder_events (customer_id, occurred_at)"
    ))
    bind.execute(text(
        "CREATE INDEX ix_lg_cylinder_events_session "
        "ON lg_cylinder_events (session_id, occurred_at)"
    ))

    bind.execute(text(
        "ALTER TABLE lg_cylinder_events "
        "ADD CONSTRAINT fk_cylinder_events_tenant "
        "FOREIGN KEY (tenant_id) REFERENCES tenants (id)"
    ))
    bind.execute(text(
        "ALTER TABLE lg_cylinder_events "
        "ADD CONSTRAINT fk_cylinder_events_cylinder "
        "FOREIGN KEY (cylinder_id) REFERENCES lg_cylinders (id)"
    ))
    bind.execute(text(
        "ALTER TABLE lg_cylinder_events "
        "ADD CONSTRAINT fk_cylinder_events_warehouse "
        "FOREIGN KEY (warehouse_id) REFERENCES lg_warehouses (id)"
    ))
    bind.execute(text(
        "ALTER TABLE lg_cylinder_events "
        "ADD CONSTRAINT fk_cylinder_events_session "
        "FOREIGN KEY (session_id) REFERENCES lg_vehicle_sessions (id)"
    ))
    bind.execute(text(
        "ALTER TABLE lg_cylinder_events "
        "ADD CONSTRAINT fk_cylinder_events_customer "
        "FOREIGN KEY (customer_id) REFERENCES crm_customers (id)"
    ))
    bind.execute(text(
        "ALTER TABLE lg_cylinder_events "
        "ADD CONSTRAINT fk_cylinder_events_user "
        "FOREIGN KEY (created_by) REFERENCES users (id)"
    ))
