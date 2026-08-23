# A.SPEC LOGI-0022 — Update route-event context_type to renamed CUSTOMER

## WHY

El backend renombró los contextos manuales de ruta en `a8607c5`
(2026-08-05): `CUSTOMER_EMERGENCY` → `CUSTOMER`,
`WAREHOUSE_EMERGENCY` → `WAREHOUSE`
(`plugins/logistics/backend/services/route_operations.py:55`,
`VALID_CONTEXT_TYPES = {"STOP", "CUSTOMER", "WAREHOUSE"}`).
El test
`test_logistics_route_operation_effects.py::test_confirm_route_event_customer_emergency_is_idempotent_and_creates_incident`
aún envía `"context_type": "CUSTOMER_EMERGENCY"` → 400
"context_type no soportado".

## WHAT

El test usa el nombre vigente `CUSTOMER` (y aserta
`context_type == "CUSTOMER"` en la respuesta). La garantía probada es la
misma: evento fuera de parada con contexto de cliente es idempotente y crea
incidente.

## SCOPE

- `apps/api/tests/test_logistics_route_operation_effects.py`: payload y
  aserciones del test mencionado (`context_type`, `idempotency_key` puede
  mantenerse).

## OUT OF SCOPE

- Renombrar de vuelta el backend.
- Soporte para nombres legacy.

## CONTRACT

- Postcondición: `POST .../route-events/confirm` con
  `context_type="CUSTOMER"` + `customer_id` responde 200, es idempotente
  (segunda llamada devuelve misma operación) y crea un incidente OPEN.

## INVARIANTS

```yaml
invariants:
  - VALID_CONTEXT_TYPES del backend NO cambia.
  - Comportamiento de idempotencia e incidentes NO cambia.
```
#
# VERIFICATION

```
python -m pytest "apps/api/tests/test_logistics_route_operation_effects.py::test_confirm_route_event_customer_emergency_is_idempotent_and_creates_incident" -q
```

## ROLLBACK

Revertir diff del test.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/api/tests/test_logistics_route_operation_effects.py
  prohibited:
    - plugins/logistics/backend/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - test_confirm_route_event_customer_emergency_is_idempotent_and_creates_incident
  indirect: []
  must_not_affect: []
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: [LOGI-0019, LOGI-0020, LOGI-0021]
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

- Requirement: investigación fallos suite logística (causa context_type)
- Commit: 7823ab9

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
