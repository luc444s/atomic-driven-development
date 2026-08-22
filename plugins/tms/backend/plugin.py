from systutor.sdk import PluginContext

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


def register(context: PluginContext) -> None:
    context.register_router(jornadas_router)
    context.register_permissions(TMS_PERMISSIONS)
    context.register_events(TMS_EVENTS)


__all__ = ["register", "link_legacy", "TMS_PERMISSIONS", "TMS_EVENTS"]
