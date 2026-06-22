from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from packages.contracts.events import EventContract
from packages.contracts.plugins import PluginManifestContract

EventHandler = Callable[[EventContract], None]


@dataclass(slots=True)
class PluginRegistration:
    plugin_id: str
    routers: list[object] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    event_handlers: dict[str, list[EventHandler]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class PluginContext:
    def __init__(self, manifest: PluginManifestContract) -> None:
        self.manifest = manifest
        self.registration = PluginRegistration(plugin_id=manifest.id)

    def register_router(self, router: object) -> None:
        self.registration.routers.append(router)

    def register_permissions(self, permissions: list[str]) -> None:
        self.registration.permissions.extend(permissions)

    def register_events(self, events: list[str]) -> None:
        self.registration.events.extend(events)

    def register_event_handler(self, event_name: str, handler: EventHandler) -> None:
        self.registration.event_handlers.setdefault(event_name, []).append(handler)

    def set_metadata(self, key: str, value: Any) -> None:
        self.registration.metadata[key] = value
