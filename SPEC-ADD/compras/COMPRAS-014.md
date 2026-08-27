# A.SPEC COMPRAS-014 — Servicios realizados por serial en recepción

> `risk: normal` — Derivación §4.1: migración aditiva (tabla nueva), sin
> dinero (costo es dato descriptivo opcional, no muta conciliación ni ledger),
> sin escrituras stock/`lg_*` (solo lectura de `lg_cylinders` para validar
> serial), sin auth nuevo; señal de normal: introduce validación cruzada de
> dominio (serial → logistics) y gate sobre el cierre comercial de 009, con
> blast radius en el flujo de recepción. No hay señal de `high`.
> `mode: normal` per §4.2 (ciclo completo).

## WHY

VISION §19 exige registrar qué servicio realizó el proveedor a cada cilindro
en su paso por el proveedor (prueba hidrostática, retimbrado, cambio de
válvula, reparación...). Hoy la recepción (007/008/009) registra cantidades
comerciales y diferencias, pero el servicio quedó en texto libre del
`service_type` del despacho: no hay registro por serial de qué se hizo, ni
costo por servicio, ni base para el historial técnico (016) ni para PH
(015). Sin esto, el paso 8 del flujo §44 (resultado técnico) no existe.

## WHAT

Una verdad nueva: **cada recepción puede registrar líneas de servicio
realizado por serial — qué servicio, a qué cilindro, notas y costo si
aplica — ligadas al receipt de 009/008, con tipo de servicio de lista
cerrada.**

### Modelo

- `com_receipt_service_lines`:
  - `id` String(36) PK uuid, `tenant_id` FK `tenants.id`,
    `receipt_id` FK `com_purchase_receipts.id` (requerido),
  - `cylinder_id` FK `lg_cylinders.id` (requerido — el servicio es por
    serial; referencia de solo lectura al dominio logistics),
  - `serial: String(50)` (snapshot fiel al momento del registro),
  - `service_type: String(30)` — lista cerrada §19/§10:
    `LLENADO | PRUEBA_HIDROSTATICA | RETIMBRADO | INSPECCION | REPARACION |
    MANTENIMIENTO | CAMBIO_VALVULA | PINTURA | ACONDICIONAMIENTO |
    CERTIFICACION`,
  - `cost: Numeric(19,4) | NULL` (si aplica — no alimenta conciliación 011),
  - `notes: Text | NULL`, `created_by` FK `users.id`, `created_at`.

### Reglas

- Serial validado contra `lg_cylinders` del mismo tenant (lectura): serial
  desconocido → 422. Snapshot `serial` guardado en la línea (la historia no
  depende del FK vivo).
- Recepción con cierre comercial ya estampado (`commercial_closed_at`, 009)
  → alta/borrado de líneas → `409` (el servicio se registra con la
  recepción, no después silenciosamente).
- Borrado de línea permitido solo mientras no haya cierre comercial.
- Las líneas NO mutan el receipt: `qty_accepted/rejected`,
  `difference_type`, conciliación y costos (010) quedan intactos.

### Endpoints

- `POST /receipts/{receipt_id}/service-lines` (REQUIRE_ORDER_RECEIVE) → 201.
- `GET /receipts/{receipt_id}/service-lines` (REQUIRE_ORDER_READ).
- `DELETE /receipts/{receipt_id}/service-lines/{line_id}`
  (REQUIRE_ORDER_RECEIVE) → 204; `409` si receipt cerrado comercialmente.

### Frontend

- Componente nuevo `pages/purchase/ReceiptServiceLines.tsx`: editor por
  serial (serial + tipo + costo + notas) listado bajo la recepción,
  integrado en el flujo de recepción de `ReceiptPanel.tsx` (árbol post-020;
  edición del panel mínima: import + ref + render; se abre tras recepcionar).

## SCOPE

- `plugins/commerce/migrations/014_receipt_service_lines.py`
  (`revision = "0014"`): tabla + índices (`receipt_id`, `cylinder_id`),
  estilo familia (create/drop checkfirst).
- `plugins/commerce/purchase/backend/models.py`: `ComReceiptServiceLine`.
- `plugins/commerce/purchase/backend/schemas/service_lines.py`
  (+ export en `schemas/__init__.py`): `ReceiptServiceLineCreate`,
  `ReceiptServiceLineRead`, `SERVICE_TYPES`.
