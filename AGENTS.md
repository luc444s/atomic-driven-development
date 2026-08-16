# AGENTS.md

## Proposito

Define reglas operativas para agentes de IA en SYSTUTOR OSS. Reduce ambiguedad, protege la arquitectura y mantiene consistencia tecnica.

## Principios

- no reescritura impulsiva del legacy; el legacy se absorbe por dominios
- logica de negocio en Python auditable; no en stored procedures ni triggers
- kernel pequeno; modulos de negocio en plugins
- eventos para comunicacion entre modulos en vez de acoplamiento directo
- toda accion importante debe ser auditable
- migracion legacy controlada, validada y trazable

## Ley de contexto operativo

Toda vista, respuesta operativa o contrato de lectura debe priorizar contexto de negocio entendible antes que IDs crudos. Regla minima:

- que paso
- donde paso
- con quien paso
- cuando paso

Si aplica al flujo, agregar tambien:

- en que estado esta
- por que importa o que falta

Regla derivada: ninguna vista operativa debe mostrar un identificador crudo si puede mostrar contexto de negocio util.

## Orden de lectura obligatorio

1. **Engram** (`mem_context` + `mem_search` con keywords de la tarea) — prioridad sobre cualquier .md
2. `AGENTS.md`
3. **`apps/web/src/shared/ui/README.md`** — patrones de formulario y componentes (obligatorio para toda tarea de frontend)
4. `docs/avances/<modulo>.md` (si existe)
5. ADR relacionado
6. Spec de la feature
7. Contrato de datos/API
8. Archivos afectados

No implementar solo a partir de una conversacion aislada.

## Identidad visual frontend (obligatorio)

Antes de escribir una sola linea de UI, cargar la skill `frontend-ui-identity`. Todo formulario, dialogo o pagina debe sentirse nativo al sistema. Reglas minimas:

- **Labels**: `<label className="block space-y-2 text-sm text-foreground">`, nunca `text-xs` ni `text-muted-foreground`
- **Sin asteriscos rojos**: el sistema no los usa. Validacion en backend.
- **Botones**: `<Button>` de `shared/ui/button`. Nunca `<button>` con estilos inline.
- **Errores**: `<Alert>` de `shared/ui/alert`. Nunca divs rojos raw.
- **Inputs**: `<Input>`, `<Textarea>`, `<Combobox>`, `<Select>` de `shared/ui/`. Nunca elementos HTML nativos sin wrapper.
- **Espaciado**: `space-y-4` dentro de secciones, `space-y-6` entre secciones, `flex justify-end gap-3` para fila de botones.
- **Sin estilos inline**: solo Tailwind utility classes via `className`.

Si un componente no existe en `shared/ui/`, se crea alli primero como generico, luego se usa desde el plugin.

## ADRs obligatorios (leer antes de decisiones tecnicas)

`docs/adr/0001-stack-base.md` al `0009-spec-driven-development.md`, mas `0022-adopcion-monaco-editor-consola-operativa.md` y `0023-dsl-comandos-consola-patrones-seguros.md` para toda tarea que toque la consola operativa o un DSL de comandos. Si una tarea contradice un ADR, proponer nuevo ADR o actualizacion explicita.

## Stack

**Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Redis, Dramatiq, Pydantic v2.
**Calidad**: Pyright, Ruff, Pytest.
**Frontend**: React, Vite, TypeScript, Zustand, TanStack Query, React Router, Tailwind CSS (utility-first), shadcn/ui.
**Infra**: Docker Compose (local), Traefik (prod), GitHub Actions (CI/CD).

**Entorno primario: Termux**. Preferir ejecucion directa (`python3 + .env + venv`) sobre Docker. Aceptar Python 3.13 en Termux si el codigo sigue compatible con 3.12. Revisar compatibilidad nativa de dependencias con Android.

## Estructura del repositorio

```text
apps/       → aplicaciones ejecutables (api/, web/)
packages/   → librerias compartidas (sdk/, contracts/, ui/)
plugins/    → modulos de negocio
tools/      → herramientas internas (migrator/, legacy-analyzer/)
docs/       → documentacion versionada (adr/, avances/, specs/, contracts/)
infra/      → docker/, compose/
```

## Anti-monolitos (preventivo)

