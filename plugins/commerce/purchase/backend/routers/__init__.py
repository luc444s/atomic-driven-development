from fastapi import APIRouter

from plugins.commerce.purchase.backend.routers import (
    claims,
    cylinder_history,
    dispatches,
    invoices,
    orders,
    physical_counts,
    receipts,
    service_lines,
    suppliers,
)

router = APIRouter(prefix="/purchase", tags=["compras"])

router.include_router(suppliers.router, prefix="/suppliers")
router.include_router(orders.router, prefix="/orders")
# physical_counts ANTES que dispatches: sus rutas /dispatches/physical-counts
# no deben ser capturadas por GET /dispatches/{dispatch_id}.
router.include_router(physical_counts.router)
router.include_router(dispatches.router, prefix="/dispatches")
router.include_router(receipts.router)
router.include_router(service_lines.router)
router.include_router(invoices.router)
router.include_router(claims.router)
router.include_router(cylinder_history.router)
