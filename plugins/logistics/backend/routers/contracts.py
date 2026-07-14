from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Never

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_db_session
from apps.api.app.kernel.auth.dependencies import get_current_tenant_context, require_permission
from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.context import TenantContext
from plugins.logistics.backend.common import build_action_context
from plugins.logistics.backend.schemas import (
    ContractHistoryRead,
    ContractTypeRead,
    CylinderContractActivate,
    CylinderContractCreate,
    CylinderContractRead,
    CylinderContractRenew,
    CylinderContractSign,
    CylinderContractTerminate,
    CylinderContractUpdate,
)
from plugins.logistics.backend.services.contracts import (
    activate_contract,
    cancel_contract,
    create_contract,
    get_contract,
    list_contract_history,
    list_contract_types,
    list_contracts,
    renew_contract,
    resolve_contract_file_path,
    sign_contract,
    terminate_contract,
    update_contract,
    upload_contract_file,
)

router = APIRouter(prefix="/cylinders", tags=["logistics-contracts"])

DB_SESSION = Depends(get_db_session)
TENANT_CONTEXT = Depends(get_current_tenant_context)

REQUIRE_CONTRACT_VIEW = Depends(require_permission("logistics.contract.view"))
REQUIRE_CONTRACT_CREATE = Depends(require_permission("logistics.contract.create"))
REQUIRE_CONTRACT_UPDATE = Depends(require_permission("logistics.contract.update"))
REQUIRE_CONTRACT_ACTIVATE = Depends(require_permission("logistics.contract.activate"))
REQUIRE_CONTRACT_TERMINATE = Depends(require_permission("logistics.contract.terminate"))
REQUIRE_CONTRACT_RENEW = Depends(require_permission("logistics.contract.renew"))
UPLOAD_FILE = File(...)


def _conflict(exc: IntegrityError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc.orig or exc))


def _not_found(entity_name: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity_name} not found")


def _raise_service_error(exc: Exception) -> Never:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    raise exc


def _extract_customer_name(contract) -> str | None:
    snapshot = contract.customer_snapshot
    if snapshot and isinstance(snapshot, dict):
        return snapshot.get("legal_name") or snapshot.get("commercial_name")
    return None


def _contract_to_read(contract) -> CylinderContractRead:
    return CylinderContractRead(
        id=contract.id,
        document_type_code=contract.document_type_code,
        document_prefix=contract.document_prefix,
        warehouse_id=contract.warehouse_id,
        series=contract.series,
        number=contract.number,
        contract_number=contract.contract_number,
        contract_type=contract.contract_type,
        status=contract.status,
        customer_id=contract.customer_id,
        customer_name=_extract_customer_name(contract),
        start_date=contract.start_date,
        end_date=contract.end_date,
        renewal_type=contract.renewal_type,
        cylinder_type_id=contract.cylinder_type_id,
        cylinder_condition=contract.cylinder_condition,
        quantity=contract.quantity,
        unit_price=float(contract.unit_price),
        signed_flag=contract.signed_flag,
        signed_at=contract.signed_at,
        signed_by=contract.signed_by,
        signature_type=contract.signature_type,
        contract_file_path=contract.contract_file_path,
        notes=contract.notes,
        observations=contract.observations,
        created_at=contract.created_at,
    )


@router.get("/contracts/types", response_model=list[ContractTypeRead])
def get_contract_types(
    db: Session = DB_SESSION,
    _: User = REQUIRE_CONTRACT_VIEW,
) -> list[ContractTypeRead]:
    return [ContractTypeRead.model_validate(item) for item in list_contract_types(db)]


@router.get("/contracts", response_model=list[CylinderContractRead])
def get_contracts(
    customer_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    contract_type: str | None = Query(default=None, alias="type"),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_VIEW,
) -> list[CylinderContractRead]:
    parsed_from = date.fromisoformat(date_from) if date_from else None
    parsed_to = date.fromisoformat(date_to) if date_to else None
    return [
        _contract_to_read(contract)
        for contract in list_contracts(
            db,
            tenant_id=tenant_context.current_tenant_id,
            customer_id=customer_id,
            status=status_filter,
            contract_type=contract_type,
            date_from=parsed_from,
            date_to=parsed_to,
        )
    ]


