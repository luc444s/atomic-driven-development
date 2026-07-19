---
id: "0024.1"
title: "Vehicle Session UI Architecture — consola operativa"
domain: logistics
module: vehicle-sessions
status: vigente
extends:
  - docs/specs/core/0024-vehicle-session-stepper.md
---

# SPEC 0024.1 - VehicleSession UI Architecture

## Contexto

`SPEC 0024` resolvió la base del control de transición de jornada:

- stepper explícito;
- acción principal determinista;
- blockers decididos por backend;
- eliminación del botón mutante.

Sin embargo, la pantalla `VehicleSessionDetailPage` todavía conserva estructura pesada para operación real:

- composición monolítica;
- demasiadas herramientas visibles al mismo tiempo;
- navegación tipo pantalla administrativa (`Tabs`);
- carga eager de datos que no siempre se necesitan;
- mezcla entre contexto operativo y herramientas de trabajo.

El problema ya no es la transición en sí, sino la **arquitectura visual y funcional de la consola**.

## Objetivo

Convertir la pantalla de jornada en una consola operativa centrada en flujo:

```text
SessionHeader
-> SessionStepper
-> SessionContext
-> SessionWorkspace
```

La UI debe hacer evidente:

1. qué jornada se está operando;
2. en qué punto del flujo está;
3. cuál es la única acción principal siguiente;
4. qué herramienta corresponde usar ahora.

## No objetivos

- No rediseñar reglas de negocio backend.
- No agregar estados nuevos a `VehicleSession`.
- No inventar nuevos blockers en frontend.
- No convertir la pantalla en dashboard analítico.
- No implementar todavía el modo handheld/campo extremo.
- No ampliar alcance funcional de ruta más allá del workspace actual V1.

## Principios obligatorios

1. El `SessionStepper` es el centro de control.
2. El usuario ve una sola acción principal a la vez.
3. El frontend no contiene lógica de negocio.
4. Todo bloqueo viene del snapshot backend.
5. Los panels son herramientas de soporte, no controladores del flujo.
6. La pantalla debe sentirse ligera, directa y usable en operación real.
7. La data debe cargarse on-demand cuando el workspace lo necesita.

## Arquitectura objetivo

### Estructura visual

```text
+--------------------------------------------------------------+
| SessionHeader                         | SessionStepper       |
+--------------------------------------------------------------+
| SessionContext                                             |
+--------------------------------------------------------------+
| SessionWorkspace                                           |
|   -> LoadPanel | RoutePanel | ReconciliationPanel | Empty   |
+--------------------------------------------------------------+
```

### Orden semántico

1. Identidad de jornada
2. Control de flujo
3. Contexto mínimo
4. Herramienta activa

## Estructura de archivos objetivo

```text
plugins/logistics/frontend/pages/
  VehicleSessionDetailPage.tsx

plugins/logistics/frontend/components/vehicle-sessions/
  SessionHeader.tsx
  SessionStepper.tsx
  SessionContext.tsx
  SessionWorkspace.tsx
  session-ui-map.ts

plugins/logistics/frontend/components/vehicle-sessions/workspace/
  LoadPanel.tsx
  RoutePanel.tsx
  ReconciliationPanel.tsx
  EmptyWorkspace.tsx

plugins/logistics/frontend/components/vehicle-sessions/secondary/
  SessionHistoryPanel.tsx
```

## Responsabilidades por componente

### `VehicleSessionDetailPage.tsx`

Hace:

- fetch del snapshot principal;
- orquestación de mutations;
- invalidación de queries;
- control del `activeWorkspace`;
- conexión entre stepper, contexto y workspace.

No hace:

- no calcula reglas de transición;
- no renderiza lógica operativa pesada de forma inline;
- no decide blockers;
- no contiene múltiples controles primarios distribuidos.

### `SessionHeader.tsx`

Hace:

- mostrar placa;
- mostrar conductor;
- mostrar warehouse origen;
- mostrar warehouse móvil;
- mostrar badge de estado.

No hace:

- no dispara acciones;
- no muestra métricas secundarias;
- no contiene controles del flujo.

### `SessionStepper.tsx`

Hace:

- representar el avance del ciclo;
- mostrar pasos completados, actual y futuros;
- renderizar la única acción principal;
- navegar al workspace correspondiente;
- mostrar blockers y errores de acción.

No hace:

