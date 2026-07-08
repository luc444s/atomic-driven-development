from __future__ import annotations

from sqlalchemy import inspect, text
from sqlalchemy.schema import CreateColumn

from plugins.logistics.backend.models import LogisticsCylinder
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
        text(
            "SELECT c.id, c.tenant_id, c.gas_group_id "
            "FROM lg_cylinders c "
            "WHERE c.product_id IS NULL AND c.gas_group_id IS NOT NULL"
        )
    ).all()
    for row in rows:
        gas_code = db.scalar(
            text("SELECT code FROM lg_gas_products WHERE id = :gid AND tenant_id = :tid"),
            {"gid": row.gas_group_id, "tid": row.tenant_id},
        )
        if gas_code is None:
            continue
        product = db.scalar(
            text(
                "SELECT id FROM prod_products "
                "WHERE tenant_id = :tid AND sku = :code LIMIT 1"
            ),
            {"tid": row.tenant_id, "code": gas_code},
        )
        if product is None:
            continue
        db.execute(
            text("UPDATE lg_cylinders SET product_id = :product_id WHERE id = :cylinder_id"),
            {"product_id": product, "cylinder_id": row.id},
        )


def downgrade(db) -> None:
    bind = db.connection()
    existing_columns = {column["name"] for column in inspect(bind).get_columns("lg_cylinders")}
    if "product_id" not in existing_columns:
        return
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cylinders_product_id"))
    bind.execute(text("ALTER TABLE lg_cylinders DROP COLUMN product_id"))
