# Reporte tecnico mensual - 2026-07-10 a 2026-08-10

## Estado del reporte

- Tipo: reporte tecnico developer-facing
- Corte: 2026-08-10
- Ventana analizada: 2026-07-10 -> 2026-08-10
- Fuentes: `git log`, `docs/specs/core/`, `docs/changelogs/`, `docs/avances/`, ADRs, estructura real del repo, memorias Engram
- Nota metodologica: no fue posible consultar milestones de GitHub desde `gh` porque la herramienta no existe en este entorno. La evidencia de milestone se reconstruyo desde commits, changelogs y Engram.

## Hallazgos de code review primero

### 1. Alto - la arquitectura declarada de inter-plugin sigue sin cerrarse y el codigo real mantiene imports directos entre plugins

La regla documental vigente dice que ningun plugin debe importar modelos de otro plugin directamente y que la comunicacion debe pasar por `core/internal_api/` (`docs/specs/faltantes.md:7-8`, `22-28`, `104-116`).

La implementacion real todavia no llego ahi:

- `plugins/logistics/backend/services/product_bridge.py:1-18` importa `plugins.productos.backend.models` y `plugins.productos.backend.schemas` de forma directa.
- `plugins/stock/backend/services/catalog.py:6-7` importa `LogisticsWarehouse` y `Product` desde plugins hermanos.
- `plugins/logistics/backend/services/stock_bridge.py:16-20` consume modelos y servicios de `stock` y `productos` directamente.

Impacto tecnico:

- dificulta separar plugins fuera del monorepo;
- hace mas fragil cualquier refactor de modelos internos;
- contradice la direccion de `core/internal_api` y deja deuda arquitectonica visible.

### 2. Alto - el kernel ya contiene comportamiento especifico de `logistics`, debilitando neutralidad del core

`apps/api/app/kernel/plugins/persistent.py:116-181` ejecuta `_ensure_logistics_catalogs()` dentro del flujo generico de sincronizacion del runtime. Esa funcion importa modelos y definiciones concretas de `logistics` y repuebla catalogos del plugin desde el kernel.

Impacto tecnico:

- el core deja de ser estrictamente generico;
- el runtime de plugins conoce detalles de un dominio concreto;
- futuras reglas especiales por plugin pueden seguir contaminando el kernel si no se extraen a lifecycle hooks o bootstrap del propio plugin.

### 3. Medio - el shell frontend hace eager-load de todos los plugins, incluso deshabilitados

`apps/web/src/features/plugins/runtime.tsx:29-32` usa `import.meta.glob(..., { eager: true })` para registrar frontend plugins.

Impacto tecnico:

- el bundle del shell carga codigo de plugins aunque el runtime backend los marque disabled;
- el aislamiento actual es funcional y visual, no de carga;
- a medida que `logistics`, `ventas`, `crm` y `productos` sigan creciendo, el costo de bootstrap del shell va a subir aunque el usuario no use todos los modulos.

### 4. Medio - hay deriva anti-monolito clara en backends clave

Conteo actual de lineas:

- `plugins/logistics/backend/router.py` -> 2577 lineas
- `plugins/logistics/backend/schemas.py` -> 1926 lineas
- `plugins/productos/backend/router.py` -> 1774 lineas
- `plugins/crm/backend/router.py` -> 1070 lineas
- `plugins/stock/backend/router.py` -> 807 lineas

Esto ya contradice de hecho la regla operativa del repo de no seguir creciendo archivos grandes. El caso mas critico sigue siendo `logistics`, aunque el documento de avance ya congelo el crecimiento del router principal y empuja nuevos endpoints a subrouters (`docs/avances/logistics.md:30-33`).

### 5. Medio - hay drift documental en documentos base y en avance de `logistics`

Dos ejemplos concretos:

- `README.md:19-39` todavia describe un sistema sin modulos grandes, con `apps/web` como "Placeholder frontend" y `logistics` como "Plugin ejemplo inicial". Eso ya no representa el repositorio real.
- `docs/avances/logistics.md:19` afirma que `almacen movil` y `flota` quedaron retirados del runtime, pero entre `2026-07-13` y `2026-08-10` el repo y Engram muestran reconstruccion activa de `VehicleSession`, `MOBILE warehouses`, reconciliacion y control de ruta.

