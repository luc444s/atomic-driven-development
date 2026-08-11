from __future__ import annotations

from hashlib import sha256

from plugins.logistics.backend.services.routing.models import Coordinate, TimeDistanceMatrix
from plugins.logistics.backend.services.routing.provider import MatrixProvider


def _matrix_cache_key(coordinates: list[Coordinate]) -> str:
    raw = "|".join(f"{item.lat:.6f},{item.lng:.6f}" for item in coordinates)
    return f"routing:matrix:{sha256(raw.encode('utf-8')).hexdigest()}"


def build_time_distance_matrix(
    *,
    provider: MatrixProvider,
    coordinates: list[Coordinate],
    cache_get,
    cache_set,
) -> TimeDistanceMatrix:
    cache_key = _matrix_cache_key(coordinates)
    cached = cache_get(cache_key)
    if isinstance(cached, TimeDistanceMatrix):
        return cached

    matrix = provider.build_matrix(coordinates)
    cache_set(cache_key, matrix)
    return matrix
