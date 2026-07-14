from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.kernel.documents.service import build_document_download_url, render_document_pdf
from plugins.logistics.backend.models.contracts import LogisticsCylinderContract
from plugins.productos.backend.models import Product

CONTRACT_DOCUMENT_TEMPLATE = "logistics.cylinder_contract"
CONTRACT_DOCUMENT_MODULE = "logistics"
CONTRACT_DOCUMENT_ENTITY = "cylinder_contract"
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_uuid_text(value: str | None) -> bool:
    return bool(value and UUID_PATTERN.match(value.strip()))


def contract_customer_name(contract: LogisticsCylinderContract) -> str:
    customer_snapshot = contract.customer_snapshot or {}
    return str(
        customer_snapshot.get("legal_name")
        or customer_snapshot.get("commercial_name")
        or "Cliente"
    )


def _contract_product_name(db: Session, contract: LogisticsCylinderContract) -> str:
    if not contract.cylinder_type_id:
        return "-"
    product_name = db.scalar(
        select(Product.name).where(
            Product.tenant_id == contract.tenant_id,
            Product.id == contract.cylinder_type_id,
        )
    )
    if product_name:
        return str(product_name)
    if is_uuid_text(contract.cylinder_type_id):
        return "Producto no resuelto"
    return contract.cylinder_type_id


def _display_signer_name(
    contract: LogisticsCylinderContract,
    signer_name: str | None,
) -> str | None:
    if signer_name:
        return contract_customer_name(contract) if is_uuid_text(signer_name) else signer_name
    if contract.signed_by:
        if is_uuid_text(contract.signed_by):
            return contract_customer_name(contract)
        return contract.signed_by
    return None


def _contract_document_payload(
    db: Session,
    contract: LogisticsCylinderContract,
    *,
    title: str,
    signer_name: str | None = None,
) -> dict[str, object]:
    display_signer = _display_signer_name(contract, signer_name)
    lines = [
        f"Contrato: {contract.contract_number or '(borrador)'}",
        f"Cliente: {contract_customer_name(contract)}",
        f"Tipo: {contract.contract_type}",
        f"Inicio: {contract.start_date.isoformat()}",
        f"Fin: {contract.end_date.isoformat() if contract.end_date else '-'}",
        f"Producto/envase: {_contract_product_name(db, contract)}",
        f"Condicion: {contract.cylinder_condition or '-'}",
        f"Cantidad contratada: {contract.quantity}",
        f"Precio unitario: {contract.unit_price}",
        f"Estado: {contract.status}",
    ]
    if display_signer:
        lines.append(f"Firmante: {display_signer}")
    if contract.notes:
        lines.append(f"Notas: {contract.notes}")
    if contract.observations:
        lines.append(f"Observaciones: {contract.observations}")
    return {"document_title": title, "document_lines": lines}


def render_contract_document(
    db: Session,
    *,
    contract: LogisticsCylinderContract,
    created_by: str | None,
    status: str,
    signer_name: str | None = None,
) -> str:
    document = render_document_pdf(
        db,
        tenant_id=contract.tenant_id,
        module=CONTRACT_DOCUMENT_MODULE,
        entity_type=CONTRACT_DOCUMENT_ENTITY,
        entity_id=contract.id,
        template_code=CONTRACT_DOCUMENT_TEMPLATE,
        payload=_contract_document_payload(
            db,
            contract,
            title=f"Contrato {contract.contract_number or contract.id}",
            signer_name=signer_name,
        ),
        created_by=created_by,
        status=status,
    )
    return build_document_download_url(document.id)