@router.get("/contracts/{contract_id}", response_model=CylinderContractRead)
def get_contract_detail(
    contract_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_VIEW,
) -> CylinderContractRead:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    return _contract_to_read(contract)


@router.post("/contracts/{contract_id}/file", response_model=CylinderContractRead)
async def upload_contract_file_endpoint(
    contract_id: str,
    request: Request,
    file: UploadFile = UPLOAD_FILE,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_UPDATE,
) -> CylinderContractRead:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    try:
        content = await file.read()
        contract = upload_contract_file(
            db,
            contract=contract,
            filename=file.filename or "archivo",
            content=content,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return _contract_to_read(contract)


@router.get("/contracts/{contract_id}/file/download/{stored_name}")
def download_contract_file_endpoint(
    contract_id: str,
    stored_name: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_VIEW,
) -> FileResponse:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    try:
        path = resolve_contract_file_path(contract)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if path.name != Path(stored_name).name or not path.exists():
        raise _not_found("Contract file")
    return FileResponse(path)


@router.get("/contracts/{contract_id}/history", response_model=list[ContractHistoryRead])
def get_contract_history(
    contract_id: str,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_VIEW,
) -> list[ContractHistoryRead]:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    return [
        ContractHistoryRead.model_validate(item)
        for item in list_contract_history(db, contract_id=contract_id)
    ]


@router.post(
    "/contracts",
    response_model=CylinderContractRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contract_endpoint(
    payload: CylinderContractCreate,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_CREATE,
) -> CylinderContractRead:
    try:
        contract = create_contract(
            db,
            tenant_id=tenant_context.current_tenant_id,
            created_by=tenant_context.current_user_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return _contract_to_read(contract)


@router.patch("/contracts/{contract_id}", response_model=CylinderContractRead)
def update_contract_endpoint(
    contract_id: str,
    payload: CylinderContractUpdate,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_UPDATE,
) -> CylinderContractRead:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    try:
        contract = update_contract(
            db,
            contract=contract,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return _contract_to_read(contract)


@router.post("/contracts/{contract_id}/activate", response_model=CylinderContractRead)
@router.post("/contracts/{contract_id}/issue", response_model=CylinderContractRead)
def activate_contract_endpoint(
    contract_id: str,
    _body: CylinderContractActivate | None = None,
    request: Request = None,  # type: ignore[assignment]
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_ACTIVATE,
) -> CylinderContractRead:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    try:
        contract = activate_contract(
            db,
            contract=contract,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(exc) from exc
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return _contract_to_read(contract)


@router.post("/contracts/{contract_id}/sign", response_model=CylinderContractRead)
def sign_contract_endpoint(
    contract_id: str,
    payload: CylinderContractSign,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_UPDATE,
) -> CylinderContractRead:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    try:
        contract = sign_contract(
            db,
            contract=contract,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return _contract_to_read(contract)


@router.post("/contracts/{contract_id}/renew", response_model=CylinderContractRead)
def renew_contract_endpoint(
    contract_id: str,
    payload: CylinderContractRenew,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_RENEW,
) -> CylinderContractRead:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    try:
        contract = renew_contract(
            db,
            contract=contract,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return _contract_to_read(contract)


@router.post("/contracts/{contract_id}/terminate", response_model=CylinderContractRead)
def terminate_contract_endpoint(
    contract_id: str,
    payload: CylinderContractTerminate,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_TERMINATE,
) -> CylinderContractRead:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    try:
        contract = terminate_contract(
            db,
            contract=contract,
            reason=payload.reason,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return _contract_to_read(contract)


@router.post("/contracts/{contract_id}/cancel", response_model=CylinderContractRead)
def cancel_contract_endpoint(
    contract_id: str,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_CONTRACT_UPDATE,
) -> CylinderContractRead:
    contract = get_contract(db, tenant_id=tenant_context.current_tenant_id, contract_id=contract_id)
    if contract is None:
        raise _not_found("Contract")
    try:
        contract = cancel_contract(
            db,
            contract=contract,
            action_context=build_action_context(request, tenant_context),
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
    return _contract_to_read(contract)
