# A.SPEC COMPRAS-015 — PH y retimbrado: datos legales de seguridad

> `risk: normal` — Derivación §4.1: migración aditiva (ADD COLUMNs), sin
> dinero, sin stock, sin auth, sin escrituras `lg_*`; señal de normal: toca
> **datos legales de seguridad** (fecha de retimbrado, próxima prueba
> hidrostática, resultado) cuyo error de registro tiene consecuencia de
> cumplimiento, y añade validación condicional sobre el flujo de 014.
> No hay señal de `high` (reversible, blast radius compra-only).
> `mode: normal` per §4.2 (ciclo completo).

## WHY

Cuando el proveedor realiza una prueba hidrostática o retimbrado (§20), la
empresa debe poder responder "¿cuándo vence la PH de este envase?" desde el
sistema. La línea de servicio de COMPRAS-014 registra que se hizo un
`PRUEBA_HIDROSTATICA`/`RETIMBRADO`, pero no cuándo, con qué resultado ni
cuál es la próxima vigencia — la información legal de seguridad se pierde
en notas de texto. VISION §20 exige: cilindro, proveedor, fecha, resultado,
vigencia, referencia documental, observaciones.

## WHAT

Una verdad nueva: **toda línea de servicio de tipo PH o retimbrado lleva sus
datos legales obligatorios (fecha del trabajo, resultado y — si aprobado —
próxima prueba hidrostática), quedando la vigencia del envase registrada y
consultable desde Compras.**

### Modelo (extiende tabla de COMPRAS-014)

- `com_receipt_service_lines` gana columnas:
  - `test_date: Date | NULL` — fecha del trabajo legal (PH o retimbrado).
  - `next_test_date: Date | NULL` — próxima prueba hidrostática (vigencia).
  - `result: String(20) | NULL` — `APROBADO | RECHAZADO`.
  - `document_ref: String(80) | NULL` — referencia documental del
    certificado/acta (§20).

### Reglas

- `service_type ∈ {PRUEBA_HIDROSTATICA, RETIMBRADO}` ⇒ obligatorio:
  `test_date` + `result` (422 si falta). `result = APROBADO` ⇒
  `next_test_date` obligatorio (422 si falta). `result = RECHAZADO` ⇒
  `next_test_date` debe ser NULL (422 si viene).
- Tipos no legales: las columnas legales se rechazan si vienen pobladas
  (422) — evita datos legales colgados del servicio equivocado.
- Corrección solo vía delete+alta de la línea (014 no define PUT) y siempre
  fuera del cierre comercial (gate 009/014).
