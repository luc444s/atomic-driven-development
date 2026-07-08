#!/usr/bin/env python3
"""
split-tsx.py — Analiza y extrae secciones (dialogs, modals) de un archivo
TSX/TS monolítico en componentes React independientes.

Modos:
  analyze <file>              Escanea y muestra secciones extraíbles
  split   <file> --config c   Extrae secciones según JSON de configuración

Config JSON:
  {
    "output_dir": "ruta/hacia/salida",
    "sections": [
      {
        "name": "HydrotestDialog",
        "start": 1216,
        "end": 1239,
        "props": ["selectedCylinderId", "hydrotestForm", "setHydrotestForm"],
        "extra_imports": ["type { HydrotestFormState } from \\"./forms/cylinder-form-state\\""]
      }
    ]
  }

En analyze mode, el script reporta el nombre sugerido, line range y props
auto-detectadas. Puedes copiar ese reporte como base del config JSON.

En split mode, el script:
  - Extrae cada sección a un archivo .tsx separado
  - Crea un componente React con props tipada
  - Reporta los cambios necesarios en el original

Prerequisitos:
  - Ejecutar desde la raiz del repositorio
  - Hacer commit limpio antes por si hay que revertir
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


# ── diálogo detect ──────────────────────────────────────────────────


def find_dialogs(source: str) -> list[dict]:
    """
    Encuentra bloques <Dialog ...>...</Dialog> en el source.
    Usa balance de profundidad de tags JSX (no parser completo).
    """
    lines = source.splitlines(keepends=True)
    dialogs: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # buscar apertura <Dialog (no </Dialog>
        if re.search(r'<Dialog\b', line) and not re.search(r'</Dialog\b', line):
            start = i
            depth = 0
            j = i
            in_block = False
            while j < len(lines):
                l = lines[j]
                # contar aperturas <Dialog
                for m in re.finditer(r'<Dialog\b', l):
                    # check it's not self-closing
                    after = l[m.end():]
                    if '/>' in after[:5]:
                        continue
                    depth += 1
                    in_block = True
                # contar cierres </Dialog>
                depth -= l.count('</Dialog>')
                if depth == 0 and in_block:
                    break
                j += 1
            if depth == 0 and in_block:
                dialogs.append({
                    "name": None,
                    "start": start,
                    "end": j,
                    "text": "".join(lines[start:j+1]),
                })
            i = j + 1
        else:
            i += 1
    return dialogs


# ── auto-detect props ───────────────────────────────────────────────


# Identificadores que definitivamente no son props
_LOCAL_DECL = re.compile(
    r'\b(const|let|var|function|return|import|export|type|interface|if|else|for|while|switch|case|default|async|await|from)\b'
)
_JSX_INTRINSICS = {
    'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'form', 'input', 'button', 'select', 'option', 'textarea',
    'label', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'ul', 'ol', 'li', 'a', 'img', 'br', 'hr', 'section', 'nav',
    'header', 'footer', 'main', 'aside', 'article', 'figure',
    'svg', 'path', 'circle', 'rect', 'line', 'g',
}
_COMMON_PROPS = {
    'open', 'onOpenChange', 'onClose', 'title', 'description',
    'disabled', 'placeholder', 'type', 'className', 'onClick',
    'onChange', 'onSubmit', 'value', 'key', 'ref', 'children',
    'variant', 'size', 'destructive', 'align', 'rows', 'cols',
    'maxWidthClassName', 'confirmLabel',
}
_REACT_BUILTINS = {
    'useState', 'useEffect', 'useMemo', 'useCallback', 'useRef',
    'useQuery', 'useMutation', 'useQueryClient',
    'FormEvent', 'MouseEvent', 'ChangeEvent', 'KeyboardEvent',
}
_SKIP_PREFIXES = {
    'use', 'set', 'is', 'on', 'can', 'has',
    'EMPTY_', '_',
}


_SPANISH_WORDS = {
    'de', 'la', 'del', 'el', 'los', 'las', 'un', 'una', 'y', 'e', 'o',
    'con', 'en', 'por', 'para', 'como', 'entre', 'sin', 'sobre', 'tras',
    'no', 'si', 'es', 'se', 'su', 'lo', 'que', 'ser', 'este', 'esta',
    'envase', 'ficha', 'estado', 'etiqueta', 'datos', 'acciones',
    'operativa', 'servicio', 'tipo', 'resumen', 'uso', 'general', 'vista',
    'fecha', 'notas', 'cliente', 'producto',
    'tiene', 'debe', 'hay', 'estos', 'campo', 'la', 'los', 'las',
    'antes', 'tras', 'durante', 'desde', 'hasta',
    'marcado', 'origen', 'destino', 'valor',
    'comercial', 'legal', 'operativo', 'final',
    'cada', 'todo', 'una', 'sus',
}


def _tokenize(text: str) -> set[str]:
    """Extrae identificadores de un texto JSX."""
    return set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text))


def _local_decls(text: str) -> set[str]:
    """Encuentra nombres declarados localmente (const, let, function)."""
    decls: set[str] = set()
    for m in re.finditer(r'\b(const|let|var)\s+(\w+)', text):
        decls.add(m.group(2))
    for m in re.finditer(r'\bfunction\s+(\w+)', text):
        decls.add(m.group(1))
    # destructured props patterns: { a, b, c }
    for m in re.finditer(r'\{\s*([^}]+)\s*\}\s*=', text):
        for name in re.split(r'[,:\s]+', m.group(1)):
            name = name.strip().rstrip(',')
            if name and re.match(r'^\w+$', name):
                decls.add(name)
    return decls


def _jsx_expr_tokens(text: str) -> set[str]:
    """
    Extrae solo identificadores que aparecen dentro de expresiones JSX { ... }.
    Esto filtra palabras en texto plano HTML (como español).
    """
    tokens: set[str] = set()
    depth = 0
    expr = ''
    capturing = False
    for ch in text:
        if ch == '{':
            if capturing:
                depth += 1
            else:
                capturing = True
                depth = 0
                expr = ''
        elif ch == '}':
            if capturing and depth == 0:
                tokens.update(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expr))
                capturing = False
            elif capturing:
                depth -= 1
        elif capturing:
            expr += ch
    return tokens


def auto_detect_props(section_text: str, whole_file: str) -> list[str]:
    """
    Detecta qué variables externas usa un bloque extraído.
    Solo considera identificadores dentro de expresiones JSX { ... }.
    """
    section_tokens = _jsx_expr_tokens(section_text)
    file_tokens = _tokenize(whole_file)

    local = _local_decls(section_text)

    props: set[str] = set()
    for token in section_tokens:
        if token in local:
            continue
        if token in _JSX_INTRINSICS:
            continue
        if token in _REACT_BUILTINS:
            continue
        if token in _COMMON_PROPS:
            continue
        if token in _SPANISH_WORDS:
            continue
        if token.startswith('_'):
            continue
        if token == token.upper() and len(token) > 1:
            continue  # constants
        if token.lower() in {'true', 'false', 'null', 'undefined'}:
            continue
        props.add(token)

    common_ignore = {
        'event', 'target', 'value', 'current', 'preventDefault',
        'stopPropagation', 'Error',
    }
    props -= common_ignore

    return sorted(props)


# ── section analysis ────────────────────────────────────────────────


def _suggest_component_name(dialog_text: str, idx: int) -> str:
    """Sugiere un nombre de componente basado en el contenido del dialogo."""
    title_match = re.search(r'title="([^"]+)"', dialog_text)
    if title_match:
        title = title_match.group(1)
        # Normalizar a PascalCase (eliminar acentos, coger solo palabras con mayúscula inicial)
        title = title.replace('Ó', 'O').replace('É', 'E').replace('Í', 'I').replace('Á', 'A').replace('Ú', 'U').replace('Ñ', 'N')
        words = re.findall(r'[A-Za-z]{3,}', title)
        # preferir palabras con mayúscula inicial
        capped = [w for w in words if w[0].isupper()]
        words = capped if capped else words
        name = ''.join(w.capitalize() for w in words[:3])
        return f'{name}Dialog'
    # Buscar variable de estado isXxxOpen
    state_match = re.search(r'is(\w+)Open', dialog_text[:200])
    if state_match:
        return f'{state_match.group(1)}Dialog'
    return f'SectionDialog{idx}'


def analyze_file(filepath: str) -> list[dict]:
    source = Path(filepath).read_text()
    dialogs = find_dialogs(source)

    results = []
    for i, dlg in enumerate(dialogs):
        dlg_text = dlg["text"]
        props = auto_detect_props(dlg_text, source)
        name = _suggest_component_name(dlg_text, i)
        lines = f'{dlg["start"]+1}-{dlg["end"]+1}'
        size = dlg["end"] - dlg["start"] + 1
        results.append({
            "name": name,
            "start": dlg["start"] + 1,
            "end": dlg["end"] + 1,
            "lines": size,
            "auto_props": props,
        })

    return results


# ── section extraction ──────────────────────────────────────────────


def _resolve_path(from_dir: Path, target_file: Path) -> str:
    """Resuelve ruta relativa para import."""
    rel = target_file.parent.relative_to(from_dir.parent)  # len
    parts = []
    # count how many levels up
    up = len(from_dir.relative_to(from_dir.anchor).parts) - 1
    for _ in range(up):
        # Actually, compute proper relative path
        pass

    # Simple: compute relative path from output file to source
    try:
        rel = target_file.resolve().parent.relative_to(from_dir.resolve())
        parts = ['..'] * len(rel.parts)
        prefix = '/'.join(parts) if parts else '.'
        return prefix
    except ValueError:
        # files on different drives / paths
        return '..'


def _compute_import_path(output_file: Path, source_file: Path) -> str:
    """
    Compute the relative path from output_file to source_file, for the
    import statement in the NEW component file.
    Eg: output = .../cylinders/dialogs/HydrotestDialog.tsx
        source = .../LogisticsPage.tsx
    Returns: ../../LogisticsPage  (no extension)
    """
    out_dir = output_file.resolve().parent
    src = source_file.resolve().with_suffix('')
    try:
        rel = src.relative_to(out_dir)
        parts = ['..'] * (len(out_dir.relative_to(out_dir.anchor).parts) - len(rel.parent.relative_to(out_dir.anchor).parts))
        # simpler calculation
        rel_str = str(src.relative_to(out_dir))
        if not rel_str.startswith('.'):
            rel_str = './' + rel_str
        return rel_str.replace('\\', '/')
    except ValueError:
        # try reverse
        try:
            # compute relative properly
            out_parts = list(out_dir.parts)
            src_parts = list(src.parts)
            common = 0
            for a, b in zip(out_parts, src_parts):
                if a == b:
                    common += 1
                else:
                    break
            up = ['..'] * (len(out_parts) - common)
            down = list(src_parts[common:])
            rel = '/'.join(up + down)
            if not rel.startswith('.'):
                rel = './' + rel
            return rel
        except Exception:
            return f'./{src.name}'


COMPONENT_TMPL = """\
// Auto-generado por split-tsx.py
import {{ Fragment }} from "react";
{extra_imports}
import {{ Dialog }} from "../../../apps/web/src/shared/ui/dialog";
import {{ Button }} from "../../../apps/web/src/shared/ui/button";
import {{ Input, Textarea }} from "../../../apps/web/src/shared/ui/input";
import {{ Select }} from "../../../apps/web/src/shared/ui/select";
import {{ Field }} from "{utils_path}";
import type {{ {prop_types} }} from "{source_rel}";

