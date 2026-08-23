# A.SPEC LOGI-0029 — Add address_id to customer-context delivery point fallbacks

## WHY

LOGI-0017 introdujo la lectura `delivery_point.address_id` en
`confirm_route_operation_effects`
(`plugins/logistics/backend/services/route_operation_confirmation.py:718`).
En operaciones con contexto `CUSTOMER` (sin parada de ruta),
`_resolve_operation_context` construye el delivery_point como
`SimpleNamespace` con solo `customer_id/customer_name/address`
(`plugins/logistics/backend/services/route_operations.py:222`), e ídem
`_delivery_point_for_operation` (`route_operations.py:568`). Ambos
fallbacks carecen de `address_id` → `AttributeError` al confirmar un
evento fuera de parada. Crash alcanzable en producción vía
route-events/confirm con contexto CUSTOMER.

## WHAT

Ambos fallbacks exponen `address_id=None`. La verdad vigente es la del
contrato LOGI-0017: evento `CUSTOMER_*` sin delivery_point real queda
con `customer_address_id = NULL`.

## SCOPE

- `plugins/logistics/backend/services/route_operations.py`: agregar
  `address_id=None` a los dos `SimpleNamespace` (líneas ~222 y ~568).

## OUT OF SCOPE

- Resolver dirección real desde el cliente (requiere elegir una
  dirección; hoy el flujo manual no la captura).
- Cambiar route_operation_confirmation.py.

## CONTRACT

- Precondición: operación/evento con contexto CUSTOMER (customer_id,
  sin route_stop).
- Postcondición: confirmación responde 200; eventos `CUSTOMER_*`
  generados llevan `customer_address_id = NULL`.

## INVARIANTS

```yaml
invariants:
  - Contrato LOGI-0017 intacto (NULL si no hay delivery_point.address_id).
  - Rutas con parada siguen resolviendo address_id desde delivery_point real.
  - Ningún otro atributo de los fallbacks cambia.
```

## VERIFICATION

```
python -m pytest "apps/api/tests/test_logistics_route_operation_effects.py::test_confirm_route_event_customer_emergency_is_idempotent_and_creates_incident" -q
```

## ROLLBACK

Revertir diff (quitar address_id de los fallbacks). Sin efectos externos.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/backend/services/route_operations.py
  prohibited:
    - plugins/logistics/backend/services/route_operation_confirmation.py
    - plugins/logistics/frontend/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - confirm_route_operation / confirm_route_event con contexto CUSTOMER
  indirect:
    - lg_cylinder_events (eventos con customer_address_id NULL)
  must_not_affect:
    - operaciones STOP/WAREHOUSE con delivery_point real
```

## Composition

```yaml
composition:
  requires_aspecs: [LOGI-0017]
  must_compose_with: [LOGI-0022]
  systemic_invariants:
    - confirmación de evento nunca crashea por falta de address_id
  composition_checks:
    - LOGI-0017 + LOGI-0029: eventos fuera de parada con address NULL, eventos en parada con address real
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

- Requirement: crash destapado por LOGI-0022 durante ejecución (falla de composición LOGI-0017 × contextos manuales)
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
