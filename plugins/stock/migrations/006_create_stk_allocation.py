from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0006"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "stk_allocation" not in tables:
        bind.execute(text("""
            CREATE TABLE stk_allocation (
                id                  VARCHAR(36) PRIMARY KEY,
                tenant_id           VARCHAR(36) NOT NULL REFERENCES tenants(id),
                allocation_group_id VARCHAR(36),
                product_id          VARCHAR(36) NOT NULL REFERENCES prod_products(id),
                warehouse_id        VARCHAR(36) NOT NULL REFERENCES lg_warehouses(id),
                quantity            NUMERIC(12,3) NOT NULL,
                remaining_quantity  NUMERIC(12,3) NOT NULL,
                reference_type      VARCHAR(50) NOT NULL,
                reference_id        VARCHAR(255) NOT NULL,
                status              VARCHAR(20) NOT NULL DEFAULT 'active',
                created_by          VARCHAR(36) NOT NULL REFERENCES users(id),
                created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
                expires_at          TIMESTAMPTZ,
                released_at         TIMESTAMPTZ,
                released_by         VARCHAR(36) REFERENCES users(id),
                release_reason      TEXT,
                CONSTRAINT ck_stk_allocation_qty_pos CHECK (quantity > 0),
                CONSTRAINT ck_stk_allocation_rem_range CHECK (
                    remaining_quantity >= 0 AND remaining_quantity <= quantity
                ),
                CONSTRAINT ck_stk_allocation_status CHECK (
                    status IN ('active','partially_consumed',
                               'consumed','released','expired')
                ),
                CONSTRAINT uq_stk_allocation_ref UNIQUE (
                    tenant_id, reference_type, reference_id,
                    product_id, warehouse_id
                )
            )
        """))
        bind.execute(text(
            "CREATE INDEX ix_stk_allocation_tenant_group "
            "ON stk_allocation(tenant_id, allocation_group_id)"
        ))
        bind.execute(text(
            "CREATE INDEX ix_stk_allocation_tenant_expires "
            "ON stk_allocation(tenant_id, expires_at) "
            "WHERE status = 'active' AND expires_at IS NOT NULL"
        ))
        bind.execute(text(
            "CREATE INDEX ix_stk_allocation_tenant_status "
            "ON stk_allocation(tenant_id, status)"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    inspect_conn = inspect(bind)
    if "stk_allocation" in inspect_conn.get_table_names():
        bind.execute(text("DROP TABLE IF EXISTS stk_allocation CASCADE"))
