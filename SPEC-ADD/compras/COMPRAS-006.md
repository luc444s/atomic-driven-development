# A.SPEC COMPRAS-006 — Despachos operativos end-to-end: autenticación interna y queryFn correcto

> A.SPEC de estabilización posterior a COMPRAS-005: dos fallas funcionales que
> impedían usar los despachos en producción, encontradas en pruebas reales del
> usuario y diagnosticadas con evidencia CDP (Chrome DevTools Protocol).

## WHY

COMPRAS-005 pasó su suite (15/15) pero falló en uso real por dos defectos:

1. **Recepción contra stock imposible**: `internal_api_token` nunca existió en
   `Settings`; el conector enviaba `Bearer ` vacío → httpx
   `LocalProtocolError: Illegal header value`. Toda recepción con stock real
   crasheaba.
2. **Dropdown de proveedor vacío**: el form de despacho pasaba
   `queryFn: listSuppliers` como referencia directa. React Query invoca el
   queryFn con su objeto de contexto como primer argumento; ese objeto entró al
   parámetro opcional `search` → request
   `?search=[object+Object]` → backend devolvía **0 resultados con estado
   success** (falla silenciosa: sin error visible, estado "success" en cache).

## WHAT

Dos verdades falsables ahora:

1. Las llamadas servidor-a-servidor de compras autentican con un JWT real:
   `_internal_token()` hace login con credenciales configurables
   (`Settings.internal_user_email/password`) y ese token se usa en
   `stock/purchase-in` y en lecturas de Logística (`/tanks`).
2. El queryFn del selector de proveedor está protegido contra la inyección de
   contexto (`() => listSuppliers()`); el dropdown lista proveedores reales.

Además: el dialog de recepción usa Combobox de almacenes reales
(`listWarehouses` filtrados) en vez de Input de ID manual.

## SCOPE

- `apps/api/app/config.py`: settings `internal_user_email/password`.
- `routers/common.py`: helper `_internal_token()`.
- `routers/receipts.py`: usa token interno en `/tanks`.
- `components/DispatchFormModal.tsx`: arrow queryFn.
- `pages/PurchaseOrdersPage.tsx`: dropdown de almacenes + muestra SKU·nombre
  en items a recibir (no UUIDs).
- Grant SQL documentado: permisos de compras al rol operativo (SYSTUTOR).

## OUT OF SCOPE

- Service account dedicada con permisos acotados (hoy usa admin — deuda
  declarada).
- Auditoría automática de grants al habilitar plugins.
- Retorno de cilindros y conciliación por serial (siguiente spec).

## CONTRACT

Postcondiciones:

- Recibir mercadería contra stock real funciona sin errores HTTP.
- Abrir "Nuevo despacho" lista los proveedores existentes.
- Un usuario cuyo rol carezca de permisos de compras NO ve datos (grant es
  explícito por rol).

## INVARIANTS

```yaml
invariants:
  - "Credenciales internas solo en Settings/env, jamás hardcodeadas fuera de
     defaults de desarrollo."
  - "La regla queryFn-arrow aplica a todo queryFn nuevo cuya función acepte
     parámetros."
```

## VERIFICATION

- Suite backend: `pytest tests/test_compras_plugin.py tests/test_compras_dispatch.py -q`
  → 15 passed (mocks intactos).
- Live CDP (tablet): `__queryClient` tras invalidate → `dataLen: 1`, select con
  opción SYSTUTOR.
- Recepción real contra stock sin LocalProtocolError.

## ROLLBACK

Reversible por git. El grant de permisos en DB se revierte con DELETE sobre
role_permissions.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/api/app/config.py
    - apps/api/tests/test_compras_dispatch.py
    - plugins/commerce/purchase/backend/routers/common.py
    - plugins/commerce/purchase/backend/routers/receipts.py
    - plugins/commerce/purchase/frontend/components/DispatchFormModal.tsx
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
  prohibited:
    - plugins/logistics/**
    - plugins/stock/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.receipts.stock_integration
    - compras.dispatches.ui
  indirect:
    - logistics.cylinders.read (/tanks ahora autenticado)
  must_not_affect:
    - máquina de estados de órdenes/despachos
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-002
    - COMPRAS-003
    - COMPRAS-004
    - COMPRAS-005
  systemic_invariants:
    - "Los permisos nuevos de plugin requieren 3 pasos: manifest +
       register_permissions + grant a rol."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: helpers de infraestructura HTTP interna viven en routers/common.py
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - routers/common.py
```

## Traceability

- Requirement: reportes del usuario con stacktrace httpx (`Illegal header
  value b'Bearer '`) y reporte visual de dropdown vacío; diagnóstico con
  evidencia vía CDP sobre Cromite Android.
- Commits: `2a4808e` (auth interna) · `e7b91e2`+`db80f32` (almacenes dropdown)
  · fix uuid en recepción · `20105a2` (queryFn arrow) · grant SQL documentado
  en sesión.
- Estado: **DONE**

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
