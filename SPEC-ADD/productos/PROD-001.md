# A.SPEC PROD-001 — Productos: quitar "Acciones", doble-click abre detalle

## WHY

La columna "Acciones" en la lista de productos ocupa espacio y duplica lo que
el modal de detalle ya ofrece (editar vive ahí vía `onEditProduct`). Para un
feel más denso/SAP, el detalle se abre con doble-click sobre la fila.

## WHAT

En `plugins/productos/frontend/pages/ProductListPage.tsx`:
- Se elimina la columna `actions` ("Acciones") del `DataTable`.
- Se agrega `onRowDoubleClick` al `DataTable` que hace `setDetailId(row.id)`,
  abriendo `ModalDetalleProducto`.

Como el `DataTable` del shell solo exponía `onRowClick`, se añade la prop
`onRowDoubleClick` en `vendor/systutor-shell/src/ui/data-table.tsx` (mismo
patrón que `onRowClick`).

Verdad nueva falsable ahora: en la lista de productos no hay columna
"Acciones" y un doble-click en cualquier fila abre el modal de detalle; un
click simple no lo abre.

## SCOPE

- `plugins/productos/frontend/pages/ProductListPage.tsx` (quitar columna, conectar doble-click).
- `vendor/systutor-shell/src/ui/data-table.tsx` (prop `onRowDoubleClick`).

## OUT OF SCOPE

- Edición rápida desde la lista (sigue accesible en el modal de detalle).
- Cambios en `ModalDetalleProducto` (ya tiene `onEditProduct`).
- Otras páginas/tablas.

## CONTRACT

Precondiciones:
- Lista de productos muestra columna "Acciones" con botones Editar/Detalle.

Postcondiciones:
- La columna "Acciones" no existe en el `DataTable` de la lista.
- `onRowDoubleClick` en una fila → `detailId` seteado → `ModalDetalleProducto` abierto.
- Click simple en fila no abre el detalle.

## INVARIANTS

```yaml
invariants:
  - editar producto sigue accesible (boton en ModalDetalleProducto -> onEditProduct)
  - "Nuevo producto" sigue disponible en la pagina
  - otras tablas que usan DataTable sin onRowDoubleClick no cambian
  - DataTable sigue soportando onRowClick
```

## VERIFICATION

```bash
# abrir /productos (o ruta del plugin), con tema o sin:
# 1) la tabla NO tiene columna "Acciones"
# 2) doble-click en una fila abre ModalDetalleProducto
# 3) click simple no abre nada
# check de codigo:
grep -n "actions" plugins/productos/frontend/pages/ProductListPage.tsx   # sin columna Acciones
grep -n "onRowDoubleClick" plugins/productos/frontend/pages/ProductListPage.tsx vendor/systutor-shell/src/ui/data-table.tsx
```

## ROLLBACK

Reversible: restaurar columna `actions` y quitar `onRowDoubleClick` (git
checkout de los dos archivos). Sin datos en juego.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/productos/frontend/pages/ProductListPage.tsx
    - vendor/systutor-shell/src/ui/data-table.tsx
  prohibited:
    - vendor/systutor-core/**
    - plugins/logistics/**, plugins/crm/**, plugins/stock/**, plugins/tms/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - lista de productos (sin columna Acciones, doble-click abre detalle)
  indirect:
    - DataTable del shell (nueva prop opcional)
  must_not_affect:
    - otras tablas (onRowDoubleClick no usado)
    - edicion de producto
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: []
  systemic_invariants:
    - el detalle de producto ya existia; solo cambia el trigger de apertura
  composition_checks:
    - editar producto sigue alcanzable desde el modal de detalle
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - plugins/productos/frontend/pages/ProductListPage.tsx
```

## Traceability

- Requirement: "en productos desaparece Acciones; doble-click entra al detalle"
- Commit: PROD-001 (787bda8) + data-table shell (ebb06eb, submódulo)
- Deployment: main

- Commit: `787bda8`

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
