# A.SPEC [TMS-012] — Componer carga operativa por seriales que infieren producto

> Verdicto speccer: `ACCEPT_ONE`. Verdad independiente falsable: la carga operativa se arma
> seleccionando **seriales** (no productos); cada serial trae su cilindro y el cilindro infiere
> el producto. El flujo "en estado LOADING, guardar también confirma la carga y avanza la
> jornada" ya existe y se mantiene como invariante (no es truth nueva).

## WHY

El modal "Carga operativa" (`LoadModal`/`SessionLoadTab`) obliga a **elegir producto primero**
(botón "Agregar producto" → `ProductSearchDialog`) y luego capturar seriales **por producto**
(`LoadSerialsDialog` filtra cilindros con `product_id` obligatorio en `search` y `select`).
El serial no infiere producto: se elige producto, luego serial.

En legacy el operador escanea el **envase (serial)** y el producto es del cilindro. El sistema
OSS ya tiene ese vínculo (`LogisticsCylinder.product_id`/`gas_group_id`, `_product_matches_cylinder`).
El cambio: la carga se arma por **serial escaneado** y el producto se **infiere** del cilindro,
reduciendo pasos y alineando con la operación real.

## WHAT

Existe un comportamiento observable: en el modal de carga operativa, el operador escanea o
escribe un **serial** (sin elegir producto antes); el sistema resuelve el cilindro, infiere su
producto y agrega/actualiza la fila del plan con ese producto (cantidad planificada respetada).
El `product_id` deja de ser obligatorio en la búsqueda y selección de seriales cuando el serial
es suficiente para inferir el producto.

- `search` y `select` de seriales aceptan `product_id` **opcional**.
- Al buscar por serial, el resultado expone el producto inferido (para componer la fila del plan).
- Al seleccionar un serial, si no viene `product_id` se resuelve desde el cilindro.
- El modal usa captura de serial como acción primaria; el producto inferido llena la fila.

## SCOPE

- Backend: `search_load_serial_candidates` y `select_load_serial` con `product_id` opcional;
  inferir producto del cilindro cuando no viene.
- DTO backend: `product_id` optional en request de búsqueda/selección de seriales.
- Frontend: `SessionLoadTab` — acción primaria "Agregar serial" (captura sin producto previo);
  el serial seleccionado crea/actualiza la fila con producto inferido.
- Frontend: `LoadSerialsDialog` — busca serial sin `product_id` previo; devuelve producto inferido.
- Mantener (invariante): en `LOADING`, guardar llama `confirm_and_ready` (confirma + avanza).

## OUT OF SCOPE

- Confirmar/avanzar la jornada (ya existe; invariante).
- Cambiar el modelo `LogisticsCylinder` (el vínculo serial→producto ya existe).
- Materializar cilindros desde legacy (es otro trabajo; aquí se captura sobre cilindros existentes).
- Waybill/guía de remisión.
- Cambios de stock (esta rama no toca stock).

## CONTRACT

- Precondición: cilindro existe (resoluble por serial/barcode en la jornada/tenant).
- Postcondición: al seleccionar un serial sin `product_id`, se crea un
  `LogisticsLoadSerialAssignment` con `product_id` = producto inferido del cilindro
  (`product_id` o `gas_group_id`).
- `search` sin `product_id`: devuelve candidatos de cilindros por serial/barcode (igual filtro de
  disponibilidad), y cada resultado expone el producto inferido.
- Si el serial no resuelve cilindro → error/primero hay que registrarlo (mismo comportamiento).
- En `LOADING`, "Guardar y confirmar" confirma la carga y avanza (`READY_TO_DEPART`).

## INVARIANTS

```yaml
invariants:
  - "en LOADING, guardar también confirma la carga y avanza la jornada (no cambia)"
  - "el serial debe resolver un cilindro activo para poder seleccionarse"
  - "consector con product_id explícito sigue funcionando (compatibilidad)"
  - "no se toca stock ni se confirma fuera del estado permitido"
```

## VERIFICATION

- Backend unit/integración: `select_load_serial` sin `product_id` → assignment con producto del
  cilindro; con `product_id` → idéntico al comportamiento actual (compatibilidad I3).
- Backend unit: `search_load_serial_candidates` sin `product_id` → resultados con producto inferido.
- Backend unit negativo (C4/I2): `select_load_serial` con serial sin cilindro → error
  "Serial no encontrado"; serial de cilindro inactivo → error "no está activo"; cilindro fuera
  de los `LOAD_PLAN_COMPATIBLE_CYLINDER_STATES` → error de estado.
