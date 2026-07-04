"""add is_operational_site to crm_customer_addresses

Revision ID: 20260703_2100
Revises: 20260703_2003
Create Date: 2026-07-03 21:00:00.000000
"""

from alembic import op


revision = "20260703_2100"
down_revision = "20260703_2003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE crm_customer_addresses "
        "ADD COLUMN IF NOT EXISTS is_operational_site BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE crm_customer_addresses "
        "ALTER COLUMN is_operational_site DROP DEFAULT"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE crm_customer_addresses "
        "DROP COLUMN IF EXISTS is_operational_site"
    )
