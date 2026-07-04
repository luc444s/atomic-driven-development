"""extend crm contacts and add commercial assignments

Revision ID: 20260703_2200
Revises: 20260703_2100
Create Date: 2026-07-03 22:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_2200"
down_revision = "20260703_2100"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "crm_customer_contacts",
        sa.Column(
            "contact_purpose",
            sa.String(length=30),
            nullable=False,
            server_default="GENERAL",
        ),
    )
    op.add_column(
        "crm_customer_contacts",
        sa.Column("notes", sa.String(length=250), nullable=True),
    )
    op.alter_column("crm_customer_contacts", "contact_purpose", server_default=None)

    op.create_table(
        "crm_customer_commercial_assignments",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("customer_id", sa.String(length=36), nullable=False),
        sa.Column("address_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("assignment_role", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.String(length=250), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["address_id"], ["crm_customer_addresses.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["crm_customers.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_crm_customer_commercial_assignments_tenant_id",
        "crm_customer_commercial_assignments",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_crm_customer_commercial_assignments_customer_id",
        "crm_customer_commercial_assignments",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_crm_customer_commercial_assignments_address_id",
        "crm_customer_commercial_assignments",
        ["address_id"],
        unique=False,
    )
    op.create_index(
        "ix_crm_customer_commercial_assignments_user_id",
        "crm_customer_commercial_assignments",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_crm_customer_commercial_assignments_user_id",
        table_name="crm_customer_commercial_assignments",
    )
    op.drop_index(
        "ix_crm_customer_commercial_assignments_address_id",
        table_name="crm_customer_commercial_assignments",
    )
    op.drop_index(
        "ix_crm_customer_commercial_assignments_customer_id",
        table_name="crm_customer_commercial_assignments",
    )
    op.drop_index(
        "ix_crm_customer_commercial_assignments_tenant_id",
        table_name="crm_customer_commercial_assignments",
    )
    op.drop_table("crm_customer_commercial_assignments")
    op.drop_column("crm_customer_contacts", "notes")
    op.drop_column("crm_customer_contacts", "contact_purpose")
