"""drop value and label from crm_customer_contacts

Revision ID: 20260703_0007
Revises: 20260703_0006
Create Date: 2026-07-03 16:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_0007"
down_revision = "20260703_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("crm_customer_contacts", "value")


def downgrade() -> None:
    op.add_column(
        "crm_customer_contacts",
        sa.Column("value", sa.String(200), nullable=False, server_default=""),
    )
    op.alter_column("crm_customer_contacts", "value", server_default=None)
