from fastapi import APIRouter

from plugins.commerce.purchase.backend.routers import orders, receipts, suppliers

router = APIRouter(prefix="/purchase", tags=["compras"])

router.include_router(suppliers.router, prefix="/suppliers")
router.include_router(orders.router, prefix="/orders")
router.include_router(receipts.router)
