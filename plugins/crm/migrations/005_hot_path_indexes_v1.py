from __future__ import annotations

from sqlalchemy import text

revision = "0005"


INDEX_STATEMENTS = [
    (
        "ix_crm_customers_tenant_active_leg",
        "CREATE INDEX IF NOT EXISTS ix_crm_customers_tenant_active_leg "
        "ON crm_customers (tenant_id, is_active, legal_name)",
    ),
    (
        "ix_crm_addr_tenant_customer_cr",
        "CREATE INDEX IF NOT EXISTS ix_crm_addr_tenant_customer_cr "
        "ON crm_customer_addresses (tenant_id, customer_id, created_at ASC)",
    ),
    (
        "ix_crm_contacts_tenant_cust_act",
        "CREATE INDEX IF NOT EXISTS ix_crm_contacts_tenant_cust_act "
        "ON crm_customer_contacts ("
        "tenant_id, customer_id, is_active, contact_purpose, "
        "is_primary DESC, created_at ASC"
        ")",
    ),
    (
        "ix_crm_comm_tenant_cust_role",
        "CREATE INDEX IF NOT EXISTS ix_crm_comm_tenant_cust_role "
        "ON crm_customer_commercial_assignments ("
        "tenant_id, customer_id, is_active, assignment_role, "
        "is_primary DESC, created_at ASC"
        ")",
    ),
    (
        "ix_crm_pricing_tenant_customer_cr",
        "CREATE INDEX IF NOT EXISTS ix_crm_pricing_tenant_customer_cr "
        "ON crm_customer_pricing_terms (tenant_id, customer_id, created_at DESC)",
    ),
    (
        "ix_crm_bank_tenant_customer_cr",
        "CREATE INDEX IF NOT EXISTS ix_crm_bank_tenant_customer_cr "
        "ON crm_customer_bank_accounts (tenant_id, customer_id, created_at DESC)",
    ),
]


def upgrade(db) -> None:
    bind = db.connection()
    for _, statement in INDEX_STATEMENTS:
        bind.execute(text(statement))


def downgrade(db) -> None:
    bind = db.connection()
    for index_name, _ in reversed(INDEX_STATEMENTS):
        bind.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
