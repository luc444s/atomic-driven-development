from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from packages.contracts.events import EventContract
from packages.contracts.plugins import PluginManifestContract

EventHandler = Callable[[EventContract], None]
LifecycleHook = Callable[[], None]


@dataclass(slots=True)
class PluginRegistration:
    plugin_id: str
    routers: list[object] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    events: list[str] = field(default_factory=list)
    event_handlers: dict[str, list[EventHandler]] = field(default_factory=dict)
    startup_hooks: list[LifecycleHook] = field(default_factory=list)
    shutdown_hooks: list[LifecycleHook] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PluginContext:
    def __init__(
        self,
        manifest: PluginManifestContract,
        *,
        config: Any = None,
        router_registry: Any = None,
        event_bus: Any = None,
        audit_service: Any = None,
        db_session_provider: Any = None,
        task_dispatcher: Any = None,
        plugin_metadata: dict[str, Any] | None = None,
    ) -> None:
        self.manifest = manifest
        self.registration = PluginRegistration(plugin_id=manifest.id)
        self.config = config
        self.router_registry = router_registry
        self.event_bus = event_bus
        self.audit_service = audit_service
        self.db_session_provider = db_session_provider
        self.task_dispatcher = task_dispatcher
        self.plugin_metadata = plugin_metadata or manifest.model_dump()

    def register_router(self, router: object) -> None:
        self.registration.routers.append(router)

    def register_permissions(self, permissions: list[str]) -> None:
        self.registration.permissions.extend(permissions)

    def register_events(self, events: list[str]) -> None:
        self.registration.events.extend(events)

    def register_event_handler(self, event_name: str, handler: EventHandler) -> None:
        self.registration.event_handlers.setdefault(event_name, []).append(handler)

    def register_startup_hook(self, hook: LifecycleHook) -> None:
        self.registration.startup_hooks.append(hook)

    def register_shutdown_hook(self, hook: LifecycleHook) -> None:
        self.registration.shutdown_hooks.append(hook)

    def set_metadata(self, key: str, value: Any) -> None:
        self.registration.metadata[key] = value
