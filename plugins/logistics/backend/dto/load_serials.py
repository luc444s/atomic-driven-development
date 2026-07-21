from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoadSerialSelectRequest(BaseModel):
    product_id: str
    source_warehouse_id: str | None = None
    serial: str = Field(min_length=1, max_length=150)


class LoadSerialReleaseRequest(BaseModel):
    release_reason: str = Field(min_length=1, max_length=30)


class LoadSerialAssignmentRead(BaseModel):
    id: str
    session_id: str
    product_id: str
    cylinder_id: str
    cylinder_serial: str
    assignment_status: str
    selected_by: str
    selected_at: datetime
    confirmed_by_operation_id: str | None = None
    confirmed_at: datetime | None = None
    released_at: datetime | None = None
    release_reason: str | None = None
    notes: str | None = None
    updated_at: datetime


class LoadSerialSearchResultRead(BaseModel):
    cylinder_id: str
    serial: str
    availability_status: str
    context_label: str | None = None
