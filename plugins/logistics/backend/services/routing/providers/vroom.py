from __future__ import annotations

from collections.abc import Sequence

import httpx

from plugins.logistics.backend.services.routing.models import Coordinate
from plugins.logistics.backend.services.routing.provider import RoutingProviderError


class VroomClient:
    def __init__(self, *, base_url: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def optimize_single_vehicle(
        self,
        *,
        coordinates: Sequence[Coordinate],
        has_end: bool,
    ) -> list[int]:
        if len(coordinates) < 2:
            return list(range(len(coordinates)))

        start = coordinates[0]
        jobs = [
            {
                "id": index,
                "location": [coordinate.lng, coordinate.lat],
            }
            for index, coordinate in enumerate(
                coordinates[1:-1] if has_end else coordinates[1:],
                start=1,
            )
        ]
        vehicle = {
            "id": 1,
            "start": [start.lng, start.lat],
        }
        if has_end:
            end = coordinates[-1]
            vehicle["end"] = [end.lng, end.lat]
        payload = self._post_json({"vehicles": [vehicle], "jobs": jobs})
        routes = payload.get("routes")
        if not isinstance(routes, list) or not routes:
            raise RoutingProviderError("VROOM response missing routes")
        steps = routes[0].get("steps") or []
        ordered = [0]
        for step in steps:
            if isinstance(step, dict) and step.get("type") == "job":
                ordered.append(int(step["job"]))
        if has_end:
            ordered.append(len(coordinates) - 1)
        return ordered

    def _post_json(self, payload: dict) -> dict:
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                response = httpx.post(
                    f"{self.base_url}",
                    json=payload,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise RoutingProviderError("VROOM response must be JSON object")
                return data
            except (httpx.TimeoutException, httpx.HTTPStatusError) as exc:
                last_error = exc
        raise RoutingProviderError(f"VROOM request failed: {last_error}")
