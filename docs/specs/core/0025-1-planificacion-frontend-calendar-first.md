---
id: "0025.1"
title: "Planificacion Frontend Calendar-First y Componente Core de Calendario"
domain: logistics
module: planificacion
status: propuesta
extends:
  - docs/specs/core/0025-planificacion-calendar-first-y-reserva-de-capacidad.md
  - docs/specs/core/0022-logistics-desmonolitizacion-frontend.md
---

# SPEC 0025.1 - Planificacion Frontend Calendar-First y Componente Core de Calendario

## Estado

Propuesta

## Contexto

`SPEC 0025` ya definio el modelo correcto:

- `Planificacion` = reserva persistida de capacidad;
- `Jornadas` = ejecucion viva;
- calendar-first en UX;
- capacity-first en dominio.

Lo que falta ahora es bajar esa decision a una arquitectura frontend implementable sin volver a caer en un `PlanningPage.tsx` monolitico.

La situacion actual confirma el problema:

- `PlanningPage.tsx` responde a una UX transicional centrada en tablas y dialogs auxiliares;
- no existe aun un componente reusable de calendario en `apps/web/src/shared/ui/`;
- el repositorio ya tiene reglas explicitas contra monolitos y a favor de componentes core reutilizables.

## Frase guia

**El calendario es core. La planificacion es dominio. La pagina es solo shell.**

## Objetivo

Definir la arquitectura frontend de `Planificacion` para que:

1. exista un componente core reusable de calendario en `shared/ui`;
2. `PlanningPage.tsx` quede como shell/orquestador;
3. la capa de dominio de planificacion viva en archivos separados dentro de `plugins/logistics/frontend/`;
4. mes, semana y dia compartan primitivas visuales y reglas de interaccion consistentes;
5. la integracion con `Jornadas` ocurra desde acciones de activacion claras;
6. la implementacion evite archivos gigantes y mezclas de concerns.

## No objetivos

- No implementar aqui el backend de reservas.
- No definir un componente calendario acoplado solo a `logistics`.
- No mover logica de negocio de planificacion al core compartido.
- No introducir Zustand nuevo solo para compensar una arquitectura de componentes mala.
- No reescribir `Jornadas`.
- No definir aun todos los detalles de drag and drop de baja prioridad si no afectan el contrato base.

## Principios obligatorios

1. El calendario base vive en `apps/web/src/shared/ui/`.
2. El calendario core no importa tipos ni logica de `logistics`.
3. `PlanningPage.tsx` no renderiza inline toda la experiencia.
4. La capa de dominio de planificacion vive en `plugins/logistics/frontend/planning/`.
5. Los wrappers de dominio pueden inyectar defaults, labels y renderers, pero no duplican el core.
6. Mes, semana y dia son vistas del mismo sistema, no tres widgets inconexos.
7. Server state va por TanStack Query; estado UI local por hooks/component state; evitar store global nuevo salvo necesidad demostrada.
8. La arquitectura debe respetar la regla anti-monolitos del repositorio: separar por responsabilidad antes de superar 400 lineas; prohibido diseñar archivos destinados a crecer mas alla de 500.

## Decision central

Se crea un componente core llamado `ResourceCalendar`.

No sera un calendario generico vacio de tipo agenda personal.

Sera un componente reusable de recursos-tiempo capaz de renderizar:

- recursos (`vehicles`, salas, equipos, etc.);
- bloques temporales;
- items posicionados por rango horario;
- vistas mes/semana/dia;
- interacciones de seleccion, click y reprogramacion.

`Planificacion` sera el primer consumidor de ese core.

## Separacion de capas

### Capa Core Compartida

Vive en:

```text
apps/web/src/shared/ui/resource-calendar/
```

Responsabilidad:

- layout de calendario;
- celdas temporales;
- recursos;
- posicionamiento de bloques;
- interacciones genericas;
- accesibilidad base;
- responsive base.

No contiene:

- conceptos de `vehiculo`, `ADR`, `carga planificada`, `jornada`, `conflict_reason`;
- badges o copy de negocio;
- mutaciones de planificacion.

### Capa Dominio Planificacion

Vive en:

