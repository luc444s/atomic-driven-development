# ADR 0029 — Extracción del core a repo público MIT (multirepo)

## Estado

Aceptado — 2026-08-15

## Contexto

El kernel de SYSTUTOR OSS alcanzó madurez como framework de infraestructura:

- auth (JWT, usuarios, password hashing);
- RBAC con permisos declarativos por plugin y roles por tenant;
- aislamiento multi-tenant activo (ADR 0003, 0004);
- auditoría y event bus con outbox persistente (ADR 0005);
- runtime de plugins persistente con estados, dependencias, migraciones propias y hooks de ciclo de vida (ADR 0004, spec 0007);
- documentos versionados y sesiones de firma genéricas;
- tasks Dramatiq con broker y dispatcher reutilizable.

Verificación de 2026-08-15: el kernel no contiene referencias a dominios de negocio (`logistics`, `lg_*`, `cylinder`, etc.). El acoplamiento documentado en el reporte técnico de 2026-08-10 ya fue removido.

El objetivo estratégico del proyecto es que el kernel sea un framework open source reutilizable (licencia MIT), mientras los plugins de negocio (`logistics`, `crm`, `productos`, `stock`, `ventas`, `commerce`) son propiedad privada del negocio gas y deben permanecer fuera del alcance público.

El repositorio actual contiene además datos reales del negocio (CSVs legacy, grabaciones, logs, dumps) y un historial git que los incluye. Ninguno de ellos puede exponerse.

ADR 0002 establece que cualquier separación a multirepo requiere una nueva decisión arquitectónica. Esta es esa decisión.

## Opciones consideradas

### A. Repo público separado con namespace `systutor.*` + submodule (elegida)

Nuevo repo `systutor-core` (MIT) con kernel, core infra, contratos y SDK bajo un único namespace público `systutor.*`. El repo gas lo consume como submodule git con instalación editable.

- Ventajas: frontera pública clara desde la primera release; corrige la deuda de ADR 0002 (plugins importaban internals de `apps.api`); historial git fresco sin riesgo de filtración; el rename del namespace solo es barato antes de la primera release pública.
- Desventajas: rename mecánico en ~115 archivos del repo privado; mantenimiento de dos configuraciones de calidad.

### B. Repo público con estructura interna idéntica (`apps.api.app.kernel`)

Extraer sin renombrar, preservando paths internos del repo gas.

- Ventajas: cero cambios en el repo privado.
- Desventajas: congela el path interno `apps.api.app.*` como API pública permanente de un framework OSS; transmite la impresión de que el framework es "los archivos internos de la app gas"; cualquier rename futuro es breaking para todos los consumidores.

### C. Paquetes publicados (PyPI/npm) sin submodule

- Descartada por ahora: el core evoluciona en ciclos cortos junto al repo gas; publicar paquetes agrega fricción de release sin consumidores externos todavía. El submodule permite pasar a publicación de paquetes después sin rediseño.

## Decisión

1. **Repo nuevo público `systutor-core`** con licencia MIT, historial git fresco (commit inicial único, sin historial del repo gas).
2. **Alcance mínimo**: kernel backend + core infra + SDK + contracts. Sin frontend shell, sin docs de specs de negocio, sin tools.
3. **Namespace público único `systutor`**:

   | Ruta actual (repo gas) | Ruta nueva (systutor-core) |
   |---|---|
   | `apps/api/app/kernel/*` | `systutor/kernel/*` |
   | `apps/api/app/core/*` | `systutor/core/*` |
   | `apps/api/app/api/deps.py` | `systutor/api/deps.py` |
   | `apps/api/app/api/v1/core/*` | `systutor/api/v1/core/*` |
   | `apps/api/app/api/v1/system.py` | `systutor/api/v1/system.py` |
   | `packages/contracts/*` | `systutor/contracts/*` |
   | `packages/sdk/*` | `systutor/sdk/*` |

4. **Consumo por submodule**: el repo gas monta `systutor-core` en `vendor/systutor-core/` y lo instala editable (`pip install -e`). Los plugins privados importan exclusivamente desde `systutor.*` — se elimina la dependencia de los plugins a internals de `apps/api` (cierre de deuda de ADR 0002).
5. **Migraciones**: el árbol Alembic existente permanece íntegro en el repo privado (las DB existentes ya lo aplicaron). El repo público genera sus propias migraciones iniciales desde sus modelos.
6. **Se quedan en el repo privado** (no son kernel genérico): `api/v1/geocode.py` (proxy Nominatim para tablets de logistics), `api/v1/core/legacy.py` (compat legacy VB), `commands/seed_*` (seed demo y masivo con modelos de negocio), tests de plugins, `packages/ui`.
7. **Renombrado mecánico** en el repo privado con verificación por suite completa de tests.

## Consecuencias

- El contrato público del kernel queda fijado desde la primera release pública; cambios de firma serán breaking para el repo gas y deberán versionarse como dependencia.
- El repo privado conserva su ciclo de desarrollo: plugins in-tree (ADR 0011) no cambia; solo cambia desde dónde importan infraestructura.
- Dos configuraciones de calidad (ruff/pyright/pytest) que deben mantenerse sincronizadas en política, no en contenido.
- Cualquier nuevo permiso/evento del kernel seguirá las mismas reglas de `plugin.json` + registro runtime (AGENTS.md), ahora documentadas como contrato del repo público.
- La publicación de paquetes (PyPI/npm) queda habilitada como evolución futura sin rediseño.

## Reglas derivadas

- Prohibido reintroducir imports `apps.api.app.*` en plugins: la superficie de plugins es `systutor.*`.
- Prohibido copiar lógica de negocio dentro de `systutor-core`.
- Toda modificación al kernel se desarrolla y testea primero en `systutor-core` y luego se consume en el repo gas.
- El submodule se actualiza por versión explícita (commit fijado), no por `HEAD` flotante.
