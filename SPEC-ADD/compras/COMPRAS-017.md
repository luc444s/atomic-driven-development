# A.SPEC COMPRAS-017 — Conciliación física del inventario en custodia

> `risk: normal` — Derivación §4.1: migración aditiva (4 tablas nuevas),
> sin dinero, sin stock, sin auth, sin escrituras `lg_*`; señal de normal:
> opera sobre la verdad de custodia (005) — un snapshot o diff incorrecto
> produce discrepancias falsas que pueden derivar en reclamaciones erróneas
> al proveedor; además introduce ciclo de vida con eventos auditable. No hay
> señal de `high` (custodia NO se muta; blast radius compra-only).
> `mode: normal` per §4.2 (ciclo completo).

## WHY

El control de permanencia (§12) dice cuántos envases tiene cada proveedor,
pero nadie verifica que lo declarado coincida con lo físico. Las reglas
críticas (§45: "las diferencias nunca deben corregirse silenciosamente",
"ningún cilindro desaparece de trazabilidad") y el objetivo operativo (§46)
exigen un cotejo físico serial-by-serial de la custodia; sin él, un envase
perdido en custodia puede permanecer años como "EN_CUSTODIA" fantasma y las
pérdidas se descubren por el costo, no por el sistema. El flujo necesita una
sesión de conteo con snapshot persistido inmutable, cálculo de discrepancias
y resolución auditada — sin borrar ni alterar la historia de custodia (§45).

NOTA de alcance: los checks de atributos físicos de §16 (lleno/vacío,
presión, válvula, capacidad, sello, PH en recepción) NO se implementan aquí —
quedan como especificación futura propia; el tracker VISION §16 NO se marca
✅ con esta A.SPEC (se anota el avance del cotejo de custodia).

## WHAT

Una verdad nueva: **el inventario en custodia de un proveedor (custodia
005) puede cotejarse físicamente serial-by-serial mediante una sesión de
conteo con snapshot inmutable, cuya Close calcula discrepancias
(FALTANTE / NO_DECLARADO / CONDICION) y cuya resolución de cada discrepancia
queda registrada con evento auditable — sin mutar la custodia ni borrar
historia.**

### Modelo

- `com_physical_counts`:
  - `id`, `tenant_id`, `supplier_id` FK `com_suppliers.id`,
    `order_id` FK `com_purchase_orders.id` | NULL (alcance opcional),
    `dispatch_id` FK `com_dispatches.id` | NULL (alcance opcional),
  - `expected_total: Integer`, `found_total: Integer`,
    `match_count: Integer`,
  - `status: String(20)` (`EN_CURSO | CERRADA`, default `EN_CURSO`),
  - `counted_by` FK `users.id`, `counted_at`, `closed_at` | NULL,
    `notes: Text | NULL`.
- `com_physical_count_expected_serials` (snapshot PERSISTIDO en creación —
  inmutable, base del diff y de la auditoría serial-by-serial; sobrevive
  reinicios y cierre):
  - `id`, `tenant_id`, `count_id` FK cascade,
    `cylinder_id` FK `lg_cylinders.id`, `serial: String(50)`,
    `captured_at`.
- `com_physical_count_items` (solo discrepancias — append-only):
  - `id`, `tenant_id`, `count_id` FK cascade,
    `cylinder_id` FK `lg_cylinders.id`, `serial: String(50)` snapshot,
  - `expected: Boolean` (estaba en snapshot persistido),
    `found: Boolean` (fue contado físicamente),
  - `discrepancy_type: String(30)` —
    `FALTANTE | NO_DECLARADO | CONDICION`,
  - `notes: Text | NULL`, `resolution: String(20) | NULL`
    (`RECLAMADA | ACEPTADA | OBSERVADA`),
    `resolved_by` FK users | NULL, `resolved_at` | NULL.
- `com_physical_count_events` (patrón `ComSupplierClaimEvent`):
  - `id`, `tenant_id`, `count_id` FK cascade, `from_status` | NULL,
    `to_status: String(20)`, `reason: Text | NULL`, `user_id` | NULL,
    `created_at`.

### Ciclo