```text
plugins/logistics/frontend/planning/
```

Responsabilidad:

- mapear reservas a items del calendario;
- renderizar detalles de dominio;
- dialogs/panels de crear/editar/activar;
- filtros de almacen, vehiculo y estado;
- acciones de override;
- navegacion a `Jornadas`.

## Estructura objetivo

### Core compartido

```text
apps/web/src/shared/ui/
  resource-calendar/
    resource-calendar.tsx
    resource-calendar-types.ts
    resource-calendar-month-view.tsx
    resource-calendar-time-grid.tsx
    resource-calendar-resource-column.tsx
    resource-calendar-event-block.tsx
    resource-calendar-now-indicator.tsx
    resource-calendar-layout.ts
    resource-calendar-dates.ts
```

### Frontend de planificacion

```text
plugins/logistics/frontend/
  pages/
    PlanningPage.tsx
  planning/
    PlanningWorkspace.tsx
    planning-query-keys.ts
    hooks/
      use-planning-calendar-range.ts
      use-planning-filters.ts
      use-planning-selection.ts
    components/
      planning-toolbar.tsx
      planning-calendar-shell.tsx
      planning-status-legend.tsx
      planning-reservation-content.tsx
      planning-vehicle-sidebar.tsx
      planning-empty-state.tsx
    dialogs/
      create-planning-reservation-dialog.tsx
      edit-planning-reservation-dialog.tsx
      activate-planning-reservation-dialog.tsx
      override-planning-conflict-dialog.tsx
    panels/
      planning-reservation-detail-panel.tsx
      planning-conflict-panel.tsx
      vehicle-planned-load-panel.tsx
    utils/
      planning-calendar-mappers.ts
      planning-calendar-colors.ts
      planning-calendar-formatters.ts
```

La ruta exacta puede ajustarse, pero no la separacion por responsabilidad.

## Responsabilidades por archivo

### `PlanningPage.tsx`

Hace:

- montar `LogisticsSection`;
- resolver permisos de entrada;
- renderizar `PlanningWorkspace`.

No hace:

- no contiene toda la UI del calendario;
- no contiene todos los dialogs;
- no hace mapeos de reservas inline;
- no centraliza decenas de estados locales dispersos.

### `PlanningWorkspace.tsx`

Hace:

- orquestar queries principales;
- coordinar toolbar, calendario y paneles;
- mantener seleccion actual y apertura de dialogs de alto nivel.

No hace:

- no implementa el layout interno del calendario;
- no dibuja cada bloque a mano;
- no mezcla helpers puros, JSX pesado y mutaciones en un solo archivo gigante.

### `ResourceCalendar`

Hace:

- recibir `view`, `range`, `resources` e `items`;
- resolver layout base de mes/semana/dia;
- exponer callbacks genericos (`onSlotSelect`, `onItemClick`, `onItemMove`, `onItemResize`, `onRangeChange`);
- soportar render prop o slot para contenido de items y encabezados.

No hace:

- no decide semantica de estados de planificacion;
- no llama APIs;
- no conoce `VehicleSession`;
- no resuelve conflictos de negocio.

### `planning-calendar-shell.tsx`

Hace:

- adaptar datos del dominio al core;
- inyectar renderers de reservas;
- centralizar wiring de callbacks del calendario.

No hace:

- no duplica el motor de layout;
- no reemplaza `ResourceCalendar` con JSX propio paralelo.

## Contrato minimo del componente core

### `resources`

```ts
type CalendarResource = {
  id: string;
  label: string;
  subtitle?: string;
  disabled?: boolean;
};
```

### `items`

```ts
type CalendarItem = {
  id: string;
  resourceId: string;
  start: string;
  end: string;
  title: string;
  status?: string;
  colorVariant?: string;
  isConflicted?: boolean;
  isLocked?: boolean;
};
```

### Props minimas esperadas

