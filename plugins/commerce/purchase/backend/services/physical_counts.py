"""Conciliación física del inventario en custodia (COMPRAS-017).

Sesión de conteo serial-by-serial sobre la custodia del proveedor (005):
snapshot PERSISTIDO e inmutable al crear, diff al cerrar (FALTANTE /
NO_DECLARADO / CONDICION) y resolución auditada por discrepancia.

La custodia es verdad ajena: aquí com_dispatch_cylinders SOLO se lee
(SELECT); jamás se muta ni se borra historia (§45: las diferencias nunca
se corrigen silenciosamente; ningún cilindro desaparece de trazabilidad).
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import (
    ComDispatch,
    ComDispatchCylinder,
    ComPhysicalCount,
    ComPhysicalCountEvent,
    ComPhysicalCountExpectedSerial,
    ComPhysicalCountItem,
    ComPurchaseOrder,
    ComSupplier,
)
from plugins.logistics.backend.models.cylinder import LogisticsCylinder

STATUS_EN_CURSO = "EN_CURSO"
STATUS_CERRADA = "CERRADA"

DISCREPANCY_FALTANTE = "FALTANTE"
DISCREPANCY_NO_DECLARADO = "NO_DECLARADO"
DISCREPANCY_CONDICION = "CONDICION"

COUNT_RESOLUTIONS = ("RECLAMADA", "ACEPTADA", "OBSERVADA")


class PhysicalCountStateError(ValueError):
    """Operación inválida por el estado de la sesión de conteo (→ 409)."""


def _stamp_event(
    db: Session,
    *,
    count: ComPhysicalCount,
    from_status: str | None,
    to_status: str,
    reason: str | None = None,
    user_id: str | None = None,
) -> None:
    db.add(
        ComPhysicalCountEvent(
            tenant_id=count.tenant_id,
            count_id=count.id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            user_id=user_id,
        )
    )
    db.flush()


def _custody_query(
    db: Session,
    *,
    tenant_id: str,
    supplier_id: str,
    order_id: str | None = None,
    dispatch_id: str | None = None,
):
    """Lectura pura de la custodia EN_CUSTODIA del proveedor (fuente 005)."""
    stmt = (
        select(ComDispatchCylinder, LogisticsCylinder.serial)
        .join(ComDispatch, ComDispatch.id == ComDispatchCylinder.dispatch_id)
        .join(
            LogisticsCylinder,
            LogisticsCylinder.id == ComDispatchCylinder.cylinder_id,
        )
        .where(
            ComDispatchCylinder.tenant_id == tenant_id,
            ComDispatch.supplier_id == supplier_id,
            ComDispatch.status == "DESPACHADO",
            ComDispatchCylinder.status == "EN_CUSTODIA",
        )
        .order_by(ComDispatch.dispatch_date.asc(), ComDispatchCylinder.created_at.asc())
    )
    if order_id is not None:
        stmt = stmt.where(ComDispatch.order_id == order_id)
    if dispatch_id is not None:
        stmt = stmt.where(ComDispatch.id == dispatch_id)
    return db.execute(stmt).all()


def create_count(
    db: Session,
    *,
    tenant_id: str,
    supplier_id: str,
    counted_by: str,
    order_id: str | None = None,
    dispatch_id: str | None = None,
    notes: str | None = None,
) -> ComPhysicalCount:
    """Crea la sesión EN_CURSO y PERSISTE el snapshot de custodia (inmutable)."""
    supplier = db.scalar(
        select(ComSupplier).where(
            ComSupplier.id == supplier_id, ComSupplier.tenant_id == tenant_id
        )
    )
    if supplier is None:
        raise ValueError("Proveedor no encontrado")

    if order_id is not None:
        order = db.scalar(
            select(ComPurchaseOrder).where(
                ComPurchaseOrder.id == order_id,
                ComPurchaseOrder.tenant_id == tenant_id,
                ComPurchaseOrder.supplier_id == supplier_id,
            )
        )
        if order is None:
            raise ValueError("Orden no encontrada o ajena al proveedor")
    if dispatch_id is not None:
        dispatch = db.scalar(
            select(ComDispatch).where(
                ComDispatch.id == dispatch_id,
                ComDispatch.tenant_id == tenant_id,
                ComDispatch.supplier_id == supplier_id,
            )
        )
        if dispatch is None:
            raise ValueError("Despacho no encontrado o ajeno al proveedor")

    custody = _custody_query(
        db,
        tenant_id=tenant_id,
        supplier_id=supplier_id,
        order_id=order_id,
        dispatch_id=dispatch_id,
    )

    count = ComPhysicalCount(
        tenant_id=tenant_id,
        supplier_id=supplier_id,
        order_id=order_id,
        dispatch_id=dispatch_id,
        expected_total=len(custody),
        found_total=0,
        match_count=0,
        status=STATUS_EN_CURSO,
        counted_by=counted_by,
        notes=notes,
    )
    db.add(count)
    db.flush()

    for item, serial in custody:
        db.add(
            ComPhysicalCountExpectedSerial(
                tenant_id=tenant_id,
                count_id=count.id,
                cylinder_id=item.cylinder_id,
                serial=serial or item.cylinder_id,
            )
        )
    db.flush()

    _stamp_event(
        db,
        count=count,
        from_status=None,
        to_status=STATUS_EN_CURSO,
        reason=notes,
        user_id=counted_by,
    )
    return count


def get_count(
    db: Session, *, tenant_id: str, count_id: str
) -> ComPhysicalCount | None:
    return db.scalar(
        select(ComPhysicalCount).where(
            ComPhysicalCount.id == count_id,
            ComPhysicalCount.tenant_id == tenant_id,
        )
    )


def list_counts(
    db: Session,
    *,
    tenant_id: str,
    supplier_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[ComPhysicalCount], int]:
    stmt = select(ComPhysicalCount).where(ComPhysicalCount.tenant_id == tenant_id)
    count_stmt = select(func.count()).select_from(ComPhysicalCount).where(
        ComPhysicalCount.tenant_id == tenant_id
    )
    if supplier_id:
        stmt = stmt.where(ComPhysicalCount.supplier_id == supplier_id)
        count_stmt = count_stmt.where(ComPhysicalCount.supplier_id == supplier_id)
    if status:
        stmt = stmt.where(ComPhysicalCount.status == status)
        count_stmt = count_stmt.where(ComPhysicalCount.status == status)
    total = db.scalar(count_stmt) or 0
    stmt = stmt.order_by(ComPhysicalCount.counted_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all()), total


def list_expected_serials(
    db: Session, *, count: ComPhysicalCount
) -> list[ComPhysicalCountExpectedSerial]:
    stmt = (
        select(ComPhysicalCountExpectedSerial)
        .where(ComPhysicalCountExpectedSerial.count_id == count.id)
        .order_by(ComPhysicalCountExpectedSerial.serial.asc())
    )
    return list(db.scalars(stmt).all())


def list_items(db: Session, *, count: ComPhysicalCount) -> list[ComPhysicalCountItem]:
    stmt = (
        select(ComPhysicalCountItem)
        .where(ComPhysicalCountItem.count_id == count.id)
        .order_by(ComPhysicalCountItem.serial.asc())
    )
    return list(db.scalars(stmt).all())


def list_events(db: Session, *, count: ComPhysicalCount) -> list[ComPhysicalCountEvent]:
    stmt = (
        select(ComPhysicalCountEvent)
        .where(ComPhysicalCountEvent.count_id == count.id)
        .order_by(ComPhysicalCountEvent.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def _cylinder_id_by_serial(db: Session, *, tenant_id: str, serial: str) -> str | None:
    return db.scalar(
        select(LogisticsCylinder.id).where(
            LogisticsCylinder.tenant_id == tenant_id,
            LogisticsCylinder.serial == serial,
        )
    )


def close_count(
    db: Session,
    *,
    count: ComPhysicalCount,
    found_payload: list[dict],
    closed_by: str,
    notes: str | None = None,
) -> ComPhysicalCount:
    """Diff contra el snapshot PERSISTIDO → ítems de discrepancia + totales.

    NO_DECLARADO precede sobre CONDICION: un serial no esperado es
    NO_DECLARADO y su condition_note se conserva en `notes` del ítem.
    """
    if count.status != STATUS_EN_CURSO:
        raise PhysicalCountStateError(
            f"La sesión de conteo ya está {count.status}"
        )

    found_by_serial: dict[str, str | None] = {}
    for entry in found_payload:
        serial = (entry.get("serial") or "").strip()
        if not serial:
            raise ValueError("Serial contado vacío")
        if serial in found_by_serial:
            raise ValueError(f"Serial duplicado en el conteo: {serial}")
        found_by_serial[serial] = entry.get("condition_note")

    # Base del diff: SIEMPRE el snapshot persistido al crear, no la custodia
    # actual (el snapshot sobrevive reinicios y cierre; es la auditoría).
    snapshot = list_expected_serials(db, count=count)
    pending_found = dict(found_by_serial)

    faltantes: list[ComPhysicalCountExpectedSerial] = []
    matches: list[tuple[ComPhysicalCountExpectedSerial, str | None]] = []
    for row in snapshot:
        if row.serial in pending_found:
            note = pending_found.pop(row.serial)
            matches.append((row, note))
        else:
            faltantes.append(row)

    undeclared: list[tuple[str, str | None]] = sorted(pending_found.items())

    for row in faltantes:
        db.add(
            ComPhysicalCountItem(
                tenant_id=count.tenant_id,
                count_id=count.id,
                cylinder_id=row.cylinder_id,
                serial=row.serial,
                expected=True,
                found=False,
                discrepancy_type=DISCREPANCY_FALTANTE,
            )
        )
    for row, condition_note in matches:
        if condition_note:
            db.add(
                ComPhysicalCountItem(
                    tenant_id=count.tenant_id,
                    count_id=count.id,
                    cylinder_id=row.cylinder_id,
                    serial=row.serial,
                    expected=True,
                    found=True,
                    discrepancy_type=DISCREPANCY_CONDICION,
                    notes=condition_note,
                )
            )
    for serial, condition_note in undeclared:
        cylinder_id = _cylinder_id_by_serial(db, tenant_id=count.tenant_id, serial=serial)
        if cylinder_id is None:
            raise ValueError(
                f"Serial {serial} no corresponde a un envase registrado en el sistema"
            )
        db.add(
            ComPhysicalCountItem(
                tenant_id=count.tenant_id,
                count_id=count.id,
                cylinder_id=cylinder_id,
                serial=serial,
                expected=False,
                found=True,
                discrepancy_type=DISCREPANCY_NO_DECLARADO,
                notes=condition_note,
            )
        )
    db.flush()

    count.expected_total = len(snapshot)
    count.found_total = len(found_by_serial)
    count.match_count = len(matches)
    count.status = STATUS_CERRADA
    count.closed_at = datetime.now(UTC)
    if notes:
        count.notes = f"{count.notes}\n{notes}" if count.notes else notes
    db.add(count)

    _stamp_event(
        db,
        count=count,
        from_status=STATUS_EN_CURSO,
        to_status=STATUS_CERRADA,
        reason=notes,
        user_id=closed_by,
    )
    return count


def resolve_item(
    db: Session,
    *,
    count: ComPhysicalCount,
    item_id: str,
    resolution: str,
    reason: str,
    resolved_by: str,
) -> ComPhysicalCountItem:
    """Resuelve UNA discrepancia con evento auditable (append-only)."""
    if resolution not in COUNT_RESOLUTIONS:
        raise ValueError(f"Resolución inválida: {resolution}")
    if count.status != STATUS_CERRADA:
        raise PhysicalCountStateError(
            "Solo se resuelven discrepancias de una sesión CERRADA"
        )
    item = db.scalar(
        select(ComPhysicalCountItem).where(
            ComPhysicalCountItem.id == item_id,
            ComPhysicalCountItem.count_id == count.id,
            ComPhysicalCountItem.tenant_id == count.tenant_id,
        )
    )
    if item is None:
        raise ValueError("Discrepancia no encontrada")
    if item.resolution is not None:
        raise PhysicalCountStateError(
            f"La discrepancia {item.serial} ya fue resuelta ({item.resolution})"
        )

    item.resolution = resolution
    item.resolved_by = resolved_by
    item.resolved_at = datetime.now(UTC)
    db.add(item)

    _stamp_event(
        db,
        count=count,
        from_status=item.discrepancy_type,
        to_status=resolution,
        reason=f"[{item.serial}] {reason}",
        user_id=resolved_by,
    )
    return item