Impacto tecnico:

- un desarrollador nuevo puede arrancar desde una verdad documental obsoleta;
- el riesgo mayor no es cosmetico: afecta decisiones de implementacion y lectura del estado real.

## Filosofia de trabajo del sistema y por que se eligio

La filosofia dominante del mes fue una combinacion de cuatro decisiones:

1. `ADR 0009` - Spec Driven Development.
2. atomizacion de cambios en specs cortas o slices incrementales.
3. separacion explicita entre `core`, `shell` y `plugins`.
4. trazabilidad tecnica por capas: ADR -> spec -> codigo -> tests -> changelog -> memoria Engram.

### Por que se eligio este modelo

`ADR 0009` fija el problema base: varios humanos y agentes de IA trabajando sobre un ERP modular sin specs terminan produciendo cambios grandes, ambiguos y poco trazables. El costo de escribir specs sube, pero baja la ambiguedad operativa, de negocio y de arquitectura.

Durante este mes eso se volvio visible en la practica:

- `Jornadas` no evoluciono como un unico documento enorme; avanzo por slices pequenos (`0024`, `0024.1.3.3`, `0024.1.3.4`, `0030`, `0031`, `0037`, `0041`, `0043`).
- `Planificacion` se redefinio con semantica propia en `0025`, luego bajo a correcciones concretas en `0044`.
- la consola operativa no nacio como "UI bonita" sino como sistema de entrada estructurada del core: `ADR 0022`, `ADR 0023`, `ADR 0028`, `SPEC 0027`.
- `stock` paso de una semantica mas valorizada a una direccion de "quantity-first" con decisiones explicitadas y luego endurecidas en Engram el 2026-08-10.

### Que significa "atomical spec based" en este repo

No significa escribir specs pequenas por gusto. Significa:

- partir una necesidad grande en invariantes y gaps verificables;
- implementar slices que se puedan revisar de forma aislada;
- evitar PRs o sesiones que cambien demasiadas reglas de negocio al mismo tiempo;
- dejar evidencia tecnica exacta de que regla cambio, donde y por que.

Ejemplo claro del mes:

- `0029` no describe un rediseño abstracto de `logistics`; identifica cuatro gaps reales del flujo operativo.
- `0031` fija coherencia entre estados, retorno y semantica de seriales.
- `0043` documenta un bloque de cambios de sesion intensiva ya implementados, separando frontend, backend, transiciones y migraciones.

### Beneficio real observado

El modelo permitio que la implementacion creciera rapido sin perder del todo el hilo tecnico:

- changelogs explican deltas visibles al operador;
- specs explican intencion, alcance y criterio;
- Engram captura el trabajo del mismo dia que aun no esta reflejado en un commit "limpio";
- el code review puede comparar comportamiento real contra spec, no contra memoria humana.

## Core y shell como partes independientes del sistema

## Core

### Definicion operacional

En este repo, `core` no es modulo de negocio. Es infraestructura transversal y superficie compartida.

### Core backend

Responsabilidades reales:

- auth, JWT, current user, permisos y tenancy;
- auditoria, eventos y outbox;
- runtime persistente de plugins;
- migraciones de plugins y registro de estados;
- APIs administrativas `/api/v1/core/*`;
- bootstrap de FastAPI y lifecycle del sistema.

Rutas y carpetas clave:

- `apps/api/app/core/`
- `apps/api/app/kernel/`
- `apps/api/app/api/v1/core/`
- `apps/api/app/core/lifecycle.py`
- `apps/api/app/core/database.py`
- `apps/api/app/api/deps.py`

Avances del ultimo mes en core backend:

- `2026-07-14`: documentos y firmas digitales entran en runtime core con endpoints y migracion base.
- `2026-08-07`: arranca infraestructura dual sync/async con `SPEC 0045` en `database.py`, `deps.py` y `lifecycle.py`.
- el core tambien absorbio reglas de soporte para claims contextuales y runtime plugin ya visibles en docs de `stock`, aunque la mayor consolidacion de eso venia de iteraciones anteriores.

### Core frontend/shared

Responsabilidades reales:

- componentes base en `apps/web/src/shared/ui/`;
- wrappers de router/query/api para plugins;
- componentes reutilizables de consola Monaco y `resource-calendar`;
- patrones de formularios del sistema.

