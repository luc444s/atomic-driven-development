"""Entrypoint HTTP del plugin compras (ADD §12.3: composition root fino).

Las rutas viven divididas por dominio en backend/routers/.
"""
from plugins.commerce.purchase.backend.routers import router

__all__ = ["router"]
