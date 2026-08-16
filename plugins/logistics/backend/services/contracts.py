from __future__ import annotations

import re
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from systutor.kernel.signatures.service import (
    complete_signature_session,
    create_signature_session,
)

from apps.api.app.config import PROJECT_ROOT
from plugins.crm.backend.services.customers import require_customer
from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models.contracts import (
    LogisticsContractType,
    LogisticsCylinderContract,
    LogisticsCylinderContractHistory,
)
from plugins.logistics.backend.models.resources import LogisticsWarehouse
from plugins.logistics.backend.schemas import (
    CylinderContractCreate,
    CylinderContractRenew,
    CylinderContractSign,
    CylinderContractUpdate,
)
from plugins.logistics.backend.services.contract_documents import (
    contract_customer_name,
    render_contract_document,
)

CONTRACT_DOCUMENT_TYPE_CODE = 4
CONTRACT_NUMBER_PREFIX = "CT"
CONTRACT_SEQUENCE_LENGTH = 6
CONTRACT_MEDIA_ROOT = PROJECT_ROOT / "data" / "media" / "contracts"


def build_contract_series(prefix: str, warehouse_code: str, year: int) -> str:
    normalized = "".join(char for char in warehouse_code.upper() if char.isalnum())
    if not normalized:
        raise ValueError("El almacen debe tener un codigo valido para generar la serie")
    return f"{prefix}{normalized}{year % 100:02d}"


def format_contract_number(series: str, number: int) -> str:
    return f"{series}-{number:0{CONTRACT_SEQUENCE_LENGTH}d}"


def _snapshot_customer(customer) -> dict[str, str | None]:
    return {
        "legal_name": customer.legal_name,
        "commercial_name": customer.commercial_name,
        "document_number": customer.document_number,
        "fiscal_address": customer.fiscal_address_id,
        "phone": customer.phone,
        "email": customer.email,
    }


def _resolve_warehouse(
    db: Session,
    *,
    tenant_id: str,
    warehouse_id: str | None,
) -> LogisticsWarehouse:
    if not warehouse_id:
        raise ValueError("El contrato debe tener un almacen asignado")
    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.id == warehouse_id,
            LogisticsWarehouse.tenant_id == tenant_id,
            LogisticsWarehouse.is_active.is_(True),
        )
    )
    if warehouse is None:
        raise LookupError("Warehouse not found")
    return warehouse


def _require_contract_type(db: Session, *, contract_type: str) -> LogisticsContractType:
    contract_type_row = db.scalar(
        select(LogisticsContractType).where(
            LogisticsContractType.code == contract_type,
            LogisticsContractType.is_active.is_(True),
        )
    )
    if contract_type_row is None:
        raise ValueError("Tipo de contrato invalido")
    return contract_type_row


def _next_contract_sequence(db: Session, *, tenant_id: str, series: str) -> int:
    last_number = db.scalar(
        select(func.max(LogisticsCylinderContract.number)).where(
            LogisticsCylinderContract.tenant_id == tenant_id,
            LogisticsCylinderContract.series == series,
        )
    )
    return int(last_number or 0) + 1


def _append_history(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    event_type: str,
    description: str | None,
    created_by: str | None,
) -> None:
    db.add(
        LogisticsCylinderContractHistory(
            tenant_id=contract.tenant_id,
            contract_id=contract.id,
            event_type=event_type,
            description=description,
            created_by=created_by,
        )
    )


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", filename.strip())
    return cleaned or "archivo"


def resolve_contract_file_path(contract: LogisticsCylinderContract) -> Path:
    if not contract.contract_file_path:
        raise ValueError("El contrato no tiene archivo asociado")
    stored_name = contract.contract_file_path.rstrip("/").split("/")[-1]
    return CONTRACT_MEDIA_ROOT / contract.id / stored_name


