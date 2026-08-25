"""Despacho por serial y custodia del proveedor (COMPRAS-005).

Compras lee identidad/estado del cilindro en Logistics (lg_cylinders) pero
NUNCA escribe en modelos lg_* (§32 VISION-001). La custodia es estado
derivado: filas com_dispatch_cylinders con status='EN_CUSTODIA'.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from plugins.commerce.purchase.backend.models import (
    ComDispatch,
    ComDispatchCylinder,
    ComSupplier,
)
from plugins.logistics.backend.models.cylinder import LogisticsCylinder

# Estados logísticos que impiden enviar un cilindro a proveedor (§8).
BLOCKED_CYLINDER_STATES = {"BLOQUEADO", "DE_BAJA", "PERDIDO"}

DISPATCH_STATUSES = ("PREPARADO", "DESPACHADO", "RETORNADO", "CANCELADO")
CYLINDER_ITEM_STATUSES = ("PENDIENTE", "EN_CUSTODIA", "DEVUELTO")

TRANSITIONS: dict[str, set[str]] = {
    "PREPARADO": {"DESPACHADO", "CANCELADO"},
    "DESPACHADO": {"RETORNADO"},
    "RETORNADO": set(),
    "CANCELADO": set(),
}

OPERATIONAL_SESSION_STATUSES = ("READY_TO_DEPART", "OUTBOUND", "RETURNING")


def _validate_status_transition(current: str, target: str) -> None:
    if target not in TRANSITIONS.get(current, set()):
        raise ValueError(f"No se puede pasar de {current} a {target}")


def _validate_cylinder(db: Session, *, tenant_id: str, cylinder_id: str) -> LogisticsCylinder:
    """Lectura pura sobre Logistics: identidad + estado activo (§32)."""
    cylinder = db.scalar(
        select(LogisticsCylinder).where(
            LogisticsCylinder.id == cylinder_id,
            LogisticsCylinder.tenant_id == tenant_id,
        )
    )
    if cylinder is None:
        raise ValueError(f"Cilindro {cylinder_id} no encontrado")
    if cylinder.current_state in BLOCKED_CYLINDER_STATES:
        raise ValueError(
            f"Cilindro {cylinder.serial or cylinder_id} no disponible "
            f"(estado {cylinder.current_state})"
        )
    return cylinder


def _validate_not_in_open_custody(
    db: Session,
    *,
    tenant_id: str,
    cylinder_ids: list[str],
    exclude_dispatch_id: str | None = None,
) -> None:
    """Un cilindro no puede estar en custodia (despacho DESPACHADO) de dos
    proveedores a la vez. Despachos PREPARADO no generan custodia."""
    if not cylinder_ids:
        return
    stmt = (
        select(ComDispatchCylinder.cylinder_id)
        .join(ComDispatch, ComDispatch.id == ComDispatchCylinder.dispatch_id)
        .where(
            ComDispatchCylinder.tenant_id == tenant_id,
            ComDispatch.status == "DESPACHADO",
            ComDispatchCylinder.status == "EN_CUSTODIA",
            ComDispatchCylinder.cylinder_id.in_(cylinder_ids),
        )
    )
    if exclude_dispatch_id:
        stmt = stmt.where(ComDispatchCylinder.dispatch_id != exclude_dispatch_id)
    found = set(db.scalars(stmt).all())
    if found:
        raise ValueError(
            "Cilindros ya en custodia de otro despacho: "
            + ", ".join(sorted(found))
        )


def create_dispatch(
    db: Session,
    *,
    tenant_id: str,
    supplier_id: str,
    order_id: str | None,
    warehouse_id: str | None,
    dispatch_date: date | None,
    carrier: str | None,
    vehicle_plate: str | None,
    driver_name: str | None,
    notes: str | None,
    cylinders_payload: list[dict],
    created_by: str,
) -> ComDispatch:
    supplier = db.scalar(
        select(ComSupplier).where(
            ComSupplier.id == supplier_id, ComSupplier.tenant_id == tenant_id
        )
    )
    if supplier is None:
        raise ValueError("Proveedor no encontrado")

    seen: set[str] = set()
    for entry in cylinders_payload:
        cid = entry["cylinder_id"]
        if cid in seen:
            raise ValueError(f"Serial duplicado dentro del despacho: {cid}")
        seen.add(cid)

    # Validaciones §8: existencia, tenant, estado activo, custodia ajena.
    for cid in seen:
        _validate_cylinder(db, tenant_id=tenant_id, cylinder_id=cid)
    _validate_not_in_open_custody(db, tenant_id=tenant_id, cylinder_ids=sorted(seen))

    dispatch = ComDispatch(
        tenant_id=tenant_id,
        supplier_id=supplier_id,
        order_id=order_id,
        warehouse_id=warehouse_id,
        dispatch_date=dispatch_date or date.today(),
        carrier=carrier,
        vehicle_plate=vehicle_plate,
        driver_name=driver_name,
        status="PREPARADO",
        notes=notes,
        created_by=created_by,
    )
    db.add(dispatch)
    db.flush()

    for entry in cylinders_payload:
        db.add(ComDispatchCylinder(
            tenant_id=tenant_id,
            dispatch_id=dispatch.id,
            cylinder_id=entry["cylinder_id"],
            product_id=entry.get("product_id"),
            service_type=entry.get("service_type") or "LLENADO",
            status="PENDIENTE",
            notes=entry.get("notes"),
        ))
    db.flush()
    return dispatch


def get_dispatch(db: Session, *, tenant_id: str, dispatch_id: str) -> ComDispatch | None:
    return db.scalar(
        select(ComDispatch).where(
            ComDispatch.tenant_id == tenant_id,
            ComDispatch.id == dispatch_id,
        )
    )


def list_dispatches(
    db: Session,
    *,
    tenant_id: str,
    supplier_id: str | None = None,
    status: str | None = None,
    order_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[ComDispatch], int]:
    stmt = select(ComDispatch).where(ComDispatch.tenant_id == tenant_id)
    count_stmt = select(func.count()).select_from(ComDispatch).where(
        ComDispatch.tenant_id == tenant_id
    )
    if supplier_id:
        stmt = stmt.where(ComDispatch.supplier_id == supplier_id)
        count_stmt = count_stmt.where(ComDispatch.supplier_id == supplier_id)
    if status:
        stmt = stmt.where(ComDispatch.status == status)
        count_stmt = count_stmt.where(ComDispatch.status == status)
    if order_id:
        stmt = stmt.where(ComDispatch.order_id == order_id)
        count_stmt = count_stmt.where(ComDispatch.order_id == order_id)
    total = db.scalar(count_stmt) or 0
    stmt = stmt.order_by(ComDispatch.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(stmt).all()), total


def transition(
    db: Session,
    *,
    dispatch: ComDispatch,
    target: str,
) -> ComDispatch:
    """Única puerta de mutación de status del despacho."""
    _validate_status_transition(dispatch.status, target)

    if target == "DESPACHADO":
        items = list(dispatch.cylinders)  # type: ignore[attr-defined]
        if not items:
            raise ValueError("No se puede despachar sin cilindros")
        # Re-valida custodia ajena justo antes de confirmar la salida física.
        _validate_not_in_open_custody(
            db,
            tenant_id=dispatch.tenant_id,
            cylinder_ids=[i.cylinder_id for i in items],
            exclude_dispatch_id=dispatch.id,
        )
        # La custodia nace aquí: los items pasan a EN_CUSTODIA.
        for item in items:
            item.status = "EN_CUSTODIA"
            db.add(item)

    dispatch.status = target
    db.add(dispatch)
    db.flush()
    return dispatch


def custody_entries(
    db: Session,
    *,
    tenant_id: str,
    supplier_id: str,
    days_gt: int | None = None,
) -> list[dict]:
    """Filas EN_CUSTODIA de un proveedor con días fuera (§11/§12)."""
    rows = db.execute(
        select(ComDispatchCylinder, ComDispatch)
        .join(ComDispatch, ComDispatch.id == ComDispatchCylinder.dispatch_id)
        .where(
            ComDispatchCylinder.tenant_id == tenant_id,
            ComDispatch.supplier_id == supplier_id,
            ComDispatch.status == "DESPACHADO",
            ComDispatchCylinder.status == "EN_CUSTODIA",
        )
        .order_by(ComDispatch.dispatch_date.asc())
    ).all()

    today = date.today()
    entries: list[dict] = []
    for item, dispatch in rows:
        days_out = (today - dispatch.dispatch_date).days
        if days_gt is not None and days_out <= days_gt:
            continue
        serial = db.scalar(
            select(LogisticsCylinder.serial).where(
                LogisticsCylinder.id == item.cylinder_id,
                LogisticsCylinder.tenant_id == tenant_id,
            )
        )
        entries.append({
            "dispatch_id": dispatch.id,
            "dispatch_date": dispatch.dispatch_date,
            "cylinder_id": item.cylinder_id,
            "serial": serial,
            "product_id": item.product_id,
            "service_type": item.service_type,
            "days_out": days_out,
            "order_id": dispatch.order_id,
        })
    return entries


def custody_summary(db: Session, *, tenant_id: str) -> list[dict]:
    """Conteo de envases en custodia y antigüedad máxima por proveedor (§40)."""
    rows = db.execute(
        select(
            ComDispatch.supplier_id,
            ComSupplier.name,
            func.count(ComDispatchCylinder.id),
            func.min(ComDispatch.dispatch_date),
        )
        .join(ComDispatch, ComDispatch.id == ComDispatchCylinder.dispatch_id)
        .join(ComSupplier, ComSupplier.id == ComDispatch.supplier_id)
        .where(
            ComDispatchCylinder.tenant_id == tenant_id,
            ComDispatch.status == "DESPACHADO",
            ComDispatchCylinder.status == "EN_CUSTODIA",
        )
        .group_by(ComDispatch.supplier_id, ComSupplier.name)
        .order_by(func.count(ComDispatchCylinder.id).desc())
    ).all()

    today = date.today()
    return [
        {
            "supplier_id": supplier_id,
            "supplier_name": name,
            "total_cylinders": total,
            "oldest_days_out": (today - oldest).days if oldest else 0,
        }
        for supplier_id, name, total, oldest in rows
    ]


def register_return(
    db: Session,
    *,
    tenant_id: str,
    dispatch: ComDispatch,
    cylinder_ids: list[str],
    notes: str | None = None,
) -> ComDispatch:
    """Retorno parcial/total por serial (§43): marca DEVUELTO solo lo listado.

    Cuando ya no queda ningún EN_CUSTODIA, el despacho transiciona a
    RETORNADO (custodia resuelta). Los seriales no listados siguen en
    custodia y visibles.
    """
    if dispatch.status != "DESPACHADO":
        raise ValueError(
            f"Solo se registra retorno de despachos DESPACHADO (actual: {dispatch.status})"
        )
    items = {i.cylinder_id: i for i in dispatch.cylinders}  # type: ignore[attr-defined]

    unknown = [cid for cid in cylinder_ids if cid not in items]
    if unknown:
        raise ValueError(f"Seriales que no pertenecen a este despacho: {', '.join(unknown)}")

    already = [
        cid for cid in cylinder_ids if items[cid].status == "DEVUELTO"
    ]
    if already:
        raise ValueError(f"Seriales ya devueltos: {', '.join(already)}")
    if not cylinder_ids:
        raise ValueError("Lista de seriales vacía")

    now = datetime.now(timezone.utc)
    for cid in cylinder_ids:
        item = items[cid]
        item.status = "DEVUELTO"
        item.returned_at = now
        if notes:
            item.notes = notes
        db.add(item)
    db.flush()

    remaining = db.scalar(
        select(func.count(ComDispatchCylinder.id)).where(
            ComDispatchCylinder.dispatch_id == dispatch.id,
            ComDispatchCylinder.status == "EN_CUSTODIA",
        )
    ) or 0

    target = "RETORNADO" if remaining == 0 else "DESPACHADO"
    _validate_status_transition(dispatch.status, target)
    dispatch.status = target
    db.add(dispatch)
    db.flush()
    return dispatch


def set_session_link(
    db: Session,
    *,
    tenant_id: str,
    dispatch: ComDispatch,
    kind: str,
    session_id: str | None,
) -> ComDispatch:
    """Vínculo OPCIONAL despacho↔jornada (§9/§32). Referencia pura: jamás
    modifica estados de Logística. Desvinculable solo en PREPARADO."""
    from plugins.logistics.backend.models.sessions import LogisticsVehicleSession

    if kind not in ("outbound", "return"):
        raise ValueError("kind debe ser outbound o return")
    if dispatch.status == "CANCELADO":
        raise ValueError("No se modifica un despacho cancelado")
    if session_id is not None and dispatch.status != "PREPARADO":
        raise ValueError(
            "La sesión solo puede asignarse mientras el despacho está PREPARADO"
        )

    column = "session_id" if kind == "outbound" else "return_session_id"
    if session_id is not None:
        session = db.scalar(
            select(LogisticsVehicleSession).where(
                LogisticsVehicleSession.tenant_id == tenant_id,
                LogisticsVehicleSession.id == session_id,
            )
        )
        if session is None:
            raise ValueError("Jornada no encontrada")
        if session.status not in OPERATIONAL_SESSION_STATUSES:
            raise ValueError(
                f"La jornada debe estar en estado operativo "
                f"(actual: {session.status})"
            )

    setattr(dispatch, column, session_id)
    db.add(dispatch)
    db.flush()
    return dispatch
