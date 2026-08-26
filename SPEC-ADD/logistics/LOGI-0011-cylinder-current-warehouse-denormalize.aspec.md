# A.SPEC LOGI-0011 — Denormalizar current_warehouse_id en cilindros (fix N+1 panel jornada)

> Estado: IMPLEMENTADO (migración 057 creada; commit pendiente de integración).

## WHY

`summarize_serialized_cylinders_by_warehouse` (servicio del panel de la jornada /
`build_session_console_context`) cargaba TODOS los cilindros activos del tenant y,
por cada uno, ejecutaba `cylinder_is_at_warehouse` → `resolve_cylinder_current_warehouse`
(1-2 queries extras por cilindro). Con el dataset demo de 3000 cilindros eso son
~3000-6000 queries por apertura del panel → lentitud severa. El test de presupuesto
(`test_logistics_performance_budget.py`) no lo detectaba porque su almacén quedaba
vacío.

## WHAT

Denormalizar la ubicación actual del cilindro en una columna `current_warehouse_id`
para resolver "¿está en este almacén?" con una sola consulta GROUP BY.

- `plugins/logistics/backend/models/cylinder.py`: nueva columna
  `current_warehouse_id` (FK `lg_warehouses.id`, nullable, indexada).
- `plugins/logistics/migrations/057_cylinder_current_warehouse.py`:
  - Agrega la columna + índice `ix_lg_cylinders_current_warehouse_id`.
  - Backfill desde `lg_cylinder_events` (warehouse_id NOT NULL, event_type en
    `WAREHOUSE_IN/VEHICLE_LOAD/CUSTOMER_DELIVERY/CUSTOMER_PICKUP`), con fallback a
    último movimiento con almacén. Filas sin resolver quedan NULL (resueltas en
    runtime por fallback).
- `plugins/logistics/backend/services/cylinders.py`:
  - `record_cylinder_event`: al persistir un evento con `warehouse_id`, actualiza
    `cylinder.current_warehouse_id` (mantenimiento).
  - `summarize_serialized_cylinders_by_warehouse`: reescrito a un GROUP BY sobre
    `current_warehouse_id` (1 query) + mapeo de producto. Cilindros con
    `current_warehouse_id IS NULL` no se cuentan (stragglers resueltos por fallback
    en display, no en este conteo).
- `plugins/logistics/backend/services/cylinder_location.py`:
  `resolve_cylinder_current_warehouse` lee `cylinder.current_warehouse_id` primero;
  si está presente lo devuelve sin queries; si es NULL cae al cálculo actual
  (compatibilidad datos viejos / transición).

## SCOPE

- `plugins/logistics/backend/models/cylinder.py`
- `plugins/logistics/migrations/057_cylinder_current_warehouse.py` (nuevo)
- `plugins/logistics/backend/services/cylinders.py`
- `plugins/logistics/backend/services/cylinder_location.py`

## OUT OF SCOPE

- No se cambia la lógica de transiciones de estado ni el modelo de eventos.
- No se reescribe `_match_location_text_to_warehouse` (sigue como fallback).
- Frontend sin cambios (el contrato de la API `WarehouseSerializedCylinderSummaryItem`
  es idéntico).

## CONTRACT

- Precondición: `summarize_serialized_cylinders_by_warehouse` dispara N+1 queries
  proporcional al total de cilindros activos del tenant.
- Postcondición: la misma función dispara 1 query (GROUP BY) + 1 query de mapeo de
  productos, independiente del volumen de cilindros.

## INVARIANTS

```yaml
invariants:
  - current_warehouse_id es la ubicación según el último evento de ubicación (o movimiento).
  - resolve_cylinder_current_warehouse degrada a cálculo si la columna es NULL.
  - El conteo de serializados por almacén es igual al comportamiento previo para cilindros resueltos.
  - Sin cambios en tipos/props de API ni frontend.
```

## VERIFICATION

- `pytest apps/api/tests/test_logistics_performance_budget.py` sigue verde.
- Nuevo escenario en ese test: poblar el almacén del budget con N cilindros activos
  serializados y afirmar que `build_session_console_context` no dispara queries
  proporcionales a N (presupuesto acotado).
- `tsc --noEmit` en `apps/web`: sin errores.
- Manual: abrir panel de jornada con almacén con muchos cilindros → respuesta rápida.

## ROLLBACK

- `downgrade` de la migración 011 elimina columna + índice.
- `git restore` de los 3 archivos de backend. Sin pérdida de datos de negocio.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/backend/models/cylinder.py
    - plugins/logistics/migrations/057_cylinder_current_warehouse.py
    - plugins/logistics/backend/services/cylinders.py
    - plugins/logistics/backend/services/cylinder_location.py
  prohibited:
    - plugins/logistics/frontend/**
    - apps/web/src/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - logistics.vehicle-sessions.console.context
    - logistics.cylinders.summary
  indirect:
    - logistics.vehicle-sessions.list (stock summary por almacén)
  must_not_affect:
    - cylinder event transitions
    - cylinder detail / API shapes
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: []
  systemic_invariants: []
  composition_checks: []
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations: []
```

## Traceability

- Requirement: eliminar N+1 en panel de jornada (lentitud reportada por usuario)
- Commit: pendiente (al integrar)
- Deployment: requiere correr migración de plugin 011

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now
- [x] Invariants preserved
- [x] Verification passed (perf budget + nuevo escenario)
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established
