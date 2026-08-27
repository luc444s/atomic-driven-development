from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import (
    ComPurchaseOrder,
    ComPurchaseReceipt,
    ComSupplierClaim,
    ComSupplierClaimEvent,
    ComSupplierInvoice,
)
from plugins.commerce.purchase.backend.schemas.claims import CLAIM_REASONS
from plugins.commerce.purchase.backend.services import invoices as invoices_service

STATUS_ABIERTA = "ABIERTA"
STATUS_EN_GESTION = "EN_GESTION"
STATUS_RESUELTA = "RESUELTA"
STATUS_ANULADA = "ANULADA"

SOURCE_MANUAL = "MANUAL"
SOURCE_DERIVED = "DERIVED"

_DERIVED_DESCRIPTION_PREFIX = "Derivada de conciliación (ítem {order_item_id}): "
_QTY_MISMATCH_TOKEN = "aceptado"
_COST_MISMATCH_PREFIX = "costo facturado"
_SIN_FACTURA_REASON = "sin factura"
_MISMATCH_STATUS = "MISMATCH"

_TERMINAL_STATUSES = {STATUS_RESUELTA, STATUS_ANULADA}
_ALLOWED_TRANSITIONS = {
    STATUS_ABIERTA: {STATUS_EN_GESTION, STATUS_RESUELTA, STATUS_ANULADA},
    STATUS_EN_GESTION: {STATUS_RESUELTA, STATUS_ANULADA},
}


class ClaimTransitionError(ValueError):
    """Transición de estado inválida de una reclamación (→ 409 en HTTP)."""


def _stamp_event(
    db: Session,
    *,
    claim: ComSupplierClaim,
    from_status: str | None,
    to_status: str,
    reason: str | None = None,
    user_id: str | None = None,
) -> None:
    db.add(
        ComSupplierClaimEvent(
            tenant_id=claim.tenant_id,
            claim_id=claim.id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            user_id=user_id,
        )
    )
    db.flush()


def create_claim(
    db: Session,
    *,
    order: ComPurchaseOrder,
    reason: str,
    description: str,
    opened_by: str,
    receipt_id: str | None = None,
    invoice_id: str | None = None,
) -> ComSupplierClaim:
    if reason not in CLAIM_REASONS:
        raise ValueError(f"Motivo de reclamo invalido: {reason}")
    if receipt_id is not None:
        receipt = db.get(ComPurchaseReceipt, receipt_id)
        if receipt is None or receipt.order_id != order.id:
            raise ValueError(f"Recepcion {receipt_id} ajena a la orden")
    if invoice_id is not None:
        invoice = db.get(ComSupplierInvoice, invoice_id)
        if invoice is None or invoice.order_id != order.id:
            raise ValueError(f"Factura {invoice_id} ajena a la orden")

    claim = ComSupplierClaim(
        tenant_id=order.tenant_id,
        order_id=order.id,
        supplier_id=order.supplier_id,
        receipt_id=receipt_id,
        invoice_id=invoice_id,
        reason=reason,
        description=description,
        status=STATUS_ABIERTA,
        opened_by=opened_by,
    )
    db.add(claim)
    db.flush()
    _stamp_event(db, claim=claim, from_status=None, to_status=STATUS_ABIERTA, user_id=opened_by)
    return claim


