from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.api.v1.core.common import build_action_context
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.commerce._shared.stock_connector import StockConnector
from plugins.commerce.purchase.backend.models import (
    ComPurchaseOrder,
    ComPurchaseReceipt,
    ComSupplier,
)
from plugins.commerce.purchase.backend.schemas import (
    CancelOrderRequest,
    PurchaseItemRead,
    PurchaseOrderCreateRequest,
    PurchaseOrderDetailRead,
    PurchaseOrderPageRead,
    PurchaseOrderRead,
    PurchaseOrderUpdateRequest,
    PurchaseReceiptRead,
    ReceiveOrderRequest,
    SupplierAddressCreateRequest,
    SupplierBankAccountCreateRequest,
    SupplierContactCreateRequest,
    SupplierCreateRequest,
    SupplierRead,
    SupplierUpdateRequest,
)
from plugins.commerce.purchase.backend.models import ComSupplierBankAccount, ComSupplierContact
import httpx
from plugins.commerce.purchase.backend.services import addresses, orders, receipts, suppliers

router = APIRouter(prefix="/purchase", tags=["compras"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)

REQUIRE_SUPPLIER_READ = Depends(require_permission("compras.supplier.read"))
REQUIRE_SUPPLIER_MANAGE = Depends(require_permission("compras.supplier.manage"))
REQUIRE_ORDER_READ = Depends(require_permission("compras.order.read"))
REQUIRE_ORDER_CREATE = Depends(require_permission("compras.order.create"))
REQUIRE_ORDER_MANAGE = Depends(require_permission("compras.order.manage"))
REQUIRE_ORDER_RECEIVE = Depends(require_permission("compras.order.receive"))


def _build_stock_connector() -> StockConnector:
    from apps.api.app.core.config import get_settings
    s = get_settings()
    return StockConnector(
        base_url=f"http://localhost:8000/api/v1/plugins/stock",
        internal_token=getattr(s, "internal_api_token", ""),
    )


def _serialize_order(order: ComPurchaseOrder) -> dict:
    from plugins.commerce.purchase.backend.services.suppliers import get_supplier
    return {
        "id": order.id,
        "supplier": None,
        "status": order.status,
        "order_date": order.order_date,
        "expected_date": order.expected_date,
        "notes": order.notes,
        "created_by": order.created_by,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
    }


def _serialize_order_detail(db: Session, order: ComPurchaseOrder) -> dict:
    result: dict = _serialize_order(order)  # type: ignore[assignment]
    result["items"] = [
        {
            "id": i.id,
            "product_id": i.product_id,
            "quantity": float(i.quantity),
            "unit_cost": float(i.unit_cost),
            "received_qty": float(i.received_qty),
        }
        for i in order.items  # type: ignore[attr-defined]
    ]
    result["receipts"] = [
        {
            "id": r.id,
            "warehouse_id": r.warehouse_id,
            "receipt_date": r.receipt_date,
            "notes": r.notes,
            "created_at": r.created_at,
        }
        for r in order.receipts  # type: ignore[attr-defined]
    ]
    return result


# ── Suppliers ──

@router.get("/suppliers", response_model=list[SupplierRead], dependencies=[REQUIRE_SUPPLIER_READ])
def list_suppliers_endpoint(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    search: str | None = None,
) -> list[SupplierRead]:
    return [
        SupplierRead.model_validate(item)
        for item in suppliers.list_suppliers(
            db, tenant_id=tenant_context.current_tenant_id, search=search
        )
    ]


@router.post(
    "/suppliers",
    response_model=SupplierRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def create_supplier(
    payload: SupplierCreateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.create_supplier(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    return SupplierRead.model_validate(item)


@router.patch(
    "/suppliers/{supplier_id}",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def update_supplier(
    supplier_id: str,
    payload: SupplierUpdateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(
        db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    item = suppliers.update_supplier(
        db, supplier=item, payload=payload.model_dump(exclude_unset=True)
    )
    db.commit()
    return SupplierRead.model_validate(item)


@router.post(
    "/suppliers/{supplier_id}/disable",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def disable_supplier(
    supplier_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(
        db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    item = suppliers.disable_supplier(db, supplier=item)
    db.commit()
    return SupplierRead.model_validate(item)


@router.post(
    "/suppliers/{supplier_id}/addresses",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def add_supplier_address(
    supplier_id: str,
    payload: SupplierAddressCreateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(
        db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    addresses.add_supplier_address(
        db,
        supplier=item,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    return SupplierRead.model_validate(item)


@router.delete(
    "/suppliers/{supplier_id}/addresses/{address_id}",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def remove_supplier_address(
    supplier_id: str,
    address_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(
        db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    try:
        addresses.delete_supplier_address(
            db, supplier=item, address_id=address_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return SupplierRead.model_validate(item)


@router.post(
    "/suppliers/{supplier_id}/contacts",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def add_supplier_contact(
    supplier_id: str,
    payload: SupplierContactCreateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    contact = ComSupplierContact(
        tenant_id=tenant_context.current_tenant_id,
        supplier_id=supplier_id,
        **payload.model_dump(exclude_unset=True),
    )
    db.add(contact)
    db.commit()
    return SupplierRead.model_validate(item)


@router.delete(
    "/suppliers/{supplier_id}/contacts/{contact_id}",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def remove_supplier_contact(
    supplier_id: str,
    contact_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    contact = db.scalar(select(ComSupplierContact).where(
        ComSupplierContact.id == contact_id, ComSupplierContact.supplier_id == supplier_id
    ))
    if contact is None:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    db.delete(contact)
    db.commit()
    item = suppliers.get_supplier(db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id)
    return SupplierRead.model_validate(item) if item else SupplierRead.model_validate({})


@router.post(
    "/suppliers/{supplier_id}/bank-accounts",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def add_supplier_bank_account(
    supplier_id: str,
    payload: SupplierBankAccountCreateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    item = suppliers.get_supplier(db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    account = ComSupplierBankAccount(
        tenant_id=tenant_context.current_tenant_id,
        supplier_id=supplier_id,
        **payload.model_dump(exclude_unset=True),
    )
    db.add(account)
    db.commit()
    return SupplierRead.model_validate(item)


@router.delete(
    "/suppliers/{supplier_id}/bank-accounts/{account_id}",
    response_model=SupplierRead,
    dependencies=[REQUIRE_SUPPLIER_MANAGE],
)
def remove_supplier_bank_account(
    supplier_id: str,
    account_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> SupplierRead:
    account = db.scalar(select(ComSupplierBankAccount).where(
        ComSupplierBankAccount.id == account_id, ComSupplierBankAccount.supplier_id == supplier_id
    ))
    if account is None:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    db.delete(account)
    db.commit()
    item = suppliers.get_supplier(db, tenant_id=tenant_context.current_tenant_id, supplier_id=supplier_id)
    return SupplierRead.model_validate(item) if item else SupplierRead.model_validate({})


@router.get(
    "/tanks",
    dependencies=[REQUIRE_ORDER_RECEIVE],
)
def list_tanks(
    product_id: str | None = None,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> list[dict]:
    from apps.api.app.core.config import get_settings
    s = get_settings()
    token = getattr(s, "internal_api_token", "")
    params = {"container_type": "CRYOGENIC_TANK", "limit": "50"}
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


# ── Purchase Orders ──

@router.get("/orders", response_model=PurchaseOrderPageRead, dependencies=[REQUIRE_ORDER_READ])
def list_orders_endpoint(
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    status: str | None = None,
    supplier_id: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    items, total = orders.list_orders(
        db,
        tenant_id=tenant_context.current_tenant_id,
        status=status,
        supplier_id=supplier_id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": [_serialize_order(o) for o in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post(
    "/orders",
    response_model=PurchaseOrderRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_ORDER_CREATE],
)
def create_order_endpoint(
    payload: PurchaseOrderCreateRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _user: User = Depends(require_permission("compras.order.create")),
) -> PurchaseOrderRead:
    item = orders.create_order(
        db,
        tenant_id=tenant_context.current_tenant_id,
        branch_id=tenant_context.current_branch_id,
        supplier_id=payload.supplier_id,
        items_payload=[i.model_dump() for i in payload.items],
        expected_date=payload.expected_date,
        notes=payload.notes,
        created_by=tenant_context.current_user_id,
    )
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))


@router.get("/orders/{order_id}", response_model=PurchaseOrderDetailRead, dependencies=[REQUIRE_ORDER_READ])
def get_order(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderDetailRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return PurchaseOrderDetailRead.model_validate(_serialize_order_detail(db, item))


@router.patch(
    "/orders/{order_id}",
    response_model=PurchaseOrderRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def update_order(
    order_id: str,
    payload: PurchaseOrderUpdateRequest,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    try:
        item = orders.update_order(
            db,
            order=item,
            payload=payload.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))


@router.post(
    "/orders/{order_id}/confirm",
    response_model=PurchaseOrderRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def confirm_order(
    order_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    item = orders.confirm_order(db, order=item)
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))


@router.post(
    "/orders/{order_id}/cancel",
    response_model=PurchaseOrderRead,
    dependencies=[REQUIRE_ORDER_MANAGE],
)
def cancel_order(
    order_id: str,
    payload: CancelOrderRequest | None = None,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> PurchaseOrderRead:
    item = orders.get_order(db, tenant_id=tenant_context.current_tenant_id, order_id=order_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    item = orders.cancel_order(db, order=item)
    db.commit()
    return PurchaseOrderRead.model_validate(_serialize_order(item))


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
