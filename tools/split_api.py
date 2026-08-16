#!/usr/bin/env python3
"""
Navaja: split_api.py

Divide un archivo api.ts de frontend en un paquete api/
con un archivo por dominio mas index.ts retrocompatible.

Uso:
  python3 tools/split_api.py plugins/logistics/frontend/api.ts

  # mapping opcional: sobreescribe dominios detectados
  python3 tools/split_api.py ruta/api.ts --mapping mapping.json

El mapping.json es un dict { "nombre_exportado": "dominio" }.
Los no listados usan deteccion automatica.
Los marcados con "_removed" no se incluyen en ningun modulo.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

# ── parsing ─────────────────────────────────────────────────────────


def _find_export_end(lines: list[str], start: int) -> int:
    """Find the end line (exclusive) of an export declaration starting at `start`."""
    brace_depth = 0
    paren_depth = 0
    was_in_block = False  # became True after first '{'

    i = start
    while i < len(lines):
        line = lines[i]
        for ch in line:
            if ch == "{":
                brace_depth += 1
                was_in_block = True
            elif ch == "}":
                brace_depth -= 1
            elif ch == "(":
                paren_depth += 1
            elif ch == ")":
                paren_depth -= 1

        stripped = line.strip()
        if brace_depth == 0:
            # Function/type body just closed, or single-line export
            if was_in_block and (stripped == "}" or stripped == "});"):
                return i + 1
            if was_in_block and stripped.endswith("};"):
                return i + 1
            if not was_in_block and stripped.endswith(";"):
                return i + 1

        i += 1
    return len(lines)


def parse_exports(text: str) -> list[dict]:
    """
    Retorna lista de exports con {kind, name, start, end, lines}.
    kind: "type" | "const" | "function" | "import" | "other"
    """
    lines = text.splitlines(keepends=True)
    exports: list[dict] = []
    i = 0

    import_re = re.compile(r"^(import\s)")
    export_re = re.compile(
        r"^(export\s+(?:type|const|function|async\s+function))\s+(\w+)"
    )

    while i < len(lines):
        stripped = lines[i].strip()

        # import block
        m = import_re.match(stripped)
        if m:
            start = i
            while i < len(lines) and ";" not in lines[i]:
                i += 1
            i += 1
            exports.append({
                "kind": "import",
                "name": None,
                "start": start,
                "end": i,
                "lines": lines[start:i],
            })
            continue

        # export type / const / (async) function
        m = export_re.match(stripped)
        if m:
            raw_kind = m.group(1).strip()
            name = m.group(2)
            kind = {
                "type": "type",
                "const": "const",
                "function": "function",
                "async function": "function",
            }.get(raw_kind, raw_kind)

            end = _find_export_end(lines, i)
            exports.append({
                "kind": kind,
                "name": name,
                "start": i,
                "end": end,
                "lines": lines[i:end],
            })
            i = end
            continue

        # blank / comment / non-exported code
        if not exports or exports[-1]["kind"] != "other":
            exports.append({
                "kind": "other",
                "name": None,
                "start": i,
                "end": i + 1,
                "lines": [],
            })
        exports[-1]["lines"].append(lines[i])
        exports[-1]["end"] = i + 1
        i += 1

    return exports


# ── domain detection ────────────────────────────────────────────────


# Reglas: nombre de dominio → lista de regex
# Se evaluan en orden, primera coincidencia gana.
DOMAIN_RULES: list[tuple[str, list[str]]] = [
    # cylinder-weight antes que cylinders para evitar match greedy
    ("cylinder-weight", [
        r"CylinderWeight",
        r"ProductContent",
        r"(?:list|get|create|update|delete)AvailableCylindersWithWeight",
        r"(?:list|get|create|update|delete)CylinderWeight",
        r"(?:list|get|create|update|delete)ProductContent",
    ]),
    # Entidades core con prefijo Logistics
    ("cylinders", [
        r"^LogisticsCylinder",
        r"^Logistics(?:GasProduct|Brand$|ServiceType$|HydrostaticTest|Warranty|Retimbrado|Ownership|LabelHistory|LabelData|ScanLog|CylinderService)",
        r"CylinderEntryMode",
        r"(?:Create|Update|Transition)Cylinder",
        r"(?:list|get|create|update|delete|transition)Cy",
        r"getCylinder",
        r"getAllowedTransitions",
        r"listConditions",
        r"listGasProducts",
        r"listBrands",
        r"listServiceTypes",
        r"Retimbrado",
        r"Ownership$",
        r"LabelHistory$",
        r"LabelData$",
        r"printLabel",
        r"Hydrotest",
        r"HydrostaticTest",
        r"Warrant",
        r"ScanLog",
        r"processScan",
        r"listScanLog",
        r"FromForm$",
    ]),
    ("warehouses", [
        r"LogisticsWarehouse",
        r"(?:list|get|create|update|delete)Warehouse",
    ]),
    ("zones", [
        r"LogisticsZone",
        r"(?:list|get|create|update|delete)Zone",
    ]),
    ("vehicles", [
        r"LogisticsVehicle",
        r"(?:list|get|create|update|delete)Vehicle",
        r"VehicleRouteRestriction",
        r"VehicleEligibility",
        r"VehicleDeliveryPoint",
        r"(?:list|get|create|update|delete)VehicleRouteRestriction",
        r"(?:list|get|create|update|delete)EligibleVehiclesForRoute",
        r"(?:list|get|create|update|delete)VehicleDeliveryPoint",
        r"(?:list|get|create|update|delete)EligibleVehiclesForMovement",
        r"DriverParameter",
        r"(?:list|get|create|update|delete)DriverParameter",
    ]),
    ("delivery-points", [
        r"LogisticsDeliveryPoint",
        r"(?:list|get|create|update|delete)DeliveryPoint",
    ]),
    ("orders", [
        r"LogisticsOrder(?!Item)",
        r"LogisticsOrderItem(?![A-Z])",
        r"LogisticsOrderItemCreatePayload",
        r"(?:list|get|create|update|delete)Order",
        r"(?:list|get|create|update|delete)OrderItem",
    ]),
    ("routes", [
        r"LogisticsRoute(?!Stop)",
        r"LogisticsRouteStop",
        r"(?:list|get|create|update|delete|start|complete|cancel)Route(?!Stop)",
        r"(?:list|get|create|update|delete)RouteStop",
        r"deliverRouteStop",
        r"createRouteAgendaTasks",
        r"replaceRouteWeekdays",
        r"RouteWeekday",
        r"updateRouteGpsStart",
        r"updateRouteStopGps",
    ]),
    ("loads", [
        r"LogisticsLoad",
        r"LoadSummary",
        r"LoadWeightSummary",
        r"(?:list|get|create|update|delete|bulkCreate|confirm)Load",
    ]),
    ("movements", [
        r"LogisticsMovement(?!Type)(?![A-Z])",
        r"LogisticsMovementType",
        r"LogisticsMovementItem",
        r"LogisticsMovementHistory",
        r"(?:list|get|create|update|delete|confirm|cancel)Movement",
        r"(?:list|get|create|update|delete)MovementType",
        r"(?:list|get|create|update|delete)MovementItem",
        r"(?:list|get|create|update|delete)MovementHistory",
    ]),
    ("scans", [
        r"LogisticsScanLog",
        r"(?:list|get|create|update|delete)ScanLog",
        r"processScan",
        r"(?:list|get|create|update|delete)ScanLogsByMovement",
    ]),
    ("agenda", [
        r"LogisticsAgendaTask",
        r"LogisticsAgendaTaskType",
        r"AgendaDailySummary",
        r"(?:list|get|create|update|delete|complete|cancel)AgendaTask",
        r"(?:list|get|create|update|delete)TaskType",
        r"(?:list|get|create|update|delete)AgendaTasksByDriver",
        r"(?:list|get|create|update|delete)AgendaDailySummary",
        r"updateAgendaTaskGps",
    ]),
    ("planning", [
        r"Planning",
        r"(?:list|get|create|update|delete|post|generate|accept|cancel)Planning",
        r"getPlanning",
        r"postPlanning",
        r"listPlanning",
        r"generatePreload",
        r"(?:list|get|create|update|delete)Preload",
        r"acceptPreload",
        r"cancelPreload",
        r"postPlanOrder",
    ]),
    ("reception", [
        r"Reception",
        r"IncidentReason",
        r"(?:list|get|create|update|delete|receive)Reception",
        r"receiveMovement",
        r"(?:list|get|create|update|delete)IncidentReason",
    ]),
    ("waybill", [
        r"Waybill",
        r"DispatchTicket",
        r"TransferAlbaran",
        r"DispatchGuide",
        r"(?:get|assign|close)Waybill",
        r"(?:get|assign|close)Dispatch",
        r"vehicleReturn",
        r"getDispatchReceipt",
    ]),
    ("equipment", [
        r"Equipment",
        r"MovementEquipment",
        r"(?:list|get|create|update|delete|assign|return)Equipment",
        r"(?:list|get|create|update|delete)MovementEquipment",
    ]),
    ("reports", [
        r"RouteAgendaReport",
        r"DispatchTicket",
        r"TransferAlbaran",
        r"LoadSummaryReport",
        r"AdrPoints",
        r"getRouteAgendaReport",
        r"getDispatchTicket",
        r"getTransferAlbaran",
        r"getLoadSummary",
        r"getAdrSummary",
    ]),
    ("adr", [
        r"AdrProductConfig",
        r"AdrIncompatibility",
        r"(?:list|get|create|update|delete|upsert)Adr",
    ]),
]


def detect_domain(name: str) -> str | None:
    if name is None:
        return None
    for domain, patterns in DOMAIN_RULES:
        for pat in patterns:
            if re.search(pat, name):
                return domain
    return None


def map_logistics_keys_to_subdomains() -> dict[str, list[str]]:
    """
    Los keys tienen nombres compuestos: logisticsKeys.cylinders.all()
    Se mantienen en keys.ts y se importan desde cada modulo.
    """
    return {"keys": ["logisticsKeys", "planningKeys", "receptionKeys", "equipmentKeys"]}


# ── grouping ────────────────────────────────────────────────────────


IMPORT_LIBS = 'import { apiRequest } from "../../../../apps/web/src/shared/api/client";\n'


def write_domain_file(
    domain: str,
    exports: list[dict],
    output_dir: Path,
    form_builders: list[dict],
) -> None:
    target = output_dir / f"{domain}.ts"
    with target.open("w") as f:
        f.write("// Auto-generado por split_api.py\n")
        f.write(IMPORT_LIBS)
        f.write('\n')
        for exp in exports:
            # add empty line before each export
            # write lines without trailing empty
            for line in exp["lines"]:
                f.write(line)
            if not exp["lines"][-1].endswith("\n\n"):
                f.write("\n")
    count = len(exports)
    print(f"  {target.name}: {count} exports")


INIT_HEADER = """\
// Auto-generado por split_api.py
// Re-exporta todo para retrocompatibilidad.
// ruff: noqa: F401

