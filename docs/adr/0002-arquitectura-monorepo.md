## ADR 0002 - Arquitectura Monorepo

## Estado

Aceptado

## Contexto

SYSTUTOR OSS tendrá backend, frontend, plugins, tooling de migración, documentación técnica y contratos compartidos.

El proyecto necesita una estructura que facilite:

* trabajo paralelo;
* consistencia arquitectónica;
* reutilización de contratos y utilidades;
* colaboración con agentes de IA;
* evolución modular;
* control claro de límites entre core, plugins, tooling e infraestructura.

SYSTUTOR OSS no debe crecer como una aplicación monolítica desordenada. Desde el inicio debe existir una separación explícita entre aplicaciones ejecutables, paquetes compartidos, plugins, herramientas internas y documentación.

## Decisión

SYSTUTOR OSS usará arquitectura monorepo.

La estructura base aprobada es:

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
│   └── logistics/
├── tools/
│   ├── migrator/
│   └── legacy-analyzer/
├── docs/
│   ├── adr/
│   ├── specs/
│   └── contracts/
├── infra/
│   ├── docker/
│   └── compose/
├── AGENTS.md
├── README.md
└── pyproject.toml
```

## Criterios estructurales

### `apps/`

Contiene las aplicaciones ejecutables principales.

Inicialmente:

* `apps/api`: backend principal con FastAPI.
* `apps/web`: frontend principal con React + Vite.

`apps/api` debe contener el kernel, la API pública, configuración base y puntos de integración, pero no debe absorber lógica pesada de negocio que pertenezca a plugins.

`apps/web` debe contener el shell principal del frontend, layouts globales, rutas principales y carga de módulos, pero no debe concentrar pantallas específicas de negocio que pertenezcan a plugins.

---

### `packages/`

Contiene piezas reutilizables compartidas.

Inicialmente:

* `packages/sdk`: SDK para crear plugins, registrar eventos, permisos, rutas y capacidades.
* `packages/contracts`: contratos compartidos entre backend, frontend, plugins y herramientas.
* `packages/ui`: componentes visuales reutilizables del frontend.

`packages/contracts` será la fuente principal para contratos compartidos, evitando duplicación de definiciones entre módulos.

---

### `plugins/`

Contiene módulos de negocio instalables.

Inicialmente:

* `plugins/logistics`

Los plugins deben tener estructura propia y no depender de imports internos no públicos del kernel.

Cada plugin debe declarar explícitamente:

* identidad;
* versión;
* dependencias;
* permisos;
* eventos;
* migraciones;
* entrypoints backend/frontend.

Durante la fase inicial los plugins vivirán dentro del monorepo para facilitar desarrollo, revisión y versionado. En el futuro, algunos plugins podrían moverse a repositorios separados si el ecosistema lo requiere.

---

### `tools/`

Contiene herramientas internas de soporte, análisis y migración.

Inicialmente:

* `tools/migrator`: migrador CSV + manifest hacia PostgreSQL.
* `tools/legacy-analyzer`: herramienta para analizar SQL Server legacy, tablas, vistas, SP, triggers y dependencias.

Las herramientas internas no deben mezclarse con la API principal ni con plugins de negocio.

---

### `docs/`

Contiene documentación versionada.

Inicialmente:

* `docs/adr`: decisiones arquitectónicas.
* `docs/specs`: specs funcionales y técnicas.
* `docs/contracts`: contratos humanos del proyecto.

Toda decisión estructural importante debe estar documentada mediante ADR.

---

### `infra/`

Contiene artefactos de infraestructura, entorno local y despliegue.

Inicialmente:

* `infra/docker`
* `infra/compose`

La infraestructura debe permitir levantar el entorno de desarrollo de forma reproducible.

## Reglas de dependencia

Las dependencias internas deben respetar estos límites:

```text
apps -> packages
apps -> plugins mediante runtime definido
plugins -> packages
tools -> packages
docs -> no aplica
infra -> no aplica
```

Reglas:

* `plugins/` no debe importar código interno no público de `apps/api`.
* `apps/api` no debe depender directamente de detalles internos de plugins.
* `packages/contracts` debe evitar depender de aplicaciones ejecutables.
* `packages/sdk` debe exponer APIs estables para plugins.
* `tools/` puede reutilizar contratos, pero no debe convertirse en dependencia obligatoria del runtime principal.

## Consecuencias

* Backend, frontend y tooling compartirán una sola raíz de versionado.
* Los plugins convivirán dentro del mismo repositorio durante la fase inicial.
* La estructura deberá mantenerse estable para facilitar automatización y generación de código.
* Los agentes de IA tendrán límites claros sobre dónde agregar o modificar archivos.
* La separación por carpetas ayudará a evitar que el kernel absorba lógica de negocio.
* Cualquier separación futura a multirepo requerirá una nueva decisión arquitectónica.
* Cualquier cambio estructural importante deberá proponerse mediante ADR.
