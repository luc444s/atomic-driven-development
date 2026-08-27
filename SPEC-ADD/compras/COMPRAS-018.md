# A.SPEC COMPRAS-018 — Devolución de mercadería al proveedor

> `risk: high` — Derivación §4.1: la A.SPEC toca señales hard declaradas en
> sus propias cláusulas (`tenant_id` en toda lectura/escritura y referencia
> a `lg_cylinders`/`lg_*`, aunque sea de solo lectura), además de migración
> aditiva y ciclo de vida con validaciones cruzadas (receipt 009, claim 012,
> serial por despacho). No hay dinero ni stock ledger, pero §4.1 manda `high`
> al tocar tenancy/`lg_*`. `mode: completo` per §4.2.

## WHY

Cuando lo recibido no se acepta (§26), hoy la única salida es anotar
`qty_rejected` en la recepción (009) o retornar envases por despacho (007):
no existe un registro de **devolución de mercadería** con qué se devuelve,
por qué, contra qué recepción de origen, ligado a un reclamo (012) y con
resolución trazable. El tracker §26 marca "devolución de mercadería ❌" y
el roadmap la exige para cerrar la Versión Base.

## WHAT

Una verdad nueva: **sobre una recepción de origen puede registrarse una
devolución de mercadería al proveedor — qué/cuánto/serial si aplica,
motivo, claim opcional de 012 — con ciclo a resolución (CONCRETADA/ANULADA)
y timeline auditable, sin borrar ni alterar la recepción original.**

### Modelo

- `com_merchandise_returns`:
  - `id`, `tenant_id`, `order_id` FK `com_purchase_orders.id`,
    `supplier_id` FK `com_suppliers.id` (= supplier de la orden, server-side),
    `receipt_id` FK `com_purchase_receipts.id` (recepción de origen,
    requerida),
  - `claim_id` FK `com_supplier_claims.id` | NULL (referencia opcional a
    reclamación de 012, misma orden),
  - `return_date: Date`, `notes: Text | NULL`,
  - `status: String(20)` (`REGISTRADA | CONCRETADA | ANULADA`,
    default `REGISTRADA`),
  - `created_by` FK users / `created_at`, `resolved_by` | NULL /
    `resolved_at` | NULL, `resolution_notes: Text | NULL`.
- `com_merchandise_return_lines`:
  - `id`, `tenant_id`, `return_id` FK cascade,
    `order_item_id` FK `com_purchase_items.id` | NULL,
    `product_id` FK `prod_products.id` | NULL,
    `cylinder_id` FK `lg_cylinders.id` | NULL (serial si aplica),
    `serial: String(50) | NULL` (snapshot),
    `qty: Numeric(10,2)`, `unit_cost: Numeric(19,4) | NULL`,
    `notes: Text | NULL`.
- `com_merchandise_return_events` (patrón `ComSupplierClaimEvent`):
  - `id`, `tenant_id`, `return_id` FK cascade, `from_status` | NULL,
    `to_status: String(20)`, `reason: Text | NULL`, `user_id` | NULL,
    `created_at`.

### Ciclo de vida (patrón claims 012)

- Alta (`create`) estampa evento de apertura (`from_status` NULL).
- `REGISTRADA → CONCRETADA` (`complete`; `resolution_notes` requerido —
  acreditación/NC/reposición acordada).
- `REGISTRADA → ANULADA` (`annul`; motivo requerido en el evento).
- `CONCRETADA | ANULADA` terminales e inmutables → `409`. Transición
  inválida → `409`. Repetición del mismo destino → `200` idempotente sin
  evento duplicado.

### Reglas

- Orden inexistente o cross-tenant → 404.
- Receipt/claim/serial cross-tenant → 404 por filtrado `tenant_id`.
- Receipt de origen de otra orden del mismo tenant → 400.
- Claim, si viene, pertenece a la misma orden (400 si es de otra orden del
  mismo tenant — patrón 012).
