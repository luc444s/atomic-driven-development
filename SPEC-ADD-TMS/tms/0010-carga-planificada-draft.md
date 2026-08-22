# A.SPEC [TMS-010] — Materializar carga planificada DRAFT en la jornada viva

> Verdicto speccer: ACCEPT_ONE. Verdad independiente falsable: la sesión viva materializada
> por el sync gana una carga planificada (`lg_load_plans`) DRAFT armada desde los items de la
> salida legacy, sin confirmar nada ni tocar stock.

## WHY

La jornada viva que el sync crea (TMS-008) nace **vacía**: `LogisticsVehicleSession` DRAFT sin
carga. En legacy, al grabar la salida la carga (items con `StkEgreso`/pesito) queda incorporada
al documento. Para que la jornada OSS herede la carga de forma fiel al legacy —sin confirmar
ni tocar stock— se materializa un **load plan DRAFT** desde los items de la salida.

## WHAT

Existe un comportamiento observable: `sync_salidas_hoy`, al crear/reutilizar la sesión viva de
una salida con placa+DNI resueltos, ejecuta `upsert_load_plan()` (DRAFT) con los items de la
salida: `product_id` resuelto por `Product.legacy_id`, `planned_quantity = pesito`,
`source_warehouse_id` = almacén origen. La sesión queda con `planned_weight_kg` calculado.
Nunca se confirma el plan ni se avanza la sesión.

## SCOPE

- `upsert_load_plan()` desde items de la salida en `_materialize_live_session`.
- Resolución producto: `cod_producto` legacy → `Product.legacy_id`.
- `planned_quantity` = `pesito` del item; `source_warehouse_id` = warehouse del almacén.
- Idempotencia: el plan se re-usa (upsert por sesión) y no duplica filas.

## OUT OF SCOPE

- Confirmar el plan ni cambiar status de la sesión.
- Seriales en el plan (es TMS-011, tiene su propia adición).
- `LogisticsCylinder` / asignaciones de seriales.
- Waybill / guía de remisión (fuera de rama).
- Stock (no `confirm_load_plan`, no `apply_stock_for_movement`).

## CONTRACT

- Postcondición: por cada salida del día con placa+DNI, la sesión viva tiene un `lg_load_plans`
  DRAFT con items que reflejan la salida (producto por `legacy_id`, cantidad=pesito) y
  `lg_vehicle_sessions.planned_weight_kg` calculado.
- Precondición: existe la sesión viva (TMS-008).
- Idempotente: re-ejecutar sync no duplica plan ni items (upsert por sesión).
- Salida sin placa o sin DNI → sin sesión y sin plan.

## INVARIANTS

```yaml
invariants:
  - "load plan SOLO si existe sesión viva (placa+DNI resueltos)"
  - "no confirm_load_plan"
  - "no cambio de status de sesión"
  - "no stock_bridge"
  - "upsert_load_plan es idempotente por sesión"
```

## VERIFICATION

- Test OSS: mock salida con items → sesión creada + `lg_load_plans` 1 + items con
  `legacy_id`→product y cantidades=pesito; `lg_vehicle_sessions.planned_weight_kg` > 0.
- Test idempotencia: re-corrrer sync → mismo load plan/session (counts estables).
- Test sin placa → sin sesión ni plan.
- E2E real: salida legacy → verificar `lg_load_plans` poblado y sesión con peso planificado.

## ROLLBACK

- Reversible: borrar `lg_load_plans`/items no afecta legacy, stock ni snapshot. Se regenera
  re-coriendo el sync.

## Change Surface

```yaml
change_surface:
  allowed:
    - "editar plugins/tms/backend/services/sync.py"
    - "usar upsert_load_plan de plugins/logistics/backend/services/load_plans.py"
    - "resolver Product por legacy_id"
  prohibited:
    - "confirmar/avanzar la sesión"
    - "tocar stock_bridge"
    - "crear cilindros ni assignments"
    - "generar waybill"
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - "filas en lg_load_plans / lg_load_plan_items"
    - "planned_weight_kg en lg_vehicle_sessions"
  indirect:
    - "sesión gana carga visible en UI logistics"
  must_not_affect:
    - "stock OSS y legacy"
    - "lg_cylinders / asignaciones"
    - "tms_jornada (snapshot)"
```

## Composition

```yaml
composition:
  requires_aspecs:
    - "TMS-008 (sesión viva)"
  must_compose_with:
    - "TMS-011 (seriales nominales, adición sobre el plan)"
  systemic_invariants: []
  composition_checks:
    - "una salida re-materializada no duplica plan"
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/tms/backend/services/sync.py"
```

## Traceability

- Requirement: jornada viva con carga planificada
- Commit: pendiente
- Deployment: rama TMS

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now (tests: sesión gana lg_load_plans DRAFT)
- [x] Invariants preserved
- [x] Verification passed (27 tests + ruff; enrich de items vía get_salida)
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established