"""Dependencias compartidas y helpers de la capa HTTP de compras."""
from __future__ import annotations

from fastapi import Depends
from systutor.api.deps import get_db_session
from systutor.kernel.auth.dependencies import get_current_tenant_context, require_permission
from systutor.kernel.tenants.context import TenantContext

from plugins.commerce._shared.stock_connector import StockConnector

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)

REQUIRE_SUPPLIER_READ = Depends(require_permission("compras.supplier.read"))
REQUIRE_SUPPLIER_MANAGE = Depends(require_permission("compras.supplier.manage"))
REQUIRE_ORDER_READ = Depends(require_permission("compras.order.read"))
REQUIRE_ORDER_CREATE = Depends(require_permission("compras.order.create"))
REQUIRE_ORDER_MANAGE = Depends(require_permission("compras.order.manage"))
REQUIRE_ORDER_RECEIVE = Depends(require_permission("compras.order.receive"))
REQUIRE_DISPATCH_READ = Depends(require_permission("compras.dispatch.read"))
REQUIRE_DISPATCH_MANAGE = Depends(require_permission("compras.dispatch.manage"))


def _internal_token() -> str:
    """Token JWT de un usuario interno para llamadas servidor-a-servidor.

    Los endpoints destino (stock.movement.purchase_in, logistics cylinders)
    exigen permisos de usuario reales; no existe mecanismo de service-token,
    así que autenticamos con credenciales configuradas y usamos ese JWT.
    """
    import httpx

    from apps.api.app.config import get_settings

    s = get_settings()
    response = httpx.post(
        "http://localhost:8000/api/v1/auth/login",
        json={
            "email": s.internal_user_email,
            "password": s.internal_user_password,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def _build_stock_connector() -> StockConnector:
    from apps.api.app.config import get_settings

    s = get_settings()
    return StockConnector(
        base_url="http://localhost:8000/api/v1/plugins/stock",
        internal_token=_internal_token(),
    )