- `plugins/commerce/purchase/backend/services/service_lines.py`:
  `create_service_line`, `list_service_lines`, `delete_service_line`
  (validaciones tenant/serial/cierre).
- `plugins/commerce/purchase/backend/routers/service_lines.py`
  (+ inclusión en `routers/__init__.py`): endpoints listados.
- Frontend: `pages/purchase/ReceiptServiceLines.tsx` (nuevo),
  `pages/purchase/ReceiptPanel.tsx` (integración mínima en flujo de
  recepción, árbol post-020), `types.ts`, `api.ts`.
- Tests: `apps/api/tests/test_compras_receipt_service_lines.py`.

## OUT OF SCOPE

- Datos legales de PH/retimbrado (fecha, vigencia, resultado) — COMPRAS-015.
- Historial técnico consolidado por serial — COMPRAS-016.
- Costo de servicio alimentando conciliación tres vías o costos 010.
- Escrituras en `lg_cylinders` o cualquier modelo logístico (solo lectura
  para resolver el serial); stock ledger intocado.
- Servicios sobre mercadería no serializada (fuera del dominio §19).

## CONTRACT

Precondiciones:

- Receipt existe en el mismo tenant (404 si no / cross-tenant).
- `service_type` ∈ lista cerrada (422 si no); serial existe en
  `lg_cylinders` del tenant (422 si no).
- Receipt sin cierre comercial para alta/borrado (409 si ya cerrado).

Postcondiciones:

- Línea persistida con snapshot de serial, ligada al receipt; sin efecto
  sobre el receipt ni sus costos ni la conciliación.
- `GET /receipts/{id}/service-lines` devuelve las líneas del receipt
  ordenadas por `created_at`.

## INVARIANTS

```yaml
invariants:
  - "Recepción comercial (009) intocada: qty_accepted/rejected, difference_type y commercial-close sin cambios (suite test_compras_receipt_commercial verde); líneas de servicio no mutan el receipt."
  - "Costos (010) y conciliación (011) intocados: cost de la línea es descriptivo, no entra en reconcile_order ni extra_total."
  - "Despachos/custodia (005/007/008) intocados."
  - "Reclamaciones (012) y derivación (013) intocadas: claims, timeline y derive endpoint operan igual."
  - "Lifecycle de órdenes (002) intocado: status/estampado de eventos de orden sin cambios (suite test_compras_plugin verde)."
  - "Cero escrituras lg_* y core stock ledger: lg_cylinders solo SELECT (resolución/validación de serial)."
  - "Toda lectura/escritura filtrada por tenant_id; acceso cross-tenant 404."
  - "Permisos existentes reutilizados (REQUIRE_ORDER_READ/RECEIVE): ningún permiso nuevo ni cambio en kernel auth."
  - "Suite compras previa completa verde; tsc --noEmit limpio."
```

## VERIFICATION

Tests nuevos (`pytest apps/api/tests/test_compras_receipt_service_lines.py -q`):

- `test_service_line_created_linked_to_receipt`.
- `test_service_line_types_closed_list_422`.
- `test_service_line_rejects_unknown_serial_422`.
- `test_service_line_tenant_isolated_404`.
- `test_service_line_rejected_after_commercial_close_409`.
- `test_service_line_delete_before_close_ok`.
- `test_service_lines_do_not_mutate_receipt`.
- `test_service_lines_listed_by_receipt`.

Regresión (composición): `pytest apps/api/tests/test_compras_plugin.py
apps/api/tests/test_compras_dispatch.py
apps/api/tests/test_compras_receipt_commercial.py
apps/api/tests/test_compras_receipt_cost.py
apps/api/tests/test_compras_invoice_reconciliation.py
apps/api/tests/test_compras_claims.py
apps/api/tests/test_compras_claim_derivation.py -q` — verde. `tsc --noEmit` limpio.

Prueba de reversibilidad (SPECIFICATION §9.1 — presence no es execution):
invocar `downgrade(db)` del módulo `plugins/commerce/migrations/014_receipt_service_lines.py`
directamente contra una base de prueba migrada, o el runner con
`target_revision="0013"` (anterior). NOTA: `downgrade("0014")` sobre una base
ya en `"0014"` es NO-OP por diseño del runner
(`vendor/systutor-core/src/systutor/kernel/plugins/migrations.py:105`) — no
sirve como prueba. Aserción negativa: `com_receipt_service_lines` AUSENTE
(inspección de catálogo); receipts, claims y facturas intactos.

