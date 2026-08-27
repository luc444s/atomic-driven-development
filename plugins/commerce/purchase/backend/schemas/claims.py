from __future__ import annotations

from datetime import datetime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

CLAIM_REASONS: Final[tuple[str, ...]] = (
    "FALTANTE",
    "PRODUCTO_INCORRECTO",
    "MALA_CALIDAD",
    "CILINDRO_DANADO",
    "SERVICIO_INCOMPLETO",
    "SERVICIO_DEFECTUOSO",
    "PRECIO_INCORRECTO",
    "DOCUMENTO_INCORRECTO",
    "DEMORA",
    "PERDIDA_ENVASE",
    "DANO_EN_CUSTODIA",
)

CLAIM_REASON = Literal[
    "FALTANTE",
    "PRODUCTO_INCORRECTO",
    "MALA_CALIDAD",
    "CILINDRO_DANADO",
    "SERVICIO_INCOMPLETO",
    "SERVICIO_DEFECTUOSO",
    "PRECIO_INCORRECTO",
    "DOCUMENTO_INCORRECTO",
    "DEMORA",
    "PERDIDA_ENVASE",
    "DANO_EN_CUSTODIA",
]


class SupplierClaimCreate(BaseModel):
    reason: CLAIM_REASON
    description: str = Field(min_length=1, max_length=2000)
    receipt_id: str | None = None
    invoice_id: str | None = None


class ClaimResolveRequest(BaseModel):
    resolution_notes: str = Field(min_length=1, max_length=4000)


class ClaimAnnulRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=4000)


class SupplierClaimEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    from_status: str | None
    to_status: str
    reason: str | None
    user_id: str | None
    created_at: datetime


class SupplierClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    order_id: str
    supplier_id: str
    receipt_id: str | None
    invoice_id: str | None
    reason: str
    description: str
    status: str
    opened_by: str
    opened_at: datetime
    resolved_by: str | None
    resolved_at: datetime | None
    resolution_notes: str | None


class SupplierClaimDetailRead(SupplierClaimRead):
    events: list[SupplierClaimEventRead] = []