def upload_contract_file(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    filename: str,
    content: bytes,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    contract_dir = CONTRACT_MEDIA_ROOT / contract.id
    contract_dir.mkdir(parents=True, exist_ok=True)

    if contract.contract_file_path:
        previous = resolve_contract_file_path(contract)
        if previous.exists():
            previous.unlink()

    safe_name = _safe_filename(filename)
    stored_name = f"contract_{contract.id}_{safe_name}"
    file_path = contract_dir / stored_name
    file_path.write_bytes(content)

    contract.contract_file_path = (
        f"/api/v1/plugins/logistics/cylinders/contracts/{contract.id}/file/download/{stored_name}"
    )
    db.add(contract)
    db.flush()
    _append_history(
        db,
        contract=contract,
        event_type="FILE_UPDATED",
        description=f"Archivo de contrato actualizado: {safe_name}",
        created_by=action_context.actor_user_id,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.file_uploaded",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        details={"contract_number": contract.contract_number, "filename": safe_name},
    )
    return contract


def list_contract_types(db: Session) -> list[LogisticsContractType]:
    return list(
        db.scalars(
            select(LogisticsContractType)
            .where(LogisticsContractType.is_active.is_(True))
            .order_by(LogisticsContractType.duration_value.asc(), LogisticsContractType.name.asc())
        ).all()
    )


def list_contracts(
    db: Session,
    *,
    tenant_id: str,
    customer_id: str | None = None,
    status: str | None = None,
    contract_type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> list[LogisticsCylinderContract]:
    stmt = select(LogisticsCylinderContract).where(LogisticsCylinderContract.tenant_id == tenant_id)
    if customer_id:
        stmt = stmt.where(LogisticsCylinderContract.customer_id == customer_id)
    if status:
        stmt = stmt.where(LogisticsCylinderContract.status == status)
    if contract_type:
        stmt = stmt.where(LogisticsCylinderContract.contract_type == contract_type)
    if date_from:
        stmt = stmt.where(LogisticsCylinderContract.start_date >= date_from)
    if date_to:
        stmt = stmt.where(LogisticsCylinderContract.start_date <= date_to)
    stmt = stmt.order_by(LogisticsCylinderContract.created_at.desc())
    return list(db.scalars(stmt).all())


def get_contract(
    db: Session, *, tenant_id: str, contract_id: str
) -> LogisticsCylinderContract | None:
    return db.scalar(
        select(LogisticsCylinderContract).where(
            LogisticsCylinderContract.id == contract_id,
            LogisticsCylinderContract.tenant_id == tenant_id,
        )
    )


def list_contract_history(
    db: Session, *, contract_id: str
) -> list[LogisticsCylinderContractHistory]:
    return list(
        db.scalars(
            select(LogisticsCylinderContractHistory)
            .where(LogisticsCylinderContractHistory.contract_id == contract_id)
            .order_by(LogisticsCylinderContractHistory.occurred_at.desc())
        ).all()
    )


def create_contract(
    db: Session,
    *,
    tenant_id: str,
    created_by: str,
    payload: CylinderContractCreate,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    customer = require_customer(db, tenant_id=tenant_id, customer_id=payload.customer_id)
    _require_contract_type(db, contract_type=payload.contract_type)
    warehouse = _resolve_warehouse(db, tenant_id=tenant_id, warehouse_id=payload.warehouse_id)

    contract = LogisticsCylinderContract(
        tenant_id=tenant_id,
        branch_id=action_context.branch_id,
        warehouse_id=warehouse.id,
        document_type_code=CONTRACT_DOCUMENT_TYPE_CODE,
        document_prefix=CONTRACT_NUMBER_PREFIX,
        contract_type=payload.contract_type,
        status="DRAFT",
        customer_id=customer.id,
        customer_snapshot=_snapshot_customer(customer),
        start_date=payload.start_date,
        end_date=payload.end_date,
        renewal_type=payload.renewal_type,
        cylinder_type_id=payload.cylinder_type_id,
        cylinder_condition=payload.cylinder_condition,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        contract_file_path=payload.contract_file_path,
        notes=payload.notes,
        observations=payload.observations,
        excess_wait_days=payload.excess_wait_days,
        auto_renew_on_excess=payload.auto_renew_on_excess,
        source_contract_id=payload.source_contract_id,
        created_by=created_by,
    )
    db.add(contract)
    db.flush()
    _append_history(
        db,
        contract=contract,
        event_type="CREATED",
        description="Contrato creado en borrador",
        created_by=created_by,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.created",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        details={
            "customer_id": payload.customer_id,
            "contract_type": payload.contract_type,
            "warehouse_id": payload.warehouse_id,
            "quantity": payload.quantity,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder_contract.created",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        payload={
            "customer_id": payload.customer_id,
            "contract_type": payload.contract_type,
            "warehouse_id": payload.warehouse_id,
        },
    )
    return contract


def update_contract(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    payload: CylinderContractUpdate,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    if contract.status not in {"DRAFT", "PENDING_SIGNATURE"}:
        raise ValueError("Solo se pueden editar contratos en borrador o por firmar")
    if payload.contract_type is not None:
        _require_contract_type(db, contract_type=payload.contract_type)
        contract.contract_type = payload.contract_type
    if payload.customer_id is not None:
        customer = require_customer(
            db, tenant_id=contract.tenant_id, customer_id=payload.customer_id
        )
        contract.customer_id = customer.id
        contract.customer_snapshot = _snapshot_customer(customer)
    if payload.warehouse_id is not None:
        warehouse = _resolve_warehouse(
            db, tenant_id=contract.tenant_id, warehouse_id=payload.warehouse_id
        )
        contract.warehouse_id = warehouse.id
    if payload.start_date is not None:
        contract.start_date = payload.start_date
    if payload.end_date is not None:
        contract.end_date = payload.end_date
    if payload.renewal_type is not None:
        contract.renewal_type = payload.renewal_type
    if payload.cylinder_type_id is not None:
        contract.cylinder_type_id = payload.cylinder_type_id
    if payload.cylinder_condition is not None:
        contract.cylinder_condition = payload.cylinder_condition
    if payload.quantity is not None:
        contract.quantity = payload.quantity
    if payload.unit_price is not None:
        contract.unit_price = payload.unit_price
    if payload.contract_file_path is not None:
        contract.contract_file_path = payload.contract_file_path
    if payload.notes is not None:
        contract.notes = payload.notes
    if payload.observations is not None:
        contract.observations = payload.observations
    db.add(contract)
    db.flush()
    _append_history(
        db,
        contract=contract,
        event_type="UPDATED",
        description="Datos del contrato actualizados",
        created_by=action_context.actor_user_id,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.updated",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        details={"status": contract.status},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder_contract.updated",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        payload={"status": contract.status},
    )
    return contract


def activate_contract(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    if contract.status != "DRAFT":
        raise ValueError("Solo se pueden emitir contratos en estado DRAFT")
    if contract.quantity <= 0:
        raise ValueError("La cantidad debe ser mayor a 0")

    warehouse = _resolve_warehouse(
        db, tenant_id=contract.tenant_id, warehouse_id=contract.warehouse_id
    )
    year = datetime.now(UTC).year
    series = build_contract_series(CONTRACT_NUMBER_PREFIX, warehouse.code, year)
    next_number = _next_contract_sequence(db, tenant_id=contract.tenant_id, series=series)

    contract.document_type_code = CONTRACT_DOCUMENT_TYPE_CODE
    contract.document_prefix = CONTRACT_NUMBER_PREFIX
    contract.series = series
    contract.number = next_number
    contract.contract_number = format_contract_number(series, next_number)
    contract.status = "PENDING_SIGNATURE" if not contract.signed_flag else "ACTIVE"
    contract.contract_file_path = render_contract_document(
        db,
        contract=contract,
        created_by=action_context.actor_user_id,
        status="PENDING_SIGNATURE" if contract.status == "PENDING_SIGNATURE" else "SIGNED",
    )

    db.add(contract)
    db.flush()
    _append_history(
        db,
        contract=contract,
        event_type="ISSUED",
        description=f"Contrato emitido con numero {contract.contract_number}",
        created_by=action_context.actor_user_id,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.activated",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        details={
            "contract_number": contract.contract_number,
            "series": contract.series,
            "warehouse_id": contract.warehouse_id,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder_contract.issued",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        payload={
            "contract_number": contract.contract_number,
            "series": contract.series,
            "warehouse_id": contract.warehouse_id,
        },
    )
    return contract


def sign_contract(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    payload: CylinderContractSign,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    if contract.status not in {"PENDING_SIGNATURE", "ACTIVE"}:
        raise ValueError("Solo se pueden firmar contratos emitidos")
    if not contract.contract_number:
        raise ValueError("El contrato debe emitirse antes de firmarse")

    signer_name = payload.signer_name or payload.signed_by or contract_customer_name(contract)
    contract.signed_flag = True
    contract.signed_at = payload.signed_at or datetime.now(UTC)
    contract.signed_by = signer_name
    contract.signature_type = payload.signature_type or "DIGITAL"
    if payload.contract_file_path is not None:
        contract.contract_file_path = payload.contract_file_path
    else:
        contract.contract_file_path = render_contract_document(
            db,
            contract=contract,
            created_by=action_context.actor_user_id,
            status="SIGNED",
            signer_name=signer_name,
        )
    contract.status = "ACTIVE"

    contract_file_path = contract.contract_file_path
    if not contract_file_path:
        raise ValueError("El contrato firmado debe tener un documento asociado")
    document_version_id = contract_file_path.rstrip("/").split("/")[-2]
    session = create_signature_session(
        db,
        tenant_id=contract.tenant_id,
        document_version_id=document_version_id,
        signer_name=signer_name,
        signer_email=payload.signer_email,
        signer_phone=payload.signer_phone,
        signer_role="CUSTOMER",
    )
    complete_signature_session(
        db,
        session=session,
        signer_name=signer_name,
        signer_email=payload.signer_email,
        signer_phone=payload.signer_phone,
        evidence_type="CONTRACT_SIGN",
        evidence_payload={"contract_id": contract.id, "contract_number": contract.contract_number},
    )

    db.add(contract)
    db.flush()
    _append_history(
        db,
        contract=contract,
        event_type="SIGNED",
        description="Contrato marcado como firmado",
        created_by=action_context.actor_user_id,
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder_contract.signed",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        payload={"contract_number": contract.contract_number},
    )
    return contract


def renew_contract(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    payload: CylinderContractRenew,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    if contract.status == "CANCELLED":
        raise ValueError("No se puede renovar un contrato cancelado")
    if payload.end_date is None:
        raise ValueError("La renovacion requiere una nueva fecha de fin")
    if payload.end_date < contract.start_date:
        raise ValueError("La nueva fecha fin no puede ser anterior al inicio")

    contract.end_date = payload.end_date
    if payload.observations is not None:
        contract.observations = payload.observations
    if payload.notes is not None:
        contract.notes = payload.notes
    if payload.renewal_type is not None:
        contract.renewal_type = payload.renewal_type
    if contract.status == "EXPIRED" and payload.end_date >= date.today():
        contract.status = "ACTIVE" if contract.signed_flag else "PENDING_SIGNATURE"
    contract.contract_file_path = render_contract_document(
        db,
        contract=contract,
        created_by=action_context.actor_user_id,
        status="RENEWED",
        signer_name=contract.signed_by,
    )

    db.add(contract)
    db.flush()
    _append_history(
        db,
        contract=contract,
        event_type="RENEWED",
        description=f"Contrato renovado hasta {payload.end_date.isoformat()}",
        created_by=action_context.actor_user_id,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.renewed",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        details={
            "contract_number": contract.contract_number,
            "end_date": payload.end_date.isoformat(),
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder_contract.renewed",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        payload={
            "contract_number": contract.contract_number,
            "end_date": payload.end_date.isoformat(),
        },
    )
    return contract


def terminate_contract(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    reason: str,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    if contract.status not in {"ACTIVE", "PENDING_SIGNATURE"}:
        raise ValueError("Solo se pueden vencer contratos emitidos")
    if not reason.strip():
        raise ValueError("Se requiere un motivo para terminar el contrato")

    contract.status = "EXPIRED"
    contract.terminated_at = datetime.now(UTC)
    contract.termination_reason = reason.strip()
    db.add(contract)
    db.flush()
    _append_history(
        db,
        contract=contract,
        event_type="EXPIRED",
        description=reason.strip(),
        created_by=action_context.actor_user_id,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.terminated",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        details={
            "contract_number": contract.contract_number,
            "reason": reason,
        },
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder_contract.terminated",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        payload={
            "contract_number": contract.contract_number,
            "reason": reason,
        },
    )
    return contract


def cancel_contract(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    action_context: LogisticsActionContext,
) -> LogisticsCylinderContract:
    if contract.status == "CANCELLED":
        raise ValueError("El contrato ya esta cancelado")

    contract.status = "CANCELLED"
    contract.cancelled_at = datetime.now(UTC)
    db.add(contract)
    db.flush()
    _append_history(
        db,
        contract=contract,
        event_type="CANCELLED",
        description="Contrato anulado",
        created_by=action_context.actor_user_id,
    )
    audit_logistics_action(
        db,
        context=action_context,
        action="cylinder_contract.cancelled",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        details={"status": "CANCELLED"},
    )
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.cylinder_contract.cancelled",
        entity_type="cylinder_contract",
        entity_id=contract.id,
        payload={"status": "CANCELLED"},
    )
    return contract
