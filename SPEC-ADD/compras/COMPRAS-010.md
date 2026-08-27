# A.SPEC COMPRAS-010 — Costos adicionales de recepción + costo real

## WHY

COMPRAS-009 cierra cuánto se **aceptó** físicamente. Pero el costo real de lo
recibido incluye gastos que no vienen en el precio del ítem: flete, aranceles,
manipuleo, seguros (VISION §22). Hoy `unit_cost` del ítem ignora esos cargos,
así que el costo inventariado está subestimado y la futura conciliación tres
vías (§24) contrastaría factura contra un costo incompleto.

## WHAT

Una verdad nueva: **el costo real por unidad aceptada prorratea el costo del
ítem más los costos adicionales de la recepción.**

1. Nueva tabla `com_receipt_cost_lines`:
   - `id`, `tenant_id`, `receipt_id` FK (`com_purchase_receipts`),
     `cost_type` (`FLETE | ARANCEL | MANIPULEO | SEGURO | OTRO`),
     `amount: Numeric(19,4)`, `currency: String(3)`, `notes: Text | NULL`.
2. `ReceiveOrderRequest` (y `commercial-close`) aceptan
   `cost_lines: list[{cost_type, amount, currency?, notes?}]` opcional.
3. Servicio `recompute_receipt_real_cost(receipt)`:
   - `item_cost_total` = Σ(`unit_cost * qty_accepted`) de los ítems del receipt.
   - `extra_total` = Σ(`amount`) de `com_receipt_cost_lines`.
   - `real_total` = `item_cost_total + extra_total`.
   - `unit_cost_real` = `real_total / Σ(qty_accepted)` (por receipt; expuesto
     también por ítem vía prorrateo simple `extra_total * peso_item / total`).
4. `PurchaseReceiptRead` expone `extra_total`, `real_total`,
   `unit_cost_real` y `cost_lines[]`.
5. Hook opcional: si el conector de stock lo soporta, se re-emite el costo
   real al ledger de costo (§33) solo sobre `qty_accepted`. Si no, se deja
   solo en lectura (ver OUT OF SCOPE).

## SCOPE

- `plugins/commerce/migrations/010_receipt_cost_lines.py`: nueva tabla +
  índice `ix_com_receipt_cost_lines_receipt_id`.
- `plugins/commerce/purchase/backend/models.py`: `ComReceiptCostLine`.
- `plugins/commerce/purchase/backend/schemas/orders.py`:
  `ReceiveCostLine`, `PurchaseReceiptRead` con costos.
- `plugins/commerce/purchase/backend/services/receipts.py`:
  `recompute_receipt_real_cost`, persistencia de `cost_lines`.
- `plugins/commerce/purchase/backend/routers/orders.py` / `receipts.py`:
  serializan costos.
- Frontend: `PurchaseOrdersPage.tsx` (sección "Costos adicionales" en dialog),
  `types.ts`.
- Tests: `apps/api/tests/test_compras_receipt_cost.py`.

## OUT OF SCOPE

- Factura de proveedor y tres vías (§23/§24) — COMPRAS-011.
- Reescritura obligatoria del ledger de stock con costo real (se deja como
  hook opcional; si el conector no implementa, solo se expone en lectura).
- Diferencias/incidencias (§17/§18) — ya en COMPRAS-009.
- Costos por devolución de mercadería (§26 mercadería) — futura.

## CONTRACT

Precondiciones:

- Receipt existe (ya creado vía 002/008/009).
- `cost_lines[].amount >= 0`; `cost_type` en catálogo permitido.

Postcondiciones:

- `extra_total` = suma exacta de las líneas.
- `unit_cost_real` = (`item_cost + extra`) / `Σ qty_accepted`, definido
  (0 si no hay aceptadas → se reporta NULL, no división por cero).
- Sin `cost_lines`: `extra_total = 0`, `unit_cost_real = unit_cost` del ítem
  (retrocompatibilidad).

## INVARIANTS

```yaml
invariants:
  - "unit_cost_real NUNCA divide por cero (NULL si qty_accepted=0)."
  - "cost_lines son solo lectura-contable; no afectan qty recibidas."
  - "Sin cost_lines: comportamiento idéntico al actual."
  - "Cero escrituras lg_* (§32 intacta)."
  - "Suite compras previa verde; tsc limpio."
```

## VERIFICATION

- `test_receipt_cost_lines_sum_to_extra_total`.
- `test_receipt_unit_cost_real_prorates_extras`.
- `test_receipt_no_cost_lines_keeps_unit_cost`.
- `test_receipt_cost_zero_accepted_returns_null_unit_real`.
- Suite compras previa verde; `tsc --noEmit` limpio.

Manual: recepcionar con flete 100 + arancel 50 sobre 8 aceptadas →
`unit_cost_real` sube; detalle de orden muestra `extra_total=150`.

## ROLLBACK

Reversible: revertir commit; migración 010 `downgrade` elimina la tabla
(solo se pierde desglose de costos adicionales).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/migrations/010_receipt_cost_lines.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/orders.py
    - plugins/commerce/purchase/backend/services/receipts.py
    - plugins/commerce/purchase/backend/routers/orders.py
    - plugins/commerce/purchase/backend/routers/receipts.py
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
    - plugins/commerce/purchase/frontend/types.ts
    - apps/api/tests/test_compras_receipt_cost.py
  prohibited:
    - plugins/logistics/**
    - plugins/stock/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.receipts.costo_real
  indirect:
    - compras.ui.recepcion # sección costos
  must_not_affect:
    - qty recibidas/aceptadas (009)
    - stock ledger (salvo hook optativo)
    - lifecycle de órdenes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-009 # usa qty_accepted para prorrateo
  must_compose_with:
    - COMPRAS-011 # tres vías contrastará factura vs unit_cost_real
  systemic_invariants:
    - "El costo real siempre incluye cargos de recepción."
  composition_checks:
    - Receipt con cost_lines → unit_cost_real > unit_cost ítem.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: costeo vive en receipts existente + 1 tabla cost_lines
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - services/receipts.py
```

## Traceability

- Requirement: VISION §22 (costos adicionales + costo real). Milestone
  procure-to-pay hasta COMPRAS-011 (sesión 2026-08-26).
- Commit: pendiente (al ejecutar).
- Deployment: migración 010 en runtime del plugin commerce.

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
