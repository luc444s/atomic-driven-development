from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0035"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    cylinder_cols = {col["name"] for col in inspector.get_columns("lg_cylinders")}
    if "session_id" not in cylinder_cols:
        bind.execute(text(
            "ALTER TABLE lg_cylinders ADD COLUMN session_id VARCHAR(36)"
        ))
        bind.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_lg_cylinders_session "
            "ON lg_cylinders(tenant_id, session_id)"
        ))

    fks = inspector.get_foreign_keys("lg_cylinders")
    has_session_fk = any(
        fk.get("constrained_columns") == ["session_id"]
        for fk in fks
    )
    if not has_session_fk:
        bind.execute(text(
            "ALTER TABLE lg_cylinders ADD CONSTRAINT fk_cylinder_session "
            "FOREIGN KEY (session_id) REFERENCES lg_vehicle_sessions(id)"
        ))

    checks = inspector.get_check_constraints("lg_cylinders")
    has_transit_ck = any("transit_requires_session" in (c.get("name") or "")
                         for c in checks)
    if not has_transit_ck:
        bind.execute(text(
            "ALTER TABLE lg_cylinders ADD CONSTRAINT "
            "ck_cylinder_transit_requires_session CHECK ("
            "current_state NOT IN ('CARGA_EN_VEHICULO', 'EN_RUTA') "
            "OR session_id IS NOT NULL"
            ")"
        ))

    orphan_count = bind.execute(text(
        "SELECT COUNT(*) FROM lg_cylinders "
        "WHERE current_state IN ('CARGA_EN_VEHICULO', 'EN_RUTA') "
        "AND session_id IS NULL"
    )).scalar()
    if orphan_count and orphan_count > 0:
        bind.execute(text(
            "UPDATE lg_cylinders SET current_state = 'EN_ALMACEN_VACIO' "
            "WHERE current_state IN ('CARGA_EN_VEHICULO', 'EN_RUTA') "
            "AND (session_id IS NULL "
            "  OR session_id NOT IN (SELECT id FROM lg_vehicle_sessions))"
        ))


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    checks = inspector.get_check_constraints("lg_cylinders")
    for ck in checks:
        if "transit_requires_session" in (ck.get("name") or ""):
            bind.execute(text(
                "ALTER TABLE lg_cylinders DROP CONSTRAINT "
                f"{ck['name']}"
            ))

    fks = inspector.get_foreign_keys("lg_cylinders")
    for fk in fks:
        if fk.get("constrained_columns") == ["session_id"]:
            bind.execute(text(
                "ALTER TABLE lg_cylinders DROP CONSTRAINT "
                f"{fk['name']}"
            ))

    bind.execute(text(
        "DROP INDEX IF EXISTS ix_lg_cylinders_session"
    ))

    cylinder_cols = {col["name"] for col in inspector.get_columns("lg_cylinders")}
    if "session_id" in cylinder_cols:
        bind.execute(text(
            "ALTER TABLE lg_cylinders DROP COLUMN session_id"
        ))