- no calcula si puede avanzar;
- no sabe reglas de conciliación, carga o stock;
- no ejecuta ramas condicionales de negocio fuera del mapa determinista.

### `SessionContext.tsx`

Hace:

- mostrar únicamente:
  - ruta;
  - peso planificado;
  - peso confirmado.

No hace:

- no muestra stock detallado;
- no muestra historial;
- no muestra métricas decorativas;
- no compite visualmente con el stepper.

### `SessionWorkspace.tsx`

Hace:

- recibir `activeWorkspace`;
- montar solo el panel necesario;
- cargar data del panel bajo demanda.

No hace:

- no decide transiciones de estado;
- no reemplaza al stepper como controlador;
- no carga todos los datasets desde el inicio.

### `LoadPanel.tsx`

Hace:

- editar plan de carga;
- guardar plan;
- confirmar carga;
- mostrar disponibilidad de origen.

No hace:

- no mueve la jornada a `READY_TO_DEPART`;
- no decide si ya puede salir.

### `RoutePanel.tsx`

Hace:

- mostrar el espacio de operación de ruta actual;
- ser base para `deliver/pickup/exchange` en slice posterior.

No hace:

- no controla `OUTBOUND -> RETURNING`;
- no agrega navegación paralela de flujo.

### `ReconciliationPanel.tsx`

Hace:

- registrar conteo físico;
- mostrar diferencias;
- soportar guardado de conciliación.

No hace:

- no cierra la jornada;
- no define si la conciliación habilita cierre.

## Flujo de datos

### Fuente de verdad

El snapshot de sesión sigue siendo la única fuente de verdad para control de avance:

- `status`
- `next_transition_allowed`
- `next_transition_blocker`
- `closed_at`

### Mapas UI

Se centralizan en `session-ui-map.ts`:

```text
NEXT_ACTION_BY_STATUS
WORKSPACE_BY_STATUS
STEP_LABEL_BY_STATUS
```

Reglas:

1. el stepper usa `NEXT_ACTION_BY_STATUS` para su acción principal;
2. el workspace usa `WORKSPACE_BY_STATUS` para decidir qué panel abrir;
3. no pueden existir mapas duplicados en componentes separados.

### Workspace por estado

| Status | Workspace activo |
|---|---|
| `DRAFT` | `load` |
| `LOADING` | `load` |
| `READY_TO_DEPART` | `load` |
| `OUTBOUND` | `route` |
| `RETURNING` | `route` |
| `AWAITING_RECONCILIATION` | `reconciliation` |
| `CLOSED` | `reconciliation` |
| `CANCELLED` | `null` o último workspace visible |

### Carga on-demand

- `loadPlanQuery` y balances de origen: solo cuando `activeWorkspace === "load"`
- `reconciliationQuery`: solo cuando `activeWorkspace === "reconciliation"`
- datos de ruta: solo cuando `activeWorkspace === "route"`

La query principal de snapshot sí es eager porque gobierna toda la pantalla.

## Reglas de navegación

1. El stepper puede abrir el workspace correspondiente al estado actual.
2. El click en paso navega herramienta, no muta estado.
3. El cambio de estado exitoso debe re-evaluar automáticamente el workspace activo.
4. No habrá `Tabs` como navegación principal del flujo.

## Eliminaciones obligatorias

Eliminar completamente del flujo principal:

- `Tabs` como patrón central;
- `SessionSummaryTab` en la pantalla operativa principal;
- acciones múltiples simultáneas compitiendo con el stepper;
- botones de transición dentro de panels;
- `primaryLabel` y cualquier derivado de botón mutante;
- lógica `if/switch` dispersa para transiciones.

## Implementación propuesta por pasos

### Paso 1 - Convertir la página en orquestador

- limpiar `VehicleSessionDetailPage.tsx`;
- introducir `activeWorkspace`;
- dejar al page component como composition root.

### Paso 2 - Separar header y contexto

- extraer `SessionHeader.tsx`;
- extraer `SessionContext.tsx` desde el bloque actual de datos.

### Paso 3 - Centralizar mapas UI

- crear `session-ui-map.ts`;
- mover allí mappings de acción, labels y workspace.

### Paso 4 - Introducir `SessionWorkspace`

- render condicional único según `activeWorkspace`;
- estado vacío explícito cuando no haya herramienta seleccionada.

### Paso 5 - Migrar tabs a panels

