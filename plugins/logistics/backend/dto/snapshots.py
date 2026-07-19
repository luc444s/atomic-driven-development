from __future__ import annotations

from pydantic import BaseModel, Field

from .sessions import SessionHistoryEntryRead, SessionStockSummaryRead


class SessionSnapshotRead(BaseModel):
    session_id: str
    vehicle_id: str
    vehicle_plate: str
    driver_id: str
    driver_name: str
    route_id: str | None = None
    status: str
    occupancy_percent: float | None = None
    current_stock: SessionStockSummaryRead
    last_activity: str | None = None
    alerts: list[str] = Field(default_factory=list)
    can_depart: bool = False
    can_close: bool = False
    history: list[SessionHistoryEntryRead] = Field(default_factory=list)
