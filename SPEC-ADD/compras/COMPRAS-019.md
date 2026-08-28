# A.SPEC COMPRAS-019 — Versión Base Compras: integración del set 013–018

> `risk: high` — Derivación §4.1 honesta: A.SPEC **de integración** (§10.1)
> sin superficie de código propia, pero sus propias invariantes y blast radius
> tocan tenancy, `lg_*`/stock ledger y permisos existentes; además depende del
> cierre de una A.SPEC `high` (018) y del gate con approver humano.
> `mode: extreme-poverty` (skill `ADD/skills/extreme-poverty-add/Extreme-Poverty-ADD.md`,
> decisión approver 2026-08-28) — compose-gate: los `composition_checks` los
> ejecuta el **hilo principal** (función de COMPOSER absorbida, sin subagentes);
> approver humano con **presence-check**.

## WHY

El owner aprobó cerrar la **Versión Base del módulo Compras** (plugin
commerce/purchase): TODO lo que el negocio de gases necesita para operar el
ciclo de llenado end-to-end, excluyendo integraciones con otros dominios y
reporting. Las piezas 013–018, apoyadas por la extracción estructural 020
(más las 002–012 ya integradas), forman
un conjunto cuyo valor está en la composición: un MISMATCH se deriva a
reclamación, un servicio queda ligado al serial con su vigencia PH, la
custodia es cotejable físicamente y lo no aceptado se devuelve con
historia. Sin una A.SPEC de integración que declare y ordene los checks del
conjunto, nadie demuestra que la Versión Base compone (SPECIFICATION §10.1:
la verdad compuesta pertenece a una spec de integración).

## WHAT

Una verdad nueva, declarativa: **existe un release "Versión Base Compras"
definido por el conjunto {002..018} soportado por la A.SPEC estructural
pareada 020, con owner declarado, checks de composición ordenados y
ejecutables, e invariantes sistémicas del set — y
su veredicto de composición es juzgable por el compose-gate en el hilo
principal (función de COMPOSER absorbida) con presencia del approver.**

Esta A.SPEC NO agrega feature, código, migración ni endpoint. Declara:

- `composition.owner` del release.
- `composition_checks` ordenados y ejecutables del flujo completo:
  orden → despacho → recepción/retorno → conciliación tres vías →
  derivación claim → servicio → PH → historial → conciliación física →
  devolución de mercadería → close.
- `systemic_invariants` del set.
- `must_compose_with` 013..018 (más base 002..012 implícita en los checks)
  sobre la estructura ya extraída por 020.

## SCOPE

- Este documento (`SPEC-ADD/compras/COMPRAS-019.md`) como contrato de
  integración.
- Actualización del tracker de `SPEC-ADD/compras/COMPRAS-VISION-001.md`
  (cabecera "Última actualización" y filas 16, 19, 20, 25, 26, 40, 42, 44)
  al cerrar la integración.
- Ejecución de los checks en el compose-gate (hilo principal, función de
  COMPOSER absorbida).

## OUT OF SCOPE

- Cualquier cambio de código, migración, endpoint o test nuevo (los tests
  de cada miembro ya existen y corren en los checks).
- Integraciones con otros dominios (Logistics escritura §32, Finanzas §35,
  Stock salidas §33) y reporting (§39/§41) — excluidos por el owner.
- Re-derivación o modificación del alcance de 013..018 (sus contratos son
  insumo, no objeto de revisión aquí).

## CONTRACT

Precondiciones:

- COMPRAS-013..018 y COMPRAS-020 integradas en el SHA candidato con sus Definition of Done
  completos
  (migraciones aplicables del lote: 0013, 0014, 0015, 0017 y 0018, con
  proofs verdes en sus A.SPEC hoja; 0016 no migra).
- Suites de cada miembro verdes en el SHA de integración.

Postcondiciones:

- Los `composition_checks` pasan en orden sobre el SHA candidato, con proofs
  explícitas del lote (suite, migraciones, flujo integrado, auditorías,
  presence-check).
- El approver del release queda registrado con presence-check (quién
  presenció la ejecución del gate y cuándo).
- Tracker VISION actualizado: cabecera "Última actualización" al día;
  §16 ✅, §19 ✅, §20 ✅, §25 ✅ (derivación incluida), §26 ✅
  (devolución de mercadería), §40 ✅ (historial por cilindro), §42 ✅
  (flujo principal completo), §44 ✅.

## INVARIANTS

