from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RouteStopResultUpsertRequest(BaseModel):
    status: str = Field(min_length=1, max_length=20)
    completion_percent: float = Field(ge=0, le=100)
    outcome_type: str = Field(min_length=1, max_length=40)
    driver_note: str | None = Field(default=None, max_length=1000)


class RouteStopResultRead(BaseModel):
    id: str
    session_id: str
    route_stop_id: str
    status: str
    completion_percent: float
    outcome_type: str
    driver_note: str | None = None
    created_at: datetime
    updated_at: datetime
