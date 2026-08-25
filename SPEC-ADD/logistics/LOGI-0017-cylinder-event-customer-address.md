# A.SPEC LOGI-0017 — Capture customer_address_id on customer cylinder events

## WHY

La trazabilidad de cilindros (`lg_cylinder_events`) distingue solo
`WAREHOUSE` / `VEHICLE` / `CUSTOMER` vía `location_type` + `customer_id`.
Un cliente puede tener múltiples direcciones (`crm_customer_addresses`), pero
el sistema no registra en qué dirección quedó el cilindro tras un envío o
recogida. No hay granularidad de dirección de cliente en la trazabilidad.

## WHAT

Se añade `customer_address_id` (FK nullable a `crm_customer_addresses.id`) a
`lg_cylinder_events`. Los eventos `CUSTOMER_DELIVERY` y `CUSTOMER_PICKUP`
(resueltos en parada de ruta) lo poblann con la dirección derivada
automáticamente del punto de entrega de la parada:
`route_stop → delivery_point → address_id`.

Es una sola verdad observable: tras confirmar una operación de ruta de
entrega/recojo, el último evento `CUSTOMER_*` del cilindro lleva la dirección
de cliente donde quedó/fue retirado el cilindro.

## SCOPE

- Nueva migration `plugins/logistics/migrations/056_cylinder_event_customer_address_v1.py`:
  columna `customer_address_id VARCHAR(36)` nullable + FK a `crm_customer_addresses(id)`
  + índice `(customer_address_id, occurred_at)`.
- `plugins/logistics/backend/models/operations.py` (`LogisticsCylinderEvent`):
  campo `customer_address_id`.
- `plugins/logistics/backend/services/cylinders.py` (`record_cylinder_event`):
  nuevo parámetro `customer_address_id: str | None = None`; se persiste.
- `plugins/logistics/backend/services/route_operation_confirmation.py`:
  - `_record_delivery_cylinder_events`: acepta `customer_address_id` y lo pasa a
    `record_cylinder_event`. Caller (confirmación de operación) lo resuelve desde
    `delivery_point.address_id`.
  - `_record_physical_pickup_events`: resuelve `customer_address_id` desde
    `operation.route_stop_id → LogisticsRouteStop.delivery_point_id →
    LogisticsDeliveryPoint.address_id` y lo pasa.
  - `_record_pickup_cylinder_events`: recibe `customer_address_id` desde el caller
    (`delivery_point.address_id`) y lo pasa.

## OUT OF SCOPE

- UI de selección manual de dirección (opción A: derivación automática).
- Visualización/resumen de la dirección (ver LOGI-0018).
- Cambios en CRM, stock bridge, transiciones de estado de cilindro.

## CONTRACT

- Postcondición: tras un evento `CUSTOMER_DELIVERY`/`CUSTOMER_PICKUP` originado
  en parada con `delivery_point` que tiene `address_id`, el evento queda con
  `customer_address_id == delivery_point.address_id`.
- Si la parada no tiene `delivery_point` o el `delivery_point` no tiene
  `address_id`, el evento queda con `customer_address_id = NULL`.
- `record_cylinder_event` mantiene su firma compatible (nuevo parámetro con
  default `None`); callers sin dirección (load_plans, TMS materialize, alta de
  cilindro) no la pasan → `NULL`.

## INVARIANTS

```yaml
invariants:
  - _VALID_TRANSITIONS de cylinders.py DEBE quedar idéntica.
  - Idempotencia de record_cylinder_event (dedup por cylinder_id+event_type+location_id+source_type+source_id) DEBE quedar idéntica.
  - location_type / location_id / customer_id mantienen su semántica actual.
  - Eventos existentes sin dirección deben quedar con customer_address_id = NULL y ser tratados como "sin dirección específica".
  - Resolución de ubicación actual (cylinder_location.py) NO debe cambiar.
```

## VERIFICATION

- Test unitario: parada de ruta con `delivery_point.address_id = A`; confirmar
  operación de entrega; asertar
  `get_last_location_event(cylinder).customer_address_id == A`.
- Test unitario: operación de recojo (`_record_physical_pickup_events`) con
  `delivery_point.address_id = A`; asertar evento `CUSTOMER_PICKUP` lleva `A`.
- Test migration: columna e índice existen; FK presente.
- Regresión: `test_cylinder_location_events.py` y `test_logistics_plugin.py`
  deben seguir pasando (sin cambio de comportamiento de ubicación).

## ROLLBACK

- Migration down: `DROP COLUMN customer_address_id` + drop FK + drop índice.
- Backend: revertir writer a no setear el campo; eliminar parámetro.
- No hay reversión física de eventos ya registrados; compensación = reconfirmar
  operación con dirección correcta genera nuevo evento (idempotencia no lo
  bloquea porque location_id = customer_id, no address_id). Auditoría forense
  vía `lg_cylinder_events`.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/migrations/056_cylinder_event_customer_address_v1.py
    - plugins/logistics/backend/models/operations.py
    - plugins/logistics/backend/services/cylinders.py
    - plugins/logistics/backend/services/route_operation_confirmation.py
  prohibited:
    - plugins/crm/**
    - plugins/logistics/frontend/**
    - plugins/logistics/backend/services/customer_cylinder_summary.py
    - plugins/logistics/backend/services/cylinder_location.py
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - cylinder event recording en entrega/recojo de ruta
  indirect:
    - customer_cylinder_summary (LOGI-0018 lo consumirá)
  must_not_affect:
    - warehouse location resolution
    - cylinder state transitions
    - stock bridge
    - crm
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - LOGI-0018 (visibilidad consume customer_address_id)
  systemic_invariants:
    - trazabilidad de cilindro sigue siendo resoluble sin la dirección cuando es NULL
  composition_checks:
    - tras LOGI-0017 + LOGI-0018, resumen de cilindros en cliente muestra dirección
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - route_operation_confirmation.py (resolución de address desde stop)
```

## Traceability

- Requirement: refinación trazabilidad cilindro por dirección de cliente (opción A: auto desde delivery_point)
- Commit: cdc2291 (junto a LOGI-0018)
- Deployment: pendiente (migración 056 se aplica vía migrate_plugins)

- Commit: `cdc2291`

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
- [x] Traceability established (commit pendiente)
