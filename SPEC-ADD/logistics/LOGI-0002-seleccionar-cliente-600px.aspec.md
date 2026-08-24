# A.SPEC LOGI-0002 — Set 600px width on Seleccionar cliente modal in Nueva Jornada

> Cambio ya implementado y verificado. Modal "Seleccionar cliente" de la
> creación de jornada (logistics) pasa a 600px de ancho.

## WHY

El modal de búsqueda de clientes (`CustomerSearchDialog`) usaba el ancho por
defecto del `SearchDialog` (`max-w-4xl`, ~56rem), demasiado ancho para la
acción de "Agregar cliente" dentro de "Nueva jornada". Se solicitó un ancho
fijo de 600px para esa modal en particular.

## WHAT

- Se expuso `maxWidthClassName` en `SearchDialog` (shell) y en
  `CustomerSearchDialog` (CRM), con default `max-w-4xl` (sin romper el resto
  de usos).
- En `CreateJornadaDialog` (logistics) la instancia de "Seleccionar cliente"
  ahora pasa `maxWidthClassName="max-w-[600px]"`.

## SCOPE

- `vendor/systutor-shell/src/ui/search-dialog.tsx` (prop `maxWidthClassName` + default)
- `plugins/crm/frontend/components/CustomerSearchDialog.tsx` (prop threading)
- `plugins/logistics/frontend/components/vehicle-sessions/CreateJornadaDialog.tsx` (uso con 600px)

## OUT OF SCOPE

- No se cambia el ancho de las demás instancias de `CustomerSearchDialog`
  (contracts, delivery points, orders, agenda, cylinders, planning): siguen en
  `max-w-4xl`.
- No se modifica la lógica de búsqueda ni las columnas del diálogo.

## CONTRACT

- Precondición: el `Dialog` base acepta `maxWidthClassName`.
- Postcondición: al abrir "Agregar cliente" en "Nueva jornada", la modal mide
  hasta 600px de ancho. Las demás modales de cliente quedan igual.

## INVARIANTS

```yaml
invariants:
  - CustomerSearchDialog en otros módulos MUST seguir en max-w-4xl por defecto.
  - La búsqueda y selección de clientes MUST seguir funcionando.
  - El cierre de la modal (onClose) MUST seguir disponible.
```

## VERIFICATION

- `apps/web` tsc --noEmit: sin errores nuevos (único error es pre-existente
  `api/index.ts` duplicate export, ajeno).
- Grep: `grep -n "max-w-\[600px\]" plugins/logistics/frontend/components/vehicle-sessions/CreateJornadaDialog.tsx` -> presente.

## ROLLBACK

Reversible con `git restore` de los 3 paths. Sin migraciones ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - vendor/systutor-shell/src/ui/search-dialog.tsx
    - plugins/crm/frontend/components/CustomerSearchDialog.tsx
    - plugins/logistics/frontend/components/vehicle-sessions/CreateJornadaDialog.tsx
  prohibited:
    - plugins/crm/frontend/api/**
    - plugins/logistics/backend/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - logistics.nueva_jornada.cliente.modal.width
  indirect:
    - crm.CustomerSearchDialog (prop nuevo, default preserva comportamiento)
  must_not_affect:
    - otras modales de cliente
    - busqueda de clientes
    - backend
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

- Requirement: ancho fijo 600px para modal Seleccionar cliente en Nueva Jornada
- Commit main: 675cf81 — "LOGI-0002: set 600px width on Seleccionar cliente modal in Nueva Jornada"
- Commit shell (submodule systutor-shell): df798d2 — "ui: expose maxWidthClassName on SearchDialog (default max-w-4xl)"
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
- [x] Traceability established (commit 675cf81 + shell df798d2)
