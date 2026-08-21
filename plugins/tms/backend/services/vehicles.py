from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from systutor.kernel.tenants.models import Tenant

from plugins.logistics.backend.models import LogisticsVehicle

# Vehiculos de flota real mapeados desde legacy (transporte de salidas).
# AYRTOM/LEON -> TAF-948, REYES POLO -> T3G081, ARANGO -> RAM/BEI-793.
SEED_PLATES = ["TAF-948", "T3G081", "RAM/BEI-793"]


def normalize_plate(placa: str) -> str:
    """Normaliza placas legacy ('taf-948'/'TAF948') a forma canonica de busqueda."""
    return placa.strip().upper().replace("-", "").replace("/", "")


def find_vehicle_by_plate(db: Session, *, tenant_id: str, plate: str) -> LogisticsVehicle | None:
    canonical = normalize_plate(plate)
    candidates = list(
        db.scalars(
            select(LogisticsVehicle).where(
                LogisticsVehicle.tenant_id == tenant_id,
                LogisticsVehicle.is_active.is_(True),
            )
        ).all()
    )
    for vehicle in candidates:
        if normalize_plate(vehicle.plate) == canonical:
            return vehicle
    return None


def ensure_vehicle(
    db: Session,
    *,
    tenant: Tenant,
    plate: str,
    vehicle_type: str | None = None,
) -> LogisticsVehicle:
    plate = plate.strip().upper()
    if not plate:
        raise ValueError("Placa vacia")

    existing = find_vehicle_by_plate(db, tenant_id=tenant.id, plate=plate)
    if existing is not None:
        return existing

    vehicle = LogisticsVehicle(
        tenant_id=tenant.id,
        plate=plate,
        vehicle_type=vehicle_type or "CAMION",
        is_active=True,
    )
    db.add(vehicle)
    db.flush()
    return vehicle


__all__ = ["SEED_PLATES", "ensure_vehicle", "find_vehicle_by_plate", "normalize_plate"]