Rutas y carpetas clave:

- `apps/web/src/shared/ui/`
- `apps/web/src/lib/`
- `apps/web/src/shared/api/client.ts`
- `packages/sdk/frontend/index.ts`

Avances del ultimo mes en core frontend/shared:

- `2026-07-22`: `paginated-data-table.tsx` sube a shared para reutilizacion multi-modulo.
- `2026-07-24`: nacen `console-editor/`, `console-shell/`, piezas de `resource-calendar/`, `confirm.ts` y `neofetch.ts` como capacidades transversales del shell/core.
- `2026-07-24` y `2026-07-25`: se formaliza identidad visual compartida en `apps/web/src/shared/ui/README.md` y skill `frontend-ui-identity`.
- `2026-07-24`: fix de cold-start del calendario mediante `font-display: optional` y proteccion del grid mensual.

### Observacion critica sobre core frontend

El shared frontend existe, pero hoy vive mayormente dentro de `apps/web/src/shared/`, no en `packages/ui`. Eso vuelve difuso el borde entre "core reutilizable" y "shell host".

## Shell

### Definicion operacional

El `shell` es la aplicacion host de frontend. No es owner de negocio. Es owner de acceso, layout, runtime y navegacion.

### Responsabilidades reales

- login, logout y bootstrap de sesion;
- carga del runtime plugin en frontend;
- rutas protegidas `/app/*`;
- sidebar, header, dashboard y boundaries de permisos;
- exposicion del sistema y de plugins habilitados.

Rutas y carpetas clave:

- `apps/web/src/app/`
- `apps/web/src/features/auth/`
- `apps/web/src/features/plugins/`
- `apps/web/src/features/system/`
- `apps/web/src/shared/layout/`
- `apps/web/src/app/router.tsx`

### Avances del ultimo mes en shell

- el shell dejo de ser una base casi vacia y paso a hospedar un runtime frontend real de plugins.
- `runtime.tsx` y las boundaries de plugin ya filtran por estado habilitado y permisos del usuario.
- el shell absorbio la consola operativa y el calendario como primitivas de entrada, no como widgets aislados.
- el shell paso a ser tambien punto de integracion de `ventas/cotizacion`, `logistics/planning` y dashboards compartidos.

### Limite sano entre core y shell

La lectura correcta del repo hoy es:

- `core backend` = infraestructura server-side
- `core frontend/shared` = componentes y wrappers reusables
- `shell` = host ejecutable del frontend
- `plugins` = negocio real

El problema no es que el limite no exista; el problema es que en frontend shared y shell aun estan demasiado cerca fisicamente.

## Cronologia tecnica absoluta del periodo

## 2026-07-10

- Evidencia: commits `2f04aa1`, `6721015`, `ce7ff42`, `df32529`, `78e2cb1`, `5b02c43`, `0c2f253`.
- Trabajo visible: refinamiento visual en CRM y ficha de cliente.
- Impacto: no cambia arquitectura de `core`, `shell`, `stock`, `productos` o `logistics`; es churn UI localizado.

## 2026-07-13

- Evidencia: commit `9a0c24b`.
- Trabajo visible: base documental para reconstruccion de `almacen movil` y `vehicle session`.
- Interpretacion: dia de preparacion de dominio y de framing de la nueva etapa operativa de `logistics`.

## 2026-07-14

- Evidencia: commit `8ee38a5`.
- Implementacion principal: contratos, posesion de cliente, documentos y firmas digitales.
- Capas tocadas:
  - core backend: `api/v1/core/documents.py`, `signatures.py`, kernel de documents/signatures.
  - logistics backend: contratos, resumen por cliente, documentos contractuales.
  - frontend: `ContractsPage.tsx`, dialogos de detalle contractual, piezas CRM.
- Lectura tecnica: arranca un patron donde el `core` absorbe primitivas de documento/firma y `logistics` las consume desde un caso de uso de negocio.

## 2026-07-15

- Spec creada: `0024-vehicle-session-stepper.md`.
- Evidencia de implementacion: commit `6ca85d7`.
- Implementacion principal: stepper de jornada sobre detalle de sesion.
- Archivos/capas relevantes: DTOs y servicios de sesion/reconciliacion en backend; `SessionStepper.tsx` y `VehicleSessionDetailPage.tsx` en frontend.
- Importancia: este dia empieza la transicion de `logistics` desde CRUD de envases/rutas hacia runtime operativo de jornada.

