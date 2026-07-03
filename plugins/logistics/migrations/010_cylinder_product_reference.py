from __future__ import annotations

from sqlalchemy import inspect, select, text
from sqlalchemy.schema import CreateColumn

from plugins.logistics.backend.models import LogisticsCylinder, LogisticsGasProduct
from plugins.productos.backend.models import Product

revision = "0010"


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
    _add_missing_column(bind, cylinder_table, "product_id")
    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_cylinders_product_id "
            "ON lg_cylinders (product_id)"
        )
    )

    rows = db.execute(
        select(
            LogisticsCylinder.id,
            LogisticsCylinder.tenant_id,
            LogisticsCylinder.gas_group_id,
        ).where(
            LogisticsCylinder.product_id.is_(None),
            LogisticsCylinder.gas_group_id.is_not(None),
        )
    ).all()
    for row in rows:
        gas = db.scalar(
            select(LogisticsGasProduct).where(
                LogisticsGasProduct.tenant_id == row.tenant_id,
                LogisticsGasProduct.id == row.gas_group_id,
            )
        )
        if gas is None:
            continue
        product = db.scalar(
            select(Product).where(
                Product.tenant_id == row.tenant_id,
                Product.sku == gas.code,
            )
        )
        if product is None:
            continue
        db.execute(
            text("UPDATE lg_cylinders SET product_id = :product_id WHERE id = :cylinder_id"),
            {"product_id": product.id, "cylinder_id": row.id},
        )


def downgrade(db) -> None:
    bind = db.connection()
    existing_columns = {column["name"] for column in inspect(bind).get_columns("lg_cylinders")}
    if "product_id" not in existing_columns:
        return
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cylinders_product_id"))
    bind.execute(text("ALTER TABLE lg_cylinders DROP COLUMN product_id"))