```yaml
invariants:
  - "Ningún check de composición muta código ni migraciones: solo ejecutan superficies ya integradas."
  - "El comportamiento de cada A.SPEC miembro 013..018 permanece intacto: la suite completa compras del lote corre verde sobre el SHA de integración."
  - "Los checks no alteran datos de otros tenants (todo flujo corre dentro de un tenant de prueba)."
  - "Ningún movimiento del flujo borra historia (append-only en claims, servicios, conteos, devoluciones)."
  - "El set no introduce escrituras lg_*/stock/ledger nuevas respecto de los miembros ya aprobados."
  - "Permisos existentes intactos: ningún permiso nuevo en routers del lote (mismo conjunto REQUIRE_)."
```

## VERIFICATION

Los `composition_checks` (abajo, Composition) SON la verificación de esta
A.SPEC — ejecutados en orden por el compose-gate en el hilo principal
(función de COMPOSER absorbida). Resumen ejecutable:

1. `pytest apps/api/tests/test_compras_plugin.py
   apps/api/tests/test_compras_dispatch.py
   apps/api/tests/test_compras_receipt_commercial.py
   apps/api/tests/test_compras_receipt_cost.py
   apps/api/tests/test_compras_invoice_reconciliation.py
   apps/api/tests/test_compras_claims.py
   apps/api/tests/test_compras_claim_derivation.py
   apps/api/tests/test_compras_receipt_service_lines.py
   apps/api/tests/test_compras_ph_restamp.py
   apps/api/tests/test_compras_cylinder_history.py
   apps/api/tests/test_compras_physical_reconciliation.py
   apps/api/tests/test_compras_merchandise_returns.py -q` → todo verde.
2. Proofs de migración aplicables del lote verdes en el SHA candidato:
   `pytest apps/api/tests/test_compras_claim_derivation.py::test_migration_013_downgrade_drops_source_preserving_rows
   apps/api/tests/test_compras_claim_derivation.py::test_migration_013_upgrade_backfills_manual_and_is_idempotent
   apps/api/tests/test_compras_receipt_service_lines.py::test_downgrade_0014_drops_table_receipts_intact
   apps/api/tests/test_compras_ph_restamp.py::test_downgrade_0015_drops_legal_columns_table_intact
   apps/api/tests/test_compras_physical_reconciliation.py::test_downgrade_017_drops_tables_custody_intact
   apps/api/tests/test_compras_merchandise_returns.py::test_return_migration_downgrade_removes_tables_only -q`
   → verde.
3. Evidencia ejecutable del flujo integrado con tests hoja del set:
   `pytest apps/api/tests/test_compras_claim_derivation.py::test_derive_is_idempotent_no_duplicates_on_rerun
   apps/api/tests/test_compras_receipt_service_lines.py::test_service_line_created_linked_to_receipt
   apps/api/tests/test_compras_ph_restamp.py::test_retimbrado_line_accepts_legal_fields
   apps/api/tests/test_compras_cylinder_history.py::test_history_lists_services_with_ph_legal_data
   apps/api/tests/test_compras_physical_reconciliation.py::test_close_computes_faltante_and_no_declarado
   apps/api/tests/test_compras_physical_reconciliation.py::test_resolution_stamps_event
   apps/api/tests/test_compras_merchandise_returns.py::test_return_created_linked_to_receipt
   apps/api/tests/test_compras_merchandise_returns.py::test_repeat_transition_idempotent_no_duplicate_event -q`
   → verde como prueba explícita del flujo compuesto.
4. Auditorías estáticas del set:
   `rg -n "lg_|stock_" plugins/commerce/purchase/backend/services/claims.py plugins/commerce/purchase/backend/services/service_lines.py plugins/commerce/purchase/backend/services/cylinder_history.py plugins/commerce/purchase/backend/services/physical_counts.py plugins/commerce/purchase/backend/services/returns.py`
   → solo lecturas ya aprobadas; sin escrituras nuevas.
   `rg -o "REQUIRE_[A-Z_]+" plugins/commerce/purchase/backend/routers/*.py | sort -u`
   → conjunto exacto `{REQUIRE_SUPPLIER_READ, REQUIRE_SUPPLIER_MANAGE, REQUIRE_ORDER_READ, REQUIRE_ORDER_CREATE, REQUIRE_ORDER_MANAGE, REQUIRE_ORDER_RECEIVE, REQUIRE_DISPATCH_READ, REQUIRE_DISPATCH_MANAGE}`; `npx tsc --noEmit` limpio ejecutado con `apps/web` como working directory.
5. Presence-check del approver registrado (§10.1/§10.2) — la integración
   no se libera sin él.

