# AGENTS.md

## Proposito

Este archivo define las reglas operativas para agentes de IA y colaboradores que trabajen en SYSTUTOR OSS.

Su objetivo es reducir ambiguedad, proteger la arquitectura y mantener consistencia tecnica durante la construccion del core, plugins, migradores y tooling interno.

---

## Principios del proyecto

SYSTUTOR OSS se construye con estas reglas base:

- no es una reescritura impulsiva del legacy;
- el legacy se absorbe por dominios;
- la logica de negocio vive en codigo Python auditable;
- no se introduce logica nueva en stored procedures o triggers;
- el kernel debe ser pequeno;
- los modulos de negocio deben vivir en plugins;
- los modulos deben comunicarse por eventos cuando aplique;
- toda accion importante debe ser auditable;
- la migracion legacy debe ser controlada, validada y trazable.

---
## Orden de lectura obligatorio

Antes de trabajar, todo agente debe leer en este orden:

1. **Engram memory** — llamar `mem_context` y `mem_search` con palabras clave de la tarea para recuperar decisiones, bugs, patrones y contexto de sesiones anteriores. Engram tiene prioridad sobre cualquier archivo .md.
2. `AGENTS.md`
3. `docs/avances/<modulo>.md` — documento de avance del módulo afectado (si existe)
4. ADR relacionado con la tarea
5. Spec de la feature
6. Contrato de datos/API si existe
7. Archivos afectados

No implementar únicamente a partir de una conversación o instrucción aislada.

## ADRs obligatorios

Antes de tomar decisiones tecnicas, leer:

- `docs/adr/0001-stack-base.md`
- `docs/adr/0002-arquitectura-monorepo.md`
- `docs/adr/0003-modelo-tenancy-permisos.md`
- `docs/adr/0004-runtime-plugins.md`
- `docs/adr/0005-event-bus-y-auditoria.md`
- `docs/adr/0006-migracion-legacy-csv-manifest.md`
- `docs/adr/0007-observabilidad.md`
- `docs/adr/0008-testing-y-calidad.md`
- `docs/adr/0009-spec-driven-development.md`

Si una tarea contradice un ADR aceptado, no implementarla sin proponer un nuevo ADR o una actualizacion explicita.

---

## Stack oficial

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL 16
- Redis
- Dramatiq + Redis
- Pydantic v2

### Calidad backend

- Pyright
- Ruff
- Pytest

### Frontend

- React
- Vite
- TypeScript
- Zustand
- TanStack Query
- React Router
- Tailwind CSS (utility-first)
- shadcn/ui (componentes sobre Tailwind)

### Infraestructura

- Docker Compose para desarrollo local
- Traefik para reverse proxy en produccion
- GitHub Actions para CI/CD

No introducir herramientas base alternativas sin justificacion y ADR cuando corresponda.

### Entorno local primario

El entorno local primario de trabajo es **Termux**.

Reglas operativas:

- no asumir Docker como mecanismo principal de ejecucion local;
- preferir ejecucion directa con `python3`, entorno virtual y variables `.env`;
- tratar `docker-compose.yml` como soporte secundario fuera de Termux;
- no asumir wheels binarias de Linux de escritorio;
- revisar compatibilidad real de dependencias nativas con Android/Termux antes de agregarlas;
- aceptar Python 3.13 en desarrollo local de Termux mientras el codigo siga siendo compatible con la base objetivo 3.12.

---

## Estructura del repositorio

La estructura objetivo del repositorio es:

```text
systutor-oss/
├── apps/
│   ├── api/
│   └── web/
├── packages/
│   ├── sdk/
│   ├── contracts/
│   └── ui/
├── plugins/
├── tools/
│   ├── migrator/
│   └── legacy-analyzer/
├── docs/
│   ├── adr/
│   ├── avances/
│   ├── specs/
│   └── contracts/
├── infra/
│   ├── docker/
│   └── compose/
├── AGENTS.md
├── README.md
└── pyproject.toml
```

Reglas:

- `apps/` contiene aplicaciones ejecutables;
- `packages/` contiene librerias compartidas;
- `plugins/` contiene modulos de negocio;
- `tools/` contiene herramientas internas;
- `docs/` contiene documentacion versionada;
- `infra/` contiene entorno local y despliegue.

---

## Reglas de arquitectura

### Kernel

El kernel provee infraestructura, no logica pesada de negocio.

Puede incluir:

- auth;
- users;
- roles;
- permissions;
- tenants;
- audit;
- events;
- plugin registry;
- config;
- storage;
- tasks;
- observability.

