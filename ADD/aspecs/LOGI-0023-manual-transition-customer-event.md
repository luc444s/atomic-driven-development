# A.SPEC LOGI-0023 — Record mirror location event on manual transition to customer states

## WHY

`transition_cylinder`
(`plugins/logistics/backend/services/cylinders.py:557`) cambia
`current_state` pero NO registra eventos de ubicación
(`lg_cylinder_events`). La máquina de transiciones de ubicación
(`_VALID_TRANSITIONS`, `cylinders.py:1475`) usa el último evento como
verdad física. Resultado: un cilindro llevado manualmente a
`EN_CLIENTE_LLENO/VACIO` queda con último evento `WAREHOUSE_IN`; el
recojo posterior en ruta intenta `CUSTOMER_PICKUP` y falla con
"Transición inválida: WAREHOUSE → CUSTOMER_PICKUP"
(`cylinders.py:1508`). El estado dice cliente, la trazabilidad dice
almacén — se contradicen. Gap alcanzable en producción vía transición
manual + recojo en ruta.

Rompe 2 tests: `test_pickup_serialized_route_scan_uses_customer_empty_cylinders`,
`test_reconfirm_load_skips_cylinder_already_in_vehicle`.

## WHAT

Una sola transición observable: la corrección manual hacia estados de
cliente deja trazabilidad consistente —

1. `_VALID_TRANSITIONS` acepta `CUSTOMER_DELIVERY` también desde
   `WAREHOUSE` y desde `CUSTOMER` (la corrección manual ocurre fuera del
   flujo vehículo→cliente normal y puede reiterarse entre estados
   cliente). Filas restantes intactas.
2. `transition_cylinder`, al mover a `EN_CLIENTE_LLENO`/`EN_CLIENTE_VACIO`
   con `customer_id` presente, registra evento espejo `CUSTOMER_DELIVERY`
   (`location_type=CUSTOMER`, `location_id=customer_id`,
   `source_type="MANUAL_TRANSITION"`, `source_id=None`) atómicamente con
   el cambio de estado.

Verdad falsable ahora: tras transición manual a cliente, el último
evento de ubicación es `CUSTOMER_DELIVERY` y el recojo en ruta procede;
transiciones manuales reiteradas son idempotentes vía dedup.

## SCOPE

- `plugins/logistics/backend/services/cylinders.py`:
  - Delta exacto de `_VALID_TRANSITIONS`:
    - `"WAREHOUSE"`: `{"VEHICLE_LOAD"}` → `{"VEHICLE_LOAD", "CUSTOMER_DELIVERY"}`
    - `"CUSTOMER"`: `{"CUSTOMER_PICKUP", "VEHICLE_LOAD", "WAREHOUSE_IN"}`
      → `+ {"CUSTOMER_DELIVERY"}`
    - `"VEHICLE"` y `None`: intactos.
  - En `transition_cylinder`: tras validar y persistir el nuevo estado,
    llamar `record_cylinder_event(...)` para destinos `EN_CLIENTE_*`;
    cualquier excepción propaga → rollback completo de estado + evento
    (misma transacción).
- Tests afectados quedan verdes sin cambios adicionales (verificado:
  ambos tests ya transicionan manualmente con `customer_id`; el bloqueo
  era exclusivamente la ausencia del evento).

## OUT OF SCOPE

- Eventos espejo para destinos no-cliente (`CARGA_EN_VEHICULO`,
  `EN_RUTA`, `EN_ALMACEN_*`) — specs futuras.
- Cambiar orden validación/dedup dentro de `record_cylinder_event`.
- Flujo por route operations (ya registra sus propios eventos).

## CONTRACT

- Precondiciones: cilindro existente; `to_state` ∈
  `{EN_CLIENTE_LLENO, EN_CLIENTE_VACIO}`; `customer_id` presente.
- Postcondición 1: existe evento `CUSTOMER_DELIVERY` con
  `location_type=CUSTOMER`, `location_id=customer_id`,
  `source_type=MANUAL_TRANSITION`.
- Postcondición 2 (atomicidad): si `record_cylinder_event` falla, la
  transición de estado NO se persiste (400 al caller, sin medio-cambio).
- Postcondición 3: confirmar operación PICKUP sobre ese cilindro responde
  200 y registra `CUSTOMER_PICKUP`.
- Repetir la misma transición manual no duplica eventos (dedup por
  cylinder+event_type+location_id+source_type+source_id).
- Transición a estado cliente sin `customer_id`: comportamiento actual
  se mantiene (sin evento).

## INVARIANTS

```yaml
invariants:
  - _VALID_TRANSITIONS: ÚNICO delta permitido es agregar CUSTOMER_DELIVERY a WAREHOUSE y CUSTOMER. Filas None/VEHICLE intactas.
  - Orden validación→dedup dentro de record_cylinder_event intacto.
  - Flujos de ruta (route_operation_confirmation) intactos: sus orígenes de evento siguen siendo VEHICLE/CUSTOMer válidos bajo la máquina extendida.
  - ensure_transition_allowed, state log, auditoría y emisión de eventos existentes intactos.
  - Ningún endpoint cambia de contrato salvo dejar de fallar en el escenario del gap.
```

## VERIFICATION

```
python -m pytest "apps/api/tests/test_logistics_route_operation_effects.py::test_pickup_serialized_route_scan_uses_customer_empty_cylinders" "apps/api/tests/test_logistics_route_operation_effects.py::test_reconfirm_load_skips_cylinder_already_in_vehicle" -q
python -m pytest apps/api/tests/test_logistics_route_control_v1.py apps/api/tests/test_logistics_vehicle_sessions_v1.py apps/api/tests/test_logistics_customer_cylinder_summary.py apps/api/tests/test_cylinder_location_events.py apps/api/tests/test_logistics_plugin.py::test_logistics_serialized_cylinder_summary_by_warehouse -q
```

Esperado: 0 fallos en ambas corridas (regresión incluida).

## ROLLBACK

Revertir diff de `transition_cylinder` + `_VALID_TRANSITIONS`.
Compensación: repetir la transición manual regenera el evento (dedup
evita duplicados). Auditoría forense via `lg_cylinder_events`
(source_type=MANUAL_TRANSITION) + audit log existente.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/backend/services/cylinders.py
  prohibited:
    - plugins/logistics/backend/routers/**
    - plugins/crm/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - transition_cylinder (endpoint /cylinders/{id}/transition)
  indirect:
    - cylinder_location resolution (nuevos eventos CUSTOMER visibles)
    - customer_cylinder_summary / LOGI-0018 visibility
  must_not_affect:
    - flujos de ruta (route_operation_confirmation registra sus eventos)
    - stock bridge
    - TMS materialize
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: [LOGI-0017]
  systemic_invariants:
    - current_state y último evento de ubicación nunca contradicen para estados de cliente
    - la extensión de la máquina no habilita saltos ilegítimos en flujos automáticos (solo la transición manual consume los nuevos orígenes)
  composition_checks:
    - suite route_operation_effects + route_control + vehicle_sessions verde
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

- Requirement: investigación fallos suite logística (gap real pickup); revisión speccer (verdict ACCEPT_ONE con revisiones)
- Commit: b5192f0

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now
- [x] Invariants preserved
- [x] Verification passed
- [x] Rollback / compensation is honest
- [x] No unrelated changes
- [x] Traceability established

## Execution Result

- Ejecutada y verificada 2026-08-23; ver memoria de sesión para detalle.
