from __future__ import annotations

from datetime import timedelta

from apps.api.app.core.config import Settings
from plugins.logistics.backend.services.routing.cache import RoutingCache
from plugins.logistics.backend.services.routing.geometry import build_route_geometry
from plugins.logistics.backend.services.routing.matrix import build_time_distance_matrix
from plugins.logistics.backend.services.routing.models import (
    Coordinate,
    RoutingCalculatedStop,
    RoutingCalculationRequest,
    RoutingCalculationResponse,
    RoutingProviderAvailability,
    RoutingTotals,
)
from plugins.logistics.backend.services.routing.optimizer import optimize_stop_sequence
from plugins.logistics.backend.services.routing.provider import RoutingCapabilityError
from plugins.logistics.backend.services.routing.providers.osrm import OsrmClient
from plugins.logistics.backend.services.routing.providers.vroom import VroomClient


class RoutingService:
    def __init__(
        self,
        settings: Settings,
        *,
        osrm: OsrmClient | None = None,
        vroom: VroomClient | None = None,
    ) -> None:
        self.settings = settings
        self.cache = RoutingCache(ttl_seconds=settings.logistics_routing_cache_ttl_seconds)
        self.osrm = osrm or (
            OsrmClient(
                base_url=settings.logistics_osrm_base_url,
                timeout_seconds=settings.logistics_routing_request_timeout_seconds,
            )
            if settings.logistics_osrm_base_url
            else None
        )
        self.vroom = vroom or (
            VroomClient(
                base_url=settings.logistics_vroom_base_url,
                timeout_seconds=settings.logistics_routing_request_timeout_seconds,
            )
            if settings.logistics_vroom_base_url
            else None
        )

    def availability(self) -> RoutingProviderAvailability:
        osrm_configured = self.osrm is not None
        vroom_configured = self.vroom is not None
        enabled = self.settings.logistics_routing_enabled
        return RoutingProviderAvailability(
            enabled=enabled,
            osrm_configured=osrm_configured,
            vroom_configured=vroom_configured,
            ready=enabled and osrm_configured and vroom_configured,
        )

    def calculate_preview(
        self,
        request: RoutingCalculationRequest,
    ) -> RoutingCalculationResponse:
        availability = self.availability()
        if not availability.ready or self.osrm is None or self.vroom is None:
            raise RoutingCapabilityError("routing stack unavailable")
        if not request.stops:
            raise ValueError("routing preview requires at least one stop")

        coordinates = self._build_coordinates(request)
        build_time_distance_matrix(
            provider=self.osrm,
            coordinates=coordinates,
            cache_get=self.cache.get,
            cache_set=self.cache.set,
        )
        ordered_indexes = optimize_stop_sequence(provider=self.vroom, coordinates=coordinates)
        ordered_coordinates = [coordinates[index] for index in ordered_indexes]
        geometry = build_route_geometry(
            provider=self.osrm,
            coordinates=ordered_coordinates,
            cache_get=self.cache.get,
            cache_set=self.cache.set,
        )

        stop_lookup = {offset + 1: stop for offset, stop in enumerate(request.stops)}
        ordered_stops: list[RoutingCalculatedStop] = []
        running_at = request.departure_at
        service_seconds = 0

        for sequence, index in enumerate(ordered_indexes[1:-1], start=1):
            stop = stop_lookup[index]
            leg = geometry.legs[sequence - 1] if sequence - 1 < len(geometry.legs) else None
            eta_at = None
            etd_at = None
            if running_at is not None and leg is not None:
                eta_at = running_at + timedelta(seconds=leg.duration_s)
                etd_at = eta_at + timedelta(minutes=stop.service_minutes)
                running_at = etd_at
            service_seconds += stop.service_minutes * 60
            ordered_stops.append(
                RoutingCalculatedStop(
                    stop_id=stop.stop_id,
                    sequence=sequence,
                    eta_at=eta_at,
                    etd_at=etd_at,
                    distance_from_prev_m=leg.distance_m if leg is not None else None,
                    travel_seconds_from_prev=leg.duration_s if leg is not None else None,
                    service_minutes=stop.service_minutes,
                )
            )

        return RoutingCalculationResponse(
            provider_stack="osrm+vroom",
            route_id=request.route_id,
            session_id=request.session_id,
            ordered_stops=ordered_stops,
            totals=RoutingTotals(
                distance_m=geometry.distance_m,
                travel_seconds=geometry.duration_s,
                service_seconds=service_seconds,
                total_seconds=geometry.duration_s + service_seconds,
            ),
            polyline=geometry.polyline,
            committed=False,
        )

    def _build_coordinates(self, request: RoutingCalculationRequest) -> list[Coordinate]:
        return [
            request.vehicle.start_coordinate(),
            *(stop.coordinate() for stop in request.stops),
            request.vehicle.end_coordinate(),
        ]