- Serial/cylinder, si viene, pertenece a un despacho de la misma orden
  (`com_dispatch_cylinders` → `com_dispatches.order_id`; 400 si es de otra
  orden del mismo tenant).
- `qty > 0` por línea (422).
- La devolución NO muta la recepción (qty_accepted/rejected,
  difference_type intocados), NO muta la orden, NO escribe stock ni
  lg_*.

### Endpoints

- `POST /orders/{order_id}/returns` (REQUIRE_ORDER_MANAGE) → 201.
- `GET /orders/{order_id}/returns` (REQUIRE_ORDER_READ).
- `GET /orders/{order_id}/returns/{return_id}` (REQUIRE_ORDER_READ;
  detalle con líneas + timeline).
- `POST /orders/{order_id}/returns/{return_id}/complete|annul`
  (REQUIRE_ORDER_MANAGE) — transiciones con evento.

### Frontend

- Componente nuevo `pages/purchase/MerchandiseReturnDialog.tsx` (alta con
  recepción de origen, líneas qty/serial/claim, resolver/anular con
  motivo, timeline), integrado sobre la estructura post-020:
  `PurchaseOrdersPage.tsx` queda en wiring mínimo (mount/ref) y
  `pages/purchase/OrdersPanel.tsx` agrega el botón de apertura.

## SCOPE

- `plugins/commerce/migrations/018_merchandise_returns.py`
  (`revision = "0018"`): 3 tablas + índices (`order_id`, `receipt_id`,
  `return_id`), estilo familia.
- `plugins/commerce/purchase/backend/returns_models.py`:
  `ComMerchandiseReturn`, `ComMerchandiseReturnLine`,
  `ComMerchandiseReturnEvent` (responsabilidad nueva extraída per §12.4).
- `plugins/commerce/purchase/backend/models.py`: import/re-export mínimo de
  los modelos de devoluciones para registrar metadata y preservar el punto de
  import existente del plugin.
- `plugins/commerce/purchase/backend/schemas/returns.py`
  (+ export `schemas/__init__.py`): payloads y reads del ciclo.
- `plugins/commerce/purchase/backend/services/returns.py`:
  `create_return`, `list_returns`, `get_return`, `complete_return`,
  `annul_return` (máquina de estados + eventos + validaciones cruzadas).
- `plugins/commerce/purchase/backend/routers/returns.py`
  (+ inclusión `routers/__init__.py`): endpoints listados.
- Frontend: `pages/purchase/MerchandiseReturnDialog.tsx` (nuevo),
  `pages/purchase/OrdersPanel.tsx` (botón/acción),
  `pages/PurchaseOrdersPage.tsx` (wiring mínimo), `types.ts`, `api.ts`.
- Tests: `apps/api/tests/test_compras_merchandise_returns.py`.

## OUT OF SCOPE

- Salida de stock / reversión de ledger por la devolución (§33 — Inventario
  informa por connector; futura).
- Nota de crédito / obligación financiera (§35 — futura).
- Retorno de envases por despacho (ya existe en 007; esta spec es
  mercadería).
- Gating del close (002) por devoluciones abiertas.

## CONTRACT

Precondiciones:

- Orden existe en el mismo tenant (404 si no / cross-tenant).
- Receipt/claim/serial, si vienen, existen en el tenant (404 si no /
  cross-tenant).
- Receipt de origen, claim y serial pertenecen a la misma orden cuando
  aplican (400 si refieren objetos de otra orden del mismo tenant).
- `qty > 0` (422).

Postcondiciones:

- Devolución persistida en `REGISTRADA` con evento de apertura; toda
  transición genera exactamente un evento; terminales inmutables;
  repetición idempotente sin duplicar eventos.
- La recepción de origen, sus cantidades comerciales y su conciliación
  quedan EXACTAMENTE iguales (toda la historia conservada — §26/§45).

## INVARIANTS

