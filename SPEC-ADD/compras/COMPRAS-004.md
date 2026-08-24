# A.SPEC COMPRAS-004 — Catálogo de proveedores como vista principal con detalle estilo cliente

## WHY

Hoy Compras aterriza en `PurchaseOrdersPage`, que mezcla un dialog lateral de
proveedores (`SupplierManagementDialog`, 389 líneas, con acciones dentro de
tablas) y la tabla de órdenes. El usuario definió la UX objetivo: entrar a
Compras muestra **solo el catálogo de proveedores**, filas limpias sin botones,
y **doble click abre el detalle del proveedor** imitando exactamente el patrón
probado de clientes (`CustomersListPage` + `ModalDetalleCliente`), con lugar
para la futura sección "Envases en custodia" (COMPRAS-VISION §11/§40).

Las órdenes de compra no desaparecen: se mudana una pestaña/ruta secundaria.

## WHAT

Una transición observable: al entrar a Compras se ve el **catálogo de
proveedores** (búsqueda + tabla limpia + paginación + "Nuevo proveedor"), y el
doble click en una fila abre el **detalle de proveedor** estructurado igual que
el detalle de cliente. La vista de órdenes pasa a pestaña secundaria.

Estructura nueva (espejo del patrón CRM):

```text
frontend/
├── pages/
│   ├── SuppliersPage.tsx        # landing: buscador + tabla + doble click
│   └── PurchaseOrdersPage.tsx   # se conserva, ya sin dialog de proveedores
└── components/
    ├── SupplierDetailModal.tsx  # espejo ModalDetalleCliente:
    │                            # OverviewCard + Direcciones + Contactos +
    │                            # Bancos + Términos + [Envases en custodia]
    └── SupplierOverviewCard.tsx # cabecera resumen del detalle
```

Comportamientos observables:

1. Ruta `commerce/purchase-orders` pasa a ser pestaña "Órdenes"; nueva ruta
   `commerce/suppliers` es la entrada ("Proveedores") del grupo Gestión
   Comercial.
2. Tabla de proveedores: columnas nombre/comercial, documento, teléfono,
   email, activo — sin botones por fila.
3. Doble click → `SupplierDetailModal` con:
   - OverviewCard (razón social, comercial, documento, contacto, estado);
   - secciones Direcciones / Contactos / Cuentas bancarias / Términos de pago
     reutilizando la lógica existente del dialog actual;
   - sección "Envases en custodia" con empty-state ("Sin envases en custodia
     todavía") — placeholder funcional para COMPRAS-005;
   - acción Editar que abre el formulario existente precargado.
4. El botón "Nuevo proveedor" vive fuera de la tabla (header de la card).
5. Eliminación de `SupplierManagementDialog` (su lógica migra al modal de
   alta/edición y al detalle).

## SCOPE

- `plugins/commerce/purchase/frontend/register.ts` (rutas/nav).
- `pages/SuppliersPage.tsx` (nuevo), `PurchaseOrdersPage.tsx` (quita dialog).
- `components/SupplierDetailModal.tsx`, `SupplierOverviewCard.tsx` (nuevos).
- Formulario de alta/edición de proveedor (extraído del dialog actual o nuevo
  `SupplierFormModal.tsx`).
- Eliminación de `components/SupplierManagementDialog.tsx`.

## OUT OF SCOPE

- Backend: cero cambios (la API de suppliers ya expone todo lo necesario).
- Datos reales de custodia de envases (requiere COMPRAS-005 despacho/custodia).
- Órdenes: no cambia su comportamiento; solo deja de contener proveedores.
- Permisos nuevos: se reutilizan `compras.supplier.read/manage`.

## CONTRACT

Precondiciones:

- API suppliers operativa (list/create/update/disable + addresses/contacts/banks).

Postcondiciones:

- Entrar a Compras renderiza SuppliersPage; ninguna fila tiene botones.
- Doble click en fila abre detalle con las 4 secciones + placeholder custodia.
- Las rutas de órdenes siguen accesibles y funcionales (tabla + acciones
  contextuales de COMPRAS-002 intactas).
- `grep -r "SupplierManagementDialog" plugins/commerce/purchase/frontend`
  → vacío.

## INVARIANTS

```yaml
invariants:
  - Patrón visual y de interacción idéntico al catálogo de clientes
    (buscador, DataTable, onRowDoubleClick, Pagination, modal detalle).
  - Colores solo vía tokens semánticos del tema (UI-THEMES-001); nada hardcodeado.
  - Los permisos compras.supplier.read/manage siguen gateando lectura/gestión.
  - La suite backend sigue en verde (este spec no toca backend).
```

## VERIFICATION

- Frontend: `cd apps/web && npx tsc --noEmit` limpio.
- `grep -rn "SupplierManagementDialog" plugins/commerce/purchase/frontend` vacío.
- Manual verificable:
  1. Nav "Compras" → aterriza en Proveedores (no en órdenes).
  2. Filas sin botones; doble click abre detalle con OverviewCard + 4 secciones
     + placeholder "Envases en custodia".
  3. Alta desde "Nuevo proveedor" y edición desde el detalle funcionan;
     los datos persisten tras refetch.
  4. Pestaña/ruta Órdenes mantiene confirmar/recepcionar/cerrar/cancelar.
- Tests frontend existentes si hay del módulo compras siguen verdes.

## ROLLBACK

Reversible por git (revert de commits). Sin efectos en datos ni backend.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/purchase/frontend/**
  prohibited:
    - plugins/commerce/purchase/backend/**
    - plugins/crm/**          # se imita el patrón, NO se importa ni modifica
    - vendor/**
    - apps/api/tests/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.frontend.navegacion
    - compras.frontend.proveedores
  indirect:
    - compras.frontend.ordenes # pierde el dialog, gana limpieza
  must_not_affect:
    - crm clientes (patrón fuente, solo referencia)
    - backend compras
    - otros plugins
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-001 # plugin enabled
    - COMPRAS-002 # órdenes conservan sus acciones contextuales
  must_compose_with:
    - UI-THEMES-001 # tokens semánticos obligatorios
    - COMPRAS-003 # split backend independiente pero previo en espíritu
  systemic_invariants:
    - Un mismo gesto (doble click) significa "detalle" en clientes y proveedores.
  composition_checks:
    - Recorrer CRM clientes y Compras proveedores en la misma sesión:
      interacción indistinguible salvo contenido.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: un componente por responsabilidad (page / detail modal /
    overview card / form), espejando la estructura de crm/frontend
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - components/SupplierDetailModal.tsx
    - components/SupplierFormModal.tsx
```

## Traceability

- Requirement: feedback directo del usuario — "cuando entre aquí solo vea la
  vista de proveedores, nada de botones dentro de tablas; doble click abre
  detalles del proveedor parecido a clientes... imitar detalle cliente";
  confirmación "exactamente las mismas características".
- Referencia de patrón: plugins/crm/frontend/pages/CustomersListPage.tsx +
  components/ModalDetalleCliente.tsx.
- Commit: pendiente.

## Definition of Done

- [ ] Objective satisfied
- [ ] Scope respected
- [ ] Contract satisfied
- [ ] Independent falsable truth exists now
- [ ] Invariants preserved
- [ ] Verification passed
- [ ] Rollback / compensation is honest
- [ ] Composition checks passed when applicable
- [ ] No unrelated changes
- [ ] Structural constraints respected
- [ ] Traceability established
