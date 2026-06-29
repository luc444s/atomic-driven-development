from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0006"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "crm_customers" not in tables:
        return

    if "lg_delivery_points" in tables:
        columns = {column["name"] for column in inspector.get_columns("lg_delivery_points")}
        statements: list[str] = []
        if "contact_email" not in columns:
            statements.append(
                "ALTER TABLE lg_delivery_points ADD COLUMN contact_email VARCHAR(100)"
            )
        if "warehouse_id" not in columns:
            statements.append("ALTER TABLE lg_delivery_points ADD COLUMN warehouse_id VARCHAR(36)")
        if "address_id" not in columns:
            statements.append("ALTER TABLE lg_delivery_points ADD COLUMN address_id VARCHAR(36)")
        if "visit_day" not in columns:
            statements.append("ALTER TABLE lg_delivery_points ADD COLUMN visit_day VARCHAR(50)")
        if "time_window" not in columns:
            statements.append("ALTER TABLE lg_delivery_points ADD COLUMN time_window VARCHAR(50)")
        if "instructions" not in columns:
            statements.append("ALTER TABLE lg_delivery_points ADD COLUMN instructions VARCHAR(200)")
        if "service_time_min" not in columns:
            statements.append("ALTER TABLE lg_delivery_points ADD COLUMN service_time_min INTEGER")
        if "demand_units" not in columns:
            statements.append("ALTER TABLE lg_delivery_points ADD COLUMN demand_units INTEGER")
        if "demand_weight_kg" not in columns:
            statements.append(
                "ALTER TABLE lg_delivery_points ADD COLUMN demand_weight_kg NUMERIC(19, 4)"
            )
        if "agent_user_id" not in columns:
            statements.append("ALTER TABLE lg_delivery_points ADD COLUMN agent_user_id VARCHAR(36)")
        if "fiscal_operation_document" not in columns:
            statements.append(
                "ALTER TABLE lg_delivery_points ADD COLUMN fiscal_operation_document VARCHAR(50)"
            )
        if "fiscal_operation_type" not in columns:
            statements.append(
                "ALTER TABLE lg_delivery_points ADD COLUMN fiscal_operation_type VARCHAR(30)"
            )
        for statement in statements:
            bind.execute(text(statement))


def downgrade(db) -> None:
    return None
