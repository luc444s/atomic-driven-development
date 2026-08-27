# A.SPEC COMPRAS-020 — Extracción estructural de PurchaseOrdersPage.tsx

> `risk: normal` — `mode: judges-lite` (§4.2): split de estructura pura con
> proofs mecánicas (tsc + suites + wc + diff semánticamente vacío), sin
> migraciones ni semántica de negocio. Derivación §4.1: reversible, sin
> señales hard; normal por tocar el entrypoint principal del dominio.

## WHY

`PurchaseOrdersPage.tsx` está en 596/600 líneas y el lote 013/014/018 le suma
ediciones (~+9–15) → cruza el umbral de extracción §12.2 (600) al cerrar la
Versión Base. Hoy mezcla órdenes, recepción, facturas/conciliación y
reclamaciones — múltiples razones de cambio. Trigger §12.4: la A.SPEC del
lote que la cruce DEBE extraer o abrir A.SPEC estructural pareada — esta es
esa A.SPEC (pareada, ANTES de integrar 013/014/018 en esa página).

## WHAT

Una verdad estructural: **PurchaseOrdersPage.tsx queda como entrypoint
(wiring) de <150 líneas y su lógica vive en módulos cohesivos por dominio**
— sin cambiar NINGÚN comportamiento observable (rutas, props, schemas,
llamadas API, permisos, texto de UI idénticos).

### Layout objetivo (patrón ATOMIZER: entry + route-groups)

```
plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx   → wiring (<150)
plugins/commerce/purchase/frontend/pages/purchase/
  ├── OrdersPanel.tsx          → tabla órdenes + ciclo de vida (002)
  ├── ReceiptPanel.tsx         → recepción comercial/costos (009/010)
  ├── InvoicePanel.tsx         → facturas + conciliación + derivar (011/013)
  ├── ClaimsPanel.tsx          → reclamaciones (012)
  └── shared.ts                → tipos/helpers compartidos del panel (si aplica)
```

Orden de extracción (menor riesgo primero): shared → ClaimsPanel →
InvoicePanel → ReceiptPanel → OrdersPanel; cada extracción verifica tsc antes
de la siguiente.

## SCOPE

- `plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx` (reduce).
- `plugins/commerce/purchase/frontend/pages/purchase/*.tsx|ts` (nuevos).
- `apps/api/tests/` NO cambian (behavior-preserving; suites existentes prueban
  backend, frontend se valida por tsc + smoke).
- `SPEC-ADD/compras/COMPRAS-020.md` — esta spec.

## OUT OF SCOPE

- Cualquier cambio semántico: textos, rutas API, tipos, estados, permisos.
- DispatchesPage.tsx (198 líneas — sin presión).
- Nueva funcionalidad (los paneles ganan features con 013/014/018 DESPUÉS
  de esta extracción).

## CONTRACT

Precondiciones: suites de compras y tsc verdes en el punto de partida.

Postcondiciones:

- Entrypoint <150 líneas, solo wiring (imports + composición de paneles).
- Cada panel con UNA responsabilidad de dominio; `shared.ts` sin lógica de
  negocio (solo helpers puros/tipos reutilizados).
- Dif de comportamiento: cero (git diff de los .tsx extraídos muestra solo
  movimiento de código, sin renombres de API ni textos).

## INVARIANTS

```yaml
invariants:
  - "Comportamiento observable idéntico: mismas rutas API, payloads, textos y props (tsc --noEmit limpio + smoke visual)."
  - "Contratos públicos frontend intactos: types.ts y api.ts sin cambios (git diff --stat no los lista)."
  - "Cero escrituras lg_*/stock (cambio 100% frontend compras)."
  - "Backend y migraciones byte-idénticos (diff vacío fuera de frontend)."
  - "Suites compras completas verdes tras la extracción."
  - "Entrypoint final <150 líneas y sin lógica de negocio."
```

Correspondencia must_not_affect → INVARIANTS (§7.1): Blast Radius abajo.

## VERIFICATION

- `wc -l plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx` → <150.
- `git diff --stat` → solo archivos de la Change Surface.
- `cd apps/web && npx tsc --noEmit` → 0 errores.
- Suites backend intactas: `pytest apps/api/tests/test_compras_plugin.py
  apps/api/tests/test_compras_dispatch.py apps/api/tests/test_compras_receipt_commercial.py
  apps/api/tests/test_compras_receipt_cost.py apps/api/tests/test_compras_invoice_reconciliation.py
  apps/api/tests/test_compras_claims.py -q` → verde (invariante: backend byte-idéntico,
  las suites prueban que nada más se movió).
- Inspección de dif: los .tsx nuevos contienen código MOVIDO (git diff muestra
  bloques sin alterar salvo imports/exports), cero renombres de rutas/textos.
- Smoke manual: abrir página de órdenes → tabs Recepción/Facturas/Reclamaciones
  operan igual.

## ROLLBACK

Reversible: revert del commit (sin migraciones, sin estado). El comportamiento
no cambia, así que el rollback es trivialmente seguro.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
    - plugins/commerce/purchase/frontend/pages/purchase/**
    - SPEC-ADD/compras/COMPRAS-020.md   # self-inclusion (§5)
  prohibited:
    - plugins/commerce/purchase/backend/**
    - plugins/commerce/migrations/**
    - plugins/commerce/purchase/frontend/types.ts   # no renombres públicos
    - plugins/commerce/purchase/frontend/api.ts
    - apps/**
    - plugins/logistics/**
    - plugins/stock/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.ui.ordenes (reorganización interna)
  indirect:
    - paneles Recepción/Facturas/Reclamaciones (mismo DOM, misma lógica)
  must_not_affect:
    - backend y migraciones → invariant "byte-idénticos"
    - contratos públicos frontend (types/api) → prohibited + invariant
    - comportamiento observable → invariant idéntico
    - otros dominios → prohibited
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-012   # ClaimsPanel existe y debe extraerse tal como está
    - COMPRAS-011   # InvoicePanel existente
  must_compose_with:
    - COMPRAS-013   # ClaimDerivationPanel aterriza sobre InvoicePanel ya extraído
    - COMPRAS-014   # ReceiptServiceLines aterriza sobre ReceiptPanel ya extraído
    - COMPRAS-018   # panel de devoluciones entra en estructura ya extraída
    - COMPRAS-019   # miembro del set Versión Base
  systemic_invariants:
    - "La estructura frontend del dominio compras escala sin god-files durante toda la Versión Base."
  composition_checks:
    - "Entrypoint <150 líneas tras integrar 013/014/018 sobre la estructura extraída (wc medible)."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: >-
    split STRUCTURE not semantics; extracción por dominio de panel; shared.ts
    sin lógica de negocio
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - pages/purchase/*
```

## Traceability

- Requirement: SPEC-REVIEWER set-review 013..019 (finding cross-spec 2):
  PurchaseOrdersPage cruza 600 con el lote → A.SPEC estructural pareada §12.4,
  ANTES de integrar 013/014/018 en esa página.
- owner: Owner del canon ADD (rol)
- approver: Approver repo padre Systutor-oss (rol)
- Commit: al ejecutar.
- Deployment: frontend estático del plugin (build).

## Definition of Done

- [ ] Objective satisfied
- [ ] Scope respected
- [ ] Contract satisfied
- [ ] Independent falsable truth exists now
- [ ] Invariants preserved
- [ ] Verification passed
- [ ] Rollback honest (revert trivial)
- [ ] Composition checks passed when applicable
- [ ] No unrelated changes
- [ ] Structural constraints respected
- [ ] Traceability established
