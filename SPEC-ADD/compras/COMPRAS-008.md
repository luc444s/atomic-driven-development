# A.SPEC COMPRAS-008 — Vínculo recepción ↔ despacho

## WHY

El ciclo de custodia quedó cerrado en COMPRAS-007 por el lado físico
(despacho → retorno por serial → RETORNADO), pero la recepción comercial
(`POST /orders/{id}/receive`, VISION §13) sigue siendo una isla: un receipt no
dice de qué despacho de envases proviene. Sin ese vínculo no se puede responder
"¿esta recepción corresponde a los cilindros que mandé a proveedor?" ni
conciliar ordenado → despachado → retornado → recibido (§42 paso final del
flujo principal).

## WHAT

Una verdad nueva: **toda recepción puede declarar (opcionalmente) el despacho
de envases al que corresponde.**

1. `com_purchase_receipts.dispatch_id`: FK nullable a `com_dispatches`
   (migración 005). `NULL` = recepción pura de mercadería sin envases propios
   (flujo 3.1) — semántica idéntica a la actual.
2. Al recepcionar (`POST /orders/{id}/receive`) se acepta `dispatch_id`
   opcional en el payload. Validaciones: despacho existe, mismo tenant y
   pertenece a la misma orden (`dispatch.order_id == {order_id}`). Rechazo con
   400 si falla cualquiera.
3. El receipt queda expuesto con su `dispatch_id` en la serialización de la
   orden (`receipts[]` de `_serialize_order`).
4. Frontend: el dialog "Recepcionar mercadería" agrega Combobox opcional
   "Despacho asociado" con los despachos de esa orden (solo lectura vía
   `GET /dispatches?order_id=...`).

## SCOPE

- `plugins/commerce/migrations/005_receipt_dispatch_link.py`: +1 columna
  nullable + índice.
- `models.py`: columna en `ComPurchaseReceipt`.
- `schemas/orders.py`: `ReceiveOrderRequest.dispatch_id` opcional.
- `services/receipts.py`: validación de pertenencia (orden + tenant).
- `routers/receipts.py`: pasa el campo al servicio.
- `routers/orders.py`: serializa `dispatch_id` en receipts.
- `services/dispatches.py` + `routers/dispatches.py`: filtro de lectura
  `order_id` en `list_dispatches` (necesario para poblar el Combobox del
  dialog de recepción; solo lectura, sin mutaciones).
- Frontend: `PurchaseOrdersPage.tsx` (Combobox en receive dialog),
  `api.ts` / `types.ts`.
- Tests: nuevos casos en `apps/api/tests/test_compras_dispatch.py`.

## OUT OF SCOPE

- Conciliación tres vías orden–recepción–factura (§24) — requiere facturas.
- Cantidades aceptadas/rechazadas o diferencias/incidencias (§17/§18).
- Conciliar seriales contra el receipt (el retorno ya concilia por serial;
  aquí solo se referencia el despacho comercialmente).
- Escritura de movimientos en Logística/Stock adicionales a los existentes.
- Bloquear recepción si el despacho no está RETORNADO (la mercadería puede
  llegar antes que el retorno físico de algún envase).

## CONTRACT

Precondiciones:

- Orden en `ORDERED|PARTIAL` (sin cambios).
- Si `dispatch_id` presente: despacho existe, mismo tenant,
  `dispatch.order_id == order_id`.

Postcondiciones:

- Receipt creado con `dispatch_id` persistido exactamente como enviado.
- Respuesta de `/receive` incluye el receipt con su vínculo.
- Sin `dispatch_id`: comportamiento bit a bit idéntico al actual.

## INVARIANTS

```yaml
invariants:
  - "El vínculo es OPCIONAL: flujo 3.1 (mercadería sin envase) no cambia."
  - "Un receipt nunca referencia un despacho de otra orden ni otro tenant."
  - "Cero escrituras en modelos lg_* (§32)."
  - "stock_connector.purchase_in sigue disparándose igual (idempotencia intacta)."
  - "Suite previa compras (tests existentes) sigue verde."
```

## VERIFICATION

Nuevos tests:

- `test_receive_links_dispatch_same_order` → receipt guarda dispatch_id.
- `test_receive_rejects_dispatch_of_other_order` → 400.
- `test_receive_without_dispatch_unchanged` → receipt con dispatch_id NULL.

Suite previa compras verde; tsc limpio.

Manual: orden con despacho → Recepcionar eligiendo el despacho → detalle de
orden muestra receipt vinculado; recepción de orden sin despachos funciona
igual que antes.

## ROLLBACK

Reversible: revertir commits; migración 005 con downgrade que elimina la
columna (se pierde solo el vínculo, no receipts).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/migrations/005_receipt_dispatch_link.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/orders.py
    - plugins/commerce/purchase/backend/services/receipts.py
    - plugins/commerce/purchase/backend/services/dispatches.py
    - plugins/commerce/purchase/backend/routers/receipts.py
    - plugins/commerce/purchase/backend/routers/orders.py
    - plugins/commerce/purchase/backend/routers/dispatches.py
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
    - plugins/commerce/purchase/frontend/api.ts
    - plugins/commerce/purchase/frontend/types.ts
    - apps/api/tests/test_compras_dispatch.py
  prohibited:
    - plugins/logistics/**
    - plugins/stock/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.receipts.vinculo_despacho
  indirect:
    - compras.ui.recepcion # nuevo campo opcional
  must_not_affect:
    - custodia/despachos existentes
    - stock ledger
    - lifecycle de órdenes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-002 # receipts + lifecycle orden
    - COMPRAS-005 # despacho por serial
  must_compose_with:
    - futura conciliación tres vías (§24) consumirá este vínculo
  systemic_invariants:
    - "Toda recepción con envases propios puede trazarse a su despacho."
  composition_checks:
    - Ciclo completo: orden → despacho → retorno → recepción vinculada →
      detalle de orden muestra la cadena completa.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: vínculo vive en dominio receipts existente
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - services/receipts.py
```

## Traceability

- Requirement: VISION §13 ("vínculo receipt↔despacho pendiente"), §42 flujo
  principal; decisión de sesión 2026-08-25 tras cerrar COMPRAS-007.
- Commits: (ver git log COMPRAS-008)
- Correcciones durante ejecución: `PurchaseReceiptRead` necesitaba el campo
  `dispatch_id` (model_validate lo strippeaba → KeyError en test);
  `FakeStockConnector` duplicado localmente (los tests no son paquete
  importable); Change Surface ampliado antes de tocar dispatches
  (`list_dispatches?order_id=`) para poblar el Combobox.

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