- `POST /dispatches/physical-counts` (REQUIRE_DISPATCH_MANAGE) → sesión
  `EN_CURSO`; el servidor PERSISTE el snapshot de los seriales
  `EN_CUSTODIA` del supplier (filtro order/dispatch opcional) en
  `com_physical_count_expected_serials` al crear (inmutable para el diff;
  visible en el detalle y tras reinicio/cierre).
- `POST /dispatches/physical-counts/{id}/close` con
  `{found: [{serial, condition_note?}], notes?}` (REQUIRE_DISPATCH_MANAGE):
  diff contra snapshot persistido → ítems de discrepancia persistidos
  (FALTANTE = en custodia no encontrado; NO_DECLARADO = encontrado no en
  custodia — precedencia sobre CONDICION: un serial no esperado es
  NO_DECLARADO y su `condition_note` se conserva en `notes` del ítem;
  CONDICION = esperado y encontrado con `condition_note`), totales calculados,
  estado `CERRADA`, evento de cierre. Close de sesión ya `CERRADA` → `409`.
- `POST /dispatches/physical-counts/{id}/items/{item_id}/resolve` con
  `{resolution, reason}` (REQUIRE_DISPATCH_MANAGE): resuelve UNA
  discrepancia (RECLAMADA sugerida si luego se reclama vía 012/013), estampa
  evento auditable. `409` si la sesión no está `CERRADA` o ítem ya resuelto.
- `GET /dispatches/physical-counts` / `GET .../{id}` (REQUIRE_DISPATCH_READ;
  detalle con ítems + timeline de eventos).
