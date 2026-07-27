from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.ventas.cotizacion.backend.models import QuoteDraft, QuoteItem
from plugins.ventas.cotizacion.backend.schemas import (
    AmbiguityError,
    CustomerSummary,
    QuoteDraftResponse,
    QuoteItemResponse,
    ValidationError,
    VehicleSummary,
)

WEEKDAYS: dict[str, int] = {
    "lunes": 0, "martes": 1, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sabado": 5, "domingo": 6,
}

TIME_ALIASES: dict[str, str] = {
    "mañana": "06:00", "manana": "06:00",
    "tarde": "14:00",
    "noche": "20:00",
}

DUPLICATE_WINDOW_SECONDS = 60


def _build_command_hash(tenant_id: str, customer_id: str, items: str, delivery_date: str, delivery_time: str | None, vehicle_id: str | None, conditions: str | None) -> str:
    payload = f"{tenant_id}|{customer_id}|{items}|{delivery_date}|{delivery_time or ''}|{vehicle_id or ''}|{conditions or ''}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _resolve_date(raw: str, reference_date: date | None = None) -> date | None:
    ref = reference_date or date.today()
    normalized = raw.strip().lower()

    if normalized == "hoy":
        return ref
    if normalized in ("mañana", "manana"):
        return ref + timedelta(days=1)
    if normalized in ("pasado mañana", "pasado manana"):
        return ref + timedelta(days=2)

    if normalized in WEEKDAYS:
        target = WEEKDAYS[normalized]
        current = ref.weekday()
        diff = target - current
        if diff <= 0:
            diff += 7
        return ref + timedelta(days=diff)

    iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", raw.strip())
    if iso_match:
        return date(int(iso_match[1]), int(iso_match[2]), int(iso_match[3]))

    return None


def _resolve_time(raw: str) -> time | None:
    normalized = raw.strip().lower()

    if normalized in TIME_ALIASES:
        h, m = TIME_ALIASES[normalized].split(":")
        return time(int(h), int(m))

    time_match = re.match(r"^(\d{1,2})[:h](\d{2})?", normalized)
    if time_match:
        h = int(time_match[1])
        m = int(time_match[2]) if time_match[2] else 0
        if 0 <= h <= 23 and 0 <= m <= 59:
            return time(h, m)

    simple_match = re.match(r"^(\d{1,2})\s*(hrs?|h)$", normalized)
    if simple_match:
        h = int(simple_match[1])
        if 0 <= h <= 23:
            return time(h)

    return None