## 2026-07-18

- Specs creadas: `0024.0.1`, `0024.1.1`, `0024.1.2`, `0024.1.3.1`, `0024.1.3.2`.
- Evidencia de implementacion: commits `6113247` y `fcd356f`.
- Implementacion principal:
  - `VehicleSession` como aggregate operativo mas fuerte;
  - operaciones de ruta;
  - carta porte inicial;
  - reconstruccion del contexto de jornada y carga.
- Capas tocadas:
  - backend `logistics`: `sessions.py`, `session_operations.py`, `load_plans.py`, `reconciliation.py`, `route_operations.py`, `session_waybills.py`.
  - frontend `logistics`: `SessionStepper.tsx`, tabs de carga/reconciliacion/resumen, `VehicleSessionConsole.tsx`, `RouteModal.tsx`.
- Lectura tecnica: a partir de aqui `logistics` deja de ser solo data entry y empieza a parecerse a un TMS-lite operable.

## 2026-07-20

- Spec creada: `0024.1.3.3`.
- Evidencia de implementacion: commit `8034755`.
- Implementacion principal: reconciliacion controlada sobre incidencias de ruta.
- Impacto: la jornada ya no registra solo "lo que salio" sino tambien el desajuste explicito entre esperado, hecho fisico e incidencia.

## 2026-07-21

- Specs creadas: `0024.1.3.4`, `0024.1.3.5`, `0024.1.3.6`, `0024.3.1`.
- Evidencia de implementacion: commit `3778484`.
- Changelogs asociados:
  - `2026-07-21-jornadas-cantidad-obligatoria-en-carga-operativa.md`
  - `2026-07-21-jornadas-espanolizacion-formal.md`
  - `2026-07-21-customer-scan-fallback-register-cylinder.md`
  - `2026-07-21-real-warehouses-dropdowns.md`
- Implementacion principal:
  - seriales en carga operativa;
  - `stop result` minimo por parada;
  - resumen operacional de jornada;
  - cancelacion temprana;
  - dropdowns que filtran almacenes `MOBILE` fuera de UX general;
  - fallback de registrar envase desde scanner cuando el serial no existe.
- Valor tecnico: se afinaron reglas de entrada operativa y se aplico la ley del contexto operativo del repo: menos codigos crudos, mas semantica para el operador.

## 2026-07-22

- Spec creada: `0025-planificacion-calendar-first-y-reserva-de-capacidad.md`.
- Evidencia de implementacion: commits `7b63dc2` y `35ad1d0`.
- Changelogs asociados:
  - `2026-07-22-db-index-batch-serio.md`
  - `2026-07-22-productos-catalogos-y-busqueda.md`
  - `2026-07-22-productos-paginacion-ui.md`
  - `2026-07-22-envases-paginacion-real.md`
  - `2026-07-22-envases-busqueda-pg-trgm.md`
  - `2026-07-22-correccion-de-estado-envases.md`
  - `2026-07-22-retiro-escaneo-en-campo-envases.md`
  - `2026-07-22-seriales-autoagregado-numerico.md`
  - `2026-07-22-contratos-derecho-cupo.md`
- Implementacion principal:
  - planificacion se redefine como reserva de capacidad, no como sombra de jornada;
  - batch serio de indices en `logistics`, `productos`, `stock` y `crm`;
  - paginacion real en `Envases`;
  - `pg_trgm` para busqueda de envases y productos;
  - copy operativo de `Envases` se corrige para distinguir correccion manual vs flujo principal;
  - retiro visible de acciones que ya no encajan en la UX principal.
- Lectura tecnica: este dia mezcla deuda de performance, limpieza semantica y construccion de `shared ui` reutilizable.

## 2026-07-23

- Sin evidencia material local relevante en las fuentes revisadas.

## 2026-07-24

- Spec creada: `0027-cotizacion-ui-tui-hibrida.md`.
- Evidencia de implementacion: commits `bf75dd9`, `9fc8587`, `9436f55`, `4d666e5`.
- ADRs directamente activados: `0022` y `0023`.
- Changelog asociado: `2026-07-24-calendario-planificacion-deforme-cold-start.md`.
- Implementacion principal:
  - milestone de consola operativa completa;
  - adopcion practica de Monaco como superficie de entrada estructurada;
  - parser/autocomplete/help de DSL de cotizacion;
  - visor de cotizaciones y toggle UI/TUI;
  - hardening del calendario de planificacion ante cold start.
