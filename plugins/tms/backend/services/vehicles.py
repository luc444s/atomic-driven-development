from __future__ import annotations

from plugins.tms.backend import ports

# Vehiculos de flota real mapeados desde legacy (transporte de salidas).
# AYRTOM/LEON -> TAF-948, REYES POLO -> T3G081, ARANGO -> RAM/BEI-793.
SEED_PLATES = ["TAF-948", "T3G081", "RAM/BEI-793"]


def normalize_plate(placa: str) -> str:
    """Normaliza placas legacy ('taf-948'/'TAF948') a forma canonica de busqueda."""
    return placa.strip().upper().replace("-", "").replace("/", "")


def ensure_vehicle(db, *, tenant_id: str, plate: str,
                   vehicle_type: str | None = None) -> str:
    """Garantiza el vehículo de flota vía puerto; devuelve su id."""
    if not plate.strip():
        raise ValueError("Placa vacia")
    return ports.get_ports().ensure_vehicle(
        db, tenant_id=tenant_id, plate=plate, vehicle_type=vehicle_type
    )


__all__ = ["SEED_PLATES", "ensure_vehicle", "normalize_plate"]