```ts
type ResourceCalendarProps = {
  view: "month" | "week" | "day";
  rangeStart: string;
  rangeEnd: string;
  resources: CalendarResource[];
  items: CalendarItem[];
  onRangeChange?: (nextStart: string, nextEnd: string) => void;
  onSlotSelect?: (resourceId: string | null, start: string, end: string) => void;
  onItemClick?: (itemId: string) => void;
  onItemMove?: (itemId: string, resourceId: string, start: string, end: string) => void;
  onItemResize?: (itemId: string, start: string, end: string) => void;
  renderItem?: (item: CalendarItem) => React.ReactNode;
  renderResourceHeader?: (resource: CalendarResource) => React.ReactNode;
};
```

La implementacion puede ajustar nombres, pero debe preservar separacion generica entre core y dominio.

## Vistas obligatorias

### Mes

Objetivo:

- ocupacion global;
- saturacion por dia;
- lectura rapida de conflictos;
- entrada rapida a detalle.

Interacciones minimas:

- click en dia para crear;
- click en bloque para abrir detalle;
- navegacion mensual.

### Semana

Objetivo:

- vista principal de planificacion operativa;
- comparacion por vehiculo;
- reasignacion y reprogramacion.

Interacciones minimas:

- seleccionar slot;
- mover bloque;
- redimensionar bloque;
- abrir detalle o activar.

### Dia

Objetivo:

- precision horaria fina;
- capacidad del vehiculo;
- conflictos vivos;
- transicion a `Jornadas`.

Interacciones minimas:

- crear por slot horario;
- mover/ajustar duracion;
- ver uso real vs planificado;
- activar reserva.

## Responsive

### Desktop

- mes completo;
- semana por recursos;
- dia por recursos y franja horaria;
- panel lateral de detalle o conflicto.

### Mobile

- priorizar vista dia y lista;
- semana simplificada si no degrada legibilidad;
- mes resumido con acceso a detalle;
- dialogs/panels en formato sheet o full-screen.

No se debe forzar en mobile una grilla ilegible solo por simetria visual con desktop.

## Integracion con Vehicle-First

La proyeccion `vehicle-first` de `Jornadas` debe reutilizar piezas de la capa de planificacion, pero no reimplementar el calendario.

Como minimo:

- `VehicleSessionsPage` debe poder mostrar `Carga planificada` del vehiculo;
- `vehicle-planned-load-panel.tsx` debe reutilizar formatters y estados visuales de planificacion;
- la activacion desde planificacion debe navegar a la jornada vinculada.

### Secciones visibles por vehículo

La UI de vehículo/modal debe distinguir explícitamente:

1. `Jornada activa`;
2. `Jornadas pendientes`;
3. `Planificaciones` o reservas futuras no materializadas.

La sección existente `Jornadas pendientes` debe preservarse conceptualmente.

Su semántica correcta es:

- no cerradas, excluyendo la activa;
- en cola para ese vehículo;
- ordenadas por proximidad/prioridad para el siguiente disparo.

### Regla de materialización visual

Si una reserva sigue siendo solo `Planificacion`, se muestra en la capa de planificacion/calendario.

Si ya fue materializada como `VehicleSession` futura, pasa a mostrarse en `Jornadas pendientes`.

La UI no debe mezclar ambas listas como si fueran lo mismo.

## Estado frontend

### Server state

Usar TanStack Query para:

- calendario/rango actual;
- detalle de reserva;
- catalogos de vehiculos, almacenes y rutas;
- acciones de crear/editar/activar/cancelar.

### Estado UI local

Usar hooks locales para:

- vista actual (`month`, `week`, `day`);
- fecha focal;
- reserva seleccionada;
- apertura de dialogs;
- filtros locales;
- modo de interaccion del calendario.

### No introducir por defecto

- store global de planificacion;
- contexto nuevo sin necesidad;
- duplicacion local de server state.

## Politica de componentes compartidos

### Va a `shared/ui`

- `ResourceCalendar`;
- primitivas visuales del calendario;
- indicadores genericos reutilizables del calendario.

### Se queda en `plugins/logistics/frontend/planning/`

- render de reserva de capacidad;
- badges de estado de planificacion;
- panel de conflicto;
- dialogs de activar/override;
- copy de `ADR`, `VEHICLE_IN_USE`, `CAPACITY_EXCEEDED`, etc.

Regla:

No promover a shared un componente que todavia sabe demasiado de planificacion.

## Interacciones obligatorias del dominio