interface {name}Props {{
{props_interface}
}}

export function {name}({{
{props_destructure}
}}: {name}Props) {{
  return (
{jsx_content}
  );
}}
"""


def extract_section(
    source_file: Path,
    output_dir: str,
    section: dict,
    whole_source: str,
    dry_run: bool = False,
) -> dict:
    """Extract a section into a component file. Returns info about what was done."""
    name = section["name"]
    start = section["start"] - 1  # 0-indexed
    end = section["end"]
    explicit_props = section.get("props", [])
    extra_imports = section.get("extra_imports", [])

    lines = whole_source.splitlines(keepends=True)
    section_lines = lines[start:end]

    # Detect props
    section_text = ''.join(section_lines)
    auto = auto_detect_props(section_text, whole_source)

    # Merge: explicit props first, then auto (deduplicate)
    seen = set(explicit_props)
    all_props = list(explicit_props)
    for p in auto:
        if p not in seen:
            seen.add(p)
            all_props.append(p)

    # Remove items that are definitely not props
    non_props = {
        'Fragment', 'Dialog', 'Button', 'Input', 'Textarea', 'Select', 'Field',
        'CustomerSearchDialog', 'InfoBlock', 'DataCard',
        'CylinderStateBadge', 'getCylinderStateLabel', 'toNullable',
        'toNumberOrNull', 'toIntegerOrNull', 'formatDate', 'formatDateTime',
        'DropdownMenu', 'DropdownItem',
        'DataTable', 'Card', 'CardContent', 'CardHeader', 'CardTitle',
        'CardDescription', 'Alert', 'ConfirmDialog',
        'LogisticsSection',
        'toast', 'queryClient',
    }
    all_props = [p for p in all_props if p not in non_props]

    # Compute JSX content (strip one level of indentation from the section)
    # Find base indent of the first non-empty line
    indent = ''
    for raw in section_lines:
        stripped = raw.lstrip()
        if stripped and not stripped.startswith('<'):
            continue
        if stripped.startswith('<'):
            indent = raw[:len(raw) - len(stripped)]
            break

    # Remove leading/trailing whitespace lines
    while section_lines and section_lines[0].strip() == '':
        section_lines.pop(0)
    # Remove the <Dialog ...> opening line? No, keep it as part of the component
    # Actually, the component should return the exact JSX

    jsx_lines = []
    for raw_line in section_lines:
        if raw_line.startswith(indent) and indent:
            jsx_lines.append(raw_line[len(indent):])
        else:
            jsx_lines.append(raw_line)
    jsx_content = ''.join(jsx_lines).rstrip()

    # Build props interface
    props_iface = ''
    props_dest = ''
    for p in all_props:
        ptype = _infer_prop_type(p, section_text)
        props_iface += f'  {p}: {ptype};\n'
        props_dest += f'    {p},\n'

    # Extra imports string
    extra_imports_str = '\n'.join(extra_imports)

    # Compute relative import path for utils
    utils_rel = _compute_import_path(
        Path(output_dir) / f'{name}.tsx',
        Path(source_file).parent / 'cylinders' / 'utils' / 'formatters',
    )

    # Relative path to source file (for types)
    source_rel = _compute_import_path(
        Path(output_dir) / f'{name}.tsx',
        source_file.with_suffix(''),
    )

    # Prop types string for import
    prop_types_names = [p for p in all_props if p[0].isupper() or p.endswith('FormState') or p.endswith('Props')]
    prop_types_str = ', '.join(prop_types_names) if prop_types_names else 'unknown'

    content = COMPONENT_TMPL.format(
        name=name,
        extra_imports=extra_imports_str,
        props_interface=props_iface,
        props_destructure=props_dest,
        jsx_content=jsx_content,
        utils_path=utils_rel,
        source_rel=source_rel,
        prop_types=prop_types_str,
    )

    if not dry_run:
        output_path = Path(output_dir) / f'{name}.tsx'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        print(f"  Creado: {output_path}")

    return {
        "name": name,
        "props": all_props,
        "lines_removed": end - start,
    }


def _infer_prop_type(prop_name: str, section_text: str) -> str:
    """Infiere tipo TypeScript básico para un prop."""
    # State setters
    if prop_name.startswith('set') and prop_name[3].isupper():
        state_name = prop_name[3:]
        if state_name == 'Open':
            return '(open: boolean) => void'
        if state_name.endswith('Form'):
            return f'(form: {state_name}) => void'
        return f'(value: {state_name}) => void'

    # Boolean patterns
    if prop_name.startswith('is') and prop_name[2].isupper():
        return 'boolean'
    if prop_name.startswith('can') and prop_name[3].isupper():
        return 'boolean'
    if prop_name.startswith('has') and prop_name[3].isupper():
        return 'boolean'
    if prop_name.endswith('Open'):
        return 'boolean'
    if prop_name.endswith('Pending'):
        return 'boolean'

    # Form state objects
    if 'Form' in prop_name or 'Meta' in prop_name:
        return f'typeof {prop_name}'
    if 'Mutation' in prop_name:
        return 'ReturnType<typeof useMutation>'

    # Handlers
    if prop_name.startswith('handle') or prop_name.startswith('on'):
        return '() => void'

    # Query data
    if prop_name.endswith('Query') and 'Query' not in prop_name[:-5]:
        return 'ReturnType<typeof useQuery>'
    if prop_name.endswith('Data') or prop_name.endswith('Options'):
        return 'unknown[]'

    return 'unknown'


# ── CLI ─────────────────────────────────────────────────────────────


def cmd_analyze(args):
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"ERROR: {filepath} no existe")
        sys.exit(1)

    print(f"Analizando: {filepath}")
    print()

    results = analyze_file(str(filepath))

    if not results:
        print("No se encontraron secciones extraibles (<Dialog>).")
        return

    print("Secciones detectadas:")
    print()
    for r in results:
        print(f"  [{r['name']}]")
        print(f"    Lineas: {r['start']}-{r['end']} ({r['lines']} lines)")
        print(f"    Props auto-detectados: {', '.join(r['auto_props']) if r['auto_props'] else '(ninguno)'}")
        print()

    # Print JSON ready for config
    print("---")
    print("JSON para --config (copia esto y ajusta props manualmente):")
    print()
    config_sections = []
    for r in results:
        config_sections.append({
            "name": r["name"],
            "start": r["start"],
            "end": r["end"],
            "props": r["auto_props"],
        })
    config = {
        "output_dir": str(filepath.parent),
        "sections": config_sections,
    }
    print(json.dumps(config, indent=2))


def cmd_split(args):
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"ERROR: {filepath} no existe")
        sys.exit(1)

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: config {config_path} no existe")
        sys.exit(1)

    with open(config_path) as f:
        config = json.load(f)

    output_dir = config.get("output_dir", str(filepath.parent))
    sections = config.get("sections", [])

    if not sections:
        print("ERROR: no hay secciones en el config")
        sys.exit(1)

    source = filepath.read_text()

    # create backup
    backup = filepath.with_suffix(filepath.suffix + ".bak")
    shutil.copy2(filepath, backup)
    print(f"Backup: {backup}")

    print(f"Extrayendo {len(sections)} secciones...")
    print()

    extracted_props: dict[str, list[str]] = {}

    for section in sections:
        info = extract_section(filepath, output_dir, section, source)
        extracted_props[info["name"]] = info["props"]
        print()

    # Generate import statements to add to the original file
    print("---")
    print("Imports para agregar al archivo original:")
    print()
    for sec in sections:
        rel_dir = _compute_import_path(
            filepath,
            Path(output_dir) / f'{sec["name"]}.tsx',
        )
        # Actually, compute import path from original file TO the new component
        out_file = Path(output_dir) / f'{sec["name"]}.tsx'
        imp_path = _compute_import_path(filepath, out_file)
        print(f'import {{ {sec["name"]} }} from "{imp_path}";')
    print()

    # Show what to replace in original
    print("---")
    print("Cada seccion extraida debe reemplazarse en el original")
    print("con <Componente {...props} />")
    print()

    total_removed = sum(sec["end"] - sec["start"] + 1 for sec in sections)
    total_lines = len(source.splitlines())
    print(f"Lineas extraidas: ~{total_removed} de {total_lines}")


def main():
    parser = argparse.ArgumentParser(description="Divide un TSX monolítico en componentes.")
    sub = parser.add_subparsers(dest="command", required=True)

    # analyze
    a_parser = sub.add_parser("analyze", help="Escanea el archivo y muestra secciones extraíbles")
    a_parser.add_argument("file", type=str, help="Ruta al archivo .tsx")

    # split
    s_parser = sub.add_parser("split", help="Extrae secciones como componentes según config")
    s_parser.add_argument("file", type=str, help="Ruta al archivo .tsx")
    s_parser.add_argument("--config", type=str, required=True, help="Archivo JSON de config")

    args = parser.parse_args()

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "split":
        cmd_split(args)


if __name__ == "__main__":
    main()
