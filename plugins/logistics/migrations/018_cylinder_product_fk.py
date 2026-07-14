from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0018"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "lg_cylinders" not in existing_tables:
        return

    existing_columns = {col["name"] for col in inspector.get_columns("lg_cylinders")}
    if "product_id" not in existing_columns:
        return
    if bind.dialect.name == "sqlite":
        return

    existing_fks = {
        fk["constrained_columns"][0] for fk in inspector.get_foreign_keys("lg_cylinders")
    }
    if "product_id" not in existing_fks:
        bind.execute(
            text(
                "ALTER TABLE lg_cylinders "
                "ADD CONSTRAINT fk_lg_cylinders_product "
                "FOREIGN KEY (product_id) REFERENCES prod_products(id)"
            )
        )


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "lg_cylinders" not in existing_tables:
        return
    if bind.dialect.name == "sqlite":
        return

    existing_fks = {
        fk["constrained_columns"][0] for fk in inspector.get_foreign_keys("lg_cylinders")
    }
    if "product_id" in existing_fks:
        bind.execute(text("ALTER TABLE lg_cylinders DROP CONSTRAINT fk_lg_cylinders_product"))
