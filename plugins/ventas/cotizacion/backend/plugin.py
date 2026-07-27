from packages.sdk import PluginContext
from plugins.ventas.cotizacion.backend.router import router

VENTAS_COTIZACION_PERMISSIONS = [
    "ventas.cotizacion.create",
    "ventas.cotizacion.read",
    "ventas.cotizacion.read_all",
    "ventas.cotizacion.confirm",
]

VENTAS_COTIZACION_EVENTS = [
    "ventas.cotizacion.created",
    "ventas.cotizacion.confirmed",
]


def register(context: PluginContext) -> None:
    context.register_router(router)
    context.register_permissions(VENTAS_COTIZACION_PERMISSIONS)
    context.register_events(VENTAS_COTIZACION_EVENTS)
