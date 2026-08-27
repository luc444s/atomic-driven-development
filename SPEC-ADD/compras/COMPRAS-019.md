# A.SPEC COMPRAS-019 — Versión Base Compras: integración del set 013–018

> `risk: low` — Derivación §4.1 honesta: A.SPEC **de integración** (§10.1)
> sin superficie de código propia — declara composición, no muta datos, no
> migra, no toca auth/stock/lg_*/dinero. El riesgo de cada A.SPEC miembro ya
> fue derivado individualmente (013 low; 014/015/017/018 normal; 016 low) y
> ninguna introduce migración destructiva ni señal de alto.
> `mode: normal` per §4.2 — compose-gate: los `composition_checks` los
> juzga **COMPOSER**; approver humano con **presence-check**.

## WHY

El owner aprobó cerrar la **Versión Base del módulo Compras** (plugin
commerce/purchase): TODO lo que el negocio de gases necesita para operar el
ciclo de llenado end-to-end, excluyendo integraciones con otros dominios y
reporting. Las siete piezas 013–018 (más las 002–012 ya integradas) forman
un conjunto cuyo valor está en la composición: un MISMATCH se deriva a
reclamación, un servicio queda ligado al serial con su vigencia PH, la
custodia es cotejable físicamente y lo no aceptado se devuelve con
historia. Sin una A.SPEC de integración que declare y ordene los checks del
conjunto, nadie demuestra que la Versión Base compone (SPECIFICATION §10.1:
la verdad compuesta pertenece a una spec de integración).

## WHAT

Una verdad nueva, declarativa: **existe un release "Versión Base Compras"
definido por el conjunto {002..018} con owner declarado, checks de
composición ordenados y ejecutables, e invariantes sistémicas del set — y
su veredicto de composición es juzgable por COMPOSER con presencia del
approver.**

Esta A.SPEC NO agrega feature, código, migración ni endpoint. Declara:

- `composition.owner` del release.
- `composition_checks` ordenados y ejecutables del flujo completo:
  orden → despacho → recepción/retorno → conciliación tres vías →
  derivación claim → servicio → PH → historial → conciliación física →
  devolución de mercadería → close.
- `systemic_invariants` del set.
- `must_compose_with` 013..018 (más base 002..012 implícita en los checks).

## SCOPE

- Este documento (`SPEC-ADD/compras/COMPRAS-019.md`) como contrato de
  integración.
- Actualización del tracker de `SPEC-ADD/compras/COMPRAS-VISION-001.md`
  (secciones 16, 19, 20, 25, 26, 40, 42, 43, 44) al cerrar la integración.
- Ejecución de los checks por COMPOSER en el compose-gate.

## OUT OF SCOPE

- Cualquier cambio de código, migración, endpoint o test nuevo (los tests
  de cada miembro ya existen y corren en los checks).
- Integraciones con otros dominios (Logistics escritura §32, Finanzas §35,
  Stock salidas §33) y reporting (§39/§41) — excluidos por el owner.
- Re-derivación o modificación del alcance de 013..018 (sus contratos son
  insumo, no objeto de revisión aquí).

## CONTRACT

Precondiciones:

- COMPRAS-013..018 integradas a main con sus Definition of Done completos
  (migraciones 0013–0018 aplicadas en runtime del plugin commerce).
- Suites de cada miembro verdes en el SHA de integración.

Postcondiciones:

- Los `composition_checks` pasan en orden sobre una base migrada 0013–0018.
- El approver del release queda registrado con presence-check (quién
  presenció la ejecución del gate y cuándo).
- Tracker VISION actualizado: §19 ✅, §20 ✅, §25 ✅ (derivación
  incluida), §26 ✅ (devolución de mercadería), §40 ✅ (por cilindro),
  §42 ✅ (flujo principal completo), §44 ✅, §3 Versión Base operativa.

## INVARIANTS

```yaml
invariants:
  - "Ningún check de composición muta código ni migraciones: solo ejecutan superficies ya integradas."
  - "Los checks no alteran datos de otros tenants (todo flujo corre dentro de un tenant de prueba)."
  - "Ningún movimiento del flujo borra historia (append-only en claims, servicios, conteos, devoluciones)."
  - "El set no introduce escrituras lg_*/stock/ledger nuevas respecto de los miembros ya aprobados."
  - "Auth y permisos existentes intactos: ningún permiso nuevo ni cambio en kernel (rg REQUIRE_ sobre routers sin diffs más allá de los integrados)."
```

## VERIFICATION

Los `composition_checks` (abajo, Composition) SON la verificación de esta
A.SPEC — juzgados por COMPOSER (compose-gate). Resumen ejecutable:

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
2. Presencia de migraciones 0013–0018 en el catálogo (tablas
   `com_receipt_service_lines`, `com_physical_counts*`,
   `com_merchandise_returns*`; columnas `com_supplier_claims.source` y
   legales de PH) — el flujo del check 3 no puede correr sin ellas.
3. Secuencia API end-to-end del flujo principal (check 3 de Composition)
   ejecutada contra runtime migrado, con resultados archivados.
4. Auditorías estáticas del set: `rg` sin escrituras lg_/stock nuevas en
   `services/{claims,service_lines,cylinder_history,physical_counts,returns}.py`
   y `rg -o "REQUIRE_[A-Z_]+" .../routers | sort -u` → conjunto de permisos
   igual al pre-lote; `tsc --noEmit` limpio.
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
    - systutor kernel (auth/tenancy)
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
    - plugins/logistics / plugins/stock / finanzas
    - stock ledger / logistics lg_*
    - auth y permisos existentes
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
    - "2. Migraciones 0013–0018 presentes y aplicadas (VERIFICATION check 2)."
    - "3. Flujo end-to-end ordenado sobre un tenant de prueba: crear proveedor + orden (2 ítems, seriales) → despachar → confirmar → custodia EN_CUSTODIA visible → retorno parcial → recepción con aceptadas/rechazadas (009) → cierre comercial → cost_lines (010) → factura (011) → conciliar → MISMATCH → derivar claims (013, idempotente) → registrar servicio por serial (014) con PH/retimbrado legal (015, vigencia) → GET /cylinders/{serial}/history muestra despacho+receipt+servicio+vigencia (016) → conteo físico con FALTANTE/NO_DECLARADO + resolución con evento (017) → devolución de mercadería ligada a receipt+claim, resolver (018) → close de orden (002); recepciones/servicios/claims/conteos intactos tras cada paso."
    - "4. Auditorías estáticas del set (VERIFICATION check 4): cero escrituras lg_/stock nuevas, permisos sin cambios, tsc limpio."
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

- Requirement: VISION §10.1-lote (roadmap aprobado por el owner,
  "Versión Base módulo Compras"), §42 (flujo principal end-to-end), §45
  (reglas críticas como invariantes del set), §46 (objetivo operativo).
  Excluye por decisión del owner: integraciones externas (§31/§32-escritura/
  §35) y reporting (§39/§41).
- owner: Product Owner módulo compras (equipo SYSTUTOR OSS) — composition.owner
- approver: mantenedor humano con presence-check del compose-gate
  (escalación de REVISE/SPLIT/REJECT según §10.2)
- Commit:
- Deployment: migraciones 0013–0018 en runtime del plugin commerce

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
