# A.SPEC COMPRAS-013 — Derivación de reclamaciones desde MISMATCH de conciliación

> `mode: normal` (§4.2) — superficie de 12 archivos > 3, mapeo
> MISMATCH→motivo es juicio de dominio y VERIFICATION incluye paso manual:
> no cumple condiciones del Modo A (revisión SPEC-REVIEWER aplicada).
> `risk: low` — Derivación según SPECIFICATION §4.1, solo señales del propio
> A.SPEC: migración aditiva (ADD COLUMN con default, downgrade ejecutable),
> sin dinero (lee la conciliación, no muta montos), sin stock físico, sin
> auth/seguridad ni escrituras `lg_*`, sin migración destructiva, blast radius
> acotado a reclamaciones + panel Conciliar. Ninguna señal de subvaloración.

## WHY

La conciliación tres vías (COMPRAS-011) detecta MISMATCH por ítem y la
reclamación manual (COMPRAS-012) ya trámite con motivo cerrado y timeline.
Hoy un MISMATCH (`invoiced_qty != accepted_qty`, costo facturado ≠ real)
queda observado y el operador debe transcribirlo a mano en una reclamación:
pasos manuales que se omiten, motivos mal elegidos y cero idempotencia
(reclamos duplicados al releer la conciliación). VISION §25 + §42 exigen que
las diferencias lleguen a tramite formal sin corregirse silenciosamente.

## WHAT

Una verdad nueva: **cualquier MISMATCH del output de conciliación de
COMPRAS-011 puede derivarse a reclamaciones al proveedor de forma
idempotente — re-ejecutar la derivación sobre el mismo estado nunca duplica
reclamaciones por el mismo (orden, ítem, motivo, factura).**

### Derivación (server-side, reutiliza COMPRAS-011)

- El servicio llama internamente a `invoices_service.reconcile_order`
  (misma fuente de verdad; NO reimplementa la conciliación).
- Por cada ítem con `status = "MISMATCH"`:
  - razón de cantidad (`facturado X != aceptado Y`) → reclamación motivo
    `FALTANTE`;
  - razón de costo (`costo facturado != real`) → reclamación motivo
    `PRECIO_INCORRECTO`.
- MISMATCH por "sin factura" NO deriva reclamación (no hay documento que
  reclamar aún) — se omite explícitamente.
- `claim.invoice_id` = factura registrada del orden si existe exactamente
  una no anulada; `NULL` si ninguna o múltiples. `receipt_id = NULL` (la
  conciliación es de orden/ítem, no de recepción).
- `source = "DERIVED"` y descripción autogenerada citando el mismatch
  (`reason` literal del output de 011).
- Idempotencia: existe ya una reclamación con
  `source = "DERIVED"` para la clave
  `(order_id, order_item_id, reason, invoice_id)` (cualquier estado, incluida
  ANULADA) → NO se crea otra para ese ítem. `invoice_id` NULL en la clave
  casa solo con NULL (factura ausente/múltiple). Claims `MANUAL` no bloquean
  la derivación.

### Modelo

- `com_supplier_claims` (012) gana columna:
  - `source: String(20) NOT NULL default 'MANUAL'`
    (`MANUAL | DERIVED`).

### Endpoint

- `POST /orders/{order_id}/claims/derive` (REQUIRE_ORDER_MANAGE) →
  `{"created": [SupplierClaimRead...], "skipped": int}` — `201` si creó
  alguna, `200` si ninguna.

### Frontend

- Panel "Conciliar" (`PurchaseOrdersPage.tsx`): botón "Derivar
  reclamaciones" que llama al endpoint y lista creadas/omitidas.
  Lógica encapsulada en componente nuevo `components/ClaimDerivationPanel.tsx`
  (edición de la página mínima: import + render).

## SCOPE

- `plugins/commerce/migrations/013_claim_derivation_source.py`
  (`revision = "0013"`): `ALTER TABLE com_supplier_claims ADD COLUMN source`
  + downgrade `DROP COLUMN`.
- `plugins/commerce/purchase/backend/models.py`: columna `source` en
  `ComSupplierClaim`.
- `plugins/commerce/purchase/backend/schemas/claims.py`
  (+ export en `schemas/__init__.py`): `source` en `SupplierClaimRead`,
  `ClaimDerivationResult`.
