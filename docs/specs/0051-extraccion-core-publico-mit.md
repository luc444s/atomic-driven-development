# Spec 0051 — Extracción del core público MIT (`systutor-core`)

## Estado

Vigente — 2026-08-15

## Relación con ADRs y specs

- ADR 0029 (nuevo): decisión multirepo, alcance, namespace, submodule.
- ADR 0002: regla de dependencias — esta spec la reemplaza parcialmente para `apps → packages/plugins` (ahora `apps/plugins → systutor-core`).
- ADR 0011: plugins in-tree sigue vigente en el repo privado; solo cambia la superficie de imports.
- ADR 0006: migraciones legacy no se tocan; árbol Alembic queda íntegro en repo privado.
- Spec 0006 (plugin contract), 0007 (persistent runtime): sus tests y documentación se mueven al repo público como contrato del framework.

## Alcance

### Repo público `systutor-core` (MIT)

```
systutor-core/
├── LICENSE                     (MIT)
├── README.md                   (quickstart, contrato de plugins, límites)
├── AGENTS.md                   (reglas mínimas para agentes)
├── pyproject.toml              (dist: systutor-core, src-layout)
├── src/systutor/
│   ├── __init__.py
│   ├── kernel/                 ← apps/api/app/kernel (auth, audit, documents,
│   │                              events, permissions, plugins, signatures,
│   │                              tasks, tenants, models)
│   ├── core/                   ← apps/api/app/core (cache, config, database,
│   │                              errors, lifecycle, logging, pagination,
│   │                              request_context)
│   ├── api/
│   │   ├── deps.py             ← apps/api/app/api/deps.py
│   │   └── v1/
│   │       ├── core/           ← api/v1/core (branches, common, documents,
│   │       │                      permissions, plugins, roles, schemas,
│   │       │                      services/, signatures, users)
│   │       └── system.py       ← health, ready, plugins
│   ├── contracts/              ← packages/contracts (audit, events, plugins)
│   └── sdk/                    ← packages/sdk (context, frontend/index.ts)
├── app/
│   ├── main.py                 (create_app con bootstrap desde systutor.*)
│   └── migrations/             (alembic.ini + env.py + versions iniciales
│                                autogeneradas desde modelos kernel)
├── tests/                      (tests kernel: core, apis, management apis,
│                                health, plugin registry, runtime, tenants,
│                                cors, conftest propio)
└── .gitignore / .env.example   (sanitizados)
```

### Repo privado (gas)

- Se eliminan del repo privado: `apps/api/app/kernel/`, `apps/api/app/core/`, `apps/api/app/api/deps.py`, `apps/api/app/api/v1/core/`, `apps/api/app/api/v1/system.py`, `packages/sdk/`, `packages/contracts/`.
- Se agrega submodule `vendor/systutor-core/` con commit fijado.
- Renombrado mecánico de imports en todo el repo privado:
  - `apps.api.app.kernel.*` → `systutor.kernel.*`
  - `apps.api.app.core.*` → `systutor.core.*`
  - `apps.api.app.api.deps` → `systutor.api.deps`
  - `apps.api.app.api.v1.core` → `systutor.api.v1.core`
  - `apps.api.app.api.v1.system` → `systutor.api.v1.system`
  - `packages.contracts.*` → `systutor.contracts.*`
  - `packages.sdk.*` → `systutor.sdk.*`
  - `import apps.api.app.kernel.models` → `import systutor.kernel.models` (conftest)
- `apps/api/app/api/v1/router.py` (privado) rearma el router: `systutor.api.v1.core` + `systutor.api.v1.system` + `systutor.kernel.auth.router` + `geocode` local + routers de plugins vía runtime.
- `apps/api/app/main.py` (privado) importa `create_app`-base desde `systutor` y registra plugins del repo gas.
- Instalación editable del submodule: `pip install -e vendor/systutor-core`.
- Config privada: `pyright.include` suma `vendor/systutor-core/src`; `ruff` con dos raíces; `pytest` sigue en `apps/api/tests` con conftest importando `systutor.kernel.models` + modelos de plugins.

## Excluidos explícitamente del repo público

- `plugins/*` (todos: logistics, crm, productos, stock, ventas, commerce).
- `tools/*`, `apps/web/*`, `packages/ui/*`.
- `apps/api/app/api/v1/geocode.py` (proxy específico de tablets logistics).
- `apps/api/app/commands/*` (seed demo y masivo dependen de modelos de plugins).