def list_claims(db: Session, *, order: ComPurchaseOrder) -> list[ComSupplierClaim]:
    stmt = (
        select(ComSupplierClaim)
        .where(
            ComSupplierClaim.tenant_id == order.tenant_id,
            ComSupplierClaim.order_id == order.id,
        )
        .order_by(ComSupplierClaim.opened_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_claim(
    db: Session, *, tenant_id: str, order_id: str, claim_id: str
) -> ComSupplierClaim | None:
    stmt = select(ComSupplierClaim).where(
        ComSupplierClaim.id == claim_id,
        ComSupplierClaim.tenant_id == tenant_id,
        ComSupplierClaim.order_id == order_id,
    )
    return db.scalar(stmt)


def list_events(db: Session, *, claim: ComSupplierClaim) -> list[ComSupplierClaimEvent]:
    stmt = (
        select(ComSupplierClaimEvent)
        .where(ComSupplierClaimEvent.claim_id == claim.id)
        .order_by(ComSupplierClaimEvent.created_at)
    )
    return list(db.scalars(stmt).all())


def _transition(
    db: Session,
    *,
    claim: ComSupplierClaim,
    target: str,
    user_id: str,
    event_reason: str | None = None,
) -> bool:
    """Aplica una transición; True si mutó, False si el destino ya era el actual."""
    if claim.status == target:
        return False
    if claim.status in _TERMINAL_STATUSES:
        raise ClaimTransitionError(
            f"La reclamación está en estado terminal {claim.status}"
        )
    if target not in _ALLOWED_TRANSITIONS[claim.status]:
        raise ClaimTransitionError(f"No se puede pasar de {claim.status} a {target}")
    from_status = claim.status
    claim.status = target
    db.add(claim)
    _stamp_event(
        db,
        claim=claim,
        from_status=from_status,
        to_status=target,
        reason=event_reason,
        user_id=user_id,
    )
    return True


def start_claim(db: Session, *, claim: ComSupplierClaim, user_id: str) -> ComSupplierClaim:
    _transition(db, claim=claim, target=STATUS_EN_GESTION, user_id=user_id)
    return claim


def resolve_claim(
    db: Session, *, claim: ComSupplierClaim, resolution_notes: str, user_id: str
) -> ComSupplierClaim:
    if claim.status == STATUS_RESUELTA:
        return claim
    _transition(db, claim=claim, target=STATUS_RESUELTA, user_id=user_id)
    claim.resolution_notes = resolution_notes
    claim.resolved_by = user_id
    claim.resolved_at = datetime.now(UTC)
    db.add(claim)
    db.flush()
    return claim


def annul_claim(
    db: Session, *, claim: ComSupplierClaim, reason: str, user_id: str
) -> ComSupplierClaim:
    _transition(
        db, claim=claim, target=STATUS_ANULADA, user_id=user_id, event_reason=reason
    )
    return claim


def _derived_description(order_item_id: str, reason_literal: str) -> str:
    return (
        _DERIVED_DESCRIPTION_PREFIX.format(order_item_id=order_item_id)
        + reason_literal
    )


def _derived_item_id(description: str | None) -> str | None:
    prefix = _DERIVED_DESCRIPTION_PREFIX.split("{")[0]
    if not description or not description.startswith(prefix):
        return None
    rest = description[len(prefix):]
    separator = rest.find("): ")
    return rest[:separator] if separator > 0 else None


def _mismatches_to_motives(reason_literal: str | None) -> list[str]:
    """Mapea el `reason` literal del output de conciliación (011) a motivos cerrados.

    - razón de cantidad ("facturado X != aceptado Y") → FALTANTE
    - razón de costo ("costo facturado X != real Y") → PRECIO_INCORRECTO
    - "sin factura" no deriva reclamación (no hay documento que reclamar aún).
    """
    if not reason_literal or reason_literal == _SIN_FACTURA_REASON:
        return []
    motives: list[str] = []
    for part in reason_literal.split("; "):
        if _QTY_MISMATCH_TOKEN in part:
            motives.append("FALTANTE")
        elif part.startswith(_COST_MISMATCH_PREFIX):
            motives.append("PRECIO_INCORRECTO")
    return motives


def _single_active_invoice_id(
    db: Session, *, order: ComPurchaseOrder
) -> str | None:
    invoices = [
        iv
        for iv in invoices_service.list_supplier_invoices(db, order=order)
        if iv.status != "ANULADA"
    ]
    return invoices[0].id if len(invoices) == 1 else None


def _derived_claims_for_order(
    db: Session, *, order: ComPurchaseOrder
) -> list[ComSupplierClaim]:
    stmt = select(ComSupplierClaim).where(
        ComSupplierClaim.tenant_id == order.tenant_id,
        ComSupplierClaim.order_id == order.id,
        ComSupplierClaim.source == SOURCE_DERIVED,
    )
    return list(db.scalars(stmt).all())


def derive_claims_from_reconciliation(
    db: Session, *, order: ComPurchaseOrder, opened_by: str
) -> tuple[list[ComSupplierClaim], int]:
    """Deriva reclamaciones al proveedor desde el MISMATCH de conciliación (011).

    Idempotente: la clave (order_id, order_item_id, reason, invoice_id) de cada
    reclamación DERIVED —con invoice_id NULL casando solo con NULL— bloquea
    duplicados en cualquier estado (incluida ANULADA); claims MANUAL no bloquean.
    El item de orden viaja en la descripción autogenerada (_derived_item_id).

    Devuelve (created, skipped): skipped cuenta MISMATCH que no materializaron
    reclamación — por dedup o por omisión explícita de "sin factura".
    """
    reconciliation = invoices_service.reconcile_order(db, order=order)
    invoice_id = _single_active_invoice_id(db, order=order)

    existing_keys = {
        (item_id, claim.reason, claim.invoice_id)
        for claim in _derived_claims_for_order(db, order=order)
        if (item_id := _derived_item_id(claim.description)) is not None
    }

    created: list[ComSupplierClaim] = []
    skipped = 0
    for item in reconciliation.by_item:
        if item.status != _MISMATCH_STATUS:
            continue
        motives = _mismatches_to_motives(item.reason)
        if not motives:
            skipped += 1
            continue
        for motive in motives:
            key = (item.order_item_id, motive, invoice_id)
            if key in existing_keys:
                skipped += 1
                continue
            claim = create_claim(
                db,
                order=order,
                reason=motive,
                description=_derived_description(item.order_item_id, item.reason),
                opened_by=opened_by,
                invoice_id=invoice_id,
            )
            claim.source = SOURCE_DERIVED
            db.add(claim)
            db.flush()
            existing_keys.add(key)
            created.append(claim)
    return created, skipped
