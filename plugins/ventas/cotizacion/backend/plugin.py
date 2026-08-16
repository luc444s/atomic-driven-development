# ═══════════════════════════════════════════════════════════════════
# MODULO DESHABILITADO — La cotización queda fuera de servicio hasta
# que exista un módulo de ventas completo (facturación, pedidos,
# despacho). El router y los permisos se mantienen registrados para
# que los endpoints sigan accesibles durante desarrollo, pero el
# módulo no debe usarse en producción ni mostrarse en el sidebar.
# Fecha: 2026-08-06 — ver AGENTS.md memoria de sesión.
# ═══════════════════════════════════════════════════════════════════

from systutor.sdk import PluginContext

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
