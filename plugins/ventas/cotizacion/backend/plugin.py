from packages.sdk import PluginContext
from plugins.ventas.cotizacion.backend.router import router

VENTAS_COTIZACION_PERMISSIONS = [
    "ventas.cotizacion.create",
    "ventas.cotizacion.read",
    "ventas.cotizacion.read_all",
]

VENTAS_COTIZACION_EVENTS = [
    "ventas.cotizacion.created",
]


def register(context: PluginContext) -> None:
    context.register_router(router)
    context.register_permissions(VENTAS_COTIZACION_PERMISSIONS)
    context.register_events(VENTAS_COTIZACION_EVENTS)
