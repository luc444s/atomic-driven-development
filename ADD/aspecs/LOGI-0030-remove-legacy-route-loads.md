# A.SPEC LOGI-0030 — Remove legacy route-loads flow (superseded by vehicle-sessions)

## WHY

El flujo legacy de carga por ruta (`lg_loads` + endpoints `/loads*`) fue
reemplazado por el ciclo de jornadas (`vehicle-sessions` con load-plan,
TMS-010..012). Quedó roto silenciosamente desde migration 035
(`ck_cylinder_transit_requires_session`): `confirm_loads`
(`plugins/logistics/backend/services/routes.py:435`) transiciona
cilindros a `CARGA_EN_VEHICULO` sin `session_id`, y el arranque de ruta
legacy hace lo mismo hacia `EN_RUTA`. Cualquier uso real hoy produce
400/IntegrityError. El usuario confirma que operativamente ya nadie usa
el flujo: todo vive en jornadas. La página `LoadsPage` y los endpoints
son código muerto que duplica la responsabilidad de carga.

## WHAT

Una sola verdad observable: el flujo legacy de carga-por-ruta deja de
existir en el sistema — los endpoints `/loads*` y
`/reports/load-summary` responden 404, la navegación ya no expone la
página de cargas, y toda la carga operativa se realiza vía
vehicle-sessions. Los datos históricos de `lg_loads` se preservan
(solo lectura archivo, sin escrituras nuevas posibles).

## SCOPE

Backend (`plugins/logistics/backend/`):
- `router.py`: eliminar endpoints `GET /loads`, `POST /loads`,
  `POST /loads/bulk`, `DELETE /loads/{id}`, `POST /loads/confirm`,
  `GET /loads/weight-summary`, `GET /reports/load-summary/{route_id}`
  y sus imports asociados.
- `services/routes.py`: eliminar `list_loads`, `create_load`,
  `bulk_create_loads`, `get_load`, `get_load_by_id`, `delete_load`,
  `confirm_loads`.
- `services/extensions.py`: eliminar `build_load_weight_summary` (y su
  uso interno si solo sirve al endpoint removido).
- `schemas.py`: eliminar `LoadRead`, `LoadCreateRequest`,
  `LoadBulkCreateRequest`, `LoadConfirmRequest`, `LoadWeightSummaryRead`,
  `LoadSummaryReportRead`.

Frontend (`plugins/logistics/frontend/`):
- Eliminar `pages/LoadsPage.tsx`.
- `register.ts`: quitar ruta `logistics/loads` e import.
- `api/loads.ts`: eliminar funciones del flujo (archivo completo si todo
  es loads); actualizar export en `api/index.ts`.

## OUT OF SCOPE

- Dropear tabla/modelo `LogisticsLoad` (archivo histórico; posible
  A.SPEC futura de purga con migration propia).
- Planning summaries (`PlanningExpectedLoadSummary`) — módulo distinto.
- `GET /reports/route-agenda` (sigue vigente).
- Cambios en vehicle-sessions.

## CONTRACT

- Postcondición 1: `GET|POST /loads`, `POST /loads/bulk`,
  `DELETE /loads/*`, `POST /loads/confirm`, `GET /loads/weight-summary`,
  `GET /reports/load-summary/*` responden 404.
- Postcondición 2: la app frontend compila sin `LoadsPage`; nav sin
  entrada "cargas".
- Postcondición 3: filas existentes de `lg_loads` intactas.

## INVARIANTS

```yaml
invariants:
  - Modelo LogisticsLoad y tabla lg_loads NO se eliminan ni alteran.
  - vehicle-sessions load-plan NO cambia.
  - reports/route-agenda y planning siguen funcionando.
  - Ningún otro endpoint cambia de contrato salvo pasar a 404 los listados.
```

## VERIFICATION

```
python -m pytest apps/api/tests/test_logistics_plugin.py apps/api/tests/test_logistics_vehicle_sessions_v1.py apps/api/tests/test_logistics_planning_reservations_v1.py -q
rg -n "LoadsPage|loads/confirm|loads/bulk" plugins/logistics --quiet && echo "FAIL: referencias residuales" || echo "OK"
python -m pytest apps/web --co -q   # o build del frontend si aplica
```

Esperado: suites verdes; sin referencias residuales a LoadsPage ni a los
endpoints eliminados.

## ROLLBACK

Revertir commit. Sin efectos externos: no hay migración; datos nunca se
tocaron. Compensación: el flujo de jornadas cubre la operación.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/backend/router.py
    - plugins/logistics/backend/services/routes.py
    - plugins/logistics/backend/services/extensions.py
    - plugins/logistics/backend/schemas.py
    - plugins/logistics/frontend/pages/LoadsPage.tsx
    - plugins/logistics/frontend/register.ts
    - plugins/logistics/frontend/api/loads.ts
    - plugins/logistics/frontend/api/index.ts
  prohibited:
    - plugins/logistics/backend/models/**
    - plugins/logistics/migrations/**
    - plugins/tms/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - endpoints /loads* y /reports/load-summary (desaparecen)
    - nav frontend logistics/loads
  indirect:
    - tests que ejercitaban el flujo (LOGI-0031 los recorta)
  must_not_affect:
    - vehicle-sessions / load-plans
    - planning
    - datos históricos lg_loads
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: [LOGI-0031]
  systemic_invariants:
    - única vía de carga operativa = jornada (vehicle-session)
  composition_checks:
    - suite completa logistics verde tras LOGI-0030 + LOGI-0031
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

- Requirement: usuario confirma flujo legacy sin uso; roto desde migration 035
- Commit: 5791898

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
