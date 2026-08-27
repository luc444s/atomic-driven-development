from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.orm import Session
from systutor.kernel.tenants.context import TenantContext

from plugins.commerce.purchase.backend.routers.common import (
    DB_SESSION,
    REQUIRE_ORDER_READ,
    REQUIRE_ORDER_RECEIVE,
    TENANT_CONTEXT,
)
from plugins.commerce.purchase.backend.schemas import (
    ReceiptServiceLineCreate,
    ReceiptServiceLineRead,
)
from plugins.commerce.purchase.backend.services import service_lines as service_lines_service

router = APIRouter()


@router.post(
    "/receipts/{receipt_id}/service-lines",
    response_model=ReceiptServiceLineRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[REQUIRE_ORDER_RECEIVE],
)
def create_service_line(
    receipt_id: str,
    payload: ReceiptServiceLineCreate,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> ReceiptServiceLineRead:
    receipt = service_lines_service.get_receipt(
        db, tenant_id=tenant_context.current_tenant_id, receipt_id=receipt_id
    )
    if receipt is None:
        raise HTTPException(status_code=404, detail="Recepcion no encontrada")
    try:
        line = service_lines_service.create_service_line(
            db,
            receipt=receipt,
            tenant_id=tenant_context.current_tenant_id,
            serial=payload.serial,
            service_type=payload.service_type,
            cost=payload.cost,
            notes=payload.notes,
            test_date=payload.test_date,
            next_test_date=payload.next_test_date,
            result=payload.result,
            document_ref=payload.document_ref,
            created_by=tenant_context.current_user_id,
        )
    except service_lines_service.ReceiptCommerciallyClosedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (
        service_lines_service.SerialNotFoundError,
        service_lines_service.ServiceLegalDataError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    db.commit()
    return ReceiptServiceLineRead.model_validate(line)


@router.get(
    "/receipts/{receipt_id}/service-lines",
    response_model=list[ReceiptServiceLineRead],
    dependencies=[REQUIRE_ORDER_READ],
)
def list_service_lines(
    receipt_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> list[ReceiptServiceLineRead]:
    receipt = service_lines_service.get_receipt(
        db, tenant_id=tenant_context.current_tenant_id, receipt_id=receipt_id
    )
    if receipt is None:
        raise HTTPException(status_code=404, detail="Recepcion no encontrada")
    rows = service_lines_service.list_service_lines(
        db, tenant_id=tenant_context.current_tenant_id, receipt=receipt
    )
    return [ReceiptServiceLineRead.model_validate(r) for r in rows]


@router.delete(
    "/receipts/{receipt_id}/service-lines/{line_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[REQUIRE_ORDER_RECEIVE],
)
def delete_service_line(
    receipt_id: str,
    line_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> Response:
    receipt = service_lines_service.get_receipt(
        db, tenant_id=tenant_context.current_tenant_id, receipt_id=receipt_id
    )
    if receipt is None:
        raise HTTPException(status_code=404, detail="Recepcion no encontrada")
    try:
        deleted = service_lines_service.delete_service_line(
            db, receipt=receipt, line_id=line_id
        )
    except service_lines_service.ReceiptCommerciallyClosedError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Linea de servicio no encontrada")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
