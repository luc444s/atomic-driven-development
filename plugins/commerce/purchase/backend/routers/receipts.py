from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from systutor.kernel.tenants.context import TenantContext

from plugins.commerce.purchase.backend.schemas import PurchaseOrderRead, ReceiveOrderRequest
from plugins.commerce.purchase.backend.routers.common import (
    DB_SESSION,
    REQUIRE_ORDER_RECEIVE,
    TENANT_CONTEXT,
    _build_stock_connector,
)
from plugins.commerce.purchase.backend.routers.orders import _serialize_order
from plugins.commerce.purchase.backend.services import orders, receipts

router = APIRouter()


@router.post(
    "/orders/{order_id}/receive",
    response_model=PurchaseOrderRead,
    dependencies=[REQUIRE_ORDER_RECEIVE],
)
def receive_order(
    order_id: str,
    payload: ReceiveOrderRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    try:
        connector = _build_stock_connector()
        item = receipts.receive_order(
            db,
            order=item,
            warehouse_id=payload.warehouse_id,
            items_payload=[i.model_dump() for i in payload.items],
            notes=payload.notes,
            created_by=tenant_context.current_user_id,
            stock_connector=connector,
            tank_id=payload.tank_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))


@router.get(
    "/tanks",
    dependencies=[REQUIRE_ORDER_RECEIVE],
)
def list_tanks(
    product_id: str | None = None,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> list[dict]:
    del tenant_context
    from apps.api.app.config import get_settings

    s = get_settings()
    token = getattr(s, "internal_api_token", "")
    params: dict[str, str] = {"container_type": "CRYOGENIC_TANK", "limit": "50"}
    if product_id:
        params["product_id"] = product_id
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    try:
        resp = httpx.get(
            f"http://localhost:8000/api/v1/plugins/logistics/cylinders?{qs}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", [])
    except Exception:
        return []
    return [
        {
            "id": t["id"],
            "serial": t.get("serial", ""),
            "description": t.get("description", ""),
            "product_id": t.get("product_id", ""),
            "content_kg": float(t.get("content_kg") or 0),
            "volume_m3": float(t.get("volume_m3") or 0),
        }
        for t in items
    ]
