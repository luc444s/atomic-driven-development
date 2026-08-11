from __future__ import annotations

import json
from datetime import timedelta
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.config import Settings
from plugins.logistics.backend.models import (
    LogisticsRoute,
    LogisticsRouteCalculation,
    LogisticsRouteStop,
)
from plugins.logistics.backend.services.routing.cache import RoutingCache
from plugins.logistics.backend.services.routing.geometry import build_route_geometry
from plugins.logistics.backend.services.routing.matrix import build_time_distance_matrix
from plugins.logistics.backend.services.routing.models import (
    Coordinate,
    RoutingCalculatedStop,
    RoutingCalculationRequest,
    RoutingCalculationResponse,
    RoutingCommitOrderRequest,
    RoutingCommitOrderResponse,
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

    def commit_order(
        self,
        db: Session,
        *,
        tenant_id: str,
        actor_user_id: str,
        payload: RoutingCommitOrderRequest,
    ) -> RoutingCommitOrderResponse:
        route = db.scalar(
            select(LogisticsRoute).where(
                LogisticsRoute.id == payload.route_id,
                LogisticsRoute.tenant_id == tenant_id,
            )
        )
        if route is None:
            raise LookupError("route not found")

        stops = list(
            db.scalars(
                select(LogisticsRouteStop)
                .where(LogisticsRouteStop.route_id == payload.route_id)
                .order_by(LogisticsRouteStop.stop_order.asc())
            ).all()
        )
        ordered_stop_ids = [
            item.stop_id
            for item in sorted(payload.preview.ordered_stops, key=lambda item: item.sequence)
        ]
        if not ordered_stop_ids:
            raise ValueError("commit-order requires at least one ordered stop")

        route_stop_ids = {item.id for item in stops}
        if route_stop_ids != set(ordered_stop_ids):
            raise ValueError("ordered stops do not match route stops")

        for offset, stop in enumerate(stops, start=1):
            stop.stop_order = 1000 + offset
            db.add(stop)
        db.flush()

        stop_by_id = {stop.id: stop for stop in stops}
        for sequence, stop_id in enumerate(ordered_stop_ids, start=1):
            stop = stop_by_id[stop_id]
            stop.stop_order = sequence
            db.add(stop)

        calculation = LogisticsRouteCalculation(
            tenant_id=tenant_id,
            route_id=payload.route_id,
            session_id=payload.session_id,
            planning_reservation_id=payload.planning_reservation_id,
            provider_stack=payload.preview.provider_stack,
            input_hash=self._build_input_hash(payload),
            ordered_stop_ids_json=ordered_stop_ids,
            totals_json=payload.preview.totals.model_dump(),
            violations_json=payload.preview.violations,
            polyline=payload.preview.polyline,
            created_by=actor_user_id,
        )
        db.add(calculation)
        db.flush()

        return RoutingCommitOrderResponse(
            calculation_id=calculation.id,
            route_id=payload.route_id,
            committed=True,
            stop_count=len(ordered_stop_ids),
        )

    def _build_input_hash(self, payload: RoutingCommitOrderRequest) -> str:
        raw = json.dumps(
            {
                "route_id": payload.route_id,
                "session_id": payload.session_id,
                "planning_reservation_id": payload.planning_reservation_id,
                "provider_stack": payload.preview.provider_stack,
                "ordered_stops": [
                    {
                        "stop_id": item.stop_id,
                        "sequence": item.sequence,
                        "distance_from_prev_m": item.distance_from_prev_m,
                        "travel_seconds_from_prev": item.travel_seconds_from_prev,
                    }
                    for item in payload.preview.ordered_stops
                ],
                "totals": payload.preview.totals.model_dump(),
                "violations": payload.preview.violations,
                "polyline": payload.preview.polyline,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(raw.encode("utf-8")).hexdigest()
