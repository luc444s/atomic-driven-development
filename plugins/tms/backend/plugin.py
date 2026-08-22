from typing import Any

from plugins.tms.backend.ports import HostContext
from plugins.tms.backend.routers.jornadas import router as jornadas_router
from plugins.tms.backend.services import link_legacy

TMS_PERMISSIONS = [
    "tms.legacy.read",
    "tms.legacy.link",
    "tms.stock.write",
    "tms.jornada.read",
    "tms.jornada.edit",
]

TMS_EVENTS = [
    "tms.legacy.linked",
]


def register(context: Any) -> None:
    """El host pasa su PluginContext; solo se exige el protocolo HostContext."""
    ctx: HostContext = context
    ctx.register_router(jornadas_router)
    ctx.register_permissions(TMS_PERMISSIONS)
    ctx.register_events(TMS_EVENTS)


__all__ = ["register", "link_legacy", "TMS_PERMISSIONS", "TMS_EVENTS"]
