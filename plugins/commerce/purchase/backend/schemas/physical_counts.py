from __future__ import annotations

from datetime import datetime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

COUNT_STATUS_EN_CURSO: Final[str] = "EN_CURSO"
COUNT_STATUS_CERRADA: Final[str] = "CERRADA"

DISCREPANCY_TYPES: Final[tuple[str, ...]] = (
    "FALTANTE",
    "NO_DECLARADO",
    "CONDICION",
)
DISCREPANCY_TYPE = Literal["FALTANTE", "NO_DECLARADO", "CONDICION"]

COUNT_RESOLUTIONS: Final[tuple[str, ...]] = ("RECLAMADA", "ACEPTADA", "OBSERVADA")
COUNT_RESOLUTION = Literal["RECLAMADA", "ACEPTADA", "OBSERVADA"]


class PhysicalCountCreate(BaseModel):
    supplier_id: str
    order_id: str | None = None
    dispatch_id: str | None = None
    notes: str | None = Field(default=None, max_length=4000)


class PhysicalCountFoundSerial(BaseModel):
    serial: str = Field(min_length=1, max_length=50)
    condition_note: str | None = Field(default=None, max_length=2000)


class PhysicalCountCloseRequest(BaseModel):
    found: list[PhysicalCountFoundSerial] = []
    notes: str | None = Field(default=None, max_length=4000)


class PhysicalCountItemResolveRequest(BaseModel):
    resolution: COUNT_RESOLUTION
    reason: str = Field(min_length=1, max_length=4000)


class PhysicalCountEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_status: str | None
    to_status: str
    reason: str | None
    user_id: str | None
    created_at: datetime


class PhysicalCountExpectedSerialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cylinder_id: str
    serial: str
    captured_at: datetime


class PhysicalCountItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    cylinder_id: str
    serial: str
    expected: bool
    found: bool
    discrepancy_type: DISCREPANCY_TYPE
    notes: str | None
    resolution: str | None
    resolved_by: str | None
    resolved_at: datetime | None


class PhysicalCountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    supplier_id: str
    order_id: str | None
    dispatch_id: str | None
    expected_total: int
    found_total: int
    match_count: int
    status: str
    counted_by: str
    counted_at: datetime
    closed_at: datetime | None
    notes: str | None


class PhysicalCountDetailRead(PhysicalCountRead):
    expected_serials: list[PhysicalCountExpectedSerialRead] = []
    items: list[PhysicalCountItemRead] = []
    events: list[PhysicalCountEventRead] = []
