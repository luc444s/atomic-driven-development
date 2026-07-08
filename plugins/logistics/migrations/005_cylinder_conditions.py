from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, MetaData, String, Table, inspect, text

revision = "0005"

_meta = MetaData()

_LegacyCondition = Table(
    "lg_cylinder_conditions", _meta,
    Column("code", String(20), primary_key=True),
    Column("name", String(100), nullable=False),
    Column("is_active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def _create_table(table, bind) -> None:
    table.create(bind=bind, checkfirst=True)


def _drop_table(table, bind) -> None:
    table.drop(bind=bind, checkfirst=True)


def upgrade(db) -> None:
    bind = db.connection()
    _create_table(_LegacyCondition, bind)

    inspector = inspect(bind)
    existing_cols = {c["name"] for c in inspector.get_columns("lg_cylinder_conditions")}
    needs_seed = "code" in existing_cols
    if needs_seed:
        result = bind.execute(text("SELECT code FROM lg_cylinder_conditions"))
        existing = {row[0] for row in result}
        now = datetime.now(UTC).isoformat()
        for code, name in [
            ("CILPRO", "Cilindro propio"),
            ("CILCLI", "Cilindro del cliente"),
            ("CILPROV", "Cilindro del proveedor"),
            ("CILGAR", "Cilindro en garantia"),
        ]:
            if code in existing:
                continue
            bind.execute(
                text("INSERT INTO lg_cylinder_conditions (code, name, is_active, created_at) "
                     "VALUES (:code, :name, TRUE, :now)"),
                {"code": code, "name": name, "now": now},
            )

    if bind.dialect.name == "sqlite":
        bind.execute(
            text("CREATE INDEX IF NOT EXISTS ix_lg_cylinders_condition ON lg_cylinders (condition)")
        )
        return

    bind.execute(
        text(
            "ALTER TABLE lg_cylinders "
            "ADD COLUMN IF NOT EXISTS condition_new VARCHAR(20) "
            "REFERENCES lg_cylinder_conditions(code)"
        )
    )
    bind.execute(
        text(
            "UPDATE lg_cylinders SET condition_new = condition "
            "WHERE condition IN ('CILPRO', 'CILCLI', 'CILPROV', 'CILGAR')"
        )
    )
    bind.execute(text("ALTER TABLE lg_cylinders DROP COLUMN IF EXISTS condition"))
    bind.execute(text("ALTER TABLE lg_cylinders RENAME COLUMN condition_new TO condition"))
    bind.execute(
        text("CREATE INDEX IF NOT EXISTS ix_lg_cylinders_condition ON lg_cylinders (condition)")
    )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("DROP INDEX IF EXISTS ix_lg_cylinders_condition"))
    if bind.dialect.name == "sqlite":
        return
    bind.execute(
        text("ALTER TABLE lg_cylinders ADD COLUMN condition_old VARCHAR(50)")
    )
    bind.execute(
        text("UPDATE lg_cylinders SET condition_old = condition WHERE condition IS NOT NULL")
    )
    bind.execute(text("ALTER TABLE lg_cylinders DROP COLUMN IF EXISTS condition"))
    bind.execute(text("ALTER TABLE lg_cylinders RENAME COLUMN condition_old TO condition"))
    _drop_table(_LegacyCondition, bind)