- Evidencia Engram: la sesion `#481` registra autocompletado funcional, simetria frontend/backend del parser, `--help`, case-insensitivity y 22 tests frontend + 5 backend.
- Lectura tecnica: el shell deja de ser solo host y pasa a alojar una primitiva de operacion avanzada del sistema.

## 2026-07-25

- Evidencia de implementacion: commit `d6cde96`.
- Evidencia documental: commits `7a2033d`, `c2873a7` y `docs/changelogs/2026-07-25.md`.
- Implementacion principal:
  - soporte local para arrancar Redis con `npm run services`;
  - formulario visual de cotizacion consolidado;
  - `CustomerSelect`, `ProductLinesEditor`, `VehicleSelect`, `CotizacionForm`;
  - formalizacion de identidad visual compartida y del flujo QuoteDraft -> Planning.
- Lectura tecnica: `ventas/cotizacion` queda como primer caso de uso real bajo `ADR 0028` (un caso de uso, multiples adaptadores).

## 2026-07-26

- Sin evidencia material local relevante en las fuentes revisadas.

## 2026-07-27

- Specs creadas: `0028-draft-overlay-planificacion.md`, `0029-flujo-operativo-minimo.md`.
- Evidencia de implementacion: commit `eda897d`.
- Implementacion principal:
  - `stock` cierra gaps transaccionales de `SPEC 0016.2`;
  - `ventas` agrega modo formulario sobre mismo use case;
  - `DraftOverlay` integra drafts confirmados y borradores en planificacion;
  - identidad UI de frontend se vuelve contrato operativo para agentes.
- Lectura tecnica: este dia consolida dos ideas fuertes del repo: `stock` como modulo transaccional serio y `ventas` como dominio expuesto por varios adaptadores sin duplicar logica.

## 2026-07-28

- Sin evidencia material local relevante en las fuentes revisadas.

## 2026-07-29

- Sin evidencia material local relevante en las fuentes revisadas.

## 2026-07-30

- Specs creadas: `0029B`, `0029C`, `0030`, `0031`, `0036`, `0037`.
- Evidencia de implementacion: commits `708a026` y `1424719`.
- Implementacion principal:
  - control de ruta y telemetria;
  - coherencia de seriales y de sesion;
  - filtrado de almacenes `MOBILE` como detalle tecnico, no UX normal;
  - split de `SessionRouteTab` para bajar complejidad de frontend.
- Lectura tecnica: es un dia bisagra donde varias specs nacen casi en paralelo al codigo para fijar invariantes que el runtime ya estaba exigiendo.

## 2026-07-31

- Evidencia de implementacion: commits `2a46e70`, `5a8d4df`, `a4dff60`.
- Implementacion principal:
  - hardening del route builder;
  - GPS, direcciones y fallbacks de `route_stop`/`customer`;
  - eventos de ubicacion de cilindro;
  - cierre de bugs y actualizacion de changelog.
- Lectura tecnica: `0036`, `0036.1` y `0036.2` aterrizan como control de contexto espacial y visual del flujo de jornada.

## 2026-08-01

- Sin evidencia material local relevante en las fuentes revisadas.

## 2026-08-02

- Evidencia de implementacion: commit `74f6a55`.
- Implementacion principal:
  - geolocalizacion de almacenes;
  - motor de exceso contractual;
  - limpieza de warehouse primario;
  - toques coordinados en `logistics` y `stock`.
- Lectura tecnica: el dominio de contratos deja de ser solo pantalla y empieza a influir en reglas operativas y lectura espacial.

## 2026-08-03

- Specs creadas: `0038`, `0039`, `0040`.
- Evidencia de implementacion: commit `bf416c8`.
- Implementacion principal:
  - llenado atomico de cilindros;
  - ubicacion actual atomica para jornadas;
  - ajuste de `stock` todavia bajo semantica de costo activo en `0039`.
- Capas tocadas:
  - `logistics`: `services/cylinders.py`, `cylinder_location.py`, `session_waybills.py`, `snapshots.py`.
  - frontend: `CylinderFillingDialog.tsx`, route-builder y `VehicleSession*`.
  - core/shared: geocode y componentes de mapa.