"""


def write_init(domain_files: dict[str, list[dict]], output_dir: Path) -> None:
    lines = [INIT_HEADER]
    for domain, exports in sorted(domain_files.items()):
        for exp in sorted(exports, key=lambda e: e.get("name") or ""):
            name = exp.get("name")
            if name and not name.startswith("_"):
                lines.append(f"export {{ {name} }} from \"./{domain}\";\n")
    # add form-type imports
    lines.append('\n')

    init_path = output_dir / "index.ts"
    with init_path.open("w") as f:
        f.writelines(lines)
    total = sum(len(e) for e in domain_files.values())
    print(f"  index.ts: {len(domain_files)} modulos, {total} exports")


def write_keys_file(keys_exports: list[dict], output_dir: Path) -> None:
    target = output_dir / "keys.ts"
    with target.open("w") as f:
        f.write("// Auto-generado por split_api.py\n")
        f.write(IMPORT_LIBS)
        f.write('\n')
        for exp in keys_exports:
            for line in exp["lines"]:
                f.write(line)
            if not exp["lines"][-1].endswith("\n\n"):
                f.write("\n")
    print(f"  keys.ts: {len(keys_exports)} exports")


def write_shared_file(other_exports: list[dict], output_dir: Path) -> None:
    """Escribe utilidades no exportadas o compartidas."""
    target = output_dir / "_shared.ts"
    with target.open("w") as f:
        f.write("// Auto-generado por split_api.py\n")
        f.write(IMPORT_LIBS)
        f.write('\n')
        for exp in other_exports:
            for line in exp["lines"]:
                f.write(line)
            if not exp["lines"][-1].endswith("\n\n"):
                f.write("\n")
    print(f"  _shared.ts: {len(other_exports)} bloques")


# ── main ────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Divide un api.ts monolítico en un paquete api/"
    )
    parser.add_argument("file", type=str, help="Ruta al archivo api.ts")
    parser.add_argument("--mapping", type=str, help="JSON con { nombre: dominio }")
    parser.add_argument(
        "--dry-run", action="store_true", help="Solo mostrar distribucion"
    )
    args = parser.parse_args()

    source = Path(args.file)
    if not source.exists():
        print(f"ERROR: {source} no existe")
        sys.exit(1)

    text = source.read_text()
    exports = parse_exports(text)
    print(f"Leidos {len(exports)} bloques desde {source}")

    # Cargar mapping si existe
    overrides: dict[str, str] = {}
    if args.mapping:
        with open(args.mapping) as f:
            overrides = json.load(f)

    # Detectar dominio de cada export
    domain_groups: dict[str, list[dict]] = {}
    shared_exports: list[dict] = []
    keys_exports: list[dict] = []
    import_lines: list[str] = []

    for exp in exports:
        kind = exp["kind"]
        name = exp.get("name")

        # imports → los manejamos aparte (no se mezclan)
        if kind == "import" or kind == "other":
            # detect if this is a non-exported utility
            if kind == "other":
                joined = "".join(exp["lines"]).strip()
                if joined and not joined.startswith("import"):
                    shared_exports.append(exp)
            continue

        # keys → modulo especial
        if name and "Keys" in name:
            keys_exports.append(exp)
            continue

        # mapping explícito
        if name and name in overrides:
            domain = overrides[name]
            if domain == "_removed":
                continue
            domain_groups.setdefault(domain, []).append(exp)
            continue

        # detección automática
        domain = detect_domain(name)
        if domain:
            domain_groups.setdefault(domain, []).append(exp)
        else:
            print(f"  ? sin dominio: {kind} {name}")
            shared_exports.append(exp)

    # Mostrar distribución
    print(f"\nDistribucion ({len(domain_groups)} modulos):")
    for domain, exps in sorted(domain_groups.items()):
        names = ", ".join(e["name"] for e in exps if e["name"])
        print(f"  {domain} ({len(exps)}): {names}")
    if keys_exports:
        names = ", ".join(e["name"] for e in keys_exports)
        print(f"  keys ({len(keys_exports)}): {names}")
    if shared_exports:
        print(f"  _shared ({len(shared_exports)}): utilidades no exportadas")

    if args.dry_run:
        return

    # Backup
    backup = source.with_suffix(".ts.bak")
    shutil.copy2(source, backup)
    print(f"\nBackup: {backup}")

    # Crear directorio
    output_dir = source.parent / "api"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # Escribir archivos
    for domain, exps in sorted(domain_groups.items()):
        write_domain_file(domain, exps, output_dir, [])

    if keys_exports:
        write_keys_file(keys_exports, output_dir)
    if shared_exports:
        write_shared_file(shared_exports, output_dir)

    write_init(domain_groups, output_dir)

    # Remover original
    source.unlink()
    print(f"\nEliminado: {source}")
    print("Hecho.")


if __name__ == "__main__":
    main()
