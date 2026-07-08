from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0014"


def upgrade(db) -> None:
    bind = db.connection()

    if bind.dialect.name != "postgresql":
        return

    inspector = inspect(bind)
    existing_tables = {t for t in inspector.get_table_names()}

    if "lg_brands" not in existing_tables:
        return

    # Drop all FK constraints referencing lg_* catalog tables
    old_tables = ("lg_brands", "lg_gas_products", "lg_cylinder_conditions")
    for attempt in [
        "lg_cylinders",
        "lg_cylinder_average_weights",
        "lg_cylinder_contracts",
    ]:
        if attempt not in existing_tables:
            continue
        bind.execute(
            text(
                f"""
                DO $$
                DECLARE
                    rec RECORD;
                BEGIN
                    FOR rec IN
                        SELECT con.conname, con.conrelid::regclass AS tbl
                        FROM pg_catalog.pg_constraint con
                        JOIN pg_catalog.pg_class rel ON rel.oid = con.conrelid
                        WHERE rel.relname = '{attempt}'
                          AND con.contype = 'f'
                          AND con.confrelid IN (
                              SELECT oid FROM pg_catalog.pg_class
                              WHERE relname IN {old_tables}
                          )
                    LOOP
                        EXECUTE 'ALTER TABLE ' || rec.tbl || ' DROP CONSTRAINT ' || rec.conname;
                    END LOOP;
                END;
                $$;
                """
            )
        )

    # 1. Migrate lg_cylinders
    if "lg_cylinders" in existing_tables:
        bind.execute(
            text(
                """UPDATE lg_cylinders t
                   SET brand_id = nt.id
                   FROM lg_brands ot
                   JOIN prod_brands nt ON nt.code = ot.code AND nt.tenant_id = ot.tenant_id
                   WHERE t.brand_id = ot.id"""
            )
        )
        bind.execute(
            text(
                """UPDATE lg_cylinders t
                   SET gas_group_id = nt.id
                   FROM lg_gas_products ot
                   JOIN prod_products nt ON nt.sku = ot.code AND nt.tenant_id = ot.tenant_id
                   WHERE t.gas_group_id = ot.id"""
            )
        )

    # 2. Migrate lg_cylinder_average_weights
    if "lg_cylinder_average_weights" in existing_tables:
        bind.execute(
            text(
                """UPDATE lg_cylinder_average_weights t
                   SET brand_id = nt.id
                   FROM lg_brands ot
                   JOIN prod_brands nt ON nt.code = ot.code AND nt.tenant_id = ot.tenant_id
                   WHERE t.brand_id = ot.id"""
            )
        )
        bind.execute(
            text(
                """UPDATE lg_cylinder_average_weights t
                   SET gas_group_id = nt.id
                   FROM lg_gas_products ot
                   JOIN prod_products nt ON nt.sku = ot.code AND nt.tenant_id = ot.tenant_id
                   WHERE t.gas_group_id = ot.id"""
            )
        )

    # 3. Migrate lg_cylinder_contracts
    if "lg_cylinder_contracts" in existing_tables:
        bind.execute(
            text(
                """UPDATE lg_cylinder_contracts t
                   SET cylinder_type_id = nt.id
                   FROM lg_gas_products ot
                   JOIN prod_products nt ON nt.sku = ot.code AND nt.tenant_id = ot.tenant_id
                   WHERE t.cylinder_type_id = ot.id"""
            )
        )

    # 4. Drop old tables
    for table_name in sorted(["lg_brands", "lg_gas_products", "lg_cylinder_conditions"]):
        if table_name in existing_tables:
            bind.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