- Lectura tecnica: dia fuerte de integracion entre trazabilidad fisica, UI operacional y soporte de ubicacion.

## 2026-08-04

- Specs creadas: `0040.1`, `0040.2`.
- Evidencia local: commit `0c6bab0`, `docs/avances/logistics.md:21-29`, memoria Engram `#656`.
- Implementacion principal:
  - slice criogenico `source_product_id -> result_product_id`;
  - receta criogenica en ADR activo del producto resultado;
  - `fill_operation_id` para correlacion de corrida;
  - diseño frontend de planta de llenado criogenico.
- Lectura tecnica: la spec nace el 08-04 y la evidencia de implementacion se distribuye entre update documental del mismo dia y el commit operativo del 08-05.

## 2026-08-05

- Specs creadas: `0040.3`, `0041`, `0043`.
- Evidencia de implementacion: commits `a8607c5` y `36ec555`.
- Implementacion principal:
  - tanques criogenicos como contenedor especifico;
  - entrega desde composicion y serial rapido;
  - paquete de cambios operativos intensivos en jornadas;
  - fix de carta porte;
  - migracion `050_widen_ledger_source_id.py`.
- Lectura tecnica: es el dia mas cercano a un "milestone operativo" antes de la estabilizacion de campo del 08-10.

## 2026-08-06

- Evidencia de implementacion: commits `f2b9a9c`, `d933c41`, `59b8264`.
- Implementacion principal:
  - pickup/recogo con origen historico;
  - subida real al camion;
  - liberacion de posesion del cliente;
  - guard SQLite para migracion `050`;
  - continuidad de slices criogenicos y de planning.
- Lectura tecnica: aqui se endurece la coherencia entre posesion, camion, retorno y ruta.

## 2026-08-07

- Specs creadas: `0044`, `0045`.
- Evidencia de implementacion: commit `fe0dfb5`.
- Implementacion principal:
  - planning con clientes y direcciones de la jornada, auto-creacion de ruta;
  - arranque parcial de migracion sync -> async por router;
  - fixes de reconciliacion/recogo/posesion;
  - migracion de productos.
- Lectura tecnica: mezcla feature operativa y deuda estructural de performance backend. `0045` queda iniciado, no cerrado.

## 2026-08-08

- Sin evidencia material local relevante en las fuentes revisadas.

## 2026-08-09

- Sin evidencia material local relevante en las fuentes revisadas.

## 2026-08-10

- Evidencia principal: memorias Engram recientes del proyecto.
- Trabajo registrado:
  - `#739` - desacople de `stock.adjust` respecto de costo activo.
  - `#741` - decision arquitectonica: `stock` como pure inventory counter.
  - `#742` - ajuste positivo permitido aun con balance cero y costo legado 0.
  - `#744` - UI de ajuste sin lenguaje de costo.
  - `#745` - correccion persistente de typo `Industriall` en productos de oxigeno.
  - `#747` - fix de elegibilidad de vacios criogenicos por warehouse fallback.
  - `#748` - normalizacion de tanques criogenicos a `FUENTE DE PIEDRA-MALAGA` con migracion `052`.
  - `#750` - ADR validation de llenado criogenico acepta `cargo_description` cuando falta `label`.
  - `#754` - restauracion de migracion `053` como no-op historico; una revision aplicada no debe borrarse.
  - `#757` - cierre de sesion ya no intenta transicion invalida `EN_RUTA -> EN_ALMACEN_VACIO`.
  - `#758` - reconciliacion deja de duplicar `TRANSFER_IN` y conteo fisico.
  - `#755` - milestone: `logistics` se considera estable tras el primer movimiento serio real.
- Lectura tecnica: este dia no es "ruido post-entrega"; es la verdadera estabilizacion operativa contra datos y flujos reales.

## Matriz spec -> primera evidencia de implementacion

