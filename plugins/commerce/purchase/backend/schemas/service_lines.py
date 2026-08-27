from __future__ import annotations

from datetime import datetime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

SERVICE_TYPES: Final[tuple[str, ...]] = (
    "LLENADO",
    "PRUEBA_HIDROSTATICA",
    "RETIMBRADO",
    "INSPECCION",
    "REPARACION",
    "MANTENIMIENTO",
    "CAMBIO_VALVULA",
    "PINTURA",
    "ACONDICIONAMIENTO",
    "CERTIFICACION",
)

SERVICE_TYPE = Literal[
    "LLENADO",
    "PRUEBA_HIDROSTATICA",
    "RETIMBRADO",
    "INSPECCION",
    "REPARACION",
    "MANTENIMIENTO",
    "CAMBIO_VALVULA",
    "PINTURA",
    "ACONDICIONAMIENTO",
    "CERTIFICACION",
]


class ReceiptServiceLineCreate(BaseModel):
    serial: str = Field(min_length=1, max_length=50)
    service_type: SERVICE_TYPE
    cost: float | None = Field(default=None, ge=0)
    notes: str | None = None


class ReceiptServiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    receipt_id: str
    cylinder_id: str
    serial: str
    service_type: str
    cost: float | None
    notes: str | None
    created_by: str
    created_at: datetime
