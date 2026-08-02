from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0042"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    # ── lg_cylinder_contracts: política de exceso ──
    contract_columns = {col["name"] for col in inspector.get_columns("lg_cylinder_contracts")}
    if "excess_wait_days" not in contract_columns:
        bind.execute(text(
            "ALTER TABLE lg_cylinder_contracts "
            "ADD COLUMN excess_wait_days INTEGER NOT NULL DEFAULT 3"
        ))
        bind.execute(text(
            "ALTER TABLE lg_cylinder_contracts "
            "ADD COLUMN auto_renew_on_excess BOOLEAN NOT NULL DEFAULT TRUE"
        ))
        bind.execute(text(
            "ALTER TABLE lg_cylinder_contracts "
            "ADD COLUMN source_contract_id VARCHAR(36)"
        ))
        bind.execute(text(
            "ALTER TABLE lg_cylinder_contracts "
            "ADD CONSTRAINT fk_lg_contract_source "
            "FOREIGN KEY (source_contract_id) REFERENCES lg_cylinder_contracts (id)"
        ))

    # ── lg_contract_excess_tracking: estado vivo del exceso ──
    tables = set(inspector.get_table_names())
    if "lg_contract_excess_tracking" not in tables:
        bind.execute(text(
            "CREATE TABLE lg_contract_excess_tracking ("
            "  id VARCHAR(36) NOT NULL PRIMARY KEY,"
            "  tenant_id VARCHAR(36) NOT NULL REFERENCES tenants (id),"
            "  customer_id VARCHAR(36) NOT NULL REFERENCES crm_customers (id),"
            "  cylinder_type_id VARCHAR(36) NOT NULL REFERENCES prod_products (id),"
            "  excess_qty INTEGER NOT NULL,"
            "  first_detected_at TIMESTAMP WITH TIME ZONE NOT NULL,"
            "  last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL,"
            "  excess_wait_days INTEGER NOT NULL,"
            "  auto_renew_on_excess BOOLEAN NOT NULL,"
            "  base_unit_price NUMERIC(12, 4) NOT NULL,"
            "  base_contract_type VARCHAR(50) NOT NULL,"
            "  status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',"
            "  resolved_reason VARCHAR(200),"
            "  created_contract_id VARCHAR(36) REFERENCES lg_cylinder_contracts (id),"
            "  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),"
            "  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()"
            ")"
        ))
        bind.execute(text(
            "CREATE UNIQUE INDEX uq_lg_contract_excess_active "
            "ON lg_contract_excess_tracking (tenant_id, customer_id, cylinder_type_id) "
            "WHERE status = 'ACTIVE'"
        ))
        bind.execute(text(
            "CREATE INDEX ix_lg_contract_excess_status "
            "ON lg_contract_excess_tracking (status, last_seen_at)"
        ))
        bind.execute(text(
            "CREATE INDEX ix_lg_contract_excess_customer "
            "ON lg_contract_excess_tracking (customer_id)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP TABLE IF EXISTS lg_contract_excess_tracking"))
    bind.execute(text("ALTER TABLE lg_cylinder_contracts DROP COLUMN IF EXISTS source_contract_id"))
    bind.execute(text("ALTER TABLE lg_cylinder_contracts DROP COLUMN IF EXISTS auto_renew_on_excess"))
    bind.execute(text("ALTER TABLE lg_cylinder_contracts DROP COLUMN IF EXISTS excess_wait_days"))
