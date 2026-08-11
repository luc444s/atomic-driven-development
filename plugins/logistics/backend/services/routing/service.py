from __future__ import annotations

from apps.api.app.core.config import Settings
from plugins.logistics.backend.services.routing.cache import RoutingCache
from plugins.logistics.backend.services.routing.models import RoutingProviderAvailability
from plugins.logistics.backend.services.routing.providers.osrm import OsrmClient
from plugins.logistics.backend.services.routing.providers.vroom import VroomClient


class RoutingService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cache = RoutingCache(ttl_seconds=settings.logistics_routing_cache_ttl_seconds)
        self.osrm = (
            OsrmClient(
                base_url=settings.logistics_osrm_base_url,
                timeout_seconds=settings.logistics_routing_request_timeout_seconds,
            )
            if settings.logistics_osrm_base_url
            else None
        )
        self.vroom = (
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
