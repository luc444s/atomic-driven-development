#!/usr/bin/env python3
"""
Navaja: split_models.py

Divide un archivo models.py monolítico en un paquete models/
con un archivo por dominio, manteniendo retrocompatibilidad via __init__.py.

Uso:
  # Con mapping explícito (recomendado)
  python3 tools/split_models.py ruta/a/models.py --mapping mapping.json

  # Sin mapping: agrupa por prefijo común (ej: Logistics* → segundo token)
  python3 tools/split_models.py ruta/a/models.py

Ejemplo mapping.json:
  {
    "cylinder": ["CylinderState", "StateTransition", "Cylinder$", "ScanLog"],
    "catalog":  ["GasProduct", "Brand$", "ServiceType$"],
    "_default": "other"
  }

Nota: las regex se buscan con re.search() sobre el nombre de clase.
      "$" al final ancla al final del nombre.
      La primera coincidencia gana.

Prerequisito:
  Ejecutar desde la raiz del repositorio.
  Hacer commit limpio antes por si hay que revertir.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


# ── auto-detect por prefijo común ───────────────────────────────────


def _common_prefix(class_names: list[str]) -> str | None:
    """Retorna el prefijo común más largo (ej: 'Logistics')."""
    if not class_names:
        return None
    prefix = class_names[0]
    for name in class_names[1:]:
        while not name.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return None
    return prefix


def _second_word(name: str, prefix: str) -> str:
    """Extrae el segundo token semántico (ej: LogisticsCylinderState → Cylinder)."""
    rest = name[len(prefix):] if name.startswith(prefix) else name
    # partir en CamelCase: CylinderState → ['Cylinder', 'State']
    parts = re.findall(r'[A-Z][a-z]*|[A-Z]+(?=[A-Z]|$)', rest)
    return parts[0] if parts else rest


def _auto_detect_groups(classes: list[dict]) -> dict[str, list[dict]]:
    """
    Agrupa por segundo token semántico.
    Ej: LogisticsCylinder, LogisticsCylinderState → grupo 'cylinder'.
    """
    names = [c["name"] for c in classes]
    prefix = _common_prefix(names)
    if not prefix:
        return {"__all__": classes}

    groups: dict[str, list[dict]] = {}
    for cls in classes:
        group = _second_word(cls["name"], prefix).lower()
        groups.setdefault(group, []).append(cls)
    return groups


# ── mapping loading ─────────────────────────────────────────────────


def load_mapping(path: str | None, class_names: list[str]) -> dict[str, list[str]]:
    """Load mapping from JSON file or auto-detect."""
    if path:
        with open(path) as f:
            raw = json.load(f)
        return raw

    # auto-detect: usa prefijo común para sugerir dominio
    prefix = _common_prefix(class_names)
    if not prefix:
        print("No se pudo detectar prefijo común. Usa --mapping para definir dominios.")
        sys.exit(1)

    print(f"Prefijo detectado: '{prefix}'")
    print("Dominios auto-detectados (segundo token CamelCase):")
    groups = _auto_detect_groups([{"name": n} for n in class_names])
    mapping: dict[str, list[str]] = {}
    for domain, cls_list in sorted(groups.items()):
        names = [c["name"] for c in cls_list]
        print(f"  {domain}: {names}")
        mapping[domain] = []
        for n in names:
            # usar el segundo token como regex de búsqueda
            token = _second_word(n, prefix)
            mapping[domain].append(token)
    return mapping


# ── parsing ─────────────────────────────────────────────────────────


HEADER_TMPL = """\
# ruff: noqa: E501
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

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


"""


def _class_name(line: str) -> str | None:
    m = re.match(r"^class (\w+)", line)
    return m.group(1) if m else None


def parse_classes(text: str) -> list[dict]:
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


# ── grouping ────────────────────────────────────────────────────────


def assign_domain(
    class_name: str,
    mapping: dict[str, list[str]],
    default: str = "other",
) -> str:
    for domain, patterns in mapping.items():
        if domain.startswith("_"):
            continue
        for pat in patterns:
            if re.search(pat, class_name):
                return domain
    meta_default = mapping.get("_default")
    return meta_default if meta_default else default


# ── output ──────────────────────────────────────────────────────────


def write_domain_file(domain: str, classes: list[dict], output_dir: Path) -> None:
    target = output_dir / f"{domain}.py"
    with target.open("w") as f:
        f.write(HEADER_TMPL)
        for cls in classes:
            f.write(f"\n# ── {cls['name']} ────────────────────────────────────────\n\n")
            for line in cls["lines"]:
                f.write(line)
    print(f"  {target.name}: {len(classes)} clases")


def write_init(domain_files: dict[str, list[dict]], output_dir: Path) -> None:
    lines = [
        "# Auto-generado por split_models.py\n",
        "# Re-exporta todas las clases para retrocompatibilidad.\n",
        "# ruff: noqa: F401\n",
        "from __future__ import annotations\n\n",
    ]
    for domain, classes in sorted(domain_files.items()):
        for cls in sorted(classes, key=lambda c: c["name"]):
            lines.append(f"from .{domain} import {cls['name']}\n")
    lines.append("\n")

    init_path = output_dir / "__init__.py"
    with init_path.open("w") as f:
        f.writelines(lines)
    total = sum(len(c) for c in domain_files.values())
    print(f"  __init__.py: {len(domain_files)} modulos, {total} clases")


# ── main ────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Divide un models.py monolítico en un paquete.")
    parser.add_argument("file", type=str, help="Ruta al archivo models.py")
    parser.add_argument("--mapping", type=str, help="Archivo JSON con mapeo dominio → patrones regex")
    args = parser.parse_args()

    source = Path(args.file)
    if not source.exists():
        print(f"ERROR: {source} no existe")
        sys.exit(1)

    text = source.read_text()
    classes = parse_classes(text)
    names = [c["name"] for c in classes]
    print(f"Leidas {len(classes)} clases desde {source}")

    mapping = load_mapping(args.mapping, names)

    # asignar dominio a cada clase
    domain_groups: dict[str, list[dict]] = {}
    for cls in classes:
        domain = assign_domain(cls["name"], mapping)
        domain_groups.setdefault(domain, []).append(cls)

    print("\nDistribucion:")
    for domain, cls_list in sorted(domain_groups.items()):
        names_str = ", ".join(c["name"] for c in cls_list)
        print(f"  {domain}: {names_str}")

    # backup
    backup = source.with_suffix(".py.bak")
    shutil.copy2(source, backup)
    print(f"\nBackup: {backup}")

    # crear directorio
    output_dir = source.parent / "models"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # escribir archivos
    for domain, cls_list in sorted(domain_groups.items()):
        write_domain_file(domain, cls_list, output_dir)

    write_init(domain_groups, output_dir)

    # eliminar original
    source.unlink()
    print(f"\nEliminado: {source}")
    print("Hecho.")


if __name__ == "__main__":
    main()
