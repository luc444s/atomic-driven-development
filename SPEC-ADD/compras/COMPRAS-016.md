# A.SPEC COMPRAS-016 — Historial técnico del envase (consulta consolidada por serial)

> `risk: low` — Derivación §4.1 honesta: solo lectura (ninguna tabla nueva,
> ninguna migración, ninguna mutación de estado), sin dinero, sin stock, sin
> auth nuevo, cero escrituras `lg_*` (import de lectura ya es patrón de
> familia en `services/receipts.py`). El peor fallo posible es un display
> incorrecto — no corrompe datos. Blast radius: endpoint nuevo + página
> nueva. `mode: normal` per §4.2 (composición multi-fuente con pruebas
> cerradas; no candidato mechanical por cantidad de superficies).

## WHY

Con despachos (005), recepciones (007/008), diferencias (009), servicios
(014) y PH/retimbrados (015) registrados, la pregunta "¿qué le pasó a este
cilindro?" exige hoy recorrer cinco pantallas y cruzar a mano. VISION §40
(por cilindro: cuándo fue enviado, a qué proveedor, por qué, cuándo
regresó, qué servicio recibió, qué compra lo originó) y el paso restante de
§44 (historial logístico consultable) no tienen una consulta consolidada.

## WHAT

Una verdad nueva: **dado un serial, existe una consulta única que devuelve
su historial consolidado en dominio compras: despachos (005), recepciones
con sus diferencias (007/008/009), servicios realizados (014) y pruebas/
retimbrados con su vigencia legal (015).**

### Endpoint

- `GET /cylinders/{serial}/history` (REQUIRE_ORDER_READ; namespace propio
  del router de compras: `/api/v1/plugins/compras/purchase/cylinders/
  {serial}/history` — sin colisión con el plugin logistics):
  ```json
  {
    "cylinder_id": "...", "serial": "CIL-0001",
    "dispatches": [
      {"dispatch_id": "...", "order_id": "...", "supplier_id": "...",
       "dispatch_date": "...", "service_type": "LLENADO",
       "status": "EN_CUSTODIA|DEVUELTO", "returned_at": null}
    ],
    "receipts": [
      {"receipt_id": "...", "order_id": "...", "receipt_date": "...",
       "qty_accepted": 8, "qty_rejected": 0,
       "difference_type": "FALTANTE|null"}
    ],
    "services": [
      {"receipt_id": "...", "service_type": "PRUEBA_HIDROSTATICA",
       "cost": 12.5, "notes": "...", "test_date": "...",
       "next_test_date": "...", "result": "APROBADO",
       "document_ref": "...", "created_at": "..."}
    ]
  }
  ```
- Resolución del serial: SELECT sobre `lg_cylinders` (tenant + serial,
  lectura) → serial desconocido → `404` (falsable).
- Recepciones del serial: receipts cuyo `dispatch_id` corresponda a
  despachos que contienen el cilindro (`com_dispatch_cylinders`).
- Servicios: `com_receipt_service_lines` por `cylinder_id` (014/015).
- Orden: cada lista ordenada cronológicamente.

### Frontend

- Página nueva `pages/CylinderHistoryPage.tsx` (ruta nueva en
  `register.ts`, permiso `compras.order.read`): búsqueda por serial +
  secciones Despachos / Recepciones / Servicios con vigencia PH resaltada.
- Ninguna página existente crece (estructura nueva en archivo propio).

## SCOPE

- `plugins/commerce/purchase/backend/schemas/cylinder_history.py`
  (+ export en `schemas/__init__.py`): `CylinderHistoryRead` + secciones.
- `plugins/commerce/purchase/backend/services/cylinder_history.py`:
  `get_cylinder_history` (resolución serial + 3 consultas de solo lectura).
- `plugins/commerce/purchase/backend/routers/cylinder_history.py`
  (+ inclusión en `routers/__init__.py`): `GET /cylinders/{serial}/history`.
- Frontend: `pages/CylinderHistoryPage.tsx` (nuevo), `register.ts` (ruta),
  `types.ts`, `api.ts`.
- Tests: `apps/api/tests/test_compras_cylinder_history.py`.

## OUT OF SCOPE

- Cualquier escritura (el endpoint es de solo lectura; sin migración).
- Historial técnico del lado Logistics (movimientos lg_*, eventos de
  cilindro) — dominio de Logistics §32; solo se resuelve el serial.
- Reclamaciones/desviaciones por cilindro (claims son por orden).
- Exportación/PDF del historial.

## CONTRACT

Precondiciones:

- Serial existe en `lg_cylinders` del tenant (404 si no / cross-tenant).

Postcondiciones:

- Respuesta reproducible e idempotente para los mismos datos.
- Despachos incluye los de cualquier estado (PREPARADO no genera custodia,
  se lista igual con su estado).
- Ninguna escritura ocurre como efecto de la consulta.

## INVARIANTS

