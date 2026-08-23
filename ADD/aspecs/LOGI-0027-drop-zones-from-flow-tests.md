# A.SPEC LOGI-0027 — Drop removed zones endpoints from legacy flow tests

## WHY

Los endpoints de zonas (`POST /zones`, `GET /zones`, `GET /catalog/zones`)
fueron eliminados intencionalmente en `74f6a55` (2026-08-02, "warehouse
geolocalization") — las zonas fueron reemplazadas por geolocalización de
almacenes. `DeliveryPointCreateRequest` ya no acepta `zone_id`
(`plugins/logistics/backend/schemas.py:618`). Dos tests siguen usando
zonas y fallan: `test_logistics_plugin_operations_flow` (404 en
`POST /zones`) y `test_logistics_plugin_spec_0014_flow` (KeyError por
zona no creada).

## WHAT

Los 2 tests fluyen sin zonas: se elimina la creación de zona y el campo
`zone_id` de los payloads de delivery-point (el schema vigente lo omite).
La verdad probada es la misma: flujo completo almacén→vehículo→
delivery-point→orden→jornada funciona con la API actual.

## SCOPE

- `apps/api/tests/test_logistics_plugin.py`:
  - `test_logistics_plugin_operations_flow`: quitar bloque de creación de
    zona y `zone_id` del payload de delivery-point.
  - `test_logistics_plugin_spec_0014_flow`: ídem.

## OUT OF SCOPE

- Reintroducir endpoints de zonas.
- Cambiar schemas de delivery-point.
- Agregar campos nuevos (gps, address_id) a los tests.

## CONTRACT

- Postcondición: ambos tests completan 100% contra la API vigente, sin
  referencias a `/zones` ni `zone_id`.

## INVARIANTS

```yaml
invariants:
  - Ningún endpoint ni schema de producción cambia.
  - Las aserciones de negocio restantes de ambos flujos NO cambian.
```

## VERIFICATION

```
python -m pytest "apps/api/tests/test_logistics_plugin.py::test_logistics_plugin_operations_flow" "apps/api/tests/test_logistics_plugin.py::test_logistics_plugin_spec_0014_flow" -q
```

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
  must_not_affect:
    - delivery-points API
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: [LOGI-0024, LOGI-0025, LOGI-0026, LOGI-0028]
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

- Requirement: investigación fallos suite logística (zonas eliminadas)
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