Ningun archivo >600 lineas (>1000 es punto de friccion). Reglas:
- crear archivos por dominio desde el dia 1, no un `models.py` o `api.ts` unico
- archivo nuevo antes de llegar a 400 lineas
- cada entidad/endpoint en su propio archivo de dominio
- hooks compartidos (`useCoreMutation`) en `apps/web/src/lib/`, no en el plugin
- payload builders (form→API) en `api.ts`, no en la pagina
- prohibido agregar codigo a un archivo que ya supera 500 lineas

## Component Minimal

Componentes base (tablas, modales, selects, tooltips, paginacion) en `shared/ui/`, no duplicados en plugins. `shadcn/ui` es fuente de verdad. No crear "variantes por modulo" de un mismo componente — una sola `DataTable` configurable por props. Si no cubre el caso, extender con props, no clonar.

## Reutilizacion de componentes

Priorizar uso de `shared/ui/`. Si no existe el componente generico:
1. crearlo primero en `shared/ui/`;
2. luego usarlo desde el plugin con props/funciones del dominio.

Wrappers de dominio aceptables si solo inyectan defaults sin duplicar logica interna del componente Core.

## OpenAPI como fuente de verdad de tipos

FastAPI genera `/openapi.json` desde Pydantic. `openapi-typescript` genera `api-types.ts` en build. Los plugins importan tipos desde `@/lib/api-types`, no los escriben a mano en `api/*.ts`. Excepcion: tipos puramente locales de UI. Al cambiar un schema Pydantic, regenerar tipos frontend es parte del ciclo.

Esto elimina el "schema inferno" de tipos duplicados con nombres ligeramente distintos.

## Core First — abstraer, no duplicar

**Va al Core**: componentes UI genericos (`DataTable`, `Dialog`, `Combobox`, `Pagination`, `EmptyState`, `ConfirmDialog`, `Tabs`), hooks de infraestructura (`useCoreMutation`, `usePagination`, `useDebounce`, `useFilters`), helpers de API (`apiRequest`, `withQuery`, `ApiError`), layouts de pagina, patrones CRUD reutilizables.

**Queda en el Plugin**: modelos SQLAlchemy, endpoints/routers, servicios con reglas de negocio, migraciones, hooks de dominio, wrappers finos sobre componentes Core, payload builders.

**Reglas:**
1. no implementar en plugin lo que ya existe en el Core — verificar primero
2. si no existe en el Core, crearlo alli como generico, luego usarlo desde el plugin
3. plugin no crea su propia tabla, modal, dialogo, paginacion o formulario base
4. wrappers de dominio aceptables si solo inyectan defaults
5. **prohibido el "CRUD inferno"** — si un patron CRUD se repite en dos plugins, abstraer al Core antes del tercero
6. **prohibido el "schema inferno"** — tipos se generan desde OpenAPI, no se escriben a mano

## Core externo (systutor-core)

El kernel vive en un repo publico MIT (`systutor-core`) montado como submodule
en `vendor/systutor-core/` (ADR 0029). Reglas:

- Plugins, tools y commands importan infraestructura SOLO desde `systutor.*`
  (`systutor.kernel`, `systutor.core`, `systutor.api`, `systutor.contracts`,
  `systutor.sdk`). Prohibido importar `apps.api.app.kernel|core`.
- Config de negocio: `apps/api/app/config.py` define `GasSettings(Settings)` y
  registra la factory. Plugins que necesitan settings de negocio importan
  `get_settings` desde `apps.api.app.config`, nunca desde `systutor.core.config`.
- `PROJECT_ROOT` del repo gas: `apps.api.app.config.PROJECT_ROOT`. El
  `PROJECT_ROOT` de `systutor.core.config` apunta al repo del core.
- Instalar el submodule editable: `pip install -e vendor/systutor-core`.
- Cambios al kernel se desarrollan en `systutor-core` y se consumen fijando
  el commit del submodule por version explicita. Nunca editar
  `vendor/systutor-core` desde este repo.
- Actualizar submodule: `git submodule update --remote` + commit del nuevo
  pin cuando el cambio este aprobado.

## Plugins

Estructura minima: `plugin.json`, `backend/`, `frontend/`, `migrations/`, `README.md`. Todo plugin declara: identidad, version, `api_version`, dependencias, entrypoints, permisos.

**Obligatorio**: al agregar un permiso o evento nuevo, actualizar **simultaneamente** `plugin.json` (manifiesto) y `backend/plugin.py` (registro runtime: `register_permissions`, `register_events`). Si solo se actualiza uno, el sistema no reconoce el permiso/evento y falla con 403/Permission denied.

## Base de datos