| Familia / spec | Fecha de spec | Primera evidencia de implementacion | Observacion |
|---|---|---|---|
| `0024` Vehicle Session Stepper | 2026-07-15 | 2026-07-15 (`6ca85d7`) | spec e implementacion mismo dia |
| `0024.0.1`, `0024.1.1`, `0024.1.2`, `0024.1.3.1`, `0024.1.3.2` | 2026-07-18 | 2026-07-18 (`fcd356f`) | arranque fuerte de jornadas |
| `0024.1.3.3` | 2026-07-20 | 2026-07-20 (`8034755`) | reconciliacion controlada |
| `0024.1.3.4`, `0024.1.3.5`, `0024.1.3.6`, `0024.3.1` | 2026-07-21 | 2026-07-21 (`3778484`) | resumen, stop result, seriales, cancelacion |
| `0025` Planificacion calendar-first | 2026-07-22 | 2026-07-22 (`35ad1d0`) | despues refinada en 07-24 y 08-07 |
| `0027` Cotizacion consola + formulario | 2026-07-24 | 2026-07-24 (`9436f55`, `9fc8587`) | apoyada por ADR `0022`, `0023`, `0028` |
| `0028` DraftOverlay | 2026-07-27 | 2026-07-27 (`eda897d`) | overlay de drafts en planning |
| `0029` Gaps reales del flujo operativo | 2026-07-27 | 2026-07-30 (`708a026`) | se implementa pocos dias despues |
| `0029B`, `0029C`, `0030`, `0031`, `0036`, `0037` | 2026-07-30 | 2026-07-30 (`708a026`) y 2026-07-31 (`5a8d4df`) | bloque de coherencia operativa y telemetria |
| `0038`, `0039`, `0040` | 2026-08-03 | 2026-08-03 (`bf416c8`) | llenado atomico y ubicacion actual |
| `0040.1`, `0040.2` | 2026-08-04 | 2026-08-04 (`docs/avances/logistics.md`, Engram `#656`) y 2026-08-05 (`36ec555`) | slice criogenico backend/frontend |
| `0040.3`, `0041`, `0043` | 2026-08-05 | 2026-08-05 (`36ec555`, `a8607c5`) | tanques, entrega desde composicion, fixes de sesion |
| `0044`, `0045` | 2026-08-07 | 2026-08-07 (`fe0dfb5`) | `0045` queda parcial, no cerrada |

## Avances por dominio

## Logistics

Fue el dominio dominante del mes.

Ejes de avance:

- paso de CRUD ampliado a runtime operacional de jornada;
- unificacion de seriales, composicion, ruta, retorno y reconciliacion;
- maduracion de `RouteOperation` y de contexto espacial;
- consolidacion de contratos, posesion y carta porte;
- apertura del frente criogenico;
- estabilizacion con movimiento real el 2026-08-10.

Lo mas relevante para un developer:

- el centro de gravedad ya no es `LogisticsPage.tsx` sino `vehicle sessions`, `route operations`, `reconciliation`, `load serials`, `session waybills` y `planning`;
- el modulo tiene mas comportamiento real que lo que su README base o partes viejas de la documentacion hacen pensar;
- la principal deuda ya no es falta de feature, sino exceso de acoplamiento, archivos gigantes y drift documental.

## Stock

`stock` no fue el modulo con mas commits, pero si tuvo cambios estructurales importantes.

Durante el periodo:

- venia de un estado "cerrado" funcional (`docs/avances/stock.md`), con eventos, auditoria, ledger y pruebas serias;
- el 2026-07-22 recibe indices hot-path y mejoras de lectura;
- el 2026-07-27 cierra gaps transaccionales de `0016.2`;
- el 2026-08-03 todavia convive con `0039` y una semantica de costo activo para ajuste positivo;
- el 2026-08-10 Engram registra el viraje fuerte a `stock` como contador puro de inventario.

Lectura tecnica:

- `stock` esta estable como modulo transaccional;
- su deuda actual es semantica y arquitectonica, no funcional;
- el sistema aun arrastra columnas y compatibilidad de costo, pero la direccion de negocio ya es quantity-first.

## Productos

`productos` tuvo dos bloques claros:

1. performance y UX de listados/busqueda (`2026-07-22`);
2. extension del modelo para recetas criogenicas (`2026-08-04` / `2026-08-05`).

Puntos tecnicos clave:

- `pg_trgm` y paginacion visible preparan el modulo para escala real;
- el producto resultado criogenico ya puede declarar receta contra producto fuente;
- `productos` pasa a ser owner mas explicito de la informacion necesaria para llenar cilindros criogenicos.

