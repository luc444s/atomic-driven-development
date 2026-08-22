# A.SPEC EXTRACT-002 — Repo independiente systutor-tms instalable

## WHY

EXTRACT-001 dejó el plugin sin dependencias hacia shell/core, pero el código
sigue viviendo dentro del monorepo. Para que TMS crezca como producto
independiente necesita su propio repositorio GitHub y un mecanismo de
instalación como plugin en el host.

## WHAT

Existe el repositorio público/privado `systutor-tms` en GitHub (creado con
`gh`), contiene `plugins/tms` completo (backend, tests propios, plugin.json,
frontend stub), y el host monorepo lo instala como paquete Python versionado
(`pip install git+https://github.com/<org>/systutor-tms@v0.1.0` o path local),
registrándolo por entrypoint en lugar de importarlo del árbol del monorepo.
Verdad nueva falsable ahora: desde un clone limpio del host sin el directorio
`plugins/tms`, instalar `systutor-tms` levanta el plugin funcionando.

## SCOPE

- `gh repo create systutor-tms` + push inicial con historial de la ruta
  `plugins/tms` preservado vía `git filter-repo --path plugins/tms`.
- Empaquetado Python (`pyproject.toml`) con entrypoint de plugin.
- Host: soportar carga de plugin desde paquete instalado (registro por
  entrypoint `systutor.plugins`), además de descubrimiento por directorio.
- Tag inicial `v0.1.0`.
- README del repo nuevo.

## OUT OF SCOPE

- CI del repo nuevo (futura A.SPEC).
- Migrar issues/projects de GitHub.
- Eliminar inmediatamente `plugins/tms` del monorepo (deprecación = futura
  A.SPEC tras verificar instalación).
- UI de jornadas en logistics (sigue en monorepo).

## CONTRACT

Precondiciones: EXTRACT-001 verificada (plugin autónomo, suite propia verde).

Postcondiciones:
- `gh repo view systutor-tms` responde; clone limpio compila y pasa tests.
- Host sin `plugins/tms` local + paquete instalado ⇒ plugin registrado,
  endpoints `/jornadas` operativos, sync daemon funcional.
- Historial de commits de `plugins/tms` visible en el repo nuevo.

## INVARIANTS

```yaml
invariants:
  - contrato REST /jornadas idéntico al del monorepo
  - permisos tms.* y evento tms.legacy.linked intactos
  - migraciones de jornada aplican igual (001_initial_jornada)
  - logistics/stock/crm/productos del host sin cambios
```

## IMPLEMENTATION NOTES (decisión de carga)

El loader de plugins del host está hardcodeado en `vendor/systutor-core`
(`systutor.core.lifecycle` → `PluginManifestRegistry(plugins_dir).discover()`),
que el change surface PROHÍBE editar. Decidido (**opción "Ambos"**):

- Mecanismo funcional: el paquete `systutor-tms` declara el entrypoint
  `systutor.plugins` → `plugins.tms:PLUGIN_ROOT`. El host crea un symlink
  `<plugins_dir>/tms -> PLUGIN_ROOT` en startup (sin tocar el kernel), así el
  loader por directorio existente lo descubre.
- Fidelidad de spec: el entrypoint `systutor.plugins` queda declarado en
  `pyproject.toml` para un loader nativo futuro; el descubrimiento por
  directorio se conserva ("además de").
- `apps/api/app/plugins.py::ensure_installed_plugins` (host) + llamada en
  `apps/api/app/main.py::create_app` antes de `bootstrap_app_state`.

## VERIFICATION

```bash
gh repo view systutor-tms                                                        # existe
git clone gh:<org>/systutor-tms /tmp/t && (cd /tmp/t && pytest -q)               # verde
rm -rf plugins/tms && pip install -e dist/ o git+URL                             # instala
uvicorn app.main:app & curl localhost:8000/api/plugins | grep tms                # registrado
pytest apps/api/tests -q --ignore=apps/api/tests/test_tms                        # host verde
```

## ROLLBACK

Reversible por compensación: restaurar `plugins/tms/` desde el monorepo
(git checkout), desinstalar paquete (`pip uninstall systutor-tms`). El repo
GitHub se archiva/borra si no tuvo consumo externo. Sin datos en juego
(las tablas de jornada viven en la DB compartida, no en el repo).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/tms/**            # extracción de historial
    - apps/api/app/plugins.py   # loader: entrypoint además de directorio
    - pyproject.toml (host)     # dependencia opcional
    - repo nuevo systutor-tms/**
  prohibited:
    - plugins/logistics/**
    - vendor/systutor-core/**
    - esquema DB
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - origen de verdad del código TMS (monorepo → repo dedicado)
    - loader de plugins del host
  indirect:
    - despliegues que asumen plugins por directorio
  must_not_affect:
    - comportamiento REST existente
    - otros plugins
    - datos/migraciones
```

## Composition

```yaml
composition:
  requires_aspecs:
    - EXTRACT-001
  must_compose_with: []
  systemic_invariants:
    - un solo origen de verdad para TMS tras la extracción (repo nuevo)
    - monorepo puede seguir sirviendo fallback hasta deprecación explícita
  composition_checks:
    - instalación desde clone limpio pasa checks de EXTRACT-001
    - sync daemon corre contra plugin instalado
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - systutor-tms/pyproject.toml
    - apps/api/app/plugins.py (loader)
```

## Traceability

- Requirement: "TMS crecerá como repo independiente, plugin instalable, repo con gh"
- Repo: https://github.com/luc444s/systutor-tms (privado, historial de plugins/tms preservado vía git filter-repo)
- Tag: v0.1.0 (pusheado)
- Commit host (monorepo): EXTRACT-002 host loader entrypoint + symlink (apps/api/app/plugins.py, apps/api/app/main.py)
- Deployment: tag v0.1.0 en systutor-tms + host instalando paquete (`pip install git+https://github.com/luc444s/systutor-tms@v0.1.0`)

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