PostgreSQL 16. `tenant_id` en tablas donde corresponda. Aislamiento logico por aplicacion. RLS futuro opcional. Migraciones con Alembic. No crear stored procedures ni triggers de negocio.

## Migracion legacy

No sync DB-to-DB ni dual-write. La migracion es por dominio via CSV + `manifest.json` → validacion → transformacion → PostgreSQL → auditoria. El migrador vive separado del backend principal.

## Eventos

Los eventos deben ser declarados, auditables, testeables y trazables. Usar eventos en vez de acoplamiento directo entre modulos.

## Spec Driven Development

Toda feature requiere spec con: alcance, riesgos, permisos, eventos, criterios de aceptacion. Flujo: idea → spec → revision → diseno tecnico → contrato API → implementacion → pruebas → PR → merge.

## Ley de vigencia documental

Las specs y docs versionados **no deben tratarse automaticamente como verdad vigente solo por existir**. En este repositorio la documentacion evoluciona por capas; por eso cada agente debe distinguir entre contexto historico y fuente activa.

### Jerarquia de verdad

1. ADR vigente manda en decisiones de arquitectura.
2. Spec activa mas nueva manda en funcionalidad del dominio.
3. Codigo implementado manda sobre una spec vieja cuando la spec quedo desactualizada y el cambio ya es real en el repositorio.
4. Spec historica sirve como contexto, no como contrato vigente.

### Estados de lectura obligatorios para specs

Toda spec debe interpretarse con una de estas categorias:

- `vigente` — documento canonico para decidir e implementar.
- `historica` — conserva contexto, origen o baseline; no manda sobre specs posteriores.
- `superada por` — existe un documento mas nuevo que reemplaza su rol principal.
- `absorbida en` — parte o todo su contenido fue movido a otra spec/index mas reciente.

### Reglas operativas

1. no usar una spec vieja como roadmap vigente si ya tiene banner o nota de historica/superada/absorbida
2. cuando dos specs choquen, prevalece la mas nueva que siga activa; si el choque persiste, revisar ADR y codigo real
3. no borrar historia util; marcar estado y redirigir al documento canonico actual
4. si una spec vieja sigue teniendo valor parcial, debe conservarse como baseline historica con nota explicita de que partes siguen vivas y cuales migraron
5. si el codigo ya evoluciono y la spec no, actualizar la spec o agregar nota de desalineacion; no seguir implementando desde una verdad documental obsoleta
6. al compactar specs, preferir banners, tablas de vigencia y referencias canonicas antes que fusionar o eliminar documentos indiscriminadamente

## Reglas para agentes

Leer Engram + AGENTS.md + docs antes de modificar codigo. Tocar la menor cantidad de archivos posible. Respetar limites kernel/plugins/tools/docs. No introducir dependencias base nuevas sin decision explicita. No mover logica al frontend si pertenece al backend. Crear pruebas. Actualizar docs. Dejar cambios consistentes con ADRs y specs.

Evitar: refactors amplios no pedidos, cambios especulativos, logica duplicada entre modulos, efectos secundarios ocultos, cambios silenciosos de arquitectura.

Si una tarea exige leer specs antiguas, tratarlas primero como contexto historico y confirmar cual es el documento canonico vigente antes de implementar.

## Testing y calidad

Herramientas: Ruff (lint+format), Pyright (typing), Pytest (backend), Vitest (frontend). Toda logica nueva requiere pruebas. Al cambiar backend/tests, correr `ruff check` y `pyright` como cierre tecnico.

**Obligatorio**: toda feature nueva debe incluir tests. Backend: tests de integracion con `TestClient` y SQLite. Frontend: tests de logica pura con Vitest. Si un componente usa dependencias incompatibles con `renderToStaticMarkup` (ej. Tooltip, contextos React), adaptarlo para que sea testeable (ej. atributo `title` nativo en vez de `Tooltip`). No se mergea sin tests.

## Pull Requests

Explicar: que cambia, por que, como se prueba, riesgos, modulos tocados, migraciones, eventos, permisos, docs afectados.

## Legacy

No asumir comportamiento del legacy sin evidencia. Documentar la fuente (VB, SQL Server, stored procedures, Grab2). Sin certeza: marcar como supuesto, pendiente de validacion o riesgo de migracion. No convertir suposiciones en reglas de negocio definitivas.

## Regla final

Si una decision parece rapida pero rompe modularidad, trazabilidad, migracion controlada o claridad arquitectonica, no debe implementarse como atajo permanente.
