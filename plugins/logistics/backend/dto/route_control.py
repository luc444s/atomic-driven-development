from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VehicleLocationRecordRequest(BaseModel):
    lat: float
    lng: float
    speed: float | None = None
    heading: float | None = None
    accuracy_meters: float | None = None
    recorded_at: datetime
    source: str = Field(default="WEB", min_length=1, max_length=20)


class VehicleLocationEventRead(BaseModel):
    id: str
    session_id: str
    route_id: str | None = None
    vehicle_id: str
    driver_id: str
    lat: float
    lng: float
    speed: float | None = None
    heading: float | None = None
    accuracy_meters: float | None = None
    source: str
    recorded_at: datetime
    received_at: datetime


class RouteControlStateRead(BaseModel):
    session_id: str
    route_id: str | None = None
    vehicle_id: str
    active_stop_id: str | None = None
    active_stop_started_at: datetime | None = None
    current_stop_id: str | None = None
    current_stop_index: int | None = None
    status: str
    last_lat: float | None = None
    last_lng: float | None = None
    last_speed: float | None = None
    last_heading: float | None = None
    last_recorded_at: datetime | None = None
    completed_stops: int = 0
    total_stops: int = 0
    progress_percent: float = 0
    off_route: bool = False
    next_stop_eta_minutes: int | None = None
    geofence_state: str | None = None
    updated_at: datetime
