# A.SPEC LOGI-0010 — Envases: ocultar info muerta (descripción, barcode, marca)

> Cambio IMPLEMENTADO. En la tabla de envases (`CylinderTableSection.tsx`) se
> eliminan visualmente las sub-líneas de descripción, barcode y marca: son
> información muerta y no deben aparecer NUNCA, ni siquiera cuando el dato
> subyacente existe ("real").

## WHY

El usuario considera que `description`, `barcode1/2` y `brand` de un envase son
información muerta en la vista de tabla. Los placeholders `Sin descripción`,
`Sin barcode` y `Sin marca` (y el contenido real detrás) no aportan y ensucian
la fila. Pide que desaparezcan de forma puramente visual, incluso con dato
real presente.

## WHAT

- `plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx`:
  - Columna `Envase` (`serial`): se elimina el `<p>` de descripción
    (`{row.description || "Sin descripción"}`) y el `<p>` de barcode
    (`{row.barcode2 || row.barcode1 || "Sin barcode"}`). Queda solo el botón
    con `row.serial`.
  - Columna `Gas / marca` (`gas`): se elimina el `<p>` de marca
    (`{brandById.get(row.brand_id ?? "") || "Sin marca"}`). Queda solo el
    `<p>` de gas (`productById`/`gasById` o `Sin gas`).
- Sin cambios de lógica, tipos, props ni data fetching. Cambio exclusivamente
  visual (JSX render).

## SCOPE

- `plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx`

## OUT OF SCOPE

- No se toca el modelo de datos ni la API (los campos siguen existiendo en el
  backend / tipo `Cylinder`).
- No se cambia `Sin gas` (fuera de alcance; el usuario solo pidió descripción,
  barcode y marca).
- No se afecta el detalle del envase (`onOpenDetail`), solo la tabla.
- Sin dependencias nuevas.

## CONTRACT

- Precondición: la tabla renderiza sub-líneas de descripción/barcode en la
  columna Envase y de marca en Gas/marca.
- Postcondición: esas tres sub-líneas NO se renderizan jamás (ni placeholder ni
  dato real). La fila muestra serial + gas (o `Sin gas`).

## INVARIANTS

```yaml
invariants:
  - La columna Envase MUST seguir mostrando row.serial (botón abre detalle).
  - La columna Gas/marca MUST seguir mostrando gas (o "Sin gas").
  - Sin cambios en tipos/props del componente (solo eliminación de JSX).
  - Sin dependencias nuevas.
  - El detalle del envase (modal) NO se ve afectado por este cambio.
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores nuevos.
- Grep: `grep -n "Sin descripción\|Sin barcode\|Sin marca" plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx` -> sin coincidencias.
- Runtime: en la tabla de envases, ninguna fila muestra descripción, barcode ni
  marca (con dato real o sin él). Serial y gas visibles.

## ROLLBACK

Reversible: `git restore` del único path. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx
  prohibited:
    - plugins/logistics/backend/**
    - plugins/logistics/frontend/cylinders/** (otros archivos)
    - apps/web/src/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - logistics.cylinders.table.render
  indirect:
    - logistics.cylinders.list (vista)
  must_not_affect:
    - cylinder detail modal
    - data layer / API
    - other themes or pages
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: []
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

- Requirement: ocultar visualmente descripción/barcode/marca de envases (info muerta)
- Commit: pendiente (asignar al integrar)
- Deployment: n/a

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
