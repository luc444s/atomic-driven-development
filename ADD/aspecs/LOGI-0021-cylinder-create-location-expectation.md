# A.SPEC LOGI-0021 — Update location expectation after WAREHOUSE_IN on cylinder create

## WHY

`create_cylinder` registra un evento `WAREHOUSE_IN` al dar de alta un
cilindro (`plugins/logistics/backend/services/cylinders.py:413-417`),
comportamiento introducido por la trazabilidad de ubicaciones. El test
`apps/api/tests/test_cylinder_location_events.py::test_cylinder_events_endpoint`
aún espera que `GET /cylinders/{id}/location` devuelva
`location_type = None` justo tras el alta → falla con
`assert 'WAREHOUSE' is None`. El test está desactualizado; el comportamiento
del sistema es el correcto para trazabilidad.

## WHAT

El test actualiza sus expectativas post-alta: la ubicación del cilindro es
`WAREHOUSE` (almacén de alta) en lugar de vacía. Las verificaciones de que
los endpoints `/events` y `/location` responden 200 se mantienen; se agrega
la aserción del primer evento `WAREHOUSE_IN` visible en `/events`.

Verdad observable ahora: el test documenta y verifica el contrato real —
alta de cilindro produce ubicación inicial WAREHOUSE consultable.

## SCOPE

- `apps/api/tests/test_cylinder_location_events.py`:
  - aserciones finales: `location["location_type"] == "WAREHOUSE"` y
    `location_id` resuelto al almacén de alta (no `None`).
  - aserción de evento `WAREHOUSE_IN` presente en `/events` tras alta.

## OUT OF SCOPE

- Cambiar `create_cylinder` ni `cylinder_location.py`.
- Eventos posteriores (entregas, cargas).

## CONTRACT

- Precondición: plugin logística habilitado con migrations 007..056 aplicadas.
- Postcondición: tras `POST /cylinders` exitoso, `/location` devuelve
  `location_type="WAREHOUSE"` con `location_id` no nulo, y `/events`
  incluye un evento `WAREHOUSE_IN`.

## INVARIANTS

```yaml
invariants:
  - Semántica de resolución de ubicación (get_last_location_event) NO cambia.
  - Endpoints /events y /location siguen respondiendo 200.
  - Ningún código de producción cambia.
```

## VERIFICATION

```
python -m pytest apps/api/tests/test_cylinder_location_events.py -q
```

Resultado ejecutado (2026-08-23): 1 passed, 0 failed. ✅

## ROLLBACK

Revertir el diff del test. Sin efectos externos.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/api/tests/test_cylinder_location_events.py
  prohibited:
    - plugins/logistics/backend/**
    - plugins/logistics/migrations/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - test_cylinder_events_endpoint
  indirect: []
  must_not_affect:
    - create_cylinder
    - cylinder_location resolution
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - LOGI-0019 (seed conductor)
    - LOGI-0020 (session_id en tránsito)
  systemic_invariants:
    - suite logistics verde salvo los 6 fallos propios de test_logistics_plugin.py (fuera de este set)
  composition_checks:
    - pytest conjunto de los archivos afectados por LOGI-0019/20/21 en verde
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

- Requirement: diagnóstico fallos pre-existentes suite logística (causa 3)
- Commit: e17986c
- Deployment: N/A (tests)

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
- [x] Traceability established
