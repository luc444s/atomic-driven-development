# A.SPEC COMPRAS-012 — Reclamaciones al proveedor: registro + seguimiento a resolución

> `risk: low` — Derivación según SPECIFICATION §4.1, solo señales del propio
> A.SPEC: reversible físicamente (migración aditiva, downgrade probable),
> sin dinero, sin stock físico, sin auth/seguridad ni `lg_*`, sin migración
> destructiva, blast radius acotado al plugin compra. Ninguna señal de
> subvaloración posible (todo lo explícito apunta a `low`); `low` declarado,
> SPEC-REVIEWER opcional por Trigger contract.

## WHY

VISION §24/§23 detectan diferencias (conciliación tres vías MATCH/MISMATCH)
y §25 exige poder **reclamar** al proveedor: hoy no existe ningún objeto
"reclamación" en Compras. Un MISMATCH o una recepción con `difference_type`
(009) quedan observados pero sin tramite formal: nadie puede registrar qué se
reclama, con qué motivo, ni seguirlo hasta su resolución. Eso bloquea el
seguimiento operativo de proveedores y deja huérfana la futura derivación
desde conciliación (§42 próximo paso) y la evaluación de proveedores (§30).

## WHAT

Una verdad nueva: **sobre cualquier orden del tenant puede registrarse una
reclamación al proveedor con motivo de lista cerrada (§25), y cada
reclamación puede seguirse hasta su resolución mediante estados y timeline
auditable.**

### Modelo

- `com_supplier_claims`:
  - `id` String(36) PK uuid, `tenant_id` FK `tenants.id`,
    `order_id` FK `com_purchase_orders.id` (requerido),
    `supplier_id` FK `com_suppliers.id` (= supplier de la orden, server-side),
  - vínculos opcionales con valor presente hoy: `receipt_id`
    FK `com_purchase_receipts.id` | NULL (motivo sobre diferencia registrada
    por 009), `invoice_id` FK `com_supplier_invoices.id` | NULL (motivo
    precio/documento sobre factura registrada por 011);
  - `reason: String(40)` — lista cerrada §25:
    `FALTANTE | PRODUCTO_INCORRECTO | MALA_CALIDAD | CILINDRO_DANADO |
    SERVICIO_INCOMPLETO | SERVICIO_DEFECTUOSO | PRECIO_INCORRECTO |
    DOCUMENTO_INCORRECTO | DEMORA | PERDIDA_ENVASE | DANO_EN_CUSTODIA`;
  - `description: Text`, `status: String(20)`
    (`ABIERTA | EN_GESTION | RESUELTA | ANULADA`, default `ABIERTA`),
  - `opened_by` FK users.id / `opened_at`, `resolved_by` | NULL /
    `resolved_at` | NULL, `resolution_notes: Text | NULL`.
- `com_supplier_claim_events` (patrón `ComPurchaseOrderEvent`, migration 002):
  - `id`, `tenant_id`, `claim_id` FK cascade index, `from_status` | NULL,
    `to_status: String(20)`, `reason: Text | NULL`, `user_id` FK users.id | NULL,
    `created_at`.

### Ciclo de vida

- `Alta` (`create`) estampa un evento de apertura con `from_status: NULL`
  (quién, cuándo) — timeline inicia con 1 evento.
- `ABIERTA → EN_GESTION` (`start`; evento estampado).
- `ABIERTA|EN_GESTION → RESUELTA` (`resolve`; `resolution_notes` requerido).
- `ABIERTA|EN_GESTION → ANULADA` (`annul`; motivo requerido en el evento).
- `RESUELTA | ANULADA` son terminales e inmutables.
- Transición inválida → `409 Conflict`. Repetición del mismo estado destino →
  `200` idempotente sin evento duplicado (no-repetición segura).

### Endpoints

- `POST /orders/{order_id}/claims` — alta (REQUIRE_ORDER_MANAGE).
- `GET /orders/{order_id}/claims` — lista con estado.
- `GET /orders/{order_id}/claims/{claim_id}` — detalle con timeline de eventos.
- `POST /orders/{order_id}/claims/{claim_id}/start|resolve|annul` — transiciones
  con evento auditable (REQUIRE_ORDER_MANAGE).

### Frontend

- `PurchaseOrdersPage.tsx`: panel/pestaña "Reclamaciones": alta (selector del
  motivo cerrado + descripción + vínculo opcional recepción/factura), lista con
  badge de estado, acciones Iniciar/Resolver/Anular y vista de timeline.
- `types.ts` / `api.ts` con `SupplierClaim*`.

## SCOPE

- `plugins/commerce/migrations/012_supplier_claims.py`: `revision="0012"`,
  upgrade/downgrade estilo familia (create/drop checkfirst) — 2 tablas + índices.
- `plugins/commerce/purchase/backend/models.py`: `ComSupplierClaim`,
  `ComSupplierClaimEvent`.
