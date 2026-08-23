# A.SPEC LOGI-0013 — WarehousesPage: card Almacenes centrada en modal Jornadas

> Cambio IMPLEMENTADO. En `WarehousesPage` la card "Almacenes" se mostraba
> desplazada a la izquierda dentro del modal de Jornadas (700px) porque el
> wrapper usaba `grid ... xl:grid-cols-[1.4fr,1fr]` (breakpoint `xl` es por
> viewport, no por contenedor): en desktop la card caía en la columna 1.4fr y
> quedaba un 1fr vacío a la derecha. Se centraliza la card.

## WHY

El usuario ve la card de Almacenes "rara"/no centrada dentro del modal de
Jornadas. Causa: el grid de 2 columnas (vestigial, solo hay una card) deja
espacio vacío a la derecha en viewport ≥1280px aunque el modal mida 700px.
Pide centrar la card "Almacenes".

## WHAT

- `plugins/logistics/frontend/pages/WarehousesPage.tsx`:
  - Wrapper de la card: `grid gap-6 xl:grid-cols-[1.4fr,1fr]` →
    `flex justify-center`.
  - `<Card>` → `<Card className="w-full max-w-[640px]">` (centrada con margen
    dentro del modal de 700px; full-width en pantallas chicas).

## SCOPE

- `plugins/logistics/frontend/pages/WarehousesPage.tsx`

## OUT OF SCOPE

- No se cambia el contenido de la card (tabla, columnas, acciones).
- No se cambia el modal en `VehicleSessionsPage` (ya en 700px x 400px mín).
- Sin dependencias nuevas.

## CONTRACT

- Precondición: card Almacenes en grid de 2 columnas, desplazada a la
  izquierda en viewport ancho.
- Postcondición: card Almacenes centrada horizontalmente (max 640px, con
  margen) dentro del modal.

## INVARIANTS

```yaml
invariants:
  - Tabla de almacenes MUST seguir renderizando igual (mismas columnas/datos).
  - Sin cambios en datos, API ni permisos.
  - Sin dependencias nuevas.
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores nuevos.
- Grep: `grep -n "flex justify-center\|max-w-\[640px\]" plugins/logistics/frontend/pages/WarehousesPage.tsx` -> ambas coinciden.
- Runtime: abrir "Almacenes" desde Jornadas; la card está centrada (no pegada
  a la izquierda) dentro del modal de 700px.

## ROLLBACK

Reversible: `git restore` del único path. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/frontend/pages/WarehousesPage.tsx
  prohibited:
    - plugins/logistics/frontend/pages/VehicleSessionsPage.tsx
    - plugins/logistics/backend/**
    - apps/web/src/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - logistics.warehouses.card.layout
  indirect:
    - logistics.warehouses.page (vista, standalone y embebida)
  must_not_affect:
    - warehouse table data
    - other modals / pages
    - data layer / API
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - LOGI-0012 (modal Almacenes en Jornadas, tamaño)
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

- Requirement: card Almacenes centrada dentro del modal de Jornadas
- Commit: pendiente (asignar al integrar)
- Deployment: n/a
- Pendiente: `catpuccin_mocha` (LOGI-0008) aún sin A.SPEC propio -> sugerir
  LOGI-0014 para trazabilidad completa.

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
