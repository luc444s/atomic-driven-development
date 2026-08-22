# A.SPEC COMPRAS-001 — Corregir estructura del plugin compras

## WHY

El plugin `compras` (`plugins/commerce`) aparece en el registry con estado
`failed` y error `missing plugin structure: backend, events, permissions`.
El kernel (`systutor.kernel.plugins.runtime.PluginManifestRegistry._structure_error`)
exige que la raíz del plugin contenga los directorios `backend`, `frontend`,
`migrations`, `permissions`, `events`. `compras` tiene `backend` bajo el
submódulo `purchase/` (`plugins/commerce/purchase/backend`) y no posee
`events/` ni `permissions/` en la raíz. Por eso no supera la validación y no
se carga.

## WHAT

Se añaden en la raíz de `plugins/commerce` los directorios que exige el kernel,
**sin alterar el namespace `purchase`** (los tests y el código importan
`plugins.commerce.purchase.*`):

- `plugins/commerce/backend` como symlink relativo a `purchase/backend`.
- `plugins/commerce/events/` (con `.gitkeep`).
- `plugins/commerce/permissions/` (con `.gitkeep`).

Verdad nueva falsable ahora: el kernel descubre `compras` como plugin válido
(`error_message is None`) y `PluginRuntime.load` lo deja en estado `enabled`.

## SCOPE

- `plugins/commerce/backend` (symlink relativo `purchase/backend`).
- `plugins/commerce/events/` (`.gitkeep`).
- `plugins/commerce/permissions/` (`.gitkeep`).

## OUT OF SCOPE

- Reestructurar el namespace `plugins.commerce.purchase.*`.
- Modificar el kernel (`vendor/systutor-core`).
- Arreglar fallos de carga distintos al structure check.
- UI / frontend de compras.

## CONTRACT

Precondiciones:
- `compras` registrado con `failed` y `missing plugin structure`.

Postcondiciones:
- `PluginManifestRegistry(plugins_dir).discover()` → `compras.error_message is None`.
- `PluginRuntime(registry).load()` → `compras.status == "enabled"`.

## INVARIANTS

```yaml
invariants:
  - imports plugins.commerce.purchase.* intactos (test_compras_plugin.py los parchea)
  - rutas /api/v1/plugins/compras/* funcionan igual
  - plugin.json de compras sin cambios
  - otros plugins (crm, productos, stock, logistics, tms) sin cambios
  - vendor/systutor-core sin cambios
```

## VERIFICATION

```bash
# descubrimiento + carga en dir de plugins con hermanos presentes
python - <<'PY'
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location("ens", "apps/api/app/plugins.py")
ens = importlib.util.module_from_spec(spec); spec.loader.exec_module(ens)
from systutor.kernel.plugins.runtime import PluginManifestRegistry, PluginRuntime
pd = Path("plugins")
ens.ensure_installed_plugins(pd)  # noop si ya hay dirs
reg = PluginManifestRegistry(pd); reg.discover()
c = reg.get("compras")
assert c is not None and c.error_message is None, c.error_message
rt = PluginRuntime(reg); rt.load()
r = next(x for x in rt.list_results() if x.plugin_id == "compras")
assert r.status == "enabled", (r.status, r.error_message)
print("compras enabled OK")
PY
```

## ROLLBACK

Reversible: `git clean` / borrar el symlink `plugins/commerce/backend` y los
directorios `events/`, `permissions/` añadidos. El namespace `purchase` queda
intacto, el plugin vuelve al estado previo (`failed` por estructura).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/backend            # symlink relativo
    - plugins/commerce/events/**
    - plugins/commerce/permissions/**
  prohibited:
    - vendor/systutor-core/**
    - plugins/commerce/purchase/**
    - apps/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - registro y carga del plugin compras
  indirect:
    - orden de descubrimiento de plugins (compras ahora válido)
  must_not_affect:
    - otros plugins
    - kernel / comportamiento REST
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: []
  systemic_invariants:
    - el kernel sigue siendo dueño del contrato de estructura de plugins
  composition_checks:
    - compras habilitado no rompe load de crm/productos/stock/logistics/tms
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - plugins/commerce (solo estructura)
```

## Traceability

- Requirement: "compras debe registrarse y cargarse en el host, no fallar por estructura"
- Commit: COMPRAS-001 (symlink backend + events/permissions)
- Deployment: main (plugin descubierto al arrancar el host)

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now
- [x] Invariants preserved
- [x] Verification passed
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established
