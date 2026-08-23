# A.SPEC LOGI-0024 — Bootstrap test verifies ensure_logistics_catalogs directly

## WHY

`test_bootstrap_restores_missing_logistics_transition_catalog` premisa que
`bootstrap_app_state` restaura el catálogo de transiciones borrado.
Falso bajo arquitectura vigente: `bootstrap_app_state`
(`vendor/systutor-core/src/systutor/core/lifecycle.py:27`) solo sincroniza
registro, corre migrations y carga el runtime — NO re-ejecuta hooks
`on_enable`. El restore vive exclusivamente en `ensure_logistics_catalogs`
(`plugins/logistics/backend/services/catalog_bootstrap.py:18`), invocado
por los hooks `on_install`/`on_enable` del plugin (`plugin.py:139-153`).
Verificado: mismo comportamiento pre-extracción del kernel.

## WHAT

El test verifica la garantía real y existente hoy: llamar
`ensure_logistics_catalogs(db)` repuebla una transición faltante
(`EN_CLIENTE_VACIO → EN_RUTA`, descripción "Recojo desde cliente")
sin duplicar las existentes.

## SCOPE

- `apps/api/tests/test_logistics_plugin.py`: reescribir
  `test_bootstrap_restores_missing_logistics_transition_catalog` para:
  1. borrar la transición,
  2. invocar `ensure_logistics_catalogs(db)` sobre la sesión,
  3. asertar restauración con descripción exacta,
  4. asertar idempotencia (segunda llamada no duplica).

## OUT OF SCOPE

- Cambiar el kernel (`vendor/systutor-core`) para re-ejecutar hooks en boot.
- Cambiar `bootstrap_app_state`.

## CONTRACT

- Postcondición: tras eliminar `(EN_CLIENTE_VACIO, EN_RUTA)` de
  `lg_state_transitions` y ejecutar `ensure_logistics_catalogs`, existe
  exactamente 1 fila con `description="Recojo desde cliente"`; segunda
  ejecución no agrega filas.

## INVARIANTS

```yaml
invariants:
  - TRANSITION_DEFINITIONS (catalog.py) NO cambia.
  - Hooks on_install/on_enable del plugin NO cambian.
  - vendor/systutor-core NO cambia.
```

## VERIFICATION

```
python -m pytest "apps/api/tests/test_logistics_plugin.py::test_bootstrap_restores_missing_logistics_transition_catalog" -q
```

## ROLLBACK

Revertir diff del test.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/api/tests/test_logistics_plugin.py
  prohibited:
    - vendor/**
    - plugins/logistics/backend/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - test_bootstrap_restores_missing_logistics_transition_catalog
  indirect: []
  must_not_affect:
    - ciclo de vida de plugins (kernel)
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: [LOGI-0025, LOGI-0026, LOGI-0027, LOGI-0028]
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

- Requirement: investigación fallos suite logística (premisa bootstrap falsa, decisión B1)
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