```yaml
invariants:
  - "Recepción original jamás borrada ni mutada: qty_accepted/rejected, difference_type, commercial-close y costos (009/010) intactos tras crear/transicionar devoluciones (suite test_compras_receipt_commercial verde)."
  - "Conciliación tres vías (011) intocada: devoluciones no mutan facturas ni cambian el output de reconcile_order (suite test_compras_invoice_reconciliation verde)."
  - "Ciclo de órdenes (002) intocado: devoluciones no cambian order.status ni estampan com_purchase_order_events; close sigue operando igual."
  - "Reclamaciones (012/013) intocadas: claim_id es referencia de lectura."
  - "Custodia/despachos (005/007/008) intocados: serial es FK de lectura + snapshot."
  - "Servicios (014), PH (015), historial (016) y conteos físicos (017) intocados (suites correspondientes verdes)."
  - "Cero escrituras lg_* y core stock ledger desde este feature."
  - "Toda lectura/escritura filtrada por tenant_id; cross-tenant 404."
  - "Permisos existentes reutilizados (REQUIRE_ORDER_READ/MANAGE): ningún permiso nuevo."
  - "Migración reversible: downgrade de 3 tablas demostrado ejecutado."
  - "Suite compras previa completa verde; tsc --noEmit limpio."
```

## VERIFICATION

Tests nuevos (`pytest apps/api/tests/test_compras_merchandise_returns.py -q`):

- `test_return_created_linked_to_receipt`.
- `test_return_receipt_must_belong_to_order_400`.
- `test_return_claim_must_belong_to_same_order_400`.
- `test_return_serial_must_belong_to_order_400`.
- `test_return_qty_must_be_positive_422`.
- `test_return_tenant_isolated_404`.
- `test_return_complete_requires_resolution_notes_422`.
- `test_return_terminal_409`.
- `test_repeat_transition_idempotent_no_duplicate_event`.
- `test_return_does_not_mutate_receipt`.

Regresión (composición): `pytest apps/api/tests/test_compras_plugin.py
apps/api/tests/test_compras_dispatch.py
apps/api/tests/test_compras_receipt_commercial.py
apps/api/tests/test_compras_receipt_cost.py
apps/api/tests/test_compras_invoice_reconciliation.py
apps/api/tests/test_compras_claims.py
apps/api/tests/test_compras_claim_derivation.py
apps/api/tests/test_compras_receipt_service_lines.py
apps/api/tests/test_compras_ph_restamp.py
apps/api/tests/test_compras_cylinder_history.py
apps/api/tests/test_compras_physical_reconciliation.py -q` — verde.
`npx tsc --noEmit` limpio ejecutado con `apps/web` como working directory.

Prueba de reversibilidad (SPECIFICATION §9.1 — presence no es execution):
invocar `downgrade(db)` del módulo `plugins/commerce/migrations/018_merchandise_returns.py`
directamente contra una base de prueba migrada, o el runner con
`target_revision="0017"` (anterior). NOTA: `downgrade("0018")` sobre una base
ya en `"0018"` es NO-OP por diseño del runner
(`vendor/systutor-core/src/systutor/kernel/plugins/migrations.py:105`) — no
sirve como prueba. Aserción negativa: las 3 tablas AUSENTES (inspección de
catálogo); receipts, claims y conteos físicos intactos.

Auditorías explícitas (§7.1):

- `rg -n "lg_|stock_" plugins/commerce/purchase/backend/services/returns.py
  plugins/commerce/purchase/backend/routers/returns.py` → solo FK de lectura
  sobre `lg_cylinders` (import); ninguna escritura
  (`rg -n "db.add\\(Logistics|update\\(Logistics|StockConnector" ...`
  → SIN coincidencias).
- `rg -o "REQUIRE_[A-Z_]+" plugins/commerce/purchase/backend/routers | sort -u`
  antes vs después → mismo conjunto.

Manual: recepción con DANO (009) → claim CILINDRO_DANADO (012) → devolución
de 2 unidades con serial, receipt de origen y claim → Resolver
("acreditación NC-123") → timeline 2 eventos; complete de nuevo → 200 sin
evento extra; annul tras concretar → 409; recepción original sin cambios.

