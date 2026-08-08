"""Migración: Listado de productos y peso de gas (XLS → PostgreSQL)"""
from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import xlrd
from sqlalchemy import text
from apps.api.app.core.database import build_session_factory
from apps.api.app.core.config import get_settings

XLS_PATH = Path(__file__).resolve().parents[2] / "Contratos" / "Listado de productos y peso de gas. Litros - kg.xls"

# Map sheet names → line codes
SHEET_LINE_MAP = {
    "LISTADO INDUSTRIAL": "GAS_INDUSTRIAL",
    "Gas Liquido": "GAS_LIQUIDO",
    "REFRIGERANTES": "REFRIGERANTES",
    "EXTINTORES": "EXTINTORES",
    "ACETILENO": "ACETILENO",
    "ALIMENTARIO": "GAS_ALIMENTARIO",
}

LINE_NAMES = {
    "GAS_INDUSTRIAL": "Gases Industriales",
    "GAS_LIQUIDO": "Gases Líquidos",
    "REFRIGERANTES": "Refrigerantes",
    "EXTINTORES": "Extintores",
    "ACETILENO": "Acetileno",
    "GAS_ALIMENTARIO": "Gases Alimentarios",
}

UNIT_MAP = {
    "litros": "LITROS",
    "kilos": "KILOS",
    "kilo": "KILOS",
    "kg": "KILOS",
    "m3": "M3",
}


def get_or_create_line(db, *, tenant_id: str, code: str, name: str) -> str:
    row = db.execute(
        text("SELECT id FROM prod_lines WHERE tenant_id = :tid AND code = :code"),
        {"tid": tenant_id, "code": code},
    ).fetchone()
    if row:
        return row[0]
    from uuid import uuid4
    from datetime import datetime, UTC
    line_id = str(uuid4())
    now = datetime.now(UTC)
    db.execute(
        text("INSERT INTO prod_lines (id, tenant_id, code, name, is_active, created_at, updated_at) VALUES (:id, :tid, :code, :name, true, :now, :now)"),
        {"id": line_id, "tid": tenant_id, "code": code, "name": name, "now": now},
    )
    return line_id


def get_or_create_unit(db, *, tenant_id: str, code: str, name: str) -> str:
    row = db.execute(
        text("SELECT id FROM prod_units WHERE tenant_id = :tid AND code = :code"),
        {"tid": tenant_id, "code": code},
    ).fetchone()
    if row:
        return row[0]
    from uuid import uuid4
    from datetime import datetime, UTC
    unit_id = str(uuid4())
    now = datetime.now(UTC)
    db.execute(
        text("INSERT INTO prod_units (id, tenant_id, code, name, is_active, created_at, updated_at) VALUES (:id, :tid, :code, :name, true, :now, :now)"),
        {"id": unit_id, "tid": tenant_id, "code": code, "name": name, "now": now},
    )
    return unit_id


def ensure_status_and_condition(db, *, tenant_id: str) -> None:
    db.execute(text(
        "INSERT INTO prod_status (code, name, is_active) VALUES ('ACTIVE', 'Activo', true) "
        "ON CONFLICT (code) DO NOTHING"
    ))
    db.execute(text(
        "INSERT INTO prod_conditions (code, name, is_active) VALUES ('NEW', 'Nuevo', true) "
        "ON CONFLICT (code) DO NOTHING"
    ))


