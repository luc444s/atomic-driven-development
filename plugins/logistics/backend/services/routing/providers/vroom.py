from __future__ import annotations

from collections.abc import Sequence

import httpx

from plugins.logistics.backend.services.routing.models import Coordinate
from plugins.logistics.backend.services.routing.provider import RoutingProviderError


class VroomClient:
    def __init__(self, *, base_url: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def optimize_single_vehicle(self, *, coordinates: Sequence[Coordinate]) -> list[int]:
        if len(coordinates) < 2:
            return list(range(len(coordinates)))

        start = coordinates[0]
        end = coordinates[-1]
        jobs = [
            {
                "id": index,
                "location": [coordinate.lng, coordinate.lat],
            }
            for index, coordinate in enumerate(coordinates[1:-1], start=1)
        ]
        vehicle = {
            "id": 1,
            "start": [start.lng, start.lat],
            "end": [end.lng, end.lat],
        }
        response = httpx.post(
            f"{self.base_url}",
            json={"vehicles": [vehicle], "jobs": jobs},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        routes = payload.get("routes")
        if not isinstance(routes, list) or not routes:
            raise RoutingProviderError("VROOM response missing routes")
        steps = routes[0].get("steps") or []
        ordered = [0]
        for step in steps:
            if isinstance(step, dict) and step.get("type") == "job":
                ordered.append(int(step["job"]))
        ordered.append(len(coordinates) - 1)
        return ordered
