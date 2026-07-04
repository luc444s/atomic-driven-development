"""extend crm_customer_contacts with person fields, phone, email, address_id

Revision ID: 20260703_0006
Revises: 20260629_0005
Create Date: 2026-07-03 15:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_0006"
down_revision = "20260629_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("crm_customer_contacts", sa.Column("full_name", sa.String(200), nullable=True))
    op.add_column("crm_customer_contacts", sa.Column("role", sa.String(100), nullable=True))
    op.add_column("crm_customer_contacts", sa.Column("phone", sa.String(50), nullable=True))
    op.add_column("crm_customer_contacts", sa.Column("email", sa.String(200), nullable=True))
    op.add_column("crm_customer_contacts", sa.Column("address_id", sa.String(36), nullable=True))
    op.create_index("ix_crm_customer_contacts_address_id", "crm_customer_contacts", ["address_id"])
    op.create_foreign_key(
        "fk_crm_customer_contacts_address_id",
        "crm_customer_contacts",
        "crm_customer_addresses",
        ["address_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_crm_customer_contacts_address_id", "crm_customer_contacts", type_="foreignkey"
    )
    op.drop_index("ix_crm_customer_contacts_address_id", table_name="crm_customer_contacts")
    op.drop_column("crm_customer_contacts", "address_id")
    op.drop_column("crm_customer_contacts", "email")
    op.drop_column("crm_customer_contacts", "phone")
    op.drop_column("crm_customer_contacts", "role")
    op.drop_column("crm_customer_contacts", "full_name")
