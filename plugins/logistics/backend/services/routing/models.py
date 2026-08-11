from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Coordinate(BaseModel):
    lat: float
    lng: float


class RoutingStopInput(BaseModel):
    stop_id: str
    customer_id: str | None = None
    customer_name: str | None = None
    address_id: str | None = None
    address_label: str | None = None
    lat: float
    lng: float
    service_minutes: int = 0
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    demand_units: float = 0
    demand_weight_kg: float = 0
    demand_volume_m3: float = 0
    adr_required: bool = False
    priority: int | None = None

    def coordinate(self) -> Coordinate:
        return Coordinate(lat=self.lat, lng=self.lng)


class RoutingVehicleInput(BaseModel):
    vehicle_id: str
    start_warehouse_id: str | None = None
    end_warehouse_id: str | None = None
    start_lat: float
    start_lng: float
    end_lat: float | None = None
    end_lng: float | None = None
    capacity_units: float | None = None
    capacity_weight_kg: float | None = None
    capacity_volume_m3: float | None = None
    adr_capable: bool = False

    def start_coordinate(self) -> Coordinate:
        return Coordinate(lat=self.start_lat, lng=self.start_lng)

    def end_coordinate(self) -> Coordinate:
        return Coordinate(
            lat=self.end_lat if self.end_lat is not None else self.start_lat,
            lng=self.end_lng if self.end_lng is not None else self.start_lng,
        )


class RoutingCalculationRequest(BaseModel):
    route_id: str | None = None
    session_id: str | None = None
    planning_reservation_id: str | None = None
    vehicle: RoutingVehicleInput
    stops: list[RoutingStopInput]
    departure_at: datetime | None = None
    mode: str = Field(default="preview")
    commit_order: bool = False


class RoutingCalculatedStop(BaseModel):
    stop_id: str
    sequence: int
    eta_at: datetime | None = None
    etd_at: datetime | None = None
    distance_from_prev_m: int | None = None
    travel_seconds_from_prev: int | None = None
    service_minutes: int = 0
    violation_codes: list[str] = Field(default_factory=list)


class RoutingTotals(BaseModel):
    distance_m: int
    travel_seconds: int
    service_seconds: int
    total_seconds: int


class RoutingCalculationResponse(BaseModel):
    provider_stack: str
    route_id: str | None = None
    session_id: str | None = None
    ordered_stops: list[RoutingCalculatedStop]
    totals: RoutingTotals
    polyline: str | None = None
    violations: list[str] = Field(default_factory=list)
    committed: bool = False


class RoutingCommitOrderRequest(BaseModel):
    route_id: str
    session_id: str | None = None
    planning_reservation_id: str | None = None
    preview: RoutingCalculationResponse


class RoutingCommitOrderResponse(BaseModel):
    calculation_id: str
    route_id: str
    committed: bool
    stop_count: int


class TimeDistanceMatrix(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    coordinates: list[Coordinate]
    durations_s: list[list[int]]
    distances_m: list[list[int]]


class RouteGeometryLeg(BaseModel):
    distance_m: int
    duration_s: int


class RouteGeometry(BaseModel):
    polyline: str | None = None
    distance_m: int = 0
    duration_s: int = 0
    legs: list[RouteGeometryLeg] = Field(default_factory=list)


class RoutingProviderAvailability(BaseModel):
    enabled: bool
    osrm_configured: bool
    vroom_configured: bool
    ready: bool