- **La vigencia NO se escribe en `lg_cylinders`**: la verdad legal vive en
  Compras (vínculo comercial §20: "Compras conserva el vínculo comercial;
  Logística conserva el estado técnico resultante"). La actualización
  técnica en Logistics es escritura futura vía eventos (§32) — fuera de
  alcance.

### Endpoints (mismos de 014, payload extendido)

- `POST /receipts/{receipt_id}/service-lines` acepta campos legales con las
  reglas de arriba.
- `GET /receipts/{receipt_id}/service-lines` los devuelve.

### Frontend

- `components/ReceiptServiceLines.tsx`: si el tipo elegido es PH/retimbrado,
  el editor muestra campos legales obligatorios (fecha, resultado, próxima
  PH, referencia) con validación previa al submit.

## SCOPE

- `plugins/commerce/migrations/015_ph_restamp_legal.py`
  (`revision = "0015"`): `ALTER TABLE com_receipt_service_lines ADD COLUMN`
  ×4 + índice `ix_com_receipt_service_lines_next_test_date` (consulta de
  vigencias, §12 futuro); downgrade `DROP`s.
- `plugins/commerce/purchase/backend/models.py`: 4 columnas en
  `ComReceiptServiceLine`.
- `plugins/commerce/purchase/backend/schemas/service_lines.py`: campos
  legales en Create/Read + validadores condicionales.
- `plugins/commerce/purchase/backend/services/service_lines.py`: reglas de
  obligatoriedad.
- Frontend: `components/ReceiptServiceLines.tsx`, `types.ts`, `api.ts`.
- Tests: `apps/api/tests/test_compras_ph_restamp.py`.

## OUT OF SCOPE

- Escritura de la vigencia en `lg_cylinders` o cualquier modelo logístico
  (futura A.SPEC §32 vía eventos).
- Alertas automáticas por vencimiento de PH (§12) — futura.
- Certificados en PDF/documentos del kernel — futura.
- Historial consolidado por serial — COMPRAS-016.

## CONTRACT

Precondiciones:

- Receipt existe en el mismo tenant, sin cierre comercial (reglas 014).
- Serial válido (reglas 014).

Postcondiciones:

- Línea PH/retimbrado persistida con `test_date`, `result` y — si
  `APROBADO` — `next_test_date` poblados; vigencia consultable desde la
  línea (y desde 016 cuando exista).
- Ningún dato legal queda registrado sobre tipos no legales.

## INVARIANTS

```yaml
invariants:
  - "Líneas de servicio (014) intocadas en su contrato: tipos, serial snapshot, gate de cierre comercial operan igual (suite test_compras_receipt_service_lines verde)."
  - "Recepción comercial (009) / costos (010) / conciliación (011) intocadas."
  - "Custodia/despachos (005/007/008) intocados (suite test_compras_dispatch verde)."
  - "Reclamaciones (012/013) intocadas (suite test_compras_claims + test_compras_claim_derivation verdes)."
  - "Cero escrituras lg_*: la vigencia legal vive SOLO en com_receipt_service_lines."
  - "Toda lectura/escritura filtrada por tenant_id; cross-tenant 404."
  - "Permisos existentes reutilizados (REQUIRE_ORDER_READ/RECEIVE)."
  - "Migración reversible: ADD COLUMNs con downgrade DROP demostrado ejecutado."
  - "Suite compras previa completa verde; tsc --noEmit limpio."
```

## VERIFICATION

Tests nuevos (`pytest apps/api/tests/test_compras_ph_restamp.py -q`):

- `test_ph_line_requires_test_date_and_result_422`.
- `test_ph_line_aprobado_requires_next_test_date_422`.
- `test_ph_line_rechazado_rejects_next_test_date_422`.
- `test_retimbrado_line_accepts_legal_fields`.
- `test_non_legal_type_rejects_legal_fields_422`.
- `test_ph_legal_data_visible_in_read`.
- `test_ph_line_tenant_isolated_404`.

Regresión (composición): `pytest apps/api/tests/test_compras_plugin.py
apps/api/tests/test_compras_dispatch.py
apps/api/tests/test_compras_receipt_commercial.py
apps/api/tests/test_compras_receipt_cost.py
apps/api/tests/test_compras_invoice_reconciliation.py
apps/api/tests/test_compras_claims.py
apps/api/tests/test_compras_claim_derivation.py
apps/api/tests/test_compras_receipt_service_lines.py -q` — verde.
`tsc --noEmit` limpio.

Prueba de reversibilidad (SPECIFICATION §9.1 — presence no es execution):
invocar `downgrade(db)` del módulo `plugins/commerce/migrations/015_ph_restamp_legal.py`
directamente contra una base de prueba migrada, o el runner con
`target_revision="0014"` (anterior). NOTA: `downgrade("0015")` sobre una base
ya en `"0015"` es NO-OP por diseño del runner
(`vendor/systutor-core/src/systutor/kernel/plugins/migrations.py:105`) — no
sirve como prueba. Aserción negativa: columnas `test_date/next_test_date/
result/document_ref` AUSENTES y su índice AUSENTE; tabla y datos de 014
intactos.

Auditorías explícitas (§7.1):

- `rg -n "LogisticsCylinder|lg_" plugins/commerce/purchase/backend/services/service_lines.py`
  → solo import/SELECT de lectura; ninguna escritura
  (`rg -n "db.add\\(Logistics|update\\(Logistics|delete\\(Logistics" ...`
  → SIN coincidencias).
- `rg -o "REQUIRE_[A-Z_]+" plugins/commerce/purchase/backend/routers | sort -u`
  antes vs después → mismo conjunto.

Manual: recepción → línea PRUEBA_HIDROSTATICA sin fecha → 422; con
fecha+APROBADO+próxima PH+referencia → visible; línea LLENADO con
next_test_date → 422.

## ROLLBACK

Reversible: revertir commit; ejecutar `downgrade` de la migración 0015
elimina las 4 columnas y el índice (se pierde el dato legal registrado;
líneas de servicio y receipts intactos).

## Change Surface

```yaml
change_surface:
  allowed:
    - SPEC-ADD/compras/COMPRAS-015.md   # el contrato viaja con su integración
    - plugins/commerce/migrations/015_ph_restamp_legal.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/service_lines.py
    - plugins/commerce/purchase/backend/services/service_lines.py
    - plugins/commerce/purchase/frontend/components/ReceiptServiceLines.tsx
    - plugins/commerce/purchase/frontend/types.ts
    - plugins/commerce/purchase/frontend/api.ts
    - apps/api/tests/test_compras_ph_restamp.py
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
    - compras.receipt_service_lines.legal_data
  indirect:
    - compras.ui.recepcion # campos legales condicionales en el editor
  must_not_affect:
    - contrato CRUD de líneas de servicio (014)
    - recepción comercial (009) / costos (010) / conciliación (011)
    - custodia/despachos (005/007/008)
    - reclamaciones (012/013)
    - stock ledger / logistics lg_* (escrituras)
    - auth y permisos existentes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-014   # tabla com_receipt_service_lines + tipos legales
  must_compose_with:
    - COMPRAS-016   # historial del serial muestra vigencia/resultados
    - COMPRAS-019   # set Versión Base Compras
  systemic_invariants:
    - "Todo PH/retimbrado registrado por Compras conserva fecha, resultado y vigencia consultables."
  composition_checks:
    - "Flujo: recepción con servicio PH → datos legales obligatorios → vigencia visible en la línea."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: reglas legales PH/retimbrado cohesivas en services/service_lines.py
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400       # models.py (~425 tras 014) ya en revisión:
  extraction_threshold_lines: 600   #   +4 columnas justificadas; extracción a
                                    #   módulo models/ propio sigue señalizada,
                                    #   NO en esta ronda (muy bajo 600).
  preferred_new_logic_locations:
    - services/service_lines.py
    - schemas/service_lines.py
    - frontend/components/ReceiptServiceLines.tsx
```

## Traceability

- Requirement: VISION §20 (PH y retimbrado: fecha, resultado, vigencia,
  referencia documental), §44 paso 8-9, §45 trazabilidad técnica.
  Roadmap aprobado lote 013..019.
- owner: Product Owner módulo compras (equipo SYSTUTOR OSS)
- approver: mantenedor humano responsable del squash/integración a main
- Commit:
- Deployment: migración 0015 en runtime del plugin commerce

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