- `plugins/commerce/purchase/backend/services/claims.py`:
  `derive_claims_from_reconciliation` (consume `reconcile_order`, aplica
  mapeo y dedup, estampa claims).
- `plugins/commerce/purchase/backend/routers/claims.py`: endpoint derive.
- Frontend: `components/ClaimDerivationPanel.tsx` (nuevo),
  `pages/PurchaseOrdersPage.tsx` (botón en panel Conciliar), `types.ts`,
  `api.ts`.
- Tests: `apps/api/tests/test_compras_claim_derivation.py`.

## OUT OF SCOPE

- Modificar la lógica o el output de la conciliación (011 queda intacto).
- Derivación desde `difference_type` de recepciones (009) — solo MISMATCH
  de conciliación.
- Envío/notificación de reclamaciones al proveedor (email/SLA).
- Cualquier escritura en plugins/stock, plugins/logistics o core ledger.
- Extracción de `PurchaseOrdersPage.tsx` (solo se señaliza; ver Structural
  Constraints).

## CONTRACT

Precondiciones:

- Orden existe en el mismo tenant (404 si no / cross-tenant).
- La conciliación se calcula on-the-fly con los datos vigentes (facturas no
  anuladas, aceptadas de 009, costo real de 010).

Postcondiciones:

- Cada ítem MISMATCH mapea a 0..2 reclamaciones `DERIVED` (0..1 por motivo:
  FALTANTE por diferencia de cantidad y/o PRECIO_INCORRECTO por diferencia
  de costo) con la
  lista cerrada §25 y `source = "DERIVED"`.
- Re-ejecución con los mismos datos → `skipped` sin filas nuevas (0 duplicados
  por `(order_id, order_item_id, reason, invoice_id)` derivadas).
- El output de `GET /orders/{id}/reconciliation` NO cambia por derivar.
- Claims manuales existentes y su timeline quedan intactos.

## INVARIANTS

```yaml
invariants:
  - "Conciliación (011) intocada: derivar reclamaciones no muta facturas, receipts ni cambia el output de reconcile_order para los mismos datos."
  - "Reclamaciones (012) intocadas: lifecycle, motivos cerrados y timeline operan igual; claims pre-existentes conservan source='MANUAL' (backfill)."
  - "Recepción comercial (009) y costo real (010) intocados: qty_accepted/rejected, difference_type, commercial-close y cost_lines sin cambios (suites test_compras_receipt_commercial + test_compras_receipt_cost verdes)."
  - "Custodia/despachos (005/007/008) intocados (suite test_compras_dispatch verde)."
  - "Toda lectura/escritura filtrada por tenant_id; cross-tenant 404."
  - "Cero escrituras lg_* / core stock ledger desde este feature."
  - "Permisos existentes reutilizados (REQUIRE_ORDER_READ/MANAGE): ningún permiso nuevo."
  - "Migración reversible: ADD COLUMN con downgrade DROP COLUMN demostrado ejecutado."
  - "Suite compras previa completa verde; tsc --noEmit limpio."
```

## VERIFICATION

Tests nuevos (`pytest apps/api/tests/test_compras_claim_derivation.py -q`):

- `test_derive_creates_faltante_claim_for_qty_mismatch`.
- `test_derive_creates_precio_incorrecto_claim_for_cost_mismatch`.
- `test_derive_skips_sin_factura_mismatch`.
- `test_derive_is_idempotent_no_duplicates_on_rerun`.
- `test_derive_no_duplicates_even_after_annul`.
- `test_manual_claim_does_not_block_derivation`.
- `test_derived_claim_has_source_derived`.
- `test_derive_no_mismatch_creates_nothing`.
- `test_derive_tenant_isolated_404`.
- `test_reconciliation_output_unchanged_after_derive`.

Regresión (composición): `pytest apps/api/tests/test_compras_plugin.py
apps/api/tests/test_compras_dispatch.py
apps/api/tests/test_compras_receipt_commercial.py
apps/api/tests/test_compras_receipt_cost.py
apps/api/tests/test_compras_invoice_reconciliation.py
apps/api/tests/test_compras_claims.py -q` — verde. `tsc --noEmit` limpio.

