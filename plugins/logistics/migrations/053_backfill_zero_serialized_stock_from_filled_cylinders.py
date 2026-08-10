from __future__ import annotations

revision = "053"


def upgrade(db) -> None:
    # Revision conservada como no-op historico.
    # Se uso temporalmente durante una investigacion de stock agregado
    # desde seriales, luego se revirtio por decision de producto.
    # No debe volver a mutar datos, pero la revision debe existir porque
    # algunas instalaciones ya quedaron registradas en 053.
    return None
