"""logistics mobile warehouses

Revision ID: 20260709_0009
Revises: 20260708_0008
Create Date: 2026-07-09 17:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260709_0009"
down_revision = "20260708_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lg_mobile_warehouses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=True),
        sa.Column("warehouse_id", sa.String(length=36), nullable=False),
        sa.Column("vehicle_id", sa.String(length=36), nullable=False),
        sa.Column("driver_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["lg_vehicles.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["lg_warehouses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lg_mobile_warehouses_tenant_id"), "lg_mobile_warehouses", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouses_branch_id"), "lg_mobile_warehouses", ["branch_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouses_warehouse_id"), "lg_mobile_warehouses", ["warehouse_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouses_vehicle_id"), "lg_mobile_warehouses", ["vehicle_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouses_driver_id"), "lg_mobile_warehouses", ["driver_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouses_status"), "lg_mobile_warehouses", ["status"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouses_created_by"), "lg_mobile_warehouses", ["created_by"], unique=False)

    op.create_table(
        "lg_mobile_warehouse_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("mobile_warehouse_id", sa.String(length=36), nullable=False),
        sa.Column("source_warehouse_id", sa.String(length=36), nullable=True),
        sa.Column("destination_warehouse_id", sa.String(length=36), nullable=True),
        sa.Column("movement_id", sa.String(length=36), nullable=True),
        sa.Column("cylinder_id", sa.String(length=36), nullable=True),
        sa.Column("product_id", sa.String(length=36), nullable=True),
        sa.Column("product_name", sa.String(length=200), nullable=True),
        sa.Column("quantity", sa.Numeric(19, 4), nullable=False),
        sa.Column("weight_kg", sa.Numeric(19, 4), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("loaded_by", sa.String(length=36), nullable=False),
        sa.Column("unloaded_by", sa.String(length=36), nullable=True),
        sa.Column("loaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cylinder_id"], ["lg_cylinders.id"]),
        sa.ForeignKeyConstraint(["destination_warehouse_id"], ["lg_warehouses.id"]),
        sa.ForeignKeyConstraint(["loaded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["mobile_warehouse_id"], ["lg_mobile_warehouses.id"]),
        sa.ForeignKeyConstraint(["movement_id"], ["lg_movements.id"]),
        sa.ForeignKeyConstraint(["source_warehouse_id"], ["lg_warehouses.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["unloaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lg_mobile_warehouse_items_tenant_id"), "lg_mobile_warehouse_items", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouse_items_mobile_warehouse_id"), "lg_mobile_warehouse_items", ["mobile_warehouse_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouse_items_source_warehouse_id"), "lg_mobile_warehouse_items", ["source_warehouse_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouse_items_destination_warehouse_id"), "lg_mobile_warehouse_items", ["destination_warehouse_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouse_items_movement_id"), "lg_mobile_warehouse_items", ["movement_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouse_items_cylinder_id"), "lg_mobile_warehouse_items", ["cylinder_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouse_items_product_id"), "lg_mobile_warehouse_items", ["product_id"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouse_items_status"), "lg_mobile_warehouse_items", ["status"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouse_items_loaded_by"), "lg_mobile_warehouse_items", ["loaded_by"], unique=False)
    op.create_index(op.f("ix_lg_mobile_warehouse_items_unloaded_by"), "lg_mobile_warehouse_items", ["unloaded_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_unloaded_by"), table_name="lg_mobile_warehouse_items")
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_loaded_by"), table_name="lg_mobile_warehouse_items")
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_status"), table_name="lg_mobile_warehouse_items")
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_product_id"), table_name="lg_mobile_warehouse_items")
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_cylinder_id"), table_name="lg_mobile_warehouse_items")
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_movement_id"), table_name="lg_mobile_warehouse_items")
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_destination_warehouse_id"), table_name="lg_mobile_warehouse_items")
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_source_warehouse_id"), table_name="lg_mobile_warehouse_items")
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_mobile_warehouse_id"), table_name="lg_mobile_warehouse_items")
    op.drop_index(op.f("ix_lg_mobile_warehouse_items_tenant_id"), table_name="lg_mobile_warehouse_items")
    op.drop_table("lg_mobile_warehouse_items")

    op.drop_index(op.f("ix_lg_mobile_warehouses_created_by"), table_name="lg_mobile_warehouses")
    op.drop_index(op.f("ix_lg_mobile_warehouses_status"), table_name="lg_mobile_warehouses")
    op.drop_index(op.f("ix_lg_mobile_warehouses_driver_id"), table_name="lg_mobile_warehouses")
    op.drop_index(op.f("ix_lg_mobile_warehouses_vehicle_id"), table_name="lg_mobile_warehouses")
    op.drop_index(op.f("ix_lg_mobile_warehouses_warehouse_id"), table_name="lg_mobile_warehouses")
    op.drop_index(op.f("ix_lg_mobile_warehouses_branch_id"), table_name="lg_mobile_warehouses")
    op.drop_index(op.f("ix_lg_mobile_warehouses_tenant_id"), table_name="lg_mobile_warehouses")
    op.drop_table("lg_mobile_warehouses")
