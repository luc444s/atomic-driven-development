from __future__ import annotations

from collections.abc import Sequence

import httpx

from plugins.logistics.backend.services.routing.models import (
    Coordinate,
    RouteGeometry,
    RouteGeometryLeg,
    TimeDistanceMatrix,
)
from plugins.logistics.backend.services.routing.provider import RoutingProviderError


class OsrmClient:
    def __init__(self, *, base_url: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _coordinate_param(self, coordinates: Sequence[Coordinate]) -> str:
        return ";".join(f"{item.lng},{item.lat}" for item in coordinates)

    def _get_json(self, path: str, *, params: dict[str, str] | None = None) -> dict:
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                response = httpx.get(
                    f"{self.base_url}{path}",
                    params=params,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise RoutingProviderError("OSRM response must be JSON object")
                return payload
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_error = exc
        raise RoutingProviderError(f"OSRM request failed: {last_error}")

    def build_matrix(self, coordinates: Sequence[Coordinate]) -> TimeDistanceMatrix:
        payload = self._get_json(
            f"/table/v1/driving/{self._coordinate_param(coordinates)}",
            params={"annotations": "duration,distance"},
        )
        durations = payload.get("durations")
        distances = payload.get("distances")
        if not isinstance(durations, list) or not isinstance(distances, list):
            raise RoutingProviderError("OSRM matrix response missing durations/distances")
        return TimeDistanceMatrix(
            coordinates=list(coordinates),
            durations_s=[[int(cell or 0) for cell in row] for row in durations],
            distances_m=[[int(cell or 0) for cell in row] for row in distances],
        )

    def build_route(self, coordinates: Sequence[Coordinate]) -> RouteGeometry:
        payload = self._get_json(
            f"/route/v1/driving/{self._coordinate_param(coordinates)}",
            params={"overview": "full", "geometries": "polyline", "steps": "false"},
        )
        routes = payload.get("routes")
        if not isinstance(routes, list) or not routes:
            raise RoutingProviderError("OSRM route response missing routes")
        route = routes[0]
        legs_payload = route.get("legs") or []
        return RouteGeometry(
            polyline=route.get("geometry"),
            distance_m=int(route.get("distance") or 0),
            duration_s=int(route.get("duration") or 0),
            legs=[
                RouteGeometryLeg(
                    distance_m=int(item.get("distance") or 0),
                    duration_s=int(item.get("duration") or 0),
                )
                for item in legs_payload
                if isinstance(item, dict)
            ],
        )

    def snap(self, coordinate: Coordinate) -> Coordinate:
        payload = self._get_json(
            f"/nearest/v1/driving/{coordinate.lng},{coordinate.lat}",
        )
        waypoints = payload.get("waypoints")
        if not isinstance(waypoints, list) or not waypoints:
            raise RoutingProviderError("OSRM nearest response missing waypoints")
        location = waypoints[0].get("location")
        if not isinstance(location, list) or len(location) != 2:
            raise RoutingProviderError("OSRM nearest response missing location")
        lng, lat = location
        return Coordinate(lat=float(lat), lng=float(lng))
