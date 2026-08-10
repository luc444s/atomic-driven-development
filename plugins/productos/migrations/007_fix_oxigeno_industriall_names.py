from __future__ import annotations

from sqlalchemy import text

revision = "0007"


def upgrade(db) -> None:
    bind = db.connection()
    bind.execute(
        text(
            "UPDATE prod_products "
            "SET name = replace(name, 'Industriall', 'Industrial'), "
            "sku = replace(sku, 'INDUSTRIALL', 'INDUSTRIAL') "
            "WHERE name LIKE '%Industriall%' OR sku LIKE '%INDUSTRIALL%'"
        )
    )