- `plugins/commerce/purchase/backend/schemas/claims.py` (+ export en
  `schemas/__init__.py`): `SupplierClaimCreate`, `SupplierClaimRead`,
  `SupplierClaimEventRead`, payloads de transición.
- `plugins/commerce/purchase/backend/services/claims.py`:
  `create_claim`, `list_claims`, `get_claim`, `start_claim`, `resolve_claim`,
  `annul_claim` (máquina de estados + eventos).
- `plugins/commerce/purchase/backend/routers/claims.py` (+ inclusión en
  `routers/__init__.py`): endpoints listados.
- Frontend: `PurchaseOrdersPage.tsx`, `types.ts`, `api.ts`.
- Tests: `apps/api/tests/test_compras_claims.py`.

## OUT OF SCOPE

- **Derivación/sugerencia automática de reclamaciones desde el MISMATCH de la
  conciliación tres vías** (consumo de `GET /orders/{id}/reconciliation`) —
  verdad separada con precondiciones y verificación propias; próxima A.SPEC
  del roadmap (§42 próximo paso). Aquí SOLO queda garantizado el registro
  manual y los vínculos opcionales ya útiles hoy.
- Devoluciones de mercadería (§26) y su vínculo a reclamaciones — futura.
- Gating del cierre de orden por reclamaciones abiertas (§28 refinamiento):
  el close actual (COMPRAS-002) queda intacto.
- Evaluación de proveedores (§30), SLA/plazos, notificaciones/email.
- Catálogo abierto de motivos: la lista es la de §25, cerrada.
- Escrituras en plugins/stock, plugins/logistics o core stock ledger.

## CONTRACT

Precondiciones:

- Orden existe en el mismo tenant (404 si no / cross-tenant).
- `reason` ∈ lista cerrada §25 (422 si no).
- `receipt_id` / `invoice_id`, si presentes, pertenecen a la misma orden (400
  si referencian objetos ajenos); `supplier_id` lo fija el servidor =
  supplier de la orden.

Postcondiciones:

- Reclamación persistida en `ABIERTA` con `opened_at/by` fieles y su evento de
  apertura estampado.
- Toda transición genera exactamente un evento en
  `com_supplier_claim_events` (quién, cuándo, from→to, motivo si aplica); el
  alta genera además el evento de apertura (`from_status` NULL);
  repetición idempotente NO duplica eventos.
- Estados terminales `RESUELTA | ANULADA` jamás mutan después.
- La creación/transición de reclamaciones no altera la orden, sus receipts,
  facturas ni la salida de `/reconciliation`.

## INVARIANTS

```yaml
invariants:
  - "Toda lectura/escritura está filtrada por tenant_id; acceso cross-tenant 404."
  - "Recepción comercial (009) intocada: qty_accepted/rejected, difference_type y commercial-close sin cambios (suite test_compras_receipt_commercial verde)."
  - "Facturas y conciliación (011) intocadas: crear/transicionar reclamaciones no muta facturas ni cambia el output de GET /orders/{id}/reconciliation para los mismos datos (conciliación sigue siendo solo lectura)."
  - "Despachos/custodia (005/007/008) intocados (suite test_compras_dispatch verde)."
  - "Ciclo de vida de órdenes (002) intocado: las reclamaciones no cambian order.status ni estampan com_purchase_order_events; close sigue operando igual aunque haya reclamaciones abiertas."
  - "Cero escrituras nuevas en lg_* y core stock ledger desde este feature."
  - "Permisos existentes reutilizados (REQUIRE_ORDER_READ/MANAGE): ningún permiso nuevo ni cambio en kernel auth."
  - "Suite compras previa completa verde; tsc --noEmit limpio."
```

## VERIFICATION

Tests nuevos (`pytest apps/api/tests/test_compras_claims.py -q`):

- `test_claim_created_with_closed_reason_defaults_open`.
- `test_claim_rejects_reason_outside_list_422`.
- `test_claim_link_must_belong_to_same_order_400`.
- `test_claim_tenant_isolated_404`.
- `test_claim_start_transitions_with_event`.
- `test_claim_resolve_requires_resolution_notes_422`.
- `test_claim_resolved_is_terminal_409`.
- `test_claim_annul_records_reason_event`.
- `test_repeat_transition_idempotent_no_duplicate_event`.
- `test_order_close_unaffected_by_open_claims` (invariante lifecycle 002).

Regresión (composición): `pytest apps/api/tests/test_compras_plugin.py
apps/api/tests/test_compras_dispatch.py
apps/api/tests/test_compras_receipt_commercial.py
apps/api/tests/test_compras_receipt_cost.py
apps/api/tests/test_compras_invoice_reconciliation.py -q` — verde.
`tsc --noEmit` limpio en frontend commerce.