Prueba de reversibilidad (SPECIFICATION §9.1 — presence no es execution):
invocar `downgrade(db)` del módulo `plugins/commerce/migrations/013_claim_derivation_source.py`
directamente contra una base de prueba migrada, o el runner con
`target_revision="0012"` (anterior). NOTA: `downgrade("0013")` sobre una base
ya en `"0013"` es NO-OP por diseño del runner
(`vendor/systutor-core/src/systutor/kernel/plugins/migrations.py:105`) — no
sirve como prueba. Aserción negativa: columna `source` AUSENTE en
`com_supplier_claims` (inspección de catálogo); claims y eventos intactos.

Auditorías explícitas (§7.1):

- `rg -n "lg_|stock_" plugins/commerce/purchase/backend/services/claims.py
  plugins/commerce/purchase/backend/routers/claims.py` → SIN coincidencias.
- `rg -o "REQUIRE_[A-Z_]+" plugins/commerce/purchase/backend/routers | sort -u`
  antes vs después → mismo conjunto.

Manual: orden 10 → recibir 8 → facturar 9 → Conciliar = MISMATCH → "Derivar
reclamaciones" → 1 claim FALTANTE `DERIVED`; repetir botón → `skipped`, sin
fila nueva; timeline del claim muestra apertura normal.

## ROLLBACK

Reversible: revertir commit; ejecutar `downgrade` de la migración 0013
elimina la columna `source` (claims derivadas pierden su marcador; ninguna
reclamación, factura ni recepción se pierde).

## Change Surface

```yaml
change_surface:
  allowed:
    - SPEC-ADD/compras/COMPRAS-013.md   # el contrato viaja con su integración
    - plugins/commerce/migrations/013_claim_derivation_source.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/claims.py
    - plugins/commerce/purchase/backend/schemas/__init__.py
    - plugins/commerce/purchase/backend/services/claims.py
    - plugins/commerce/purchase/backend/routers/claims.py
    - plugins/commerce/purchase/frontend/components/ClaimDerivationPanel.tsx
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
    - plugins/commerce/purchase/frontend/types.ts
    - plugins/commerce/purchase/frontend/api.ts
    - apps/api/tests/test_compras_claim_derivation.py
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
    - compras.claims.derivation
  indirect:
    - compras.ui.conciliar # botón Derivar en panel existente
  must_not_affect:
    - facturas + conciliación tres vías (011)
    - lifecycle y timeline de reclamaciones manuales (012)
    - recepción comercial (009) / costo real (010)
    - custodia/despachos (005/007/008)
    - stock ledger / logistics lg_*
    - auth y permisos existentes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-011   # output de reconciliación consumido (no reimplementado)
    - COMPRAS-012   # modelo claims + motivo cerrado + source
  must_compose_with:
    - COMPRAS-019   # set Versión Base Compras
  systemic_invariants:
    - "Todo MISMATCH de conciliación es derivable a tramite formal sin duplicados."
  composition_checks:
    - "Flujo: facturar de más → Conciliar MISMATCH → Derivar → claim FALTANTE visible; re-derivar → skipped sin duplicado."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: derivación idempotente cohesiva en services/claims.py
  entrypoints_must_stay_thin: true   # routers/claims.py solo delega
  review_threshold_lines: 400       # models.py (~397) cruza 400 con +1 columna:
  extraction_threshold_lines: 600   #   revisión justificada — models.py conserva
                                    # UNA razón de cambio (tablas del dominio
                                    # compras). Señalizada extracción a módulo
                                    # models/ propio: NO en esta ronda.
  preferred_new_logic_locations:
    - services/claims.py
    - frontend/components/ClaimDerivationPanel.tsx   # PurchaseOrdersPage.tsx (~596)
                                                     # en umbral de extracción (600):
                                                     # lógica nueva va a componente
                                                     # propio; edición de la página mínima.
```

## Traceability

- Requirement: VISION §25 (reclamaciones desde diferencias), §42 (cierre del
  flujo principal), tracker §25 "derivación desde MISMATCH futura".
  Roadmap aprobado lote COMPRAS-013..019.
- owner: Product Owner módulo compras (equipo SYSTUTOR OSS)
- approver: mantenedor humano responsable del squash/integración a main
  (escalación de REVISE/SPLIT/REJECT según §10.2)
- Commit:
- Deployment: migración 0013 en runtime del plugin commerce

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
