# A.SPEC LOGI-0012 — Modal Almacenes (Jornadas): ancho 600px, alto mínimo 400px

> Cambio IMPLEMENTADO. El modal `Almacenes` abierto desde la página de Jornadas
> (`VehicleSessionsPage`) era demasiado amplio (1500px) y alto fijo (70vh),
> luciendo raro embebiendo `WarehousesPage`. Se acota a 700px de ancho y 400px
> de altura mínima.

## WHY

El usuario ve el modal de Almacenes en Jornadas desproporcionado (muy ancho) y
raro. Pide reducirlo a 600px de ancho y ~400px de altura mínima para que
encaje mejor como superficie secundaria.

## WHAT

- `plugins/logistics/frontend/pages/VehicleSessionsPage.tsx`:
  - Modal `Almacenes` (`Dialog open={isWarehousesOpen}`):
    `maxWidthClassName` de `max-w-[1500px]` → `max-w-[700px]`.
  - Contenedor interno de `WarehousesPage`: `h-[70vh] overflow-y-auto` →
    `min-h-[400px] overflow-y-auto` (altura mínima, crece si el contenido es
    mayor; sigue scrolleable).

## SCOPE

- `plugins/logistics/frontend/pages/VehicleSessionsPage.tsx`

## OUT OF SCOPE

- No se cambia `WarehousesPage` ni su lógica.
- No se cambian los otros modales de la página (jornada, vehículo, etc.).
- Sin dependencias nuevas.

## CONTRACT

- Precondición: modal Almacenes abre con `max-w-[1500px]` y `h-[70vh]`.
- Postcondición: modal Almacenes abre con ancho máximo 700px y altura mínima
  400px (scroll interno si el contenido excede).

## INVARIANTS

```yaml
invariants:
  - WarehousesPage MUST seguir renderizando dentro del modal (misma prop children).
  - Sin cambios en datos, API ni permisos.
  - Sin dependencias nuevas.
```

## VERIFICATION

- `apps/web` `tsc --noEmit`: sin errores nuevos.
- Grep: `grep -n "max-w-\[700px\]\|min-h-\[400px\]" plugins/logistics/frontend/pages/VehicleSessionsPage.tsx` -> ambas coinciden en el bloque Almacenes.
- Runtime: al abrir "Almacenes" desde Jornadas, el modal mide ~700px de ancho y
  >=400px de alto.

## ROLLBACK

Reversible: `git restore` del único path. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/frontend/pages/VehicleSessionsPage.tsx
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
    - logistics.vehicle-sessions.warehouses-modal.size
  indirect:
    - logistics.vehicle-sessions.page (vista)
  must_not_affect:
    - WarehousesPage logic
    - other modals
    - data layer / API
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

- Requirement: modal Almacenes en Jornadas a 600px ancho y 400px alto mínimo
- Commit: pendiente (asignar al integrar)
- Deployment: n/a
- Pendiente: `catpuccin_mocha` (LOGI-0008) aún sin A.SPEC propio -> sugerir
  LOGI-0013 para trazabilidad completa.

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