El kernel no debe contener logica propia de modulos como logistica, facturacion, CRM o inventario.

### Plugins

Cada plugin debe seguir contrato explicito.

Estructura minima:

```text
plugin/
├── plugin.json
├── backend/
├── frontend/
├── migrations/
├── permissions/
├── events/
└── README.md
```

Todo plugin debe declarar al menos:

- identidad;
- version;
- `api_version`;
- dependencias;
- entrypoint backend;
- entrypoint frontend;
- permisos.

### Eventos

Cuando un modulo necesite notificar cambios relevantes a otros modulos, preferir eventos sobre acoplamiento directo.

Los eventos deben ser:

- declarados;
- auditables;
- testeables;
- trazables.

### Base de datos

La base principal es PostgreSQL 16.

Reglas:

- no crear nueva logica de negocio en stored procedures;
- no crear triggers de negocio ocultos;
- usar migraciones con Alembic;
- aplicar `tenant_id` en tablas donde corresponda;
- aislar acceso por tenant desde la aplicacion.

### Tenancy y permisos

Primera version:

- `tenant_id` por tabla cuando aplique;
- aislamiento logico por aplicacion;
- RLS de PostgreSQL solo como mejora futura opcional;
- permisos con RBAC + claims.

Ejemplo de claims:

- `tenant_id`
- `branch_id`

No construir un motor de autorizacion excesivamente complejo en la primera etapa.

---

## Migracion legacy

Reglas obligatorias:

- no hacer sync DB-to-DB inicial;
- no hacer dual-write;
- FastAPI no escribe en SQL Server;
- la migracion es por dominio, no por tabla;
- usar CSV + `manifest.json`;
- validar estructura y dominio;
- auditar cada importacion;
- mantener trazabilidad con `legacy_id` cuando aplique.

Flujo base:

```text
legacy export
-> CSV + manifest
-> validacion
-> transformacion
-> PostgreSQL
-> auditoria
```

El migrador debe vivir separado del backend principal.

---

## Spec Driven Development

Toda feature importante debe empezar con spec.

Nadie debe implementar caracteristicas importantes sin:

- spec;
- alcance;
- riesgos;
- permisos;
- eventos;
- criterios de aceptacion.

Flujo oficial:

```text
idea
-> spec
-> revision
-> diseño tecnico
-> contrato API/datos
-> implementacion
-> pruebas
-> PR
-> merge
```

Si el cambio altera arquitectura o contrato base, tambien requiere ADR.

---

## Reglas para agentes

Todo agente debe:

- leer este archivo antes de modificar codigo;
- leer el documento de avance en `docs/avances/` del modulo afectado antes de trabajar;
- **leer la documentacion en `docs/` antes de hacer busquedas exhaustivas en el proyecto** — los documentos de avance contienen el estado detallado, los gaps y el historial de decisiones;
- solo si la informacion en `docs/` es insuficiente, hacer busquedas en el codigo fuente;
- leer la spec de la feature antes de implementarla;
- tocar la menor cantidad de archivos posible;
- respetar limites entre kernel, plugins, tools y docs;
- no introducir dependencias base nuevas sin decision explicita;
- no mover logica al frontend si pertenece al backend;
- no acoplar modulos innecesariamente;
- crear pruebas cuando agregue logica;
- actualizar documentacion si cambia comportamiento;
- dejar cambios consistentes con ADRs y specs.

Todo agente debe evitar:

- refactors amplios no pedidos;
- cambios especulativos;
- logica duplicada entre modulos;
- efectos secundarios ocultos;
- cambios silenciosos de arquitectura;
- mezcla de decisiones de negocio con infraestructura.

---

## Testing y calidad

Herramientas oficiales:

- Ruff para lint y format;
- Pyright para typing;
- Pytest para backend.

En este repositorio `ruff` y `pyright` funcionan como validaciones reales del entorno de trabajo.
No deben tratarse como herramientas opcionales, ausentes o "pendientes de instalar" al cerrar una tarea.

Reglas:

- toda logica nueva relevante requiere pruebas;
- dominio con pruebas unitarias;
- servicios y APIs criticos con pruebas de integracion;
- migradores con pruebas de casos validos y rechazo;
- permisos, auditoria y eventos deben probarse.
- cuando el cambio toque backend o tests Python, correr `ruff check` y `pyright` como parte del cierre tecnico;

No se considera terminado un cambio importante sin validacion suficiente para su riesgo.

