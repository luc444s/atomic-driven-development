# A.SPEC LOGI-0028 — Seed location event for serialized summary movement fixture

## WHY

El modelo de verdad de ubicación cambió: para cilindros fuera de tránsito,
`resolve_cylinder_current_warehouse`
(`plugins/logistics/backend/services/cylinder_location.py:85-105`) usa el
último EVENTO de ubicación (`WAREHOUSE_IN`, etc.) y solo como fallback el
texto `location`; los movements son fuente de verdad únicamente en
tránsito (`CARGA_EN_VEHICULO`/`EN_RUTA`).
`test_logistics_plugin.py::test_logistics_serialized_cylinder_summary_by_warehouse`
siembra `RS-000006` (LLENADO_OK, `location=None`) contando con un movement
IC para asignarlo al almacén → hoy queda excluido y el summary devuelve
2 en vez de 3.

## WHAT

El fixture siembra para `RS-000006` un evento `WAREHOUSE_IN`
(`warehouse_id` del almacén del test) vía `record_cylinder_event`,
reflejando cómo llega realmente un cilindro a un almacén bajo el modelo
vigente. El summary devuelve 3/1 como espera el test.

## SCOPE

- `apps/api/tests/test_logistics_plugin.py`: en
  `test_logistics_serialized_cylinder_summary_by_warehouse`, registrar
  evento `WAREHOUSE_IN` para el cilindro de movimiento. Aserciones no
  cambian.

## OUT OF SCOPE

- Cambiar `resolve_cylinder_current_warehouse`.
- Reintroducir movements como fuente para estados no-tránsito.

## CONTRACT

- Postcondición: cilindro LLENADO_OK con último evento `WAREHOUSE_IN`
  hacia almacén W es contado por
  `/cylinders/serialized-summary?warehouse_id=W`.

## INVARIANTS

```yaml
invariants:
  - resolve_cylinder_current_warehouse NO cambia.
  - Prioridad eventos > texto location > (transito: movements) NO cambia.
  - Aserciones del summary (3 product_a / 1 product_b) NO cambian.
```

## VERIFICATION

```
python -m pytest "apps/api/tests/test_logistics_plugin.py::test_logistics_serialized_cylinder_summary_by_warehouse" -q
```

## ROLLBACK

Revertir diff del test.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/api/tests/test_logistics_plugin.py
  prohibited:
    - plugins/logistics/backend/**
```

## Blast Radius

```yaml
blast_radius:
  direct: [test_logistics_serialized_cylinder_summary_by_warehouse]
  indirect: []
  must_not_affect:
    - cylinder_location resolution
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: [LOGI-0024, LOGI-0025, LOGI-0026, LOGI-0027]
  systemic_invariants: []
  composition_checks:
    - test_logistics_plugin.py completo verde tras LOGI-0024..0028
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

- Requirement: investigación fallos suite logística (truth-model eventos)
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
