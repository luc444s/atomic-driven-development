from __future__ import annotations

from apps.api.app.core.config import Settings
from plugins.logistics.backend.services.routing import RoutingService
from plugins.logistics.backend.services.routing.cache import RoutingCache


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