## Ventas y consola operativa

Este fue el segundo gran frente del mes despues de `logistics`.

Puntos tecnicos clave:

- `ventas/cotizacion` se convirtio en primer consumidor serio del stack `Monaco + DSL + shell + shared/application`;
- el repo ya no trata la consola como experimento UI, sino como modo serio de operacion tipada;
- `ADR 0028` evita divergence entre formulario y consola al compartir use case.

Esto importa mucho porque abre camino a futuros DSLs de `logistics`, agenda u otros dominios sin rehacer infraestructura de entrada.

## Core y shell

El avance aqui fue menos "feature" y mas fundacional:

- primitives de consola y calendario en shared/core frontend;
- documentos y firmas en core backend;
- comienzo de async incremental;
- shell consolidado como host real del runtime plugin.

## Milestones reconstruidos del periodo

## 1. Milestone de consola operativa completa - 2026-07-24

Fuentes:

- commits `bf75dd9`, `9436f55`, `9fc8587`
- Engram `#481`
- ADR `0022`, ADR `0023`, ADR `0028`

Estado alcanzado:

- DSL de cotizacion usable;
- autocompletado contextual real;
- simetria frontend/backend del parser;
- tests duales y ayuda integrada.

## 2. Milestone de planificacion calendar-first utilizable - 2026-07-22 -> 2026-08-07

Fuentes:

- `SPEC 0025`
- changelog de cold start del 2026-07-24
- `SPEC 0044`
- commit `fe0dfb5`

Estado alcanzado:

- planning deja de ser solo lista auxiliar y pasa a reservar capacidad;
- luego agrega clientes/direcciones y auto-creacion de ruta.

## 3. Milestone criogenico funcional - 2026-08-03 -> 2026-08-10

Fuentes:

- `0040`, `0040.1`, `0040.2`, `0040.3`
- `docs/avances/logistics.md`
- Engram `#656`, `#747`, `#748`, `#750`

Estado alcanzado:

- llenado atomico simple;
- receta source-result;
- UI de planta de llenado;
- tanques criogenicos normalizados por warehouse real;
- validacion ADR adaptada a datos legacy incompletos.

## 4. Milestone `logistics` modulo completo estable tras primer movimiento real - 2026-08-10

Fuente principal:

- Engram `#755`

Lectura correcta del milestone:

- no significa "sin deuda";
- significa que el modulo ya atraveso un ciclo operativo real y los bugs aparecidos fueron corregidos en return flow, reconciliacion, warehouse attribution, ADR validation y semantica de stock mostrada al operador.

## Riesgos abiertos al cierre

1. `0045` async esta empezada, no terminada. No debe venderse como migracion completa.
2. la promesa de `core/internal_api` sigue incumplida en codigo real.
3. `logistics` sigue demasiado concentrado en archivos grandes, aunque ya exista estrategia de subrouters.
4. hay verdad documental vieja que puede inducir decisiones incorrectas (`README.md`, partes de `docs/avances/logistics.md`).
5. el shell carga demasiado codigo de plugins via eager import.

## Conclusion tecnica

El ultimo mes no fue una fase de "maquillaje". Fue la transicion del repositorio desde una base modular prometedora hacia un sistema con dos capacidades ya materializadas:

- un frente operacional serio en `logistics`, centrado en jornadas, seriales, composicion, reconciliacion y criogenicos;
- un frente de interfaz estructurada en `ventas` y `shell`, centrado en consola DSL, adaptadores multiples y componentes shared maduros.

La arquitectura elegida - monorepo modular, core pequeno, plugins de negocio, specs atomizadas y ADRs duros - demostro utilidad real durante este mes. Tambien expuso sus limites actuales: acoplamiento inter-plugin, contaminacion puntual del kernel, drift documental y archivos demasiado grandes.

Para un desarrollador que retome el sistema hoy, la lectura correcta es esta:

- `core` ya es runtime e infraestructura real, no maqueta;
- `shell` ya es host funcional, no placeholder;
- `logistics` ya es modulo operativo serio;
- `stock` ya es base transaccional madura pero esta corrigiendo su semantica de negocio;
- `productos` ya participa activamente como owner de catalogo y ADR, incluyendo criogenicos;
- la deuda principal ya no es ausencia de features, sino cerrar bordes arquitectonicos y documentales.