Auditorías explícitas (§7.1):

- `rg -n "db.add|db.delete|update\\(" plugins/commerce/purchase/backend/services/service_lines.py`
  → ninguna operación de escritura sobre modelos `lg_*` (solo `db.add` de
  `ComReceiptServiceLine`).
- `rg -o "REQUIRE_[A-Z_]+" plugins/commerce/purchase/backend/routers | sort -u`
  antes vs después → mismo conjunto.

Manual: recepción de 3 seriales → registrar RETIMBRADO + CAMBIO_VALVULA con
costos → listado visible por receipt; cerrar comercial → alta → 409.

## ROLLBACK

Reversible: revertir commit; ejecutar `downgrade` de la migración 0014
elimina la tabla (se pierde registro de líneas de servicio; receipts,
recepción comercial y facturas intactos).

## Change Surface

```yaml
change_surface:
  allowed:
    - SPEC-ADD/compras/COMPRAS-014.md   # el contrato viaja con su integración
    - plugins/commerce/migrations/014_receipt_service_lines.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/service_lines.py
    - plugins/commerce/purchase/backend/schemas/__init__.py
    - plugins/commerce/purchase/backend/services/service_lines.py
    - plugins/commerce/purchase/backend/routers/service_lines.py
    - plugins/commerce/purchase/backend/routers/__init__.py
    - plugins/commerce/purchase/frontend/pages/purchase/ReceiptServiceLines.tsx
    - plugins/commerce/purchase/frontend/pages/purchase/ReceiptPanel.tsx
    - plugins/commerce/purchase/frontend/types.ts
    - plugins/commerce/purchase/frontend/api.ts
    - apps/api/tests/test_compras_receipt_service_lines.py
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
    - compras.receipt_service_lines.crud
  indirect:
    - compras.ui.recepcion # editor de servicios en flujo de recepción
  must_not_affect:
    - recepción comercial (009) / costos (010) / conciliación (011)
    - custodia/despachos (005/007/008)
    - reclamaciones (012) / derivación (013)
    - lifecycle de órdenes (002)
    - stock ledger / logistics lg_* (escrituras)
    - auth y permisos existentes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-007/008   # receipts + vínculo receipt↔despacho (base del registro)
    - COMPRAS-009       # cierre comercial como gate del registro
  must_compose_with:
    - COMPRAS-015   # legal data PH/retimbrado sobre estas líneas
    - COMPRAS-016   # historial del serial consume estas líneas
    - COMPRAS-019   # set Versión Base Compras
  systemic_invariants:
    - "Todo servicio realizado por el proveedor queda registrado por serial y ligado a la recepción."
  composition_checks:
    - "Flujo: despachar seriales → retornar → recepción → registrar servicio por serial → visible en GET service-lines."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: registro de servicios por recepción cohesivo en services/service_lines.py
  entrypoints_must_stay_thin: true   # routers/service_lines.py solo delega
  review_threshold_lines: 400       # models.py (~398) cruza 400 con +1 tabla:
  extraction_threshold_lines: 600   #   revisión justificada — colocation por
                                    # convención de familia (models.py = UNA
                                    # razón de cambio: tablas del dominio
                                    # compras). Señalizada extracción a módulo
                                    # models/ propio: NO en esta ronda.
  preferred_new_logic_locations:
    - services/service_lines.py
    - routers/service_lines.py
    - schemas/service_lines.py
    - frontend/pages/purchase/ReceiptServiceLines.tsx   # ReceiptPanel.tsx
                                                        # (flujo de recepción,
                                                        # árbol post-020):
                                                        # lógica nueva a
                                                        # componente propio;
                                                        # edición del panel mínima.
```

## Traceability

- Requirement: VISION §19 (servicios realizados por proveedor), §44 pasos
  8-11 (resultado técnico + costo), §45 ("los servicios técnicos deben
  conservar relación con el cilindro"). Roadmap aprobado lote 013..019.
- owner: Product Owner módulo compras (equipo SYSTUTOR OSS)
- approver: mantenedor humano responsable del squash/integración a main
- Commit:
- Deployment: migración 0014 en runtime del plugin commerce

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
