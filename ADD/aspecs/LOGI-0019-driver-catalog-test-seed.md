# A.SPEC LOGI-0019 — Seed driver user in outbound session test context

## WHY

El helper compartido `_create_outbound_session_context`
(`apps/api/tests/test_logistics_route_operation_effects.py:94`) consume
`GET /vehicle-sessions/drivers/catalog` y asume que devuelve al menos un
conductor. En el entorno de tests nadie crea un usuario con rol `driver`
para el tenant de prueba → `IndexError: list index out of range`.

Esto rompe 7 tests (5 en `test_logistics_route_operation_effects.py`,
2 en `test_logistics_route_control_v1.py`, que importa el mismo helper).

No es bug de producción: el catálogo filtra por `Role.name == "driver"`
(`plugins/logistics/backend/services/sessions.py:44`) y en producción los
conductores existen (`register_user_category("driver", ..., ["driver"])`
asigna el rol automáticamente; TMS siembra vía `ensure_driver_user`).
Es un gap del seed del contexto de test.

## WHAT

`_create_outbound_session_context` crea primero un usuario conductor vía
`POST /api/v1/core/users` con `category="driver"` (mismo patrón ya usado en
`test_logistics_vehicle_sessions_v1.py::_first_driver_id`,
`test_logistics_session_console.py`, `test_logistics_performance_budget.py`)
antes de consultar el catálogo.

Verdad observable ahora: los 7 tests afectados ejecutan el flujo completo
de jornada de salida sin `IndexError`.

## SCOPE

- `apps/api/tests/test_logistics_route_operation_effects.py`: dentro de
  `_create_outbound_session_context`, crear usuario con `category="driver"`
  vía API antes de `GET /drivers/catalog`; asertar 201 y catálogo no vacío.

## OUT OF SCOPE

- Cambios en backend/plugins (catálogo y filtro por rol quedan intactos).
- Otros helpers `_first_driver_id` existentes (ya correctos).
- Los 6 fallos heterogéneos de `test_logistics_plugin.py` (causas distintas,
  investigación pendiente en A.SPEC futura).

## CONTRACT

- Precondición: tenant de test sin usuarios con rol `driver`.
- Postcondición: tras crear el usuario vía `POST /api/v1/core/users` con
  `category="driver"`, el catálogo devuelve ≥1 opción y el helper obtiene
  `driver_id` válido para crear la sesión.

## INVARIANTS

```yaml
invariants:
  - list_driver_options DEBE seguir filtrando por Role.name == "driver" activo (no category).
  - Ningún endpoint ni servicio de producción cambia.
  - Tests ya verdes NO deben romperse.
```

## VERIFICATION

```
python -m pytest apps/api/tests/test_logistics_route_operation_effects.py apps/api/tests/test_logistics_route_control_v1.py -q
```

Resultado ejecutado (2026-08-23): IndexError eliminado en los 7 tests;
4/7 verdes (ambos route_control_v1 + 3 route_operation_effects).
Los 3 restantes fallan por causas DISTINTAS, enmascaradas antes por el
IndexError y fuera del scope de esta A.SPEC:

- ×2 `Transición inválida: WAREHOUSE → CUSTOMER_PICKUP` (máquina de estados)
- ×1 `context_type no soportado` (flujo emergency)

→ Requieren A.SPECs propias (pendientes).

## ROLLBACK

Revertir el diff del helper (git revert del commit). Sin efectos externos:
cambio acotado a código de test.

## Change Surface

```yaml
change_surface:
  allowed:
    - apps/api/tests/test_logistics_route_operation_effects.py
  prohibited:
    - plugins/logistics/**
    - vendor/**
    - apps/api/app/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - suite de tests logistics (route_operation_effects, route_control_v1)
  indirect: []
  must_not_affect:
    - comportamiento de producción de /drivers/catalog
    - otros tests verdes
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - LOGI-0020 (invariant de cilindro en tránsito en tests)
    - LOGI-0021 (expectativa WAREHOUSE_IN en tests)
  systemic_invariants:
    - suite logistics queda verde salvo los 6 fallos de test_logistics_plugin.py (causas propias, fuera de este set)
  composition_checks:
    - pytest conjunto de los 3 archivos afectados por LOGI-0019/20/21 en verde
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

- Requirement: diagnóstico 15+ fallos pre-existentes en suite logística (sesión 2026-08-23)
- Commit: 138ab3d
- Deployment: N/A (tests)

## Definition of Done

- [x] Objective satisfied (IndexError eliminado; verdad: catálogo con conductor sembrado)
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now
- [x] Invariants preserved
- [x] Verification passed (4/7 verdes; 3 restantes = causas fuera de scope, documentadas)
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established