## ROLLBACK

No aplica rollback físico (no hay cambio de superficie). Si el compose-gate
falla: el release NO se declara cerrado; se escala al approver (§10.2) con
el check fallido como evidencia, y la corrección pertenece a la A.SPEC
miembro culpable (revert de ese miembro según su propio ROLLBACK). Este
contrato no introduce estado que compensar.

## Change Surface

```yaml
change_surface:
  allowed:
    - SPEC-ADD/compras/COMPRAS-019.md            # este contrato
    - SPEC-ADD/compras/COMPRAS-VISION-001.md     # tracker de estado del módulo
  prohibited:
    - plugins/**            # cero código en el compose-gate
    - apps/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.release.version_base   # declarativo
  indirect: []
  must_not_affect:
    - comportamiento de cada A.SPEC miembro (013..018)
    - stock ledger / logistics lg_*
    - permisos existentes
```

## Composition

```yaml
composition:
  owner: Product Owner módulo compras (equipo SYSTUTOR OSS)
  requires_aspecs:
    - COMPRAS-002..012   # base ya integrada (lifecycle, despachos, receipts,
                         # comercial, costos, facturas, claims)
    - COMPRAS-013   # derivación de reclamaciones desde MISMATCH (§25 completa)
    - COMPRAS-014   # servicios realizados por serial (§19)
    - COMPRAS-015   # PH y retimbrado (§20)
    - COMPRAS-016   # historial técnico del envase (§40/§44)
    - COMPRAS-017   # conciliación física (§16)
    - COMPRAS-018   # devolución de mercadería (§26)
    - COMPRAS-020   # extracción estructural requerida por 013/014/018 en UI
  must_compose_with:
    - COMPRAS-013
    - COMPRAS-014
    - COMPRAS-015
    - COMPRAS-016
    - COMPRAS-017
    - COMPRAS-018
  systemic_invariants:
    - "Todo serial en poder del proveedor tiene estado, responsable e historial trazable (custodia 005 + servicios 014/015 + historial 016 + conteo 017)."
    - "Ningún movimiento borra historia: recepciones, servicios, conteos físicos y devoluciones son append-only/auditables."
    - "Las diferencias nunca se corrigen silenciosamente: MISMATCH → reclamación derivable (013); conteo físico → discrepancia resuelta con evento (017); lo no aceptado → devolución con resolución (018)."
    - "Compras no escribe lg_*, stock ni ledger: Logistics/Stock conservan la autoridad de sus dominios (§32/§33)."
    - "El ciclo llenado end-to-end opera dentro de un tenant sin tocar otros (§37)."
  composition_checks:
    - "1. Suite completa compras verde (VERIFICATION check 1) sobre el SHA de integración."
    - "2. Proofs de migración aplicables del lote (0013, 0014, 0015, 0017, 0018) verdes en el SHA candidato (VERIFICATION check 2)."
    - "3. Evidencia ejecutable del flujo compuesto (VERIFICATION check 3): tests hoja 013/014/015/016/017/018 enlazados por pytest y verdes como prueba explícita del release integrado."
    - "4. Auditorías estáticas del set (VERIFICATION check 4): cero escrituras lg_/stock nuevas, conjunto REQUIRE_ exacto sin cambios y tsc limpio."
    - "5. Approver con presence-check: registro de quién presenció el gate y cuándo; sin esto, NO se integra (§10.2)."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: contrato declarativo de integración — cero código, cero duplicación de contratos miembros
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations: []   # no aplica: sin código
```

## Traceability

- Requirement: `SPEC-ADD/compras/COMPRAS-VISION-001.md` — tracker de estado
  del módulo (filas 16, 19, 20, 25, 26, 40, 42, 44) + §§45/46 como reglas
  críticas y objetivo operativo del set. Excluye por decisión del owner:
  integraciones externas (§31/§32-escritura/§35) y reporting (§39/§41).
- owner: Product Owner módulo compras (equipo SYSTUTOR OSS) — composition.owner
- approver: mantenedor humano con presence-check del compose-gate
  (escalación de REVISE/SPLIT/REJECT según §10.2)
- Commit: pendiente (compose-gate PASS en hilo principal 2026-08-28: 106/106
  tests, proofs migración y flujo verdes, auditorías lg_/stock_ + REQUIRE_ +
  tsc limpias; presence-check approver firmado; SHA se ancla al squash a main)
- Deployment: migraciones 0013–0018 en runtime del plugin commerce

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
- [ ] Traceability established  (SHA del squash a main pendiente)
