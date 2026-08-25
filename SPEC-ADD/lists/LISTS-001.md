# A.SPEC LISTS-001 — Stock y Envases: quitar "Acciones", doble-click abre detalle

## WHY

Mismo problema que PROD-001 (productos) y CLI-001 (clientes): la columna
"Acciones" duplica el detalle. Se aplica el patrón ya establecido a las dos
listas que lo usaban: Stock (balances) y Envases (cilindros, logistics).

## WHAT

- `plugins/stock/frontend/pages/StockBalancePage.tsx`: se elimina la columna
  `actions` ("Acciones", botones Detalle/Ajustar) y se agrega
  `onRowDoubleClick` que abre `ModalDetalleStock` via `setDetailSelection`.
- `plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx`:
  se elimina la columna `actions` ("Ver ficha") y se agrega `onRowDoubleClick`
  que llama `onOpenDetail(row)`. Se quita el import `Button` sin uso.

`DataTable` ya expone `onRowDoubleClick` (PROD-001).

Verdad nueva falsable ahora: en Stock y Envases no hay columna "Acciones"; un
doble-click en la fila abre el detalle/ ficha.

## SCOPE

- `plugins/stock/frontend/pages/StockBalancePage.tsx`.
- `plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx`.

## OUT OF SCOPE

- Otras columnas "Acciones" (MovementsPage, ProductDetailPage, dialogs de
  productos, CommercialDialog, StockConfigPage) — futuras specs.
- Cambios en modales (ya exponen las operaciones: ModalDetalleStock tiene
  onOpenAdjust/Transfer/Config).

## CONTRACT

Precondiciones:
- Stock y Envases muestran columna "Acciones".

Postcondiciones:
- Sin columna "Acciones" en ambas tablas.
- Doble-click en fila abre detalle (stock) / ficha (envase).
- Ajustar/Transferir/Configurar siguen accesibles desde ModalDetalleStock.

## INVARIANTS

```yaml
invariants:
  - operaciones de stock (ajuste/transferencia/config) siguen alcanzables desde el detalle
  - click sobre serial en envases sigue abriendo ficha
  - otras tablas sin cambios
```

## VERIFICATION

```bash
grep -n "header: \"Acciones\"" plugins/stock/frontend/pages/StockBalancePage.tsx plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx  # vacio
grep -n "onRowDoubleClick" plugins/stock/frontend/pages/StockBalancePage.tsx plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx
# manual: doble-click en fila abre detalle en /stock y /envases
```

## ROLLBACK

Reversible: restaurar columnas `actions` (git checkout).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/stock/frontend/pages/StockBalancePage.tsx
    - plugins/logistics/frontend/cylinders/components/CylinderTableSection.tsx
  prohibited:
    - vendor/**
    - plugins/crm/**, plugins/productos/** (ya tratados), otros plugins
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - listas de stock y envases
  indirect: []
  must_not_affect:
    - operaciones de stock/detalles
    - otras tablas
```

## Composition

```yaml
composition:
  requires_aspecs:
    - PROD-001 (onRowDoubleClick en DataTable)
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
  preferred_new_logic_locations:
    - pages/tablas ya existentes
```

## Traceability

- Requirement: "acciones desaparecen en stock y envases; doble-click entra a detalle"
- Commit: `103a2bf`
- Deployment: main

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