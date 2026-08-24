# A.SPEC LOGI-0011 — Envases: Almacenes fuera del sidebar (Estado revertido)

> Cambio IMPLEMENTADO (parcialmente revertido). Se elimina el item de
> navegación `Almacenes` del sidebar. La ruta y la página de almacenes siguen
> existiendo; solo desaparece del menú lateral. La columna `Estado` de la tabla
> de envases SE RESTAURÓ (había sido quitada en la primera pasada por petición
> "el estado simplemente"; el usuario la quiso de vuelta).

## WHY

- El usuario sigue depurando la vista de envases: la columna `Estado` es
  ruido visual en la tabla y pide quitarla ("el estado simplemente").
- El item `Almacenes` del sidebar debe desaparecer (decisión de navegación);
  la funcionalidad de almacenes no se elimina, solo su acceso directo por menú.

## WHAT

- `plugins/logistics/frontend/register.ts`:
  - Se elimina la entrada de navegación
    `{ to: .../logistics/warehouses, label: "Almacenes", ... }` del array
    `navigation`. La ruta `logistics/warehouses` y `WarehousesPage` se
    conservan.
- `plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx`:
  - **NO se modifica** (columna `Estado` restaurada: sigue con
    `<CylinderStateBadge state={row.current_state} />` y su import).

## SCOPE

- `plugins/logistics/frontend/register.ts` (único archivo tocado)

## OUT OF SCOPE

- No se borra la ruta `logistics/warehouses` ni `WarehousesPage`.
- No se cambia permisos, API ni backend.
- No se tocan otras columnas de la tabla (serial, gas, PH, etc.).
- Sin dependencias nuevas.

## CONTRACT

- Precondición: tabla de envases muestra columna Estado; sidebar lista item
  Almacenes.
- Postcondición: tabla de envases SIN columna Estado; sidebar SIN item
  Almacenes. Almacenes sigue accesible por URL directa.

## INVARIANTS

```yaml
invariants:
  - Columnas serial/gas/PH (y demás) MUST seguir renderizando.
  - WarehousesPage MUST seguir accesible vía ruta (no se borra route/component).
  - Sin cambios en tipos de datos ni API.
  - Sin dependencias nuevas.
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores nuevos.
- Grep: `grep -n "Almacenes" plugins/logistics/frontend/register.ts` -> sin
  coincidencias en el array `navigation`.
- Grep: `grep -n "key: \"state\"" plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx` -> SÍ existe (columna Estado restaurada).
- Runtime: tabla envases muestra columna Estado; sidebar no lista Almacenes.

## ROLLBACK

Reversible: `git restore` de los 2 paths. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx
    - plugins/logistics/frontend/register.ts
  prohibited:
    - plugins/logistics/frontend/pages/WarehousesPage.tsx
    - plugins/logistics/backend/**
    - apps/web/src/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - logistics.cylinders.table.columns
    - logistics.sidebar.navigation
  indirect:
    - logistics.cylinders.list (vista)
  must_not_affect:
    - warehouses route / page
    - data layer / API
    - other sidebar items
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - LOGI-0010 (misma tabla envases, limpieza visual previa)
  systemic_invariants: []
  composition_checks: []
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations: []
```

## Traceability

- Requirement: quitar columna Estado de envases + Almacenes fuera del sidebar
- Commit: pendiente (asignar al integrar)
- Deployment: n/a
- Pendiente: `catpuccin_mocha` (LOGI-0008) aún sin A.SPEC propio -> sugerir
  LOGI-0012 para trazabilidad completa.

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
- [x] Traceability established (commit pendiente de integración)
