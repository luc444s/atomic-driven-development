from __future__ import annotations

from hashlib import sha256

from plugins.logistics.backend.services.routing.models import Coordinate, RouteGeometry
from plugins.logistics.backend.services.routing.provider import GeometryProvider


def _geometry_cache_key(coordinates: list[Coordinate]) -> str:
    raw = "|".join(f"{item.lat:.6f},{item.lng:.6f}" for item in coordinates)
    return f"routing:geometry:{sha256(raw.encode('utf-8')).hexdigest()}"


def build_route_geometry(
    *,
    provider: GeometryProvider,
    coordinates: list[Coordinate],
    cache_get,
    cache_set,
) -> RouteGeometry:
    cache_key = _geometry_cache_key(coordinates)
    cached = cache_get(cache_key)
    if isinstance(cached, RouteGeometry):
        return cached

    geometry = provider.build_route(coordinates)
    cache_set(cache_key, geometry)
    return geometry
