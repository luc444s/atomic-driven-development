"""COMPRAS-016: historial técnico consolidado del envase por serial.

Esquemas de solo lectura: ninguna de estas entidades se crea ni se
modifica vía este endpoint; modelan la respuesta de la consulta.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class CylinderHistoryDispatchRead(BaseModel):
    dispatch_id: str
    order_id: str | None
    supplier_id: str
    dispatch_date: date
    service_type: str
    status: str
    returned_at: datetime | None


class CylinderHistoryReceiptRead(BaseModel):
    receipt_id: str
    order_id: str
    receipt_date: date
    qty_accepted: int | None
    qty_rejected: int | None
    difference_type: str | None


class CylinderHistoryServiceRead(BaseModel):
    receipt_id: str
    service_type: str
    cost: float | None
    notes: str | None
    test_date: date | None
    next_test_date: date | None
    result: str | None
    document_ref: str | None
    created_at: datetime


class CylinderHistoryRead(BaseModel):
    cylinder_id: str
    serial: str
    dispatches: list[CylinderHistoryDispatchRead] = []
    receipts: list[CylinderHistoryReceiptRead] = []
    services: list[CylinderHistoryServiceRead] = []
