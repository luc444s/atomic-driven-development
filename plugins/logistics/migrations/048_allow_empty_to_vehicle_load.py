from __future__ import annotations

from uuid import uuid4

from sqlalchemy import text

revision = "0048"


def upgrade(db) -> None:
    bind = db.connection()
    exists = bind.execute(
        text(
            """
            SELECT 1
            FROM lg_state_transitions
            WHERE from_state = 'EN_ALMACEN_VACIO'
              AND to_state = 'CARGA_EN_VEHICULO'
            """
        )
    ).first()
    if exists is not None:
        return

    bind.execute(
        text(
            """
            INSERT INTO lg_state_transitions (
                id,
                from_state,
                to_state,
                requires_adr,
                requires_hydrotest,
                description
            ) VALUES (
                :id,
                'EN_ALMACEN_VACIO',
                'CARGA_EN_VEHICULO',
                0,
                0,
                'Carga en vehiculo'
            )
            """
        ),
        {"id": str(uuid4())},
    )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(
        text(
            """
            DELETE FROM lg_state_transitions
            WHERE from_state = 'EN_ALMACEN_VACIO'
              AND to_state = 'CARGA_EN_VEHICULO'
            """
        )
    )
