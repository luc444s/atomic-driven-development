# A.SPEC LOGI-0031 — Retire legacy route-loads segments from plugin tests

## WHY

`test_logistics_plugin.py` ejercita el flujo legacy de carga-por-ruta en
2 tests: `test_logistics_plugin_operations_flow`
(`/loads/bulk` + `/loads/confirm` + transiciones a `CARGA_EN_VEHICULO`/
`EN_RUTA` sin sesión — el flujo roto que LOGI-0030 elimina) y
`test_logistics_plugin_spec_0014_flow` (`POST /loads`,
`/loads/weight-summary`, `/reports/load-summary`). Con LOGI-0030 esos
endpoints desaparecen; los segmentos deben retirarse. La cobertura real
del ciclo operativo (jornada: loading → load-plan → confirm-and-ready →
depart) ya vive completa en `test_logistics_vehicle_sessions_v1.py`.

## WHAT

Los 2 tests quedan ejercitando únicamente superficies vigentes:
`operations_flow` conserva almacén, delivery-point, orden, cilindro,
paradas y agenda; pierde el tramo carga-por-ruta/salida legacy.
`spec_0014_flow` pierde el bloque `/loads` + reportes de carga.

## SCOPE

- `apps/api/tests/test_logistics_plugin.py`:
  - `test_logistics_plugin_operations_flow`: quitar bulk-load, confirm,
    aserciones de estado por flujo legacy y el arranque de ruta legacy
    si depende de cargas (decidir en ejecución; si `/routes/{id}/start`
    funciona sin cargas, se conserva).
  - `test_logistics_plugin_spec_0014_flow`: quitar `POST /loads`,
    `/loads/weight-summary`, `/reports/load-summary`.
  - Renombrar/aserciones para reflejar lo que cada test sigue probando.

## OUT OF SCOPE

- Reescribir segmentos al flujo de jornadas (cubierto por v1 suite).
- Cambios backend (LOGI-0030).

## CONTRACT

- Postcondición: ambos tests pasan contra la API post-LOGI-0030 sin
  referencias a `/loads*` ni `/reports/load-summary`; sin huecos de
  cobertura nueva (nada que antes se probara y ahora quede sin prueba
  fuera del flujo eliminado).

## INVARIANTS

```yaml
invariants:
  - Ninguna aserción de superficies vigentes se elimina.
  - Cobertura de jornada permanece en test_logistics_vehicle_sessions_v1.py.
```

## VERIFICATION

```
python -m pytest apps/api/tests/test_logistics_plugin.py -q
```

Esperado: 0 fallos, 0 referencias a endpoints eliminados.

## ROLLBACK

Revertir diff del test.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/api/tests/test_logistics_plugin.py
  prohibited:
    - plugins/logistics/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - test_logistics_plugin_operations_flow
    - test_logistics_plugin_spec_0014_flow
  indirect: []
  must_not_affect: []
```

## Composition

```yaml
composition:
  requires_aspecs: [LOGI-0030]
  must_compose_with: [LOGI-0030]
  systemic_invariants:
    - suite logistics completa verde tras la composición
  composition_checks:
    - pytest conjunto plugin.py + vehicle_sessions_v1 + route_control_v1 + route_operation_effects + customer_cylinder_summary + cylinder_location_events
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

- Requirement: remoción del flujo legacy (LOGI-0030); usuario confirma "todo vive en jornadas"
- Commit: pendiente

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