- `SessionLoadTab.tsx` -> `LoadPanel.tsx`
- `SessionRouteTab.tsx` -> `RoutePanel.tsx`
- `SessionReconciliationTab.tsx` -> `ReconciliationPanel.tsx`

### Paso 6 - Sacar transiciones de los panels

- `ReconciliationPanel` deja de cerrar jornada;
- cualquier transición de status queda solo en el stepper.

### Paso 7 - Lazy queries por workspace

- mover `enabled` de queries secundarias para que dependan del workspace activo.

### Paso 8 - Historial como superficie secundaria

- mantener historial fuera del loop principal;
- puede quedar al final o como panel secundario colapsable.

### Paso 9 - Ajuste embedded mode

- verificar que la composición funcione igual en dialog/embebido;
- preservar salida limpia al cerrar jornada embebida.

## Riesgos

### 1. Mapas duplicados

Si el stepper y el workspace usan distintas tablas de decisión, la UI se desincroniza.

### 2. Queries eager mal conservadas

La pantalla seguirá siendo monolítica aunque visualmente parezca más limpia.

### 3. Dejar acciones primarias dentro de panels

Reaparece la competencia entre controles y vuelve la confusión operacional.

### 4. Sobrecrecer `SessionContext`

Si se vuelven a agregar métricas y bloques secundarios, se pierde foco visual.

### 5. Mantener `Tabs` escondidas

La arquitectura seguiría siendo administrativa, no operacional.

### 6. Calcular negocio en frontend

Rompe la separación establecida por `0024` y crea drift con backend.

### 7. No sincronizar workspace tras transición

El usuario puede quedar mirando la herramienta equivocada después de avanzar de estado.

## Permisos

No introduce permisos nuevos.

Se reutilizan los permisos ya existentes de lectura/gestión de `VehicleSession`, carga y conciliación.

## Eventos

No introduce eventos nuevos.

Reutiliza los eventos ya emitidos por las acciones backend actuales.

## Datos y contratos

### Backend

No requiere nuevas tablas ni cambios en modelo de datos.

Depende de que el snapshot ya exponga:

- `status`
- `next_transition_allowed`
- `next_transition_blocker`
- `closed_at`

### Frontend

El contrato principal sigue siendo `VehicleSession` + endpoints secundarios existentes.

Los cambios son de composición, ownership de queries y estructura de componentes.

## Migraciones

No requiere migración de base de datos.

## Auditoría y observabilidad

- No se debe ocultar ninguna transición detrás de atajos UI.
- La acción principal del stepper debe seguir llamando los endpoints existentes para conservar auditoría y eventos.
- El cambio de arquitectura no debe introducir transiciones silenciosas ni shortcuts locales.

## Criterios de aceptación

- [ ] `VehicleSessionDetailPage` queda estructurada como `Header -> Stepper -> Context -> Workspace`
- [ ] `SessionStepper` sigue siendo el único control de transición de estado
- [ ] `SessionContext` muestra solo ruta, peso planificado y peso confirmado
- [ ] `SessionWorkspace` muestra un solo panel dinámico según estado/workspace
- [ ] `Tabs` dejan de ser la navegación principal del flujo
- [ ] `SessionSummaryTab` sale del camino operativo principal
- [ ] `ReconciliationPanel` ya no cierra jornada directamente
- [ ] Queries secundarias cargan on-demand según workspace
- [ ] El frontend no agrega reglas de negocio nuevas sobre transición
- [ ] La UX sigue funcionando en modo embebido
- [ ] El layout sigue siendo usable en mobile y escritorio

## Pruebas requeridas

### Frontend

- prueba manual completa del flujo `DRAFT -> CLOSED` con cambio de workspace automático;
- validación manual en mobile para stepper + workspace;
- validación manual en modo embebido.

### Backend

- no requiere nuevos tests de negocio si no se cambia comportamiento backend;
- mantener verdes las pruebas ya agregadas por `SPEC 0024`.

## Notas para agentes

1. No reintroducir `Tabs` como solución temporal permanente.
2. No meter lógica de transición en `LoadPanel`, `RoutePanel` o `ReconciliationPanel`.
3. Si un componente empieza a mezclar contexto y herramienta, dividirlo.
4. Mantener el cambio incremental sobre la base ya implementada por `0024`.
5. Si se necesita más de un mapa de estado, probablemente la arquitectura se está degradando.