def _strip_quotes(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().strip('"').strip()


def _extract_tokens(command: str) -> dict[str, Any]:
    command = command.strip()

    action_match = re.match(r"^(cotizar|preview)", command, re.IGNORECASE)
    action = action_match.group(1).lower() if action_match else "cotizar"
    rest = command[action_match.end():].strip() if action_match else command

    dry_run = action == "preview"
    if dry_run:
        rest_match = re.match(r"^cotizar\s+", rest, re.IGNORECASE)
        if rest_match:
            rest = rest[rest_match.end():].strip()

    cliente_raw = None
    vehiculo_raw = None
    condiciones = None
    fecha_raw = None
    hora_raw = None

    cond_match = re.split(r"\bcondicion\b", rest, flags=re.IGNORECASE, maxsplit=1)
    if len(cond_match) > 1:
        rest = cond_match[0].strip()
        condiciones = cond_match[1].strip()

    veh_match = re.split(r"\bvehiculo\b", rest, flags=re.IGNORECASE, maxsplit=1)
    if len(veh_match) > 1:
        rest = veh_match[0].strip()
        veh_parts = veh_match[1].strip().split()
        vehiculo_raw = veh_parts[0] if veh_parts else None

    tokens = rest.split()

    if tokens and tokens[0].lower() == "cliente":
        tokens.pop(0)
        name_parts = []
        for t in tokens:
            lower = t.lower()
            if re.match(r"^\d+$", t):
                break
            if lower in ("hoy", "mañana", "manana", "lunes", "martes", "miercoles",
                          "jueves", "viernes", "sabado", "domingo") or re.match(r"^\d{4}-\d{2}-\d{2}$", t):
                break
            if re.match(r"^\d{1,2}[:h]", t, re.IGNORECASE) or lower in ("tarde", "noche"):
                break
            name_parts.append(t)
        cliente_raw = " ".join(name_parts)
        tokens = tokens[len(name_parts):]

    quantity = None
    product_parts: list[str] = []
    found_quantity = False

    while tokens:
        t = tokens[0]
        lower = t.lower()
        if re.match(r"^\d+$", t) and not found_quantity:
            quantity = int(t)
            found_quantity = True
            tokens.pop(0)
        elif found_quantity:
            if lower in ("hoy", "mañana", "manana", "lunes", "martes", "miercoles",
                          "jueves", "viernes", "sabado", "domingo") or re.match(r"^\d{4}-\d{2}-\d{2}$", t):
                break
            if re.match(r"^\d{1,2}[:h]", t, re.IGNORECASE) or lower in ("tarde", "noche"):
                break
            if lower == "vehiculo" or lower == "condicion":
                break
            product_parts.append(t)
            tokens.pop(0)
        else:
            if lower in ("hoy", "mañana", "manana", "lunes", "martes", "miercoles",
                          "jueves", "viernes", "sabado", "domingo") or re.match(r"^\d{4}-\d{2}-\d{2}$", t):
                fecha_raw = t
                tokens.pop(0)
                if tokens and (re.match(r"^\d{1,2}[:h]", tokens[0], re.IGNORECASE) or tokens[0].lower() in ("tarde", "noche", "mañana", "manana")):
                    hora_raw = tokens.pop(0)
                break
            if re.match(r"^\d{1,2}[:h]", t, re.IGNORECASE) or lower in ("tarde", "noche", "mañana", "manana"):
                hora_raw = t
                tokens.pop(0)
                break
            tokens.pop(0)

    if not fecha_raw and tokens:
        fecha_raw = tokens[0]
        lower = fecha_raw.lower()
        if lower in ("hoy", "mañana", "manana", "lunes", "martes", "miercoles",
                      "jueves", "viernes", "sabado", "domingo") or re.match(r"^\d{4}-\d{2}-\d{2}$", fecha_raw):
            tokens.pop(0)
            if tokens and (re.match(r"^\d{1,2}[:h]", tokens[0], re.IGNORECASE) or tokens[0].lower() in ("tarde", "noche", "mañana", "manana")):
                hora_raw = tokens.pop(0)

    product_raw = " ".join(product_parts) if product_parts else None

    return {
        "action": "cotizar",
        "dry_run": dry_run,
        "cliente_raw": _strip_quotes(cliente_raw),
        "items_raw": [{"cantidad": quantity, "producto": _strip_quotes(product_raw) or ""}] if quantity and product_raw else None,
        "fecha_raw": fecha_raw,
        "hora_raw": hora_raw,
        "vehiculo_raw": _strip_quotes(vehiculo_raw),
        "condiciones": condiciones,
    }


def _search_customer(db: Session, name: str, tenant_id: str) -> tuple[list[dict[str, str]], str | None]:
    from sqlalchemy import text
    result = db.execute(
        text(
            "SELECT id, first_name, last_name, legal_name, commercial_name "
            "FROM crm_customers "
            "WHERE tenant_id = :tenant_id "
            "AND (LOWER(first_name) LIKE :pattern "
            "OR LOWER(last_name) LIKE :pattern "
            "OR LOWER(legal_name) LIKE :pattern "
            "OR LOWER(commercial_name) LIKE :pattern "
            "OR LOWER(first_name || ' ' || last_name) LIKE :pattern) "
            "AND is_active = true "
            "LIMIT 10"
        ),
        {"tenant_id": tenant_id, "pattern": f"%{name.lower()}%"},
    )
    rows = result.fetchall()
    if not rows:
        return [], None
    matches = [
        {
            "id": row[0],
            "name": row[4] or row[3] or f"{row[1] or ''} {row[2] or ''}".strip(),
        }
        for row in rows
    ]
    if len(matches) == 1:
        return matches, matches[0]["id"]
    return matches, None


def _search_product(db: Session, name: str) -> tuple[list[dict[str, str]], str | None]:
    from sqlalchemy import text
    result = db.execute(
        text(
            "SELECT id, name, sku "
            "FROM prod_products "
            "WHERE (LOWER(name) LIKE :pattern OR LOWER(sku) LIKE :pattern) "
            "AND is_active = true "
            "LIMIT 10"
        ),
        {"pattern": f"%{name.lower()}%"},
    )
    rows = result.fetchall()
    if not rows:
        return [], None
    matches = [
        {
            "id": row[0],
            "name": row[1],
            "sku": row[2],
        }
        for row in rows
    ]
    if len(matches) == 1:
        return matches, matches[0]["id"]
    return matches, None


def _search_vehicle(db: Session, plate: str, tenant_id: str) -> tuple[list[dict[str, str]], str | None]:
    from sqlalchemy import text
    result = db.execute(
        text(
            "SELECT id, plate FROM lg_vehicles "
            "WHERE tenant_id = :tenant_id AND UPPER(plate) = :plate "
            "LIMIT 1"
        ),
        {"tenant_id": tenant_id, "plate": plate.upper()},
    )
    rows = result.fetchall()
    if not rows:
        return [], None
    return [{"id": rows[0][0], "plate": rows[0][1]}], rows[0][0]


def handle_cotizar(
    db: Session,
    command: str,
    tenant_id: str,
    user_id: str,
) -> QuoteDraftResponse | ValidationError | AmbiguityError:
    tokens = _extract_tokens(command)

    if not tokens["cliente_raw"]:
        return ValidationError(message="Falta el cliente. Formato: cotizar cliente <nombre> ...")
    if not tokens["items_raw"]:
        return ValidationError(message="Faltan los items. Formato: cotizar cliente <nombre> <cantidad> <producto> ...")
    if not tokens["fecha_raw"]:
        return ValidationError(message="Falta la fecha de entrega. Formato: ... mañana 14h")

    delivery_date = _resolve_date(tokens["fecha_raw"])
    if delivery_date is None:
        return ValidationError(message=f"No se pudo interpretar la fecha '{tokens['fecha_raw']}'. Usá: hoy, mañana, lunes..domingo, o YYYY-MM-DD")

    delivery_time = _resolve_time(tokens["hora_raw"]) if tokens["hora_raw"] else None

    customer_matches, customer_id = _search_customer(db, tokens["cliente_raw"], tenant_id)
    if not customer_matches:
        return ValidationError(
            message=f"No se encontró el cliente '{tokens['cliente_raw']}'.",
            details={"field": "cliente", "raw": tokens["cliente_raw"]},
        )
    if customer_id is None:
        return AmbiguityError(
            message=f"Cliente '{tokens['cliente_raw']}' tiene múltiples matches.",
            entity="cliente",
            options=customer_matches,
        )

    items_data: list[dict] = []
    for raw_item in tokens["items_raw"]:
        product_matches, product_id = _search_product(db, raw_item["producto"])
        if not product_matches:
            return ValidationError(
                message=f"No se encontró el producto '{raw_item['producto']}'.",
                details={"field": "producto", "raw": raw_item["producto"]},
            )
        if product_id is None:
            return AmbiguityError(
                message=f"Producto '{raw_item['producto']}' tiene múltiples matches.",
                entity="producto",
                options=product_matches,
            )
        items_data.append({
            "product_id": product_id,
            "product_name": product_matches[0]["name"],
            "quantity": raw_item["cantidad"],
        })

    vehicle_id: str | None = None
    vehicle_plate: str = ""
    if tokens["vehiculo_raw"]:
        veh_matches, veh_id = _search_vehicle(db, tokens["vehiculo_raw"], tenant_id)
        if not veh_matches:
            return ValidationError(
                message=f"No se encontró el vehículo con placa '{tokens['vehiculo_raw']}'.",
                details={"field": "vehiculo", "raw": tokens["vehiculo_raw"]},
            )
        vehicle_id = veh_id
        vehicle_plate = veh_matches[0]["plate"]

    if tokens["dry_run"]:
        return QuoteDraftResponse(
            id="preview",
            status="PREVIEW",
            customer=CustomerSummary(id=customer_id, name=customer_matches[0]["name"]),
            items=[
                QuoteItemResponse(
                    id="preview",
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    quantity=item["quantity"],
                )
                for item in items_data
            ],
            delivery_date=delivery_date,
            delivery_time=delivery_time,
            vehicle=VehicleSummary(id=vehicle_id, plate=vehicle_plate) if vehicle_id else None,
            conditions=tokens["condiciones"],
            created_at=datetime.now(),
        )

    items_key = "|".join(f"{i['product_id']}:{i['quantity']}" for i in sorted(items_data, key=lambda x: x["product_id"]))
    cmd_hash = _build_command_hash(
        tenant_id, customer_id, items_key,
        delivery_date.isoformat(),
        delivery_time.isoformat() if delivery_time else None,
        vehicle_id, tokens["condiciones"],
    )

    recent = db.execute(
        select(QuoteDraft)
        .where(
            QuoteDraft.tenant_id == tenant_id,
            QuoteDraft.customer_id == customer_id,
            QuoteDraft.status == "DRAFT",
        )
        .order_by(QuoteDraft.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if recent:
        recent_items = db.execute(
            select(QuoteItem).where(QuoteItem.quote_draft_id == recent.id)
        ).scalars().all()
        recent_key = "|".join(f"{i.product_id}:{i.quantity}" for i in sorted(recent_items, key=lambda x: x.product_id))
        recent_hash = _build_command_hash(
            tenant_id, recent.customer_id, recent_key,
            recent.delivery_date.isoformat(),
            recent.delivery_time.isoformat() if recent.delivery_time else None,
            recent.vehicle_id, recent.conditions,
        )
        if cmd_hash == recent_hash:
            elapsed = (datetime.now() - recent.created_at.replace(tzinfo=None)).total_seconds()
            if elapsed < DUPLICATE_WINDOW_SECONDS:
                return ValidationError(
                    message=f"Comando duplicado (ejecutado hace {int(elapsed)}s). Usá 'confirmar' para forzar.",
                    details={"duplicate": True, "existing_id": recent.id},
                )

    draft = QuoteDraft(
        tenant_id=tenant_id,
        customer_id=customer_id,
        customer_name=customer_matches[0]["name"],
        status="DRAFT",
        delivery_date=delivery_date,
        delivery_time=delivery_time,
        vehicle_id=vehicle_id,
        vehicle_plate=vehicle_plate,
        conditions=tokens["condiciones"],
        created_by=user_id,
    )
    db.add(draft)
    db.flush()

    for item_data in items_data:
        item = QuoteItem(
            quote_draft_id=draft.id,
            product_id=item_data["product_id"],
            product_name=item_data["product_name"],
            quantity=item_data["quantity"],
        )
        db.add(item)

    db.commit()

    return QuoteDraftResponse(
        id=draft.id,
        status="DRAFT",
        customer=CustomerSummary(id=customer_id, name=customer_matches[0]["name"]),
        items=[
            QuoteItemResponse(
                id="pending",
                product_id=item["product_id"],
                product_name=item["product_name"],
                quantity=item["quantity"],
            )
            for item in items_data
        ],
        delivery_date=delivery_date,
        delivery_time=delivery_time,
        vehicle=VehicleSummary(id=vehicle_id, plate=vehicle_plate) if vehicle_id else None,
        conditions=tokens["condiciones"],
        created_at=draft.created_at,
    )
