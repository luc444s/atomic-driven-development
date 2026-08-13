from __future__ import annotations

from sqlalchemy import text

revision = "0008"


def upgrade(db) -> None:
    # Corrige la fuente criogenica de los productos "Argón industrial *".
    # Quedaron apuntando a LOX o LIN durante la importacion de recetas;
    # el gas base de todos ellos es LAR (Argón Liquido).
    # Las mezclas (Hidrinac, IG541, QC) no se tocan: su fuente es decision de negocio.
    lar_id = db.execute(
        text("SELECT id FROM prod_products WHERE name = 'Argón Liquido - LAR' LIMIT 1")
    ).scalar_one_or_none()
    if lar_id is None:
        return

    db.execute(
        text(
            """
            UPDATE prod_adr
            SET source_product_id = :lar_id
            WHERE product_id IN (
                SELECT id FROM prod_products
                WHERE name LIKE 'Argón industrial%'
            )
            AND source_product_id IS NOT NULL
            AND source_product_id != :lar_id
            """
        ),
        {"lar_id": lar_id},
    )