def parse_number(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def extract_un_number(denomination: str) -> str | None:
    if not denomination:
        return None
    parts = denomination.strip().split()
    if len(parts) >= 2 and parts[0].upper() == "UN":
        return parts[1]
    return None


def extract_product_name(row_values) -> str | None:
    for v in row_values:
        s = str(v).strip() if v else ""
        if s and not s.startswith("UN ") and not s.startswith("EXTINTOR") and len(s) > 3:
            return s
    return None


def migrate():
    settings = get_settings()
    factory = build_session_factory(settings)
    db = factory()

    tenant_id = db.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()[0]
    user_id = db.execute(text("SELECT id FROM users LIMIT 1")).fetchone()[0]

    ensure_status_and_condition(db, tenant_id=tenant_id)

    # Create units
    units = {}
    for code, name in [("LITROS", "Litros"), ("KILOS", "Kilos"), ("M3", "M³")]:
        units[code] = get_or_create_unit(db, tenant_id=tenant_id, code=code, name=name)

    # Create lines
    lines = {}
    for code, name in LINE_NAMES.items():
        lines[code] = get_or_create_line(db, tenant_id=tenant_id, code=code, name=name)

    wb = xlrd.open_workbook(str(XLS_PATH))
    total_created = 0
    total_skipped = 0

    for sheet_name, line_code in SHEET_LINE_MAP.items():
        if sheet_name not in wb.sheet_names():
            print(f"  Saltando {sheet_name} (no existe)")
            continue

        ws = wb.sheet_by_name(sheet_name)
        line_id = lines[line_code]
        print(f"\n--- {sheet_name} ({ws.nrows} filas) → {line_code} ---")

        for r in range(3, ws.nrows):
            row = ws.row_values(r)

            denomination = str(row[0]).strip() if row[0] else ""
            product_name = str(row[1]).strip() if len(row) > 1 and row[1] else ""
            category_raw = row[2] if len(row) > 2 else None
            package_type = str(row[3]).strip() if len(row) > 3 and row[3] else ""
            quantity_raw = row[4] if len(row) > 4 else None
            unit_label = str(row[5]).strip().lower() if len(row) > 5 and row[5] else ""
            m3_raw = row[6] if len(row) > 6 else None
            weight_kg_raw = row[7] if len(row) > 7 else None

            if not product_name:
                continue

            # Determine unit
            unit_code = "KILOS"
            if "litro" in unit_label:
                unit_code = "LITROS"
            elif "m3" in unit_label or "m³" in unit_label:
                unit_code = "M3"

            unit_id = units[unit_code]

            # Parse values
            quantity = parse_number(quantity_raw)
            weight_kg = parse_number(weight_kg_raw)
            content_m3 = parse_number(m3_raw)
            category = str(int(parse_number(category_raw) or 0)) if category_raw else None

            # SKU: sanitize name + quantity
            sku_base = product_name.upper().replace(" ", "").replace("/", "-")[:20]
            sku = f"{sku_base}-{int(quantity) if quantity else 'X'}"

            # Check duplicate
            exists = db.execute(
                text("SELECT id FROM prod_products WHERE tenant_id = :tid AND sku = :sku"),
                {"tid": tenant_id, "sku": sku},
            ).fetchone()
            if exists:
                total_skipped += 1
                continue

            from uuid import uuid4
            product_id = str(uuid4())

            db.execute(text("""
                INSERT INTO prod_products (
                    id, tenant_id, sku, name, description, line_id, unit_id,
                    weight_kg, content_m3, status_code, condition_code,
                    is_service, is_active, created_by, created_at, updated_at
                ) VALUES (
                    :id, :tenant_id, :sku, :name, :description, :line_id, :unit_id,
                    :weight_kg, :content_m3, 'ACTIVE', 'NEW',
                    false, true, :created_by, :now, :now
                )
            """), {
                "id": product_id,
                "tenant_id": tenant_id,
                "sku": sku,
                "name": product_name.strip(),
                "description": denomination[:500] if denomination else None,
                "line_id": line_id,
                "unit_id": unit_id,
                "weight_kg": weight_kg,
                "content_m3": content_m3,
                "created_by": user_id,
                "now": datetime.now(UTC),
            })

            # ADR config
            un_number = extract_un_number(denomination)
            if un_number or category:
                from datetime import date as date_type
                db.execute(text("""
                    INSERT INTO prod_adr (
                        id, tenant_id, product_id, category, packaging_type,
                        net_weight_kg, net_volume_m3, un_number, cargo_description,
                        valid_from, created_by, created_at
                    ) VALUES (
                        :id, :tenant_id, :product_id, :category, :packaging_type,
                        :net_weight_kg, :net_volume_m3, :un_number, :cargo_description,
                        :valid_from, :created_by, :now
                    )
                """), {
                    "id": str(uuid4()),
                    "tenant_id": tenant_id,
                    "product_id": product_id,
                    "category": category,
                    "packaging_type": package_type[:50] if package_type else None,
                    "net_weight_kg": weight_kg,
                    "net_volume_m3": content_m3,
                    "un_number": un_number,
                    "cargo_description": denomination[:500] if denomination else None,
                    "valid_from": date_type.today(),
                    "created_by": user_id,
                    "now": datetime.now(UTC),
                })

            total_created += 1

    db.commit()
    print(f"\n=== Migración completada ===")
    print(f"Creados: {total_created}")
    print(f"Saltados (duplicados): {total_skipped}")

    # Verification
    print("\n--- Verificación ---")
    result = db.execute(text("""
        SELECT l.name, COUNT(*) FROM prod_products p
        JOIN prod_lines l ON p.line_id = l.id
        GROUP BY l.name ORDER BY COUNT(*) DESC
    """))
    for row in result:
        print(f"  {row[0]}: {row[1]}")

    db.close()


if __name__ == "__main__":
    migrate()
