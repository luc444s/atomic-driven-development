from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from plugins.logistics.backend.services.routing.models import (
    Coordinate,
    RouteGeometry,
    TimeDistanceMatrix,
)


class RoutingProviderError(RuntimeError):
    pass


class RoutingCapabilityError(RoutingProviderError):
    pass


class MatrixProvider(Protocol):
    def build_matrix(self, coordinates: Sequence[Coordinate]) -> TimeDistanceMatrix: ...

    def snap(self, coordinate: Coordinate) -> Coordinate: ...


class OptimizationProvider(Protocol):
    def optimize_single_vehicle(self, *, coordinates: Sequence[Coordinate]) -> list[int]: ...


class GeometryProvider(Protocol):
    def build_route(self, coordinates: Sequence[Coordinate]) -> RouteGeometry: ...