Prueba de reversibilidad (SPECIFICATION §9.1 — presence no es execution):
invocar el `downgrade(db)` del módulo de la migración 012 **directamente**
(importando `plugins/commerce/migrations/012_supplier_claims.py` contra una
base de prueba migrada), o bien el runner con `target_revision="0011"`
(anterior). NOTA: `downgrade("0012")` sobre una base ya en `"0012"` es NO-OP
por diseño del runner (`migrations.py:105`, target==current early-return) —
no sirve como prueba. Registrar resultado con aserción negativa:
`com_supplier_claims` y `com_supplier_claim_events` AUSENTES (inspección de
catálogo), resto de tablas compras intacto.

Prueba explícita de invariants lg_*/stock y auth (§7.1):

- `rg -n "lg_|stock_" plugins/commerce/purchase/backend/services/claims.py
  plugins/commerce/purchase/backend/routers/claims.py` → SIN coincidencias
  (cero escrituras stock/lg_* desde este feature).
- `rg -o "REQUIRE_[A-Z_]+" plugins/commerce/purchase/backend/routers | sort -u`
  antes vs después → mismo conjunto (REQUIRE_ORDER_READ/MANAGE reutilizados;
  ningún permiso nuevo; kernel auth sin tocar).

Manual: registrar reclamación CILINDRO_DANADO vinculada a receipt con
DANO (009) → Iniciar → Resolver con notas → timeline visible con 3 eventos;
Resolver de nuevo → 200 sin evento extra; Anular tras resolver → 409.

## ROLLBACK

Reversible: revertir commit; ejecutar `downgrade("0012")` elimina las 2 tablas
(se pierde historial de reclamaciones, no órdenes, receipts ni facturas).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/migrations/012_supplier_claims.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/claims.py
    - plugins/commerce/purchase/backend/schemas/__init__.py
    - plugins/commerce/purchase/backend/services/claims.py
    - plugins/commerce/purchase/backend/routers/claims.py
    - plugins/commerce/purchase/backend/routers/__init__.py
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
    - plugins/commerce/purchase/frontend/types.ts
    - plugins/commerce/purchase/frontend/api.ts
    - apps/api/tests/test_compras_claims.py
  prohibited:
    - plugins/logistics/**
    - plugins/stock/**
    - plugins/finanzas/**   # §35 futura
    - systutor kernel (auth/tenancy)
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.claims.crud
    - compras.claims.lifecycle
  indirect:
    - compras.ui.reclamaciones # pestaña nueva en PurchaseOrdersPage
  must_not_affect:
    - recepción comercial (009)
    - facturas + conciliación tres vías (011)
    - custodia/despachos (005/007/008)
    - lifecycle y cierre de órdenes (002)
    - stock ledger / logistics lg_*
    - auth y permisos existentes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-002 # órdenes + lifecycle sobre los que se reclama
    - COMPRAS-004 # suppliers (FK + display del proveedor)
  must_compose_with:
    - COMPRAS-009 # receipt_id apunta a recepción con difference_type (vínculo opcional útil hoy)
    - COMPRAS-011 # invoice_id apunta a factura registrada (vínculo opcional útil hoy)
    - siguiente A.SPEC (roadmap §42 próximo paso): derivación de reclamaciones desde MISMATCH de GET /orders/{id}/reconciliation
    - futura §26 devoluciones ligará claim↔devolución
  systemic_invariants:
    - "Toda reclamación vive en dominio compras, asociada a orden del mismo tenant, con historial completo preservado."
  composition_checks:
    - "Flujo manual end-to-end: reclamación sobre receipt con diferencia (009) → iniciar → resolver con notas → timeline de 3 eventos visible."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: registro+lifecycle de reclamaciones cohesivo en services/claims.py
  entrypoints_must_stay_thin: true   # routers/claims.py solo delega en service
  review_threshold_lines: 400        # models.py (~351) lo cruza con ~+45 líneas:
  extraction_threshold_lines: 600    #   revisión justificada — colocalo según
                                     # convención de familia; models.py conserva
                                     # UNA razón de cambio (tablas del dominio
                                     # compras). Extracción (models/claims.py) solo
                                     # al superar 600 líneas.
  preferred_new_logic_locations:
    - services/claims.py
    - routers/claims.py
    - schemas/claims.py
```

## Traceability

- Requirement: VISION §25 (reclamaciones, motivos cerrados, resolución);
  contexto composicional §24 (MISMATCH futuro) y §42. Baseline VISION-001,
  tracker §25 = ❌ hoy.
- owner: Product Owner módulo compras (equipo SYSTUTOR OSS)
- approver: mantenedor humano responsable del squash/integración a main
  (escalación de REVISE/SPLIT/REJECT según §10.2)
- Commit: (INTEGRATE — SHA literal al integrar, §13.5)
- Deployment: migración 0012 en runtime del plugin commerce

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
