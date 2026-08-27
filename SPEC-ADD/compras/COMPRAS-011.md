# A.SPEC COMPRAS-011 — Factura de proveedor + conciliación tres vías

## WHY

Con 009 (aceptadas/rechazadas) y 010 (costo real) ya sabemos qué entró y a
qué costo. Pero el ciclo procure-to-pay no cierra hasta contrastar la
**factura del proveedor** contra lo ordenado y lo recibido (VISION §23/§24).
Sin factura no hay conciliación tres vías, no hay reclamaciones fundadas
(§25) ni base para Finanzas (§35). Hoy Compras no registra facturas.

## WHAT

Dos verdades nuevas:

1. **Factura de proveedor** registrada y vinculada a la orden.
2. **Conciliación tres vías** orden ↔ recepción(aceptadas) ↔ factura,
   con veredicto `MATCH` / `MISMATCH` por ítem y por total.

### Modelo

- `com_supplier_invoices`:
  - `id`, `tenant_id`, `supplier_id` FK, `order_id` FK (`com_purchase_orders`),
    `invoice_number: String(60)`, `invoice_date: Date`, `currency: String(3)`,
    `subtotal`, `tax`, `total: Numeric(19,4)`, `status`
    (`REGISTRADA | CONCILIADA | ANULADA`).
- `com_supplier_invoice_lines`:
  - `id`, `invoice_id` FK, `order_item_id` FK | NULL, `product_id` FK | NULL,
    `qty`, `unit_price`, `line_total`, `notes`.

### Endpoints

- `POST /orders/{id}/invoices` → crea factura + líneas (valida tenant, orden,
  supplier coincide con orden).
- `GET /orders/{id}/invoices` → lista.
- `GET /orders/{id}/reconciliation` → tres vías:
  ```json
  {
    "by_item": [
      {
        "order_item_id": "...",
        "ordered_qty": 10,
        "accepted_qty": 8,
        "invoiced_qty": 8,
        "ordered_cost": 100.0,
        "real_cost": 118.75,      // de COMPRAS-010
        "invoiced_cost": 120.0,
        "status": "MATCH"         // o MISMATCH + reason
      }
    ],
    "totals": {
      "ordered": 100.0, "real": 118.75, "invoiced": 120.0,
      "status": "MISMATCH", "reasons": ["invoiced > real by 1.25"]
    }
    "invoice_status": "CONCILIADA"  // si todo MATCH
  }
  ```
- `POST /invoices/{id}/cancel` → `ANULADA` (solo si no usada en Finanzas).

### Conciliación

- `invoiced_qty` por ítem = Σ `qty` de líneas de factura que referencian el
  `order_item_id`.
- `MATCH` por ítem si `invoiced_qty == accepted_qty` y
  `abs(invoiced_cost - real_cost) <= tolerance` (tolerance configurable, def
  0.01 por unidad o 1% del total).
- `invoice_status = CONCILIADA` solo si todos los ítems `MATCH`.
- Si hay líneas de factura sin `order_item_id` (cargos sueltos), se comparan
  contra `extra_total` de 010 por `cost_type` cuando aplique.

### Frontend

- `PurchaseOrdersPage.tsx`: pestaña "Facturas" (alta + lista) y botón
  "Conciliar" que abre panel tres vías con diferencias resaltadas.
- `types.ts` / `api.ts` con `SupplierInvoice*`.

### Plantilla mínima genérica (factura)

Campos mínimos que debe llevar toda factura de proveedor (sin formato
regulatorio específico de país):

```
--------------------------------------------
 FACTURA DE PROVEEDOR            [borrador]
--------------------------------------------
 Emisor:      {supplier_name}  ({supplier_tax_id})
 Cliente:     {tenant_name}    ({tenant_tax_id})
 Folio:       {invoice_number}
 Fecha:       {invoice_date}
 Orden ref:   {order_code}
--------------------------------------------
 Ítem                Cant  P.Unit   Total
 ------------------------------------------
 {product_sku} {name} {qty}  {price} {line_total}
 ...
--------------------------------------------
 Subtotal:   {subtotal}
 Impuesto:   {tax}
 TOTAL:      {total} {currency}
--------------------------------------------
 Estado: {status}
 Conciliación: {MATCH|MISMATCH} ({reasons})
--------------------------------------------
```

Esta plantilla es la fuente de la UI de impresión/PDF mínima; los números se
leen directo de `com_supplier_invoices` + `com_supplier_invoice_lines`. No
incluye sellos fiscales, timbres ni layouts por país (fuera de alcance).

## SCOPE

- `plugins/commerce/migrations/011_supplier_invoice.py`: 2 tablas + índices.
- `plugins/commerce/purchase/backend/models.py`: `ComSupplierInvoice`,
  `ComSupplierInvoiceLine`.
