from __future__ import annotations

from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateColumn
from sqlalchemy.sql.schema import Table

from plugins.logistics.backend.models import (
    LogisticsBrand,
    LogisticsCylinder,
    LogisticsCylinderLabelHistory,
    LogisticsCylinderOwnership,
    LogisticsCylinderRetimbrado,
    LogisticsCylinderService,
    LogisticsGasProduct,
    LogisticsScanLog,
    LogisticsServiceType,
)

revision = "0004"


def _create_table(table: Table | Any, bind) -> None:
    table.create(bind=bind, checkfirst=True)


def _drop_table(table: Table | Any, bind) -> None:
    table.drop(bind=bind, checkfirst=True)


def _add_missing_column(bind, table: Table, column_name: str) -> None:
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
        LogisticsGasProduct.__table__,
        LogisticsBrand.__table__,
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
        LogisticsBrand.__table__,
        LogisticsGasProduct.__table__,
    ]:
        _drop_table(table, bind)
