# A.SPEC LOGI-0025 — Expect derived gas stock on full cylinder create without weight

## WHY

Desde `74f6a55` (2026-08-02), `_resolve_initial_content_kg`
(`plugins/logistics/backend/services/cylinders.py:338`) deriva
`content_kg = product.weight_kg` cuando un envase entra en estado lleno
(`FULL_FROM_SUPPLIER`) sin peso explícito, y `_register_initial_entry`
ajusta el stock de gas en consecuencia (`cylinders.py:1455-1465`).
El test
`test_logistics_plugin.py::test_logistics_create_cylinder_full_from_supplier_allows_minimal_route_create_without_content`
espera el comportamiento viejo (stock 0) y falla con `10.0 == 0`.
El producto del test tiene `weight_kg=10` → stock esperado 10.0.

## WHAT

El test aserta la verdad vigente: crear cilindro `FULL_FROM_SUPPLIER` sin
`content_kg` con producto `weight_kg=10` produce balance de stock 10.0 en
el almacén de alta. Se renombra el test para reflejar la derivación.

## SCOPE

- `apps/api/tests/test_logistics_plugin.py`: aserción de balance
  (0 → 10.0) y nombre del test.

## OUT OF SCOPE

- Cambiar `_resolve_initial_content_kg` ni el bridge de stock.
- Otros entry modes.

## CONTRACT

- Postcondición: `POST /cylinders` con `entry_mode=FULL_FROM_SUPPLIER`,
  producto con `weight_kg=10`, sin `content_kg`, `minimal_route_create=true`
  → `GET /stock/balance/{product}/{warehouse}` devuelve quantity 10.0.

## INVARIANTS

```yaml
invariants:
  - _resolve_initial_content_kg NO cambia.
  - adjust_required_product_stock y su idempotency key NO cambian.
```

## VERIFICATION

```
python -m pytest "apps/api/tests/test_logistics_plugin.py::test_logistics_create_cylinder_full_from_supplier_allows_minimal_route_create_without_content" -q
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
    - plugins/stock/**
```

## Blast Radius

```yaml
blast_radius:
  direct: [test_logistics_create_cylinder_full_from_supplier_allows_minimal_route_create_without_content]
  indirect: []
  must_not_affect: []
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: [LOGI-0024, LOGI-0026]
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

- Requirement: investigación fallos suite logística (feature content_kg derivado)
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