- Backend unit (I4): `select_load_serial` serial-first NO crea movimiento ni aplica stock
  (assert `lg_logistics_movements`/stock sin cambios); `confirm_and_ready` fuera de `LOADING`
  → error (no avanza en DRAFT/READY_TO_DEPART).
- Backend unit (I3 lado search): `search_load_serial_candidates` con `product_id` explícito
  mantiene el filtro actual (resultados limitados al producto) — mismatch queda `UNAVAILABLE`,
  NO error duro (contrato previo preservado).
- Frontend: build `apps/web` sin errores (tsc/vite).
- Manual/UI: escanear serial → fila del plan aparece con producto inferido; en LOADING,
  "Guardar y confirmar" → jornada pasa a READY_TO_DEPART.

Evidencia corrida (verifier ADD modo verify-run):
- `pytest apps/api/tests/test_tms012_serial_first.py` → 6 passed (C1/C2/C3/C4/I2-active/I4-stock).
- `pytest test_logistics_vehicle_sessions_v1.py::test_load_serial_search_shows_other_product_as_unavailable`
  → passed (I3 search compat restaurada).
- `pytest test_logistics_vehicle_sessions_v1.py::test_confirm_and_ready_*` (2 tests) → passed
  (C5/I1: guardar en LOADING confirma y avanza).
- `npx tsc --noEmit` (apps/web) → exit 0. `ruff check` + `pyright` → limpio.
- Fallos en `test_logistics_route_operation_effects.py` y `test_logistics_load_serial_customer_pickup.py`
  confirmados como PRE-EXISTENTES (setup drivers catalog roto) vía `git stash` — no causados
  por este cambio.

Cobertura vs verifier ADD:
- contract.C1 → select resuelve cilindro (test select con serial existente)
- contract.C2 → assignment producto inferido (test select sin product_id)
- contract.C3 → search sin product_id con producto inferido
- contract.C4 → test negativo serial sin cilindro
- contract.C5 → tests confirm_and_ready (2, passed)
- invariant.I1 → test confirm_and_ready en LOADING (passed)
- invariant.I2 → tests negativos: serial inactivo / estado no compatible
- invariant.I3 → test select con product_id + test search mismatch (ambos passed)
- invariant.I4 → test "no toca stock en select" (passed)

## ROLLBACK

- Reversible: revertir el cambio de DTO/servicio (product_id vuelve a ser obligatorio) y del modal
  (vuelve "Agregar producto"). No requiere migración ni limpieza de datos: los assignments ya
  creados conservan `product_id` explícito.

## Change Surface

```yaml
change_surface:
  allowed:
    - "editar plugins/logistics/backend/dto/load_serials.py"
    - "editar plugins/logistics/backend/services/load_serials.py"
    - "editar plugins/logistics/backend/routers/load_serials.py"
    - "editar plugins/logistics/frontend/components/vehicle-sessions/SessionLoadTab.tsx"
    - "editar plugins/logistics/frontend/components/vehicle-sessions/LoadSerialsDialog.tsx"
    - "editar plugins/logistics/frontend/api/load-serials.ts (tipos request opcional)"
  prohibited:
    - "tocar confirmación/avance de jornada (invariante)"
    - "cambiar modelo LogisticsCylinder o stock_bridge"
    - "generar waybill"
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - "respuesta de search/select de seriales (product_id opcional)"
    - "modal de carga operativa (flujo serial-first)"
  indirect:
    - "UI de carga de jornadas en todos los tenants del plugin logistics"
  must_not_affect:
    - "confirm_and_ready / confirm_load_plan (invariante)"
    - "ruta/operaciones ya confirmadas"
    - "stock OSS y legacy"
```

## Composition

```yaml
composition:
  requires_aspecs:
    - "TMS-010 (carga planificada DRAFT)"
    - "TMS-011 (seriales como metadato)"   # contexto: la carga hoy parte de salida legacy
  must_compose_with:
    - "logistics load_serials (endpoints search/select)"
  systemic_invariants:
    - "confirm_and_ready/confirm_load_plan no cambian"
  composition_checks:
    - "guardar en LOADING sigue confirmando y avanzando tras el cambio serial-first"
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/logistics/backend/services/load_serials.py"
    - "plugins/logistics/frontend/components/vehicle-sessions/SessionLoadTab.tsx"
```

## Traceability

- Requirement: carga operativa por seriales que infieren producto
- Commit: pendiente
- Deployment: rama TMS/`main` (afecta plugin logistics)

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now (6 tests serial-first + compat + negativos)
- [x] Invariants preserved
- [x] Verification passed (verifier ADD run)
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established