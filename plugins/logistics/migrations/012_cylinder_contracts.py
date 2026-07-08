from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0012"


def upgrade(db) -> None:
    bind = db.connection()
    existing = {t for t in inspect(bind).get_table_names()}

    if "lg_cylinder_contracts" not in existing:
        bind.execute(
            text(
                """
                CREATE TABLE lg_cylinder_contracts (
                    id VARCHAR(36) NOT NULL,
                    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
                    branch_id VARCHAR(36) NULL REFERENCES branches(id),
                    contract_number VARCHAR(50),
                    contract_type VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
                    customer_id VARCHAR(36) NOT NULL REFERENCES crm_customers(id),
                    customer_snapshot JSON NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NULL,
                    renewal_type VARCHAR(20) NULL,
                    cylinder_type_id VARCHAR(36) NULL REFERENCES lg_gas_products(id),
                    cylinder_condition VARCHAR(50) NULL REFERENCES lg_cylinder_conditions(code),
                    quantity INTEGER NOT NULL,
                    unit_price NUMERIC(12, 4) NOT NULL,
                    signed_at TIMESTAMP NULL,
                    signed_by VARCHAR(120) NULL,
                    signature_type VARCHAR(20) NULL,
                    notes TEXT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_by VARCHAR(36) NOT NULL REFERENCES users(id),
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    terminated_at TIMESTAMP NULL,
                    termination_reason TEXT NULL,
                    PRIMARY KEY (id)
                )
                """
            )
        )

    if "lg_cylinder_contract_items" not in existing:
        bind.execute(
            text(
                """
                CREATE TABLE lg_cylinder_contract_items (
                    id VARCHAR(36) NOT NULL,
                    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
                    contract_id VARCHAR(36) NOT NULL REFERENCES lg_cylinder_contracts(id),
                    cylinder_id VARCHAR(36) NULL REFERENCES lg_cylinders(id),
                    serial VARCHAR(50) NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    unit_price NUMERIC(12, 4) NOT NULL,
                    delivered_at TIMESTAMP NULL,
                    returned_at TIMESTAMP NULL,
                    PRIMARY KEY (id)
                )
                """
            )
        )

    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_cylinder_contracts_tenant_id "
            "ON lg_cylinder_contracts (tenant_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_cylinder_contracts_contract_number "
            "ON lg_cylinder_contracts (contract_number)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_cylinder_contracts_customer_id "
            "ON lg_cylinder_contracts (customer_id)"
        )
    )
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_cylinder_contract_items_contract_id "
            "ON lg_cylinder_contract_items (contract_id)"
        )
    )
    bind.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_cylinder_contracts_contract_number "
            "ON lg_cylinder_contracts (contract_number) WHERE contract_number IS NOT NULL"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP TABLE IF EXISTS lg_cylinder_contract_items"))
    bind.execute(text("DROP TABLE IF EXISTS lg_cylinder_contracts"))