- **La custodia (005/007/008) NO se muta**: ninguna fila
  `com_dispatch_cylinders` cambia de estado por un conteo; las discrepancias
  se resuelven por decisión registrada (y reclamo/devolución futura), nunca
  ajuste silencioso (§45: "las diferencias nunca deben corregirse
  silenciosamente", "ningún cilindro desaparece de trazabilidad").

### Frontend

- Componente nuevo `components/PhysicalCountDialog.tsx` (crear conteo por
  proveedor, carga de seriales contados, cierre con discrepancias
  resaltadas, resolución con motivo y timeline), integrado desde
  `DispatchesPage.tsx` (198 líneas — edición mínima: import + botón).

## SCOPE

- `plugins/commerce/migrations/017_physical_counts.py`
  (`revision = "0017"`): 4 tablas + índices (`count_id`, `supplier_id`,
  `cylinder_id`), estilo familia.
- `plugins/commerce/purchase/backend/models.py`: `ComPhysicalCount`,
  `ComPhysicalCountItem`, `ComPhysicalCountEvent`.
- `plugins/commerce/purchase/backend/schemas/physical_counts.py`
  (+ export `schemas/__init__.py`): `PhysicalCountCreate`,
  `PhysicalCountCloseRequest`, `PhysicalCountItemResolveRequest`,
  `PhysicalCountRead/Detail/ItemRead/EventRead`.
- `plugins/commerce/purchase/backend/services/physical_counts.py`:
  `create_count` (snapshot), `close_count` (diff), `resolve_item`, lecturas.
- `plugins/commerce/purchase/backend/routers/physical_counts.py`
  (+ inclusión `routers/__init__.py` — registrado ANTES que el router
  dispatches para que `GET /dispatches/physical-counts` no sea capturado por
  `/{dispatch_id}`; `test_list_physical_counts_not_shadowed` lo demuestra): endpoints listados.
- Frontend: `components/PhysicalCountDialog.tsx` (nuevo),
  `pages/DispatchesPage.tsx` (integración mínima), `types.ts`, `api.ts`.
- Tests: `apps/api/tests/test_compras_physical_reconciliation.py`.

## OUT OF SCOPE

- Mutación de `com_dispatch_cylinders` (nuevos estados tipo PERDIDO,
  transición de despacho por conteo) — decisión futura; aquí el ajuste es
  registro + resolución auditada.
- Derivación automática de reclamaciones desde FALTANTE (composición con
  012/013 queda manual/reclamada por resolución).
- Ajustes de stock/valorización por pérdida (§33/§35) — fuera.
- Conteos de stock de almacén (dominio stock) — solo custodia en proveedor.

## CONTRACT

Precondiciones:

- Supplier existe en el tenant (404 si no / cross-tenant); orden/despacho
  de alcance, si vienen, pertenecen al tenant y al supplier (400 si no).
- Close solo en `EN_CURSO`; resolve solo con sesión `CERRADA` e ítem sin
  resolución (409 si no).

Postcondiciones:

- Snapshot de custodia capturado al crear y visible en el detalle
  (`expected_total` = seriales EN_CUSTODIA del alcance).
- Close persiste TODAS las discrepancias del diff con su tipo y totales
  (`expected_total`, `found_total`, `match_count`), estampa evento de
  cierre con usuario y fecha.
- Cada resolución estampa exactamente un evento (quién, cuándo, resolución,
  motivo); repetición → `409`.
- Ninguna fila de custodia cambia; ningún ítem/conteo se borra o edita
  (append-only tras creación).

## INVARIANTS

```yaml
invariants:
  - "Custodia/despachos (005/007/008) intocados: crear/cerrar/resolver conteos no muta com_dispatch_cylinders ni estados de despacho (suite test_compras_dispatch verde)."
  - "Recepción (009) / costos (010) / conciliación (011) / reclamaciones (012/013) intocadas (suites test_compras_receipt_commercial, test_compras_invoice_reconciliation, test_compras_claims verdes)."
  - "Historia nunca se borra: ítems, eventos y snapshot persistido append-only; el snapshot capturado en create es visible e idéntico tras cierre y tras reinicio (test_count_snapshot_persisted_visible_after_restart)."
  - "Toda lectura/escritura filtrada por tenant_id; cross-tenant 404."
  - "Cero escrituras lg_* (cylinder_id solo FK de lectura)."
  - "Permisos existentes reutilizados (REQUIRE_DISPATCH_READ/MANAGE): ningún permiso nuevo."
  - "Migración reversible: downgrade de 4 tablas demostrado ejecutado."
  - "Suite compras previa completa verde; tsc --noEmit limpio."
```

## VERIFICATION

Tests nuevos (`pytest apps/api/tests/test_compras_physical_reconciliation.py -q`):

- `test_count_snapshot_captures_custody_serials`.
- `test_count_snapshot_persisted_visible_after_restart`.
- `test_close_undeclared_serial_with_note_is_no_declarado`.
- `test_close_computes_faltante_and_no_declarado`.
- `test_close_condition_note_creates_condicion_item`.
- `test_close_already_closed_409`.
- `test_close_tenant_isolated_404`.
- `test_list_physical_counts_not_shadowed`.
- `test_resolution_stamps_event`.
- `test_resolution_twice_409`.
- `test_resolution_does_not_mutate_custody`.
- `test_counts_never_delete_history`.

Regresión (composición): `pytest apps/api/tests/test_compras_plugin.py
apps/api/tests/test_compras_dispatch.py
apps/api/tests/test_compras_receipt_commercial.py
apps/api/tests/test_compras_receipt_cost.py
apps/api/tests/test_compras_invoice_reconciliation.py
apps/api/tests/test_compras_claims.py
apps/api/tests/test_compras_claim_derivation.py
apps/api/tests/test_compras_receipt_service_lines.py
apps/api/tests/test_compras_ph_restamp.py
apps/api/tests/test_compras_cylinder_history.py -q` — verde.
`tsc --noEmit` limpio.

Prueba de reversibilidad (SPECIFICATION §9.1 — presence no es execution):
invocar `downgrade(db)` del módulo `plugins/commerce/migrations/017_physical_counts.py`
directamente contra una base de prueba migrada, o el runner con
`target_revision="0016"` (anterior). NOTA: `downgrade("0017")` sobre una base
ya en `"0017"` es NO-OP por diseño del runner
(`vendor/systutor-core/src/systutor/kernel/plugins/migrations.py:105`) — no
sirve como prueba. Aserción negativa: `com_physical_counts`,
`com_physical_count_items`, `com_physical_count_events` y
`com_physical_count_expected_serials` AUSENTES;
despachos/custodia y demás tablas compras intactos.

Auditorías explícitas (§7.1):

- `rg -n "ComDispatchCylinder" plugins/commerce/purchase/backend/services/physical_counts.py`
  → solo SELECT de lectura; `rg -n "db.add\\(ComDispatch|update\\(ComDispatch"
  ...` → SIN coincidencias (custodia no se muta).
- `rg -o "REQUIRE_[A-Z_]+" plugins/commerce/purchase/backend/routers | sort -u`
  antes vs después → mismo conjunto.

Manual: supplier con 3 seriales EN_CUSTODIA → crear conteo (snapshot 3) →
close con 2 encontrados + 1 serial ajeno → 1 FALTANTE + 1 NO_DECLARADO,
match 1; resolver FALTANTE como RECLAMADA con motivo → timeline con evento;
custodia sigue mostrando 3 EN_CUSTODIA.

## ROLLBACK

Reversible: revertir commit; ejecutar `downgrade` de la migración 0017
elimina las 4 tablas (se pierden los conteos físicos; custodia, despachos y
recepciones intactos).

## Change Surface

```yaml
change_surface:
  allowed:
    - SPEC-ADD/compras/COMPRAS-017.md   # el contrato viaja con su integración
    - plugins/commerce/migrations/017_physical_counts.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/physical_counts.py
    - plugins/commerce/purchase/backend/schemas/__init__.py
    - plugins/commerce/purchase/backend/services/physical_counts.py
    - plugins/commerce/purchase/backend/routers/physical_counts.py
    - plugins/commerce/purchase/backend/routers/__init__.py
    - plugins/commerce/purchase/frontend/components/PhysicalCountDialog.tsx
    - plugins/commerce/purchase/frontend/pages/DispatchesPage.tsx
    - plugins/commerce/purchase/frontend/types.ts
    - plugins/commerce/purchase/frontend/api.ts
    - apps/api/tests/test_compras_physical_reconciliation.py
  prohibited:
    - plugins/logistics/**
    - plugins/stock/**
    - plugins/finanzas/**
    - systutor kernel (auth/tenancy)
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.physical_counts.lifecycle
  indirect:
    - compras.ui.despachos # diálogo de conteo físico
  must_not_affect:
    - custodia y ciclo de despachos (005/007/008)
    - recepción comercial (009) / costos (010) / conciliación (011)
    - reclamaciones (012/013) / servicios (014) / PH (015) / historial (016)
    - lifecycle de órdenes (002)
    - stock ledger / logistics lg_* (escrituras)
    - auth y permisos existentes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-005   # custodia = fuente del snapshot EN_CUSTODIA
    - COMPRAS-004   # FK supplier_id → com_suppliers
  must_compose_with:
    - COMPRAS-009   # estados comerciales que el conteo no altera (no consume output)
    - COMPRAS-012/013   # resolución RECLAMADA enlaza manualmente a claims
    - COMPRAS-016       # el serial contado tiene historial consultable
    - COMPRAS-019       # set Versión Base Compras
  systemic_invariants:
    - "El inventario en custodia de un proveedor es cotejable físicamente serial-by-serial con discrepancias auditadas."
  composition_checks:
    - "Flujo: custodia 3 seriales → conteo → close con faltante/ajeno → discrepancias resaltadas → resolver con evento → custodia intacta."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: ciclo de conteo físico cohesivo en services/physical_counts.py
  entrypoints_must_stay_thin: true   # routers/physical_counts.py solo delega
  review_threshold_lines: 400       # models.py (~430 tras 015) ya en revisión:
  extraction_threshold_lines: 600   #   +4 tablas justificadas (cohesión dominio
                                    #   compras); extracción a módulo models/
                                    #   sigue señalizada, NO en esta ronda
                                    #   (muy bajo 600).
  preferred_new_logic_locations:
    - services/physical_counts.py
    - routers/physical_counts.py
    - schemas/physical_counts.py
    - frontend/components/PhysicalCountDialog.tsx
```

## Traceability

- Requirement: VISION §16 (conciliación física), §12 (control de
  permanencia), §45 ("las diferencias nunca deben corregirse
  silenciosamente", "ningún cilindro desaparece de trazabilidad").
  Roadmap aprobado lote 013..019.
- owner: Product Owner módulo compras (equipo SYSTUTOR OSS)
- approver: mantenedor humano responsable del squash/integración a main
- Commit:
- Deployment: migración 0017 en runtime del plugin commerce

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