```yaml
invariants:
  - "Consulta de solo lectura: ninguna mutación en compras, logistics o stock (suites previas verdes)."
  - "Despachos/custodia (005/007/008), recepción (009), servicios (014) y PH (015) leídos tal cual están; la consulta no los altera."
  - "Toda lectura filtrada por tenant_id; serial de otro tenant → 404."
  - "Cero escrituras lg_* (solo SELECT para resolver serial)."
  - "Permisos existentes reutilizados (REQUIRE_ORDER_READ): ningún permiso nuevo."
  - "Suite compras previa completa verde; tsc --noEmit limpio."
```

## VERIFICATION

Tests nuevos (`pytest apps/api/tests/test_compras_cylinder_history.py -q`):

- `test_history_serial_unknown_404`.
- `test_history_lists_dispatches_with_status`.
- `test_history_lists_receipts_with_difference_type`.
- `test_history_lists_services_with_ph_legal_data`.
- `test_history_tenant_isolated_404`.
- `test_history_is_read_only_no_writes`.
- `test_history_ordered_chronologically`.

Regresión (composición): `pytest apps/api/tests/test_compras_plugin.py
apps/api/tests/test_compras_dispatch.py
apps/api/tests/test_compras_receipt_commercial.py
apps/api/tests/test_compras_receipt_cost.py
apps/api/tests/test_compras_invoice_reconciliation.py
apps/api/tests/test_compras_claims.py
apps/api/tests/test_compras_claim_derivation.py
apps/api/tests/test_compras_receipt_service_lines.py
apps/api/tests/test_compras_ph_restamp.py -q` — verde. `tsc --noEmit` limpio.

Auditorías explícitas (§7.1):

- `rg -n "db.add|db.delete|db.commit|update\\(|delete\\(" plugins/commerce/purchase/backend/services/cylinder_history.py`
  → SIN coincidencias (función pura de lectura).
- `rg -o "REQUIRE_[A-Z_]+" plugins/commerce/purchase/backend/routers | sort -u`
  antes vs después → mismo conjunto.

ROLLBACK no requiere downgrade físico (no hay migración): reverión =
revertir commit. VERIFICATION no incluye comando de downgrade (no aplica
§9.1 — nada que bajar); la reversibilidad queda demostrada por la ausencia
de superficie persistente.

Manual: despachar CIL-0001 → retornar parcial → recepción con servicio PH
→ `GET /cylinders/CIL-0001/history` → 1 despacho, 1 receipt, 1 servicio con
vigencia; página busca el serial y muestra las 3 secciones.

## ROLLBACK

Reversible trivialmente: revertir commit (endpoint + página nuevos; sin
migración, sin datos nuevos). No hay compensación pendiente: la consulta no
deja estado.

## Change Surface

```yaml
change_surface:
  allowed:
    - SPEC-ADD/compras/COMPRAS-016.md   # el contrato viaja con su integración
    - plugins/commerce/purchase/backend/schemas/cylinder_history.py
    - plugins/commerce/purchase/backend/schemas/__init__.py
    - plugins/commerce/purchase/backend/services/cylinder_history.py
    - plugins/commerce/purchase/backend/routers/cylinder_history.py
    - plugins/commerce/purchase/backend/routers/__init__.py
    - plugins/commerce/purchase/frontend/pages/CylinderHistoryPage.tsx
    - plugins/commerce/purchase/frontend/register.ts
    - plugins/commerce/purchase/frontend/types.ts
    - plugins/commerce/purchase/frontend/api.ts
    - apps/api/tests/test_compras_cylinder_history.py
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
    - compras.cylinder_history.read
  indirect:
    - compras.ui.historial # página nueva + ruta
  must_not_affect:
    - despachos/custodia (005/007/008)
    - recepción comercial (009) / costos (010) / conciliación (011)
    - reclamaciones (012/013)
    - servicios (014) / PH legal (015)
    - stock ledger / logistics lg_* (escrituras)
    - auth y permisos existentes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-005/007/008   # despachos por serial + receipts
    - COMPRAS-009           # diferencias de recepción
    - COMPRAS-014           # servicios por serial
    - COMPRAS-015           # legal data PH en el historial
  must_compose_with:
    - COMPRAS-019   # set Versión Base Compras
  systemic_invariants:
    - "Todo serial con actividad en compras tiene historial consultable en una sola consulta."
  composition_checks:
    - "Flujo: despachar → retornar → recepción con servicio PH → historial del serial muestra despacho, receipt y servicio con vigencia."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: consulta consolidada de solo lectura cohesiva en services/cylinder_history.py
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - services/cylinder_history.py
    - frontend/pages/CylinderHistoryPage.tsx   # archivo propio: PurchaseOrdersPage.tsx
                                               # (~596, umbral 600) NO crece.
```

## Traceability

- Requirement: VISION §40 (consultas por cilindro), §44 (historial
  pendiente del flujo de servicio técnico), §45 (trazabilidad estricta).
  Roadmap aprobado lote 013..019.
- owner: Product Owner módulo compras (equipo SYSTUTOR OSS)
- approver: mantenedor humano responsable del squash/integración a main
- Commit:
- Deployment: sin migración (solo código + página)

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