> Corrección 2026-08-15: `api/v1/core/legacy.py` SÍ se incluye en el repo público.
> Contrario a lo previsto, no es compat de VB legacy: contiene las rutas de
> management sin prefijo (`/users`, `/audit-logs`, `/branches`, `/permissions`,
> `/plugin-registry`, `/plugin-runtime/*`) que la app gas usa en producción y
> que la suite kernel cubre. Es código genérico del kernel, no de negocio.
- Datos reales: `formulas_criogenicas_*.csv`, `grabaciones/`, `data/`, logs, `dump.rdb`, `.env`.
- Historial git del repo gas (el público arranca con commit único).

## Seguridad (bloqueante para publicar)

1. Scan de secretos sobre el árbol copiado: claves JWT reales, passwords, tokens, URLs internas, `X-Internal-Api-Key`.
2. `.env.example` público solo con placeholders; sin valores de producción ni IPs internas.
3. Verificación de que ningún CSV/log/recording quedó dentro del árbol público.
4. El copyright de LICENSE queda pendiente de confirmación del titular (placeholder "SYSTUTOR OSS Authors" hasta definirlo).

## Migraciones

- Repo privado: árbol `apps/api/migrations/versions` intacto (incluye migraciones de kernel y de plugins; las DB existentes ya las tienen aplicadas).
- Repo público: **follow-up** — el esqueleto Alembic (`app/migrations/` con baseline autogenerado) no bloquea la extracción; los tests públicos usan `Base.metadata.create_all`. Pendiente para la primera release empaquetada.
- Regla futura: migraciones nuevas de kernel se escriben en `systutor-core`; el repo privado las aplica vía dependencia.

## Tests

- Público: `tests/` con los tests kernel actuales (`test_core.py`, `test_core_apis.py`, `test_core_management_apis.py`, `test_health.py`, `test_plugin_registry.py`, `test_persistent_plugin_runtime.py`, `test_plugin_runtime_completion.py`, `test_runtime_v03.py`, `test_tenant_isolation.py`, `test_cors.py`) con conftest propio: SQLite, `plugins_dir` apuntando a directorio de plugins vacío dentro del repo público, sin seed de negocio.
- Privado: suite restante (tests de plugins + tests que requieren modelos de negocio) contra el submodule instalado.

## Criterios de aceptación

1. `systutor-core` es un repo git autónomo con commit inicial único, LICENSE MIT, README y AGENTS.md.
2. `pytest`, `ruff check` y `pyright` pasan en verde dentro de `systutor-core`.
3. El repo público no contiene ninguna referencia a `logistics`, `crm`, `productos`, `stock`, `ventas`, `commerce` en código (grep limpio).
4. El repo público no contiene datos legacy ni secretos (scan limpio).
5. El repo privado funciona con el submodule instalado editable: suite completa `pytest apps/api/tests` verde.
6. Cero imports residuales `apps.api.app.kernel|core` y `packages.contracts|sdk` en plugins, tools y tests privados.
7. `ruff check .` y `pyright` verdes en el repo privado.
8. README del repo privado documenta el flujo de actualización del submodule.
9. ADR 0029 y esta spec quedan commiteados en el repo privado.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Rename mecánico rompe imports oscuros (strings, lazy imports) | Alto | Suite completa + grep de residuales; revisión de `__init__` re-exports |
| Divergencia de modelos entre migraciones privadas y baseline pública | Medio | El baseline público es solo referencia; las DB reales siguen el árbol privado |
| Publicar accidentalmente datos reales | Crítico | Scan de secretos + verificación manual del árbol antes del primer push; historial fresco |
| Dos configs de calidad que se desalinean | Bajo | Mismo policy ruff/pyright en ambos repos; documentado en READMEs |
| Submodule con HEAD flotante causa builds rotos | Medio | Commit fijado por versión; actualización explícita con PR |

## No objetivos

- Mover frontend shell o `shared/ui` al repo público.
- Publicar en PyPI/npm (futuro, sin rediseño).
- Reescribir o limpiar APIs del kernel (solo rename de namespace).
- Migrar `core/internal_api` (spec 0021 sigue pendiente como trabajo separado).