---

## Pull Requests

Todo cambio relevante debe pasar por PR.

El PR debe explicar:

- que cambia;
- por que cambia;
- como se prueba;
- que riesgos tiene;
- que modulos toca;
- si agrega migraciones;
- si agrega eventos;
- si modifica permisos;
- si requiere actualizar documentacion.

---

## Prioridad actual del proyecto

La prioridad actual no es construir modulos grandes de negocio.

La prioridad es:

1. consolidar ADRs;
2. definir core minimo;
3. definir contrato de plugins;
4. definir spec del modulo piloto;
5. crear scaffold real del repositorio;
6. iniciar kernel base.

Modulo piloto recomendado:

- `logistics`

---

## Regla final

Si una decision parece rapida pero rompe modularidad, trazabilidad, migracion controlada o claridad arquitectonica, no debe implementarse como atajo permanente.

## Tema y colores

Reglas obligatorias para mantener consistencia entre claro/oscuro y evitar colores rotos en runtime:

- **PROHIBIDO usar colores hardcodeados** (`text-white`, `text-slate-300`, `bg-slate-950`, `border-slate-800`, etc.) en componentes JSX. Usar exclusivamente las variables CSS semanticas: `text-foreground`, `text-muted-foreground`, `bg-surface`, `bg-surface-alt`, `bg-card`, `border-border`, `border-input`, `border-ring`, etc.
- las unicas excepciones son colores semanticos de estado (badges de cylinder states, alertas, etc.) que representen informacion y no estructura visual;
- `text-white` solo es aceptable si semanticamente significa "blanco puro" (ej. iconos sobre fondo primary);
- no usar valores arbitrarios (`h-[...]`, `w-[...]`, `text-[...]`, etc); extender `theme.extend` si un valor se repite;
- no usar `@apply` en componentes; poner las utility classes directamente en JSX para que Tailwind pueda purgar;
- no agregar plugins Tailwind que no se usen (`forms`, `typography`, `daisyui`, etc);
- mantener `content` apuntando solo a archivos fuente del frontend;
- los colores CSS variables van en `index.css`, no en clases inline.

## Component Minimal

Reglas para mantener los componentes React reutilizables y evitar duplicacion:

- los componentes de UI (tablas, formularios, modales, selects, tooltips, paginacion, etc) deben vivir en `packages/ui/` o `apps/web/src/components/`, no duplicados en cada modulo o plugin;
- un plugin o feature NO debe crear su propia implementacion de tabla, modal o formulario; debe importar la version compartida;
- si un componente compartido no cubre el caso, extenderlo con props en lugar de clonarlo;
- los componentes de `shadcn/ui` son la fuente de verdad para componentes base; ante la duda, usar los de shadcn;
- no crear "variantes por modulo" de un mismo componente (ej. `LogisticsTable`, `InvoiceTable`, `InventoryTable`); una sola `Table` configurable por props;
- las excepciones requieren justificacion escrita en el README del modulo.

## Limites de modificacion

Un agente solo puede modificar archivos relacionados directamente con la tarea asignada.

No debe modificar:

- arquitectura global;
- configuracion base;
- contratos de plugins;
- permisos globales;
- migraciones existentes;
- estructura del monorepo;

salvo que la spec o ADR lo autorice explicitamente.

## Reutilizacion de componentes

Un agente debe priorizar el uso de componentes reutilizables del core (`apps/web/src/shared/ui/`).

Cuando un plugin necesite un comportamiento UI que aun no existe en el core:

1. crear primero el componente generico en `apps/web/src/shared/ui/`;
2. luego usarlo desde el plugin con props y funciones especificas del dominio.

Reglas:

- no implementar logica de estado, tabla, modal o debounce dentro de un plugin si existe un componente generico en `shared/ui/`;
- si el componente generico no cubre el caso exacto, extenderlo con props en lugar de clonarlo en el plugin;
- la excepcion es cuando el comportamiento es 100% especifico del dominio y no tiene sentido fuera de el;
- los wrappers de dominio son aceptables si solo inyectan defaults (columnas, fetchFn, placeholder) sin duplicar logica interna.

## Legacy

Ningun agente debe asumir comportamiento del legacy sin evidencia.

Si una regla proviene de VB, SQL Server, stored procedures, triggers o uso operativo real, debe documentarse la fuente.

Cuando no exista certeza, marcar como:

- supuesto;
- pendiente de validacion;
- riesgo de migracion.

No convertir suposiciones en reglas de negocio definitivas.
