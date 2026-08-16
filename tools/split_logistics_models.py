#!/usr/bin/env python3
"""
Navaja: split_logistics_models.py

Divide plugins/logistics/backend/models.py en un paquete models/
con un archivo por dominio, manteniendo retrocompatibilidad via __init__.py.

Uso:
  python3 tools/split_logistics_models.py

Prerequisito:
  Ejecutar desde la raiz del repositorio.
  Tener un commit limpio antes por si hay que revertir.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

MODELS_PATH = Path("plugins/logistics/backend/models.py")
MODELS_DIR = Path("plugins/logistics/backend/models")

# ── grouping rules: class name -> target file ───────────────────────

CYLINDER_KEYWORDS = (
    "CylinderState$", "StateTransition", "Cylinder$", "CylinderStateLog",
    "CylinderCondition", "HydrostaticTest", "CylinderWarranty",
    "CylinderRetimbrado", "CylinderOwnership", "CylinderLabelHistory",
    "CylinderService", "ScanLog",
)
CATALOG_KEYWORDS = (
    "GasProduct", "Brand$", "ServiceType$", "MovementType$", "AgendaTaskType$",
)
RESOURCES_KEYWORDS = (
    "Warehouse", "Zone$", "Vehicle$", "DeliveryPoint",
)
OPERATIONS_KEYWORDS = (
    "Order$", "OrderItem", "Route$", "RouteStop", "Load$",
)
MOVEMENTS_KEYWORDS = (
    "Movement$", "MovementItem", "MovementStatusHistory",
)
PLANNING_KEYWORDS = (
    "PlanPreload", "PlanPreloadItem", "ReceptionIncident",
)
EQUIPMENT_KEYWORDS = (
    "Equipment$", "MovementEquipment", "VehicleRouteRestriction",
    "DriverParameter", "VehicleDeliveryPoint",
)
AGENDA_KEYWORDS = (
    "RouteWeekday", "AgendaTask",
)
ADR_KEYWORDS = (
    "AdrProductConfig", "AdrIncompatibility",
)

DOMAIN_MAP: list[tuple[str, tuple[str, ...]]] = [
    ("cylinder", CYLINDER_KEYWORDS),
    ("catalog", CATALOG_KEYWORDS),
    ("resources", RESOURCES_KEYWORDS),
    ("operations", OPERATIONS_KEYWORDS),
    ("movements", MOVEMENTS_KEYWORDS),
    ("planning", PLANNING_KEYWORDS),
    ("equipment", EQUIPMENT_KEYWORDS),
    ("agenda", AGENDA_KEYWORDS),
    ("adr", ADR_KEYWORDS),
]

HEADER = """# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from systutor.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


"""


def _class_name(line: str) -> str | None:
    m = re.match(r"^class (\w+)", line)
    return m.group(1) if m else None


def _target_file(class_name: str) -> str:
    for domain, keywords in DOMAIN_MAP:
        for kw in keywords:
            if re.search(kw, class_name):
                return domain
    return "other"


def parse_models(text: str) -> list[dict]:
    """Return list of {name, lines[], lineno} for each class."""
    lines = text.splitlines(keepends=True)
    classes: list[dict] = []
    current: dict | None = None

    for i, line in enumerate(lines):
        name = _class_name(line)
        if name:
            if current is not None:
                current["end"] = i
                classes.append(current)
            current = {"name": name, "start": i, "end": len(lines), "lines": []}
        if current is not None:
            current["lines"].append(line)

    if current is not None:
        classes.append(current)
    return classes


def write_domain_file(domain: str, classes: list[dict], text: str) -> None:
    """Write a domain file with header + matching classes."""
    lines = text.splitlines(keepends=True)
    target = MODELS_DIR / f"{domain}.py"
    with target.open("w") as f:
        f.write(HEADER)
        for cls in classes:
            f.write(f"\n# ── {cls['name']} ────────────────────────────────────────\n\n")
            for line in cls["lines"]:
                f.write(line)
    print(f"  {target.name}: {len(classes)} clases")


def write_init(domain_files: dict[str, list[dict]]) -> None:
    """Write __init__.py that re-exports all model classes."""
    lines = [
        "# Auto-generado por split_logistics_models.py\n",
        "# Re-exporta todas las clases para retrocompatibilidad.\n",
        "# ruff: noqa: F401\n",
        "from __future__ import annotations\n\n",
    ]
    for domain, classes in sorted(domain_files.items()):
        module = domain
        class_names = sorted(cls["name"] for cls in classes)
        for cn in class_names:
            lines.append(f"from .{module} import {cn}\n")
    lines.append("\n")

    init_path = MODELS_DIR / "__init__.py"
    with init_path.open("w") as f:
        f.writelines(lines)
    print(f"  __init__.py: {len(domain_files)} modulos, {sum(len(c) for c in domain_files.values())} clases")


def main() -> None:
    if not MODELS_PATH.exists():
        print(f"ERROR: {MODELS_PATH} no existe")
        return

    text = MODELS_PATH.read_text()
    classes = parse_models(text)
    print(f"Leidas {len(classes)} clases desde {MODELS_PATH}")

    # group by domain
    domain_groups: dict[str, list[dict]] = {}
    for cls in classes:
        domain = _target_file(cls["name"])
        domain_groups.setdefault(domain, []).append(cls)

    for domain, cls_list in sorted(domain_groups.items()):
        names = [c["name"] for c in cls_list]
        print(f"  {domain}: {names}")

    # backup original
    backup = MODELS_PATH.with_suffix(".py.bak")
    shutil.copy2(MODELS_PATH, backup)
    print(f"\nBackup: {backup}")

    # create models directory
    if MODELS_DIR.exists():
        shutil.rmtree(MODELS_DIR)
    MODELS_DIR.mkdir(parents=True)

    # write domain files
    for domain, cls_list in sorted(domain_groups.items()):
        write_domain_file(domain, cls_list, text)

    # write __init__.py
    write_init(domain_groups)

    # remove original models.py
    MODELS_PATH.unlink()
    print(f"\nEliminado: {MODELS_PATH}")
    print("Hecho.")


if __name__ == "__main__":
    main()
