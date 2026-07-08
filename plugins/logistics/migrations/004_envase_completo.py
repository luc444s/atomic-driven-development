from __future__ import annotations

from sqlalchemy import Column, DateTime, MetaData, Numeric, String, Table, Boolean, UniqueConstraint, inspect, text
from sqlalchemy.schema import CreateColumn

from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderLabelHistory,
    LogisticsCylinderOwnership,
    LogisticsCylinderRetimbrado,
    LogisticsCylinderService,
    LogisticsScanLog,
    LogisticsServiceType,
)

revision = "0004"

_meta = MetaData()

_LegacyGasProduct = Table(
    "lg_gas_products", _meta,
    Column("id", String(36), primary_key=True),
    Column("tenant_id", String(36), nullable=False, index=True),
    Column("name", String(120), nullable=False),
    Column("code", String(20), nullable=False),
    Column("content_kg", Numeric(10, 2), nullable=True),
    Column("unit", String(20), nullable=True),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("tenant_id", "code", name="uq_lg_gas_product_tenant_code"),
)

_LegacyBrand = Table(
    "lg_brands", _meta,
    Column("id", String(36), primary_key=True),
    Column("tenant_id", String(36), nullable=False, index=True),
    Column("name", String(100), nullable=False),
    Column("code", String(20), nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("tenant_id", "code", name="uq_lg_brand_tenant_code"),
)


def _create_table(table, bind) -> None:
    table.create(bind=bind, checkfirst=True)


def _drop_table(table, bind) -> None:
    table.drop(bind=bind, checkfirst=True)


def _add_missing_column(bind, table, column_name: str) -> None:
    existing_columns = {column["name"] for column in inspect(bind).get_columns(table.name)}
    if column_name in existing_columns:
        return
    column = table.columns[column_name]
    compiled = str(CreateColumn(column).compile(dialect=bind.dialect))
    bind.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {compiled}"))


def upgrade(db) -> None:
    bind = db.connection()
    cylinder_table = LogisticsCylinder.__table__
    for column_name in [
        "description",
        "barcode1",
        "barcode2",
        "gas_group_id",
        "content_kg",
        "volume_m3",
        "condition",
        "brand_id",
        "cost",
        "price",
        "country_code",
        "box_number",
        "is_service",
        "adr_package_type",
        "adr_weight_kg",
        "adr_merchandise",
        "adr_tunnel",
        "adr_subline",
        "adr_factor",
        "adr_points",
        "adr_unit_measure",
    ]:
        _add_missing_column(bind, cylinder_table, column_name)

    for table in [
        _LegacyGasProduct,
        _LegacyBrand,
        LogisticsServiceType.__table__,
        LogisticsCylinderRetimbrado.__table__,
        LogisticsCylinderOwnership.__table__,
        LogisticsCylinderLabelHistory.__table__,
        LogisticsScanLog.__table__,
        LogisticsCylinderService.__table__,
    ]:
        _create_table(table, bind)

    bind.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_cylinder_tenant_barcode1_idx "
            "ON lg_cylinders (tenant_id, barcode1) WHERE barcode1 IS NOT NULL"
        )
    )
    bind.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_cylinder_tenant_barcode2_idx "
            "ON lg_cylinders (tenant_id, barcode2) WHERE barcode2 IS NOT NULL"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS uq_lg_cylinder_tenant_barcode2_idx"))
    bind.execute(text("DROP INDEX IF EXISTS uq_lg_cylinder_tenant_barcode1_idx"))
    for table in [
        LogisticsCylinderService.__table__,
        LogisticsScanLog.__table__,
        LogisticsCylinderLabelHistory.__table__,
        LogisticsCylinderOwnership.__table__,
        LogisticsCylinderRetimbrado.__table__,
        LogisticsServiceType.__table__,
        _LegacyBrand,
        _LegacyGasProduct,
    ]:
        _drop_table(table, bind)