## ROLLBACK

Reversible: revertir commit; ejecutar `downgrade` de la migración 0018
elimina las 3 tablas (se pierde el registro de devoluciones; recepciones,
claims y órdenes intactos).

## Change Surface

```yaml
change_surface:
  allowed:
    - SPEC-ADD/compras/COMPRAS-018.md   # el contrato viaja con su integración
    - plugins/commerce/migrations/018_merchandise_returns.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/returns_models.py
    - plugins/commerce/purchase/backend/schemas/returns.py
    - plugins/commerce/purchase/backend/schemas/__init__.py
    - plugins/commerce/purchase/backend/services/returns.py
    - plugins/commerce/purchase/backend/routers/returns.py
    - plugins/commerce/purchase/backend/routers/__init__.py
    - plugins/commerce/purchase/frontend/pages/purchase/MerchandiseReturnDialog.tsx
    - plugins/commerce/purchase/frontend/pages/purchase/OrdersPanel.tsx
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
    - plugins/commerce/purchase/frontend/types.ts
    - plugins/commerce/purchase/frontend/api.ts
    - apps/api/tests/test_compras_merchandise_returns.py
  prohibited:
    - plugins/logistics/**
    - plugins/stock/**
    - plugins/finanzas/**   # §35 futura (acreditación)
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.merchandise_returns.lifecycle
  indirect:
    - compras.ui.reclamaciones # diálogo de devolución desde órdenes
  must_not_affect:
    - recepción comercial (009) / costos (010) / conciliación (011)
    - reclamaciones (012) / derivación (013)
    - servicios (014) / PH (015) / historial (016) / conteos (017)
    - custodia/despachos (005/007/008) y lifecycle de órdenes (002)
    - stock ledger / logistics lg_* (escrituras)
    - permisos existentes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-002   # orden sobre la que se devuelve
    - COMPRAS-004   # suppliers (FK server-side)
    - COMPRAS-005   # despacho/seriales en custodia usados para validar cylinder
    - COMPRAS-009   # recepción de origen (lo no aceptado)
    - COMPRAS-012   # claim opcional validado contra la misma orden
    - COMPRAS-020   # estructura frontend post-extracción donde aterriza la UI
  must_compose_with:
    - COMPRAS-019   # set Versión Base Compras
  systemic_invariants:
    - "La devolución de mercadería compone con receipt/claim/serial existentes sin reintroducir cambios en lg_*, stock ledger ni un god-file en la UI de órdenes."
  composition_checks:
    - "Flujo: recepción con rechazados → claim (012) → devolución ligada → resolver → recepción y claim intactos."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: >-
    ciclo de devoluciones cohesivo en services/returns.py; los modelos nuevos
    viven en returns_models.py y models.py solo re-exporta/registra metadata
  entrypoints_must_stay_thin: true   # routers/returns.py solo delega
  review_threshold_lines: 400       # models.py ya está bajo presión; §12.4
  extraction_threshold_lines: 600   # obliga a extraer esta nueva
                                    # responsabilidad a módulo propio.
  preferred_new_logic_locations:
    - backend/returns_models.py
    - services/returns.py
    - routers/returns.py
    - schemas/returns.py
    - frontend/pages/purchase/MerchandiseReturnDialog.tsx
    - frontend/pages/purchase/OrdersPanel.tsx           # wiring mínimo de la
                                                        # acción en estructura
                                                        # post-020.
```

## Traceability

- Requirement: VISION §26 (devoluciones: qué/por qué/cantidad/serial/
  recepción de origen/proveedor/fecha/responsable/resolución; "la
  devolución no debe borrar la recepción original"), §45. Tracker §26
  "devolución de mercadería ❌". Roadmap aprobado lote 013..019.
- owner: Product Owner módulo compras (equipo SYSTUTOR OSS)
- approver: mantenedor humano responsable del squash/integración a main
- Commit: pendiente (al ejecutar)
- Deployment: migración 0018 en runtime del plugin commerce

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
