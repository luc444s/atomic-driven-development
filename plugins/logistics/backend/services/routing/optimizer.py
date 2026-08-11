from __future__ import annotations

from plugins.logistics.backend.services.routing.models import Coordinate
from plugins.logistics.backend.services.routing.provider import OptimizationProvider


def optimize_stop_sequence(
    *,
    provider: OptimizationProvider,
    coordinates: list[Coordinate],
) -> list[int]:
    return provider.optimize_single_vehicle(coordinates=coordinates)
