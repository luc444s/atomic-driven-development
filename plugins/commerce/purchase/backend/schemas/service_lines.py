from __future__ import annotations

from datetime import date, datetime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

LEGAL_SERVICE_TYPES: Final[frozenset[str]] = frozenset(
    {"PRUEBA_HIDROSTATICA", "RETIMBRADO"}
)

LEGAL_RESULT = Literal["APROBADO", "RECHAZADO"]


class ReceiptServiceLineCreate(BaseModel):
    serial: str = Field(min_length=1, max_length=50)
    service_type: SERVICE_TYPE
    cost: float | None = Field(default=None, ge=0)
    notes: str | None = None
    test_date: date | None = None
    next_test_date: date | None = None
    result: LEGAL_RESULT | None = None
    document_ref: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def validate_legal_data(self) -> ReceiptServiceLineCreate:
        if self.service_type in LEGAL_SERVICE_TYPES:
            if self.test_date is None or self.result is None:
                raise ValueError(
                    "PRUEBA_HIDROSTATICA/RETIMBRADO requiere fecha del trabajo y resultado"
                )
            if self.result == "APROBADO" and self.next_test_date is None:
                raise ValueError(
                    "Resultado APROBADO requiere fecha de próxima prueba hidrostática"
                )
            if self.result == "RECHAZADO" and self.next_test_date is not None:
                raise ValueError(
                    "Resultado RECHAZADO no admite fecha de próxima prueba hidrostática"
                )
        elif any(
            value is not None
            for value in (
                self.test_date,
                self.next_test_date,
                self.result,
                self.document_ref,
            )
        ):
            raise ValueError(
                "Los datos legales solo aplican a PRUEBA_HIDROSTATICA o RETIMBRADO"
            )
        return self


class ReceiptServiceLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    receipt_id: str
    cylinder_id: str
    serial: str
    service_type: str
    cost: float | None
    notes: str | None
    test_date: date | None
    next_test_date: date | None
    result: str | None
    document_ref: str | None
    created_by: str
    created_at: datetime
