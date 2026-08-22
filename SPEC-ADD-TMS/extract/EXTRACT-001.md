# A.SPEC EXTRACT-001 — Desacoplar TMS del shell/core

## WHY

TMS vivirá como repo independiente e instalable. Hoy su backend importa
`systutor.sdk` (PluginContext), su frontend importa `@systutor/sdk/frontend`,
sus 6 suites de tests viven en `apps/api/tests/`, y su `plugin.json` declara
`requires: [crm, productos, stock, logistics]`. Ninguna de estas dependencias
permite que el plugin exista fuera del monorepo.

## WHAT

El código de `plugins/tms` compila y pasa su suite de tests sin importar
ningún módulo de `systutor.sdk`, `@systutor/shell`, ni residir dentro de
`apps/api`. Los tests TMS se ejecutan desde el propio plugin
(`plugins/tms/tests/`). La verdad nueva es falsable ahora: correr la suite
del plugin en un checkout aislado del monorepo debe pasar.

## SCOPE

- Reemplazar `systutor.sdk.PluginContext` por un puerto mínimo definido en el
  propio plugin (`plugins/tms/backend/ports.py`) con adaptador en el host.
- Definir contrato tipado propio para los datos que TMS consume de
  crm/productos/stock/logistics (DTOs locales, alimentados vía API REST o
  adaptador inyectado).
- Mover los 6 tests `apps/api/tests/test_tms*.py` → `plugins/tms/tests/`,
  autónomos (fixtures propios, sin conftest del core).
- Frontend stub deja de importar `@systutor/sdk/frontend`; define su tipo de
  registro localmente.

## OUT OF SCOPE

- Crear el repo GitHub ni migrar historial (EXTRACT-002).
- Mover la UI de jornadas que vive en
  `plugins/logistics/frontend/components/vehicle-sessions/`.
- Eliminar la instalación del plugin en el host monorepo.
- Cambiar comportamiento de negocio (sync, jornadas, seriales).

## CONTRACT

Precondiciones: rama TMS mergeada a `main`; suite actual verde
(`pytest apps/api/tests/test_tms* -q`).

Postcondiciones: `grep -r "systutor" plugins/tms/backend plugins/tms/frontend`
solo retorna coincidencias dentro de `plugins/tms` (puertos propios);
`pytest plugins/tms/tests -q` pasa en verde; el host sigue registrando el
plugin sin cambios visibles para el usuario.

## INVARIANTS

```yaml
invariants:
  - sync salidas cada 5 min sigue funcionando
  - materialización de jornada viva idempotente intacta
  - carga serial-first infiere producto igual que antes
  - endpoints /jornadas responden igual (contrato REST sin cambios)
  - permisos tms.* y evento tms.legacy.linked se registran igual
```

## VERIFICATION

```bash
grep -rn "from systutor\|@systutor" plugins/tms/ | grep -v ports.py | wc -l   # = 0
pytest plugins/tms/tests -q                                                    # verde
pytest apps/api/tests/test_tms* -q                                             # verde (host)
uvicorn app.main:app & curl -s localhost:8000/api/plugins | grep tms           # registrado
```

## ROLLBACK

Revert único del commit: los puertos propios vuelven a imports directos;
tests regresan a `apps/api/tests/`. Sin migraciones de datos involucradas.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/tms/**
    - apps/api/tests/test_tms*   # solo movimiento hacia plugins/tms/tests
  prohibited:
    - plugins/logistics/**
    - vendor/systutor-core/**
    - apps/api/app/config.py
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - plugins/tms/backend/plugin.py
    - plugins/tms/frontend/register.tsx
    - plugins/tms/plugin.json
    - ubicación de tests TMS
  indirect:
    - registro de plugins en host (debe seguir funcionando)
  must_not_affect:
    - logistics (vehicle-sessions)
    - stock
    - crm
    - productos
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - EXTRACT-002 (el repo nuevo hereda esta independencia)
  systemic_invariants:
    - plugin sigue instalable en host monorepo tras desacoplar
  composition_checks:
    - host arranca con plugin registrado
    - suite propia del plugin pasa fuera del árbol apps/api
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - plugins/tms/backend/ports.py
    - plugins/tms/tests/
```

## Traceability

- Requirement: TMS crecerá como repo independiente / plugin instalable
- Commit: (pendiente)
- Deployment: host monorepo sin cambios visibles

## Definition of Done

- [ ] Objective satisfied
- [ ] Scope respected
- [ ] Contract satisfied
- [ ] Independent falsable truth exists now
- [ ] Invariants preserved
- [ ] Verification passed
- [ ] Rollback / compensation is honest
- [ ] Composition checks passed when applicable
- [ ] No unrelated changes
- [ ] Structural constraints respected
- [ ] Traceability established
