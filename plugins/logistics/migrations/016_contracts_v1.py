from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0016"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "lg_contract_types" not in existing_tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_contract_types (
                    code VARCHAR(50) NOT NULL PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    duration_unit VARCHAR(20) NOT NULL,
                    duration_value INTEGER NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE
                )
                """
            )
        )

    bind.execute(
        text(
            """
            INSERT INTO lg_contract_types (code, name, duration_unit, duration_value, is_active)
            VALUES
                ('DAILY', 'Diario', 'DAY', 1, TRUE),
                ('MONTHLY', 'Mensual', 'MONTH', 1, TRUE),
                ('ANNUAL', 'Anual', 'YEAR', 1, TRUE)
            ON CONFLICT (code) DO UPDATE
            SET name = EXCLUDED.name,
                duration_unit = EXCLUDED.duration_unit,
                duration_value = EXCLUDED.duration_value,
                is_active = EXCLUDED.is_active
            """
        )
    )

    if "lg_cylinder_contract_history" not in existing_tables:
        bind.execute(
            text(
                """
                CREATE TABLE lg_cylinder_contract_history (
                    id VARCHAR(36) NOT NULL PRIMARY KEY,
                    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
                    contract_id VARCHAR(36) NOT NULL REFERENCES lg_cylinder_contracts(id),
                    event_type VARCHAR(50) NOT NULL,
                    description VARCHAR(500) NULL,
                    occurred_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    created_by VARCHAR(120) NULL
                )
                """
            )
        )

    if "lg_cylinder_contracts" in existing_tables:
        columns = {c["name"] for c in inspector.get_columns("lg_cylinder_contracts")}
        statements: list[str] = []

        if "warehouse_id" not in columns:
            statements.append(
                "ALTER TABLE lg_cylinder_contracts ADD COLUMN warehouse_id VARCHAR(36)"
            )
        if "document_type_code" not in columns:
            statements.append(
                "ALTER TABLE lg_cylinder_contracts ADD COLUMN "
                "document_type_code INTEGER NOT NULL DEFAULT 4"
            )
        if "document_prefix" not in columns:
            statements.append(
                "ALTER TABLE lg_cylinder_contracts ADD COLUMN "
                "document_prefix VARCHAR(5) NOT NULL DEFAULT 'CT'"
            )
        if "series" not in columns:
            statements.append("ALTER TABLE lg_cylinder_contracts ADD COLUMN series VARCHAR(30)")
        if "number" not in columns:
            statements.append("ALTER TABLE lg_cylinder_contracts ADD COLUMN number INTEGER")
        if "signed_flag" not in columns:
            statements.append(
                "ALTER TABLE lg_cylinder_contracts ADD COLUMN "
                "signed_flag BOOLEAN NOT NULL DEFAULT FALSE"
            )
        if "contract_file_path" not in columns:
            statements.append(
                "ALTER TABLE lg_cylinder_contracts ADD COLUMN contract_file_path VARCHAR(500)"
            )
        if "observations" not in columns:
            statements.append("ALTER TABLE lg_cylinder_contracts ADD COLUMN observations TEXT")
        if "cancelled_at" not in columns:
            statements.append("ALTER TABLE lg_cylinder_contracts ADD COLUMN cancelled_at TIMESTAMP")

        for statement in statements:
            bind.execute(text(statement))

        if bind.dialect.name == "postgresql":
            bind.execute(
                text("ALTER TABLE lg_cylinder_contracts ALTER COLUMN contract_number DROP NOT NULL")
            )

        bind.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_lg_cylinder_contracts_series "
                "ON lg_cylinder_contracts (series)"
            )
        )
        bind.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lg_cylinder_contracts_series_number "
                "ON lg_cylinder_contracts (tenant_id, series, number) "
                "WHERE series IS NOT NULL AND number IS NOT NULL"
            )
        )

    bind.execute(
        text(
            "CREATE INDEX IF NOT EXISTS ix_lg_cylinder_contract_history_contract_id "
            "ON lg_cylinder_contract_history (contract_id, occurred_at)"
        )
    )


def downgrade(db) -> None:
    bind = db.connection()

    bind.execute(text("DROP TABLE IF EXISTS lg_cylinder_contract_history"))
    bind.execute(text("DROP TABLE IF EXISTS lg_contract_types"))
