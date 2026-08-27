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

STATUS_ABIERTA = "ABIERTA"
STATUS_EN_GESTION = "EN_GESTION"
STATUS_RESUELTA = "RESUELTA"
STATUS_ANULADA = "ANULADA"

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