1. crear reserva desde slot vacio;
2. editar reserva existente;
3. reprogramar reserva por drag/move cuando el estado lo permita;
4. redimensionar duracion cuando el estado lo permita;
5. visualizar conflicto con motivo claro;
6. ejecutar override explicito cuando backend lo permita;
7. activar reserva hacia `Jornadas`;
8. abrir detalle desde calendario o lista;
9. distinguir si un elemento pertenece a `Planificacion`, `Jornada activa` o `Jornada pendiente`.

## Estados visuales minimos

La UI debe distinguir claramente:

- `PLANNED`
- `READY`
- `IN_PROGRESS`
- `COMPLETED`
- `CANCELLED`
- `CONFLICT`
- `EXPIRED`

Y debe hacer visible `conflict_reason` al menos para:

- `TIME_OVERLAP`
- `CAPACITY_EXCEEDED`
- `ADR_INCOMPATIBLE`
- `VEHICLE_IN_USE`

El estado visual no debe depender solo del color; debe apoyarse en texto/badge/iconografia ligera.

## Accesibilidad minima

1. navegacion por teclado entre bloques y celdas principales;
2. foco visible al seleccionar reserva;
3. labels accesibles para acciones de mover/editar/activar;
4. contraste suficiente para estados y conflictos;
5. no depender solo de drag and drop para crear o editar.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Crear un `calendar.tsx` gigante en shared | alto | dividir desde el inicio por vistas, layout y primitives |
| Duplicar el calendario en `logistics` | alto | usar `planning-calendar-shell.tsx` como adaptador del core |
| Llevar demasiado pronto widgets de dominio a shared | medio | promover solo primitives realmente genericas |
| Repetir el anti-pattern monolitico de `PlanningPage.tsx` | alto | dejar la pagina como shell y mover dialogs/panels/hooks desde el inicio |
| Forzar desktop grid en mobile | medio | definir vista simplificada y sheets dedicados |

## Criterios de aceptacion

1. existe un componente core reusable de calendario en `apps/web/src/shared/ui/`;
2. `PlanningPage.tsx` queda reducido a shell/orquestador;
3. la capa de planificacion se organiza en `hooks`, `components`, `dialogs`, `panels` y `utils` separados;
4. mes, semana y dia reutilizan el mismo core;
5. el calendario core no importa codigo de `logistics`;
6. la UI de planificacion soporta crear, editar, mover, redimensionar y activar reservas;
7. la UI muestra estados y conflictos de manera clara;
8. `VehicleSessionsPage` puede mostrar `Carga planificada` reutilizando piezas de planificacion;
9. la UI de vehículo distingue `Jornada activa`, `Jornadas pendientes` y `Planificaciones` no materializadas;
10. no se introduce un nuevo monolito frontend para resolver este flujo.

## Pruebas requeridas

1. unitarias para layout helpers del calendario;
2. unitarias para mapeo dominio -> `CalendarItem`;
3. unitarias para reglas visuales de estado/conflicto;
4. frontend para navegacion mes/semana/dia;
5. frontend para crear/editar/activar desde calendario;
6. frontend para responsive basico y accesibilidad minima;
7. `build:web` verde como cierre tecnico.

## Dependencias

- `docs/specs/core/0025-planificacion-calendar-first-y-reserva-de-capacidad.md`
- `docs/specs/core/0022-logistics-desmonolitizacion-frontend.md`
- `docs/specs/core/0024-1-2-vehicle-first-jornadas-projection.md`
- `plugins/logistics/frontend/pages/PlanningPage.tsx`
- `plugins/logistics/frontend/pages/VehicleSessionsPage.tsx`
- `apps/web/src/shared/ui/`

## Notas para agentes

1. Si el calendario shared empieza a conocer `vehicle_id`, `ADR` o `Jornada`, se esta rompiendo esta spec.
2. Si `PlanningPage.tsx` vuelve a crecer como archivo dueño de todo, se esta rompiendo esta spec.
3. Si hace falta un wrapper de dominio, debe adaptar el core, no clonarlo.
4. El primer calendario reusable no necesita resolver todos los casos del sistema; necesita resolver bien el contrato base sin acoplarse a `logistics`.
