"""ventas quote_drafts and quote_items

Revision ID: 20260724_0011
Revises: 20260715_0010
Create Date: 2026-07-24 05:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260724_0011"
down_revision = "20260715_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ventas_quote_drafts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("customer_id", sa.String(36), sa.ForeignKey("crm_customers.id"), nullable=False, index=True),
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT", index=True),
        sa.Column("delivery_date", sa.Date(), nullable=False),
        sa.Column("delivery_time", sa.Time(), nullable=True),
        sa.Column("vehicle_id", sa.String(36), sa.ForeignKey("lg_vehicles.id"), nullable=True, index=True),
        sa.Column("vehicle_plate", sa.String(20), nullable=True),
        sa.Column("conditions", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "ventas_quote_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("quote_draft_id", sa.String(36), sa.ForeignKey("ventas_quote_drafts.id"), nullable=False, index=True),
        sa.Column("product_id", sa.String(36), sa.ForeignKey("prod_products.id"), nullable=False, index=True),
        sa.Column("product_name", sa.String(255), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_weight_kg", sa.Numeric(10, 3), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("quote_draft_id", "product_id", name="uq_quote_item_draft_product"),
    )


def downgrade() -> None:
    op.drop_table("ventas_quote_items")
    op.drop_table("ventas_quote_drafts")
