from __future__ import annotations

from sqlalchemy import text

revision = "0009"


def upgrade(db) -> None:
    # source_quantity_liters quedo cargado con la capacidad de agua del envase
    # (B10 -> 10.000) en vez de los litros de liquido criogenico reales.
    # Valor correcto = masa de gas del envase (net_weight_kg) / densidad liquida
    # del producto fuente (default_weight_kg en kg/m3 / 1000 -> kg/L).
    # Fuente legacy: XLS "Listado de productos y peso de gas. Litros - kg",
    # hoja LISTADO INDUSTRIAL (PESO NETO KG) + hoja Gas Liquido (kg por litro).
    rows = db.execute(
        text(
            """
            SELECT pa.id, pa.net_weight_kg, pp.default_weight_kg
            FROM prod_adr pa
            JOIN prod_products pp ON pp.id = pa.source_product_id
            WHERE pa.source_quantity_liters IS NOT NULL
              AND pa.net_weight_kg IS NOT NULL
              AND pp.default_weight_kg IS NOT NULL
              AND pp.default_weight_kg > 0
            """
        )
    ).all()

    for adr_id, net_weight_kg, default_weight_kg in rows:
        liquid_liters = round(float(net_weight_kg) / (float(default_weight_kg) / 1000.0), 3)
        db.execute(
            text("UPDATE prod_adr SET source_quantity_liters = :liters WHERE id = :id"),
            {"liters": liquid_liters, "id": adr_id},
        )