- `plugins/commerce/purchase/backend/schemas/orders.py` (o `invoices.py`):
  `SupplierInvoiceCreate`, `SupplierInvoiceLineCreate`, `ReconciliationRead`,
  `SupplierInvoiceRead`.
- `plugins/commerce/purchase/backend/services/invoices.py`:
  `create_supplier_invoice`, `reconcile_order` (tres vías),
  `cancel_invoice`.
- `plugins/commerce/purchase/backend/routers/invoices.py`:
  `POST/GET /orders/{id}/invoices`, `GET /orders/{id}/reconciliation`,
  `POST /invoices/{id}/cancel`.
- Frontend: `PurchaseOrdersPage.tsx` (tab Facturas + Conciliar),
  `types.ts`, `api.ts`.
- Tests: `apps/api/tests/test_compras_invoice_reconciliation.py`.

## OUT OF SCOPE

- Asiento contable en Finanzas (§35) — futura.
- Reclamaciones derivadas de mismatch (§25) — COMPRAS-012.
- Layouts fiscales por país / sellos / timbres.
- Conciliación física serial (§16).
- Integración escritura Logística (§32 escritura) — futura.

## CONTRACT

Precondiciones:

- Orden existe, mismo tenant, `supplier_id` de factura == de orden.
- Líneas de factura con `order_item_id` referencian ítems de esa orden.

Postcondiciones:

- Factura persistida con líneas y totales coherentes.
- `/reconciliation` devuelve veredicto reproducible (idempotente).
- `invoice_status = CONCILIADA` solo si todos los ítems `MATCH`.
- Sin factura: endpoint de reconciliación devuelve `MISMATCH` por
  "sin factura" (no excepción).

## INVARIANTS

```yaml
invariants:
  - "Conciliación es de solo lectura: no muta órden ni recepción."
  - "invoiced_qty NUNCA excede lo aceptado sin marcar MISMATCH."
  - "Factura anulada no cuenta para CONCILIADA."
  - "Cero escrituras lg_* / stock (§32/§33 intactas)."
  - "Suite compras previa verde; tsc limpio."
  - "Tolerance de conciliación configurable, default 1% o 0.01/u."
```

## VERIFICATION

- `test_invoice_created_links_order`.
- `test_reconciliation_match_when_invoiced_equals_accepted_real`.
- `test_reconciliation_mismatch_when_invoiced_exceeds_accepted`.
- `test_reconciliation_no_invoice_is_mismatch_not_error`.
- `test_invoice_cancel_excluded_from_reconciliation`.
- Suite compras previa verde; `tsc --noEmit` limpio.

Manual: orden 10 → recibir 8 aceptadas → facturar 8 → Conciliar = MATCH;
facturar 9 → MISMATCH resaltado.

## ROLLBACK

Reversible: revertir commit; migración 011 `downgrade` elimina las 2 tablas
(se pierde registro de facturas, no órdenes ni recepciones).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/migrations/011_supplier_invoice.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/orders.py
    - plugins/commerce/purchase/backend/services/invoices.py
    - plugins/commerce/purchase/backend/routers/invoices.py
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
    - plugins/commerce/purchase/frontend/types.ts
    - plugins/commerce/purchase/frontend/api.ts
    - apps/api/tests/test_compras_invoice_reconciliation.py
  prohibited:
    - plugins/logistics/**
    - plugins/stock/**
    - plugins/finanzas/**   # §35 futura
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.invoices.crud
    - compras.reconciliation.three_way
  indirect:
    - compras.ui.ordenes # tab Facturas + Conciliar
  must_not_affect:
    - recepción/aceptadas (009)
    - costo real (010)
    - custodia/despachos
    - stock ledger
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-009 # accepted_qty para conciliar
    - COMPRAS-010 # real_cost para contrastar
  must_compose_with:
    - COMPRAS-012 # reclamaciones consumirán MISMATCH
    - futura §35 Finanzas consumirá factura CONCILIADA
  systemic_invariants:
    - "Toda orden con factura es conciliable orden↔recibido↔facturado."
  composition_checks:
    - Flujo cierra: orden → recibir(aceptadas) → costo real → facturar →
      reconciliar MATCH → procure-to-pay completo.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: factura + conciliación en dominio compras, sin tocar otros
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - services/invoices.py
```

## Traceability

- Requirement: VISION §23 (factura), §24 (tres vías), §42 cierre flujo
  principal. Milestone procure-to-pay hasta COMPRAS-011 (sesión 2026-08-26).
- Commit: pendiente (al ejecutar).
- Deployment: migración 011 en runtime del plugin commerce.

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
