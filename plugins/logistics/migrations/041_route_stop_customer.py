from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0041"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    columns = {col["name"] for col in inspector.get_columns("lg_route_stops")}

    if "customer_id" not in columns:
        bind.execute(text(
            "ALTER TABLE lg_route_stops ADD COLUMN customer_id VARCHAR(36)"
        ))
        bind.execute(text(
            "CREATE INDEX ix_lg_route_stops_customer ON lg_route_stops (customer_id)"
        ))
        bind.execute(text(
            "ALTER TABLE lg_route_stops "
            "ADD CONSTRAINT fk_lg_route_stops_customer "
            "FOREIGN KEY (customer_id) REFERENCES crm_customers (id)"
        ))

    if "customer_name_snapshot" not in columns:
        bind.execute(text(
            "ALTER TABLE lg_route_stops ADD COLUMN customer_name_snapshot VARCHAR(120)"
        ))
