from typing import Any

from sqlalchemy import select, text

from plugins.logistics.backend.models import LogisticsCylinderCondition

revision = "0005"


def _create_table(table: Any, bind) -> None:
    table.create(bind=bind, checkfirst=True)


def _drop_table(table: Any, bind) -> None:
    table.drop(bind=bind, checkfirst=True)


def upgrade(db) -> None:
    bind = db.connection()
    _create_table(LogisticsCylinderCondition.__table__, bind)

    existing = set(db.scalars(select(LogisticsCylinderCondition.code)).all())
    for code, name in [
        ("CILPRO", "Cilindro propio"),
        ("CILCLI", "Cilindro del cliente"),
        ("CILPROV", "Cilindro del proveedor"),
        ("CILGAR", "Cilindro en garantia"),
    ]:
        if code in existing:
            continue
        db.add(LogisticsCylinderCondition(code=code, name=name, is_active=True))
    db.flush()

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
    _drop_table(LogisticsCylinderCondition.__table__, bind)
