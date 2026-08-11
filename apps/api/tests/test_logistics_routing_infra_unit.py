from __future__ import annotations

from datetime import UTC, datetime

from apps.api.app.core.config import Settings
from plugins.logistics.backend.services.routing import RoutingService
from plugins.logistics.backend.services.routing.cache import RoutingCache
from plugins.logistics.backend.services.routing.models import (
    Coordinate,
    RouteGeometry,
    RouteGeometryLeg,
    RoutingCalculationRequest,
    RoutingStopInput,
    RoutingVehicleInput,
    TimeDistanceMatrix,
)


def test_routing_service_disabled_by_default(test_settings: Settings) -> None:
    service = RoutingService(test_settings)

    availability = service.availability()

    assert availability.enabled is False
    assert availability.osrm_configured is False
    assert availability.vroom_configured is False
    assert availability.ready is False


def test_routing_service_reports_ready_when_stack_configured(test_settings: Settings) -> None:
    settings = test_settings.model_copy(
        update={
            "logistics_routing_enabled": True,
            "logistics_osrm_base_url": "http://osrm.local",
            "logistics_vroom_base_url": "http://vroom.local",
            "logistics_routing_request_timeout_seconds": 7,
            "logistics_routing_cache_ttl_seconds": 123,
        }
    )
    service = RoutingService(settings)

    availability = service.availability()

    assert availability.enabled is True
    assert availability.osrm_configured is True
    assert availability.vroom_configured is True
    assert availability.ready is True
    assert service.cache.ttl_seconds == 123
    assert service.osrm is not None
    assert service.vroom is not None
    assert service.osrm.timeout_seconds == 7
    assert service.vroom.timeout_seconds == 7


def test_routing_cache_expires_entries() -> None:
    cache = RoutingCache(ttl_seconds=0)
    cache.set("matrix:a", {"ok": True})

    assert cache.get("matrix:a") is None


class FakeOsrm:
    def __init__(self) -> None:
        self.matrix_calls = 0
        self.route_calls = 0

    def build_matrix(self, coordinates):
        self.matrix_calls += 1
        size = len(coordinates)
        return TimeDistanceMatrix(
            coordinates=list(coordinates),
            durations_s=[[0 for _ in range(size)] for _ in range(size)],
            distances_m=[[0 for _ in range(size)] for _ in range(size)],
        )

    def build_route(self, coordinates):
        self.route_calls += 1
        return RouteGeometry(
            polyline="abc123",
            distance_m=4200,
            duration_s=900,
            legs=[
                RouteGeometryLeg(distance_m=1000, duration_s=300),
                RouteGeometryLeg(distance_m=1200, duration_s=360),
                RouteGeometryLeg(distance_m=2000, duration_s=240),
            ],
        )

    def snap(self, coordinate: Coordinate) -> Coordinate:
        return coordinate


class FakeVroom:
    def optimize_single_vehicle(self, *, coordinates):
        assert len(coordinates) == 4
        return [0, 2, 1, 3]


def test_routing_service_calculates_preview_with_fake_providers(test_settings: Settings) -> None:
    settings = test_settings.model_copy(
        update={
            "logistics_routing_enabled": True,
        }
    )
    osrm = FakeOsrm()
    service = RoutingService(settings, osrm=osrm, vroom=FakeVroom())
    request = RoutingCalculationRequest(
        route_id="route-1",
        vehicle=RoutingVehicleInput(
            vehicle_id="veh-1",
            start_lat=40.0,
            start_lng=-3.0,
            end_lat=40.0,
            end_lng=-3.0,
        ),
        stops=[
            RoutingStopInput(stop_id="stop-a", lat=40.1, lng=-3.1, service_minutes=5),
            RoutingStopInput(stop_id="stop-b", lat=40.2, lng=-3.2, service_minutes=7),
        ],
        departure_at=datetime(2026, 8, 11, 8, 0, tzinfo=UTC),
    )

    response = service.calculate_preview(request)

    assert response.provider_stack == "osrm+vroom"
    assert [item.stop_id for item in response.ordered_stops] == ["stop-b", "stop-a"]
    assert response.totals.distance_m == 4200
    assert response.totals.travel_seconds == 900
    assert response.totals.service_seconds == 720
    assert response.totals.total_seconds == 1620
    assert response.polyline == "abc123"
    assert osrm.matrix_calls == 1
    assert osrm.route_calls == 1


def test_routing_service_preview_requires_available_stack(test_settings: Settings) -> None:
    service = RoutingService(test_settings)
    request = RoutingCalculationRequest(
        vehicle=RoutingVehicleInput(vehicle_id="veh-1", start_lat=40.0, start_lng=-3.0),
        stops=[RoutingStopInput(stop_id="stop-a", lat=40.1, lng=-3.1)],
    )

    try:
        service.calculate_preview(request)
    except RuntimeError as exc:
        assert str(exc) == "routing stack unavailable"
    else:
        raise AssertionError("Expected routing stack unavailable error")


def test_routing_service_preview_rejects_stop_limit(test_settings: Settings) -> None:
    settings = test_settings.model_copy(
        update={
            "logistics_routing_enabled": True,
        }
    )
    service = RoutingService(settings, osrm=FakeOsrm(), vroom=FakeVroom())
    request = RoutingCalculationRequest(
        vehicle=RoutingVehicleInput(
            vehicle_id="veh-1",
            start_lat=40.0,
            start_lng=-3.0,
            end_lat=40.0,
            end_lng=-3.0,
        ),
        stops=[
            RoutingStopInput(stop_id=f"stop-{index}", lat=40.1 + index, lng=-3.1 - index)
            for index in range(41)
        ],
    )

    try:
        service.calculate_preview(request)
    except ValueError as exc:
        assert str(exc) == "routing preview supports up to 40 stops"
    else:
        raise AssertionError("Expected stop-limit validation error")
