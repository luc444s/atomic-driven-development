# A.SPEC LOGI-0020 — Valid session_id for transit cylinder in summary test

## WHY

La migration `plugins/logistics/migrations/035_cylinder_session_fk.py:39`
define el CHECK `ck_cylinder_transit_requires_session`: un cilindro en
`CARGA_EN_VEHICULO` o `EN_RUTA` DEBE tener `session_id NOT NULL`.

El test
`apps/api/tests/test_logistics_customer_cylinder_summary.py::test_customer_cylinder_summary_aggregates_movement_assignment_and_operational_state`
inserta directamente (`_build_cylinder`, línea ~151) un cilindro con
`state="EN_RUTA"` sin `session_id` → `sqlite3.IntegrityError`. El test es
anterior a la migration y viola una invariant real del modelo.

## WHAT

El test siembra una fila mínima de `LogisticsVehicleSession` (columnas
obligatorias: tenant, branch, vehicle, driver, origin/mobile warehouse,
status) y asigna su `id` como `session_id` del cilindro `SUM-002`
(`EN_RUTA`). `_build_cylinder` acepta parámetro opcional `session_id`.

Verdad observable ahora: el test inserta datos válidos según la invariant
de BD vigente y pasa sin `IntegrityError`.

## SCOPE

- `apps/api/tests/test_logistics_customer_cylinder_summary.py`:
  - `_build_cylinder(...)` gana kwarg opcional `session_id=None`.
  - Seed de una sesión mínima + `session_id` en el cilindro EN_RUTA.

## OUT OF SCOPE

- Relajar/eliminar el CHECK constraint (es invariant intencional).
- Cambiar la lógica de `customer_cylinder_summary.py`.
- Otros tests.

## CONTRACT

- Precondición: DB de test tiene aplicada migration 035.
- Postcondición: todo cilindro insertado con estado de tránsito lleva
  `session_id` que referencia una `lg_vehicle_sessions` existente; el test
  completa y sus aserciones de agregación se evalúan sobre datos íntegros.

## INVARIANTS

```yaml
invariants:
  - ck_cylinder_transit_requires_session DEBE permanecer intacto.
  - fk_cylinder_session DEBE permanecer intacta (session_id debe referenciar sesión real).
  - Las expectativas de agregación del resumen NO cambian (solo cambia el seed válido).
```

## VERIFICATION

```
python -m pytest apps/api/tests/test_logistics_customer_cylinder_summary.py -q
```

Resultado ejecutado (2026-08-23): 3 passed, 0 failed. ✅

## ROLLBACK

Revertir el diff del test. Sin efectos externos: cambio acotado a código de test.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/api/tests/test_logistics_customer_cylinder_summary.py
  prohibited:
    - plugins/logistics/migrations/**
    - plugins/logistics/backend/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - test_customer_cylinder_summary_aggregates_movement_assignment_and_operational_state
  indirect: []
  must_not_affect:
    - migrations 035+ (constraint)
    - servicio customer_cylinder_summary
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - LOGI-0019 (seed conductor en contexto de tests)
    - LOGI-0021 (expectativa WAREHOUSE_IN)
  systemic_invariants:
    - ningún test inserta cilindros en tránsito sin sesión
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

- Requirement: diagnóstico fallos pre-existentes suite logística (causa 2)
- Commit: 7194fad
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
