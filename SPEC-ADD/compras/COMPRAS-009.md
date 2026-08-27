# A.SPEC COMPRAS-009 — Recepción comercial: aceptadas/rechazadas + diferencias

## WHY

Hoy `POST /orders/{id}/receive` (VISION §13/§17) solo registra `qty_received`
por ítem. No distingue mercadería **aceptada** de **rechazada**, ni captura
**diferencias** (faltante/sobrante/dañado) ni incidencias. Eso impide:

- Saber cuánto entró realmente al inventario (solo lo aceptado).
- Alimentar costos reales (§22) y conciliación tres vías (§24) con datos sanos.
- Generar reclamaciones a proveedor (§25) desde una diferencia registrada.

El hueco es operativo y bloquea la capa comercial/financiera del módulo.

## WHAT

Una verdad nueva: **toda recepción comercial distingue aceptadas de
rechazadas y puede declarar una diferencia con incidencia.**

1. `com_purchase_receipts` nuevos campos:
   - `qty_accepted: Integer` (>=0)
   - `qty_rejected: Integer` (>=0)
   - `difference_type: String(20) | NULL` en
     `NULL | FALTANTE | SOBRANTE | DANO`
   - `incidence_notes: Text | NULL`
   - `commercial_closed_at: DateTime | NULL`
   - `commercial_closed_by: String(36) | NULL` (user id)
2. `ReceiveOrderRequest` acepta `lines[].qty_accepted` y `qty_rejected`
   opcionales.
   - Si se omiten: `qty_accepted = qty_received`, `qty_rejected = 0`
     (retrocompatibilidad total con recepciones actuales).
   - Validación: `qty_accepted + qty_rejected == qty_received` por línea;
     si no, 422.
   - `difference_type` se deriva: si `qty_received != qty_ordered` del ítem →
     `FALTANTE` (recibido < ordenado) o `SOBRANTE` (recibido > ordenado);
     si `qty_rejected > 0` → `DANO`. Precedencia: DANO si hay rechazo,
     sino FALTANTE/SOBRANTE por desvío vs ordenado.
3. Endpoint `POST /receipts/{id}/commercial-close` (idempotente) permite
   cerrar la parte comercial en recepción ya creada (flujo donde primero
   entra mercadería y luego se acepta/rechaza). Estampa
   `commercial_closed_at/by`.
4. Serialización de orden (`_serialize_order`) expone los nuevos campos en
   `receipts[]`.
5. Frontend: dialog "Recepcionar mercadería" muestra por línea
   `Aceptadas` / `Rechazadas` + selector de `difference_type` + notas;
   badge de incidencia en la lista de receipts.

## SCOPE

- `plugins/commerce/migrations/009_receipt_commercial_close.py`: +6 columnas
  + índice `ix_com_purchase_receipts_commercial_closed`.
- `plugins/commerce/purchase/backend/models.py`: campos en `ComPurchaseReceipt`.
- `plugins/commerce/purchase/backend/schemas/orders.py`:
  `ReceiveOrderLine.qty_accepted/rejected` opcionales;
  `PurchaseReceiptRead` con nuevos campos.
- `plugins/commerce/purchase/backend/services/receipts.py`: validación
  aceptadas+rechazadas==recibidas, derivación `difference_type`,
  `commercial_close_receipt`.
- `plugins/commerce/purchase/backend/routers/receipts.py`: nuevo endpoint
  `commercial-close`.
- `plugins/commerce/purchase/backend/routers/orders.py`: serializa campos.
- Frontend: `PurchaseOrdersPage.tsx` (campos en dialog + badge),
  `api.ts` / `types.ts`.
- Tests: `apps/api/tests/test_compras_receipt_commercial.py`.

## OUT OF SCOPE

- Costos adicionales y costo real (§22) — COMPRAS-010.
- Factura de proveedor y conciliación tres vías (§23/§24) — COMPRAS-011.
- Reclamaciones derivadas (§25) — COMPRAS-012 (futura).
- Concilación física serial vs físico (§16).
- Movimientos en Logística/Stock más allá de lo existente.

## CONTRACT

Precondiciones:

- Orden en `ORDERED | PARTIAL` (sin cambios de 002/008).
- `qty_accepted + qty_rejected == qty_received` por línea.

Postcondiciones:

- Receipt persiste `qty_accepted`, `qty_rejected`, `difference_type`,
  `incidence_notes` fieles al envío.
- Sin esos campos: comportamiento idéntico al actual (aceptadas=recibidas).
- `commercial-close` es idempotente y auditable (sello usuario/fecha).

## INVARIANTS

```yaml
invariants:
  - "aceptadas + rechazadas == recibidas SIEMPRE (invariante fuerte)."
  - "El vínculo receipt↔despacho (008) no se toca."
  - "Cero escrituras lg_* / stock ledger nuevas (§32/§33 intactas)."
  - "Suite previa compras sigue verde; tsc limpio."
  - "Recepciones históricas sin campos se leen como aceptadas=recibidas."
```

## VERIFICATION

- `test_receive_accept_reject_sums_to_received` → 422 si no cuadra.
- `test_receive_defaults_accepted_equals_received` → retrocompatibilidad.
- `test_receive_derives_difference_type_faltante_sobrante_dano`.
- `test_commercial_close_idempotent_stamps_user`.
- Suite compras previa verde; `tsc --noEmit` limpio.

Manual: recepcionar orden → poner 2 rechazadas de 10 → badge DANO; detalle
de orden muestra aceptadas=8.

## ROLLBACK

Reversible: revertir commit; migración 009 `downgrade` elimina las 6 columnas
(solo se pierde distinción aceptada/rechazada, no los receipts).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/migrations/009_receipt_commercial_close.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/orders.py
    - plugins/commerce/purchase/backend/services/receipts.py
    - plugins/commerce/purchase/backend/routers/receipts.py
    - plugins/commerce/purchase/backend/routers/orders.py
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
    - plugins/commerce/purchase/frontend/api.ts
    - plugins/commerce/purchase/frontend/types.ts
    - apps/api/tests/test_compras_receipt_commercial.py
  prohibited:
    - plugins/logistics/**
    - plugins/stock/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.receipts.comercial
  indirect:
    - compras.ui.recepcion
  must_not_affect:
    - custodia/despachos (005/007/008)
    - stock ledger
    - lifecycle de órdenes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-002 # receipts + lifecycle
    - COMPRAS-008 # vínculo receipt↔despacho
  must_compose_with:
    - COMPRAS-010 # costo real usará qty_accepted
    - COMPRAS-011 # tres vías usará aceptadas vs facturado
    - COMPRAS-012 # reclamaciones consumirán difference_type
  systemic_invariants:
    - "Toda recepción distingue aceptado de rechazado."
  composition_checks:
    - Recepción con rechazo → difference_type presente → visible en detalle.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: distinción comercial vive en receipts existente
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - services/receipts.py
```

## Traceability

- Requirement: VISION §17 (aceptadas/rechazadas), §18 (diferencias),
  §42 flujo principal. Decisión de sesión 2026-08-26 (milestone cierre
  procure-to-pay hasta COMPRAS-011).
- Commit: pendiente (al ejecutar).
- Deployment: migración 009 en runtime del plugin commerce.

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
