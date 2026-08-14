from __future__ import annotations

from pydantic import BaseModel, Field

from plugins.crm.backend.schemas import CustomerListItemRead
from plugins.logistics.backend.dto.route_operations import (
    CurrentCompositionRead,
    RouteIncidentRead,
    RouteOperationRead,
    RouteStopProgressRead,
)
from plugins.logistics.backend.dto.route_stop_results import RouteStopResultRead
from plugins.logistics.backend.dto.sessions import (
    SessionWaybillHistoryVersionRead,
    SessionWaybillStateRead,
    VehicleSessionDetailRead,
)
from plugins.logistics.backend.schemas import (
    RouteRead,
    RouteStopRead,
    RoutingAssignedRouteRead,
    WarehouseRead,
)


class RouteContextRead(BaseModel):
    session: VehicleSessionDetailRead
    route_detail: RouteRead | None = None
    assigned_route: RoutingAssignedRouteRead | None = None
    stops: list[RouteStopRead] = Field(default_factory=list)
    operations: list[RouteOperationRead] = Field(default_factory=list)
    composition: CurrentCompositionRead | None = None
    waybill: SessionWaybillStateRead | None = None
    waybill_history: list[SessionWaybillHistoryVersionRead] = Field(default_factory=list)
    incidents: list[RouteIncidentRead] = Field(default_factory=list)
    stop_progress: list[RouteStopProgressRead] = Field(default_factory=list)
    stop_results: list[RouteStopResultRead] = Field(default_factory=list)
    customers: list[CustomerListItemRead] = Field(default_factory=list)
    warehouses: list[WarehouseRead] = Field(default_factory=list)
