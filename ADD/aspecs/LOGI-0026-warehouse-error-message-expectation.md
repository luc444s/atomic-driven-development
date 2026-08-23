# A.SPEC LOGI-0026 — Update warehouse resolution error message expectation

## WHY

El mensaje de error al crear un cilindro sin almacén resoluble cambió.
El test
`test_logistics_plugin.py::test_logistics_create_cylinder_entry_requires_resolved_active_warehouse`
espera `"almacen activo unico"` en el detalle; el backend responde
"No se pudo resolver un almacen principal para la operacion. Configura
un almacen FIXED activo en la sucursal."
(`plugins/logistics/backend/routers/cylinders.py:138`). Solo drift de
mensaje; la semántica (400 + orientación al operador) es equivalente.

## WHAT

El test aserta el mensaje vigente: `400` con detalle que mencione
"almacen principal" y "FIXED".

## SCOPE

- `apps/api/tests/test_logistics_plugin.py`: aserción del detalle en el
  test mencionado.

## OUT OF SCOPE

- Cambiar mensajes del backend.
- Lógica de resolución de almacén.

## CONTRACT

- Postcondición: `POST /cylinders` sin almacén resoluble responde 400 con
  detalle conteniendo "almacen principal".

## INVARIANTS

```yaml
invariants:
  - Status code 400 NO cambia.
  - Mensaje de routers/cylinders.py NO cambia.
```

## VERIFICATION

```
python -m pytest "apps/api/tests/test_logistics_plugin.py::test_logistics_create_cylinder_entry_requires_resolved_active_warehouse" -q
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
  direct: [test_logistics_create_cylinder_entry_requires_resolved_active_warehouse]
  indirect: []
  must_not_affect: []
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: [LOGI-0024, LOGI-0025]
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

- Requirement: investigación fallos suite logística (drift de mensaje)
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
