---
id: "0024.3"
title: "Vehicle Session Hero Console — stepper protagonista y modales operativos"
domain: logistics
module: vehicle-sessions
status: vigente
extends:
  - docs/specs/core/0024-vehicle-session-stepper.md
  - docs/specs/core/0024-0-1-event-driven-stepper.md
supersedes:
  - docs/specs/core/0024-1-vehicle-session-ui-architecture.md
---

# SPEC 0024.3 — Vehicle Session Hero Console

## Contexto

`SPEC 0024` convirtió la jornada en un flujo explícito con stepper.

`SPEC 0024.0.1` movió el avance de estado a eventos reales y eliminó confirmaciones redundantes.

Sin embargo, la pantalla principal todavía conserva una inercia administrativa:

- el `SessionStepper` comparte peso visual con el bloque de resumen;
- el resumen sigue encapsulado como card separada;
- el click en el contexto operativo sigue llevando a secciones/tabs;
- el operador todavía siente que "entra a pantallas" en vez de operar desde una consola central.

El siguiente paso ya no es solo quitar fricción de transición. Es **reordenar la jerarquía visual completa** para que el ciclo operativo sea la pieza dominante de la jornada.

## Frase guía

**La jornada no se navega. La jornada se opera desde el stepper.**

## Objetivo

Convertir `VehicleSessionDetailPage` en una consola principal donde:

1. el `SessionStepper` es el centro visual y funcional;
2. el resumen operativo vive inline, sin card propia;
3. cada contexto operativo se abre en un modal contextual, no en una sección fija;
4. la pantalla base siempre conserva el contexto completo de la jornada.

## Principios obligatorios

1. El stepper debe ser el elemento de mayor jerarquía visual de la pantalla.
2. El click en un step abre un modal operativo, no navega a tabs.
3. La pantalla principal nunca pierde el contexto de jornada mientras el usuario opera.
4. El resumen operativo es una banda contextual, no un bloque que compite con el stepper.
5. El frontend no decide reglas de negocio ni transiciones fuera de los eventos ya definidos.
6. Solo existe una acción principal visible por estado.
7. La experiencia debe sentirse como consola operativa real, no como pantalla CRUD.

## No objetivos

- No agregar estados nuevos a `VehicleSession`.
- No cambiar reglas backend de transición ya definidas por `0024` y `0024.0.1`.
- No convertir la jornada en dashboard analítico.
- No diseñar todavía experiencia handheld extrema.
- No implementar GPS en este slice.
- No meter más de un flujo operativo primario abierto a la vez.

## Problema actual

Estado actual de la implementación:

- `VehicleSessionDetailPage.tsx` todavía usa `Tabs` como navegación principal.
- `SessionWorkspaceHeader.tsx` sigue siendo un `Card` que compite con el stepper.
- `SessionStepper.tsx` ya controla mejor el flujo, pero todavía no domina la composición.
- El usuario todavía interpreta los pasos como navegación entre áreas, no como puntos de operación.

## Solución

### Estructura objetivo

```text
+------------------------------------------------------------------+
| HeroConsoleHeader                                                |
| Jornada TRK-123 · badge · conductor · origen · móvil · ruta      |
+------------------------------------------------------------------+
| HeroStepper                                                      |
| [Borrador] [Cargando] [Listo] [En ruta] [Retorno] [Conciliación] |
| frase operativa del estado actual                                |
| acción principal única                                           |
+------------------------------------------------------------------+
| OperationalSummaryInline                                         |
| apertura · pesos · stock móvil · última actividad                |
+------------------------------------------------------------------+
| Secondary strip                                                  |
| historial reciente | alertas | diferencias | estado de ruta      |
+------------------------------------------------------------------+
```

### Cambio semántico

Antes:

```text
header -> tabs -> sección -> acción
```

Después:

```text
header -> stepper -> modal contextual -> retorno al mismo centro
```

## 1. Stepper hero (centro visual)

El `SessionStepper` deja de ser un card secundario y pasa a ser el **hero operativo**.

### Reglas visuales

- debe ocupar el ancho principal disponible;
- debe tener más altura que hoy;
- debe tener más separación entre pasos;
- los nodos deben ser más grandes;
- la frase operativa del estado actual debe ser visible sin esfuerzo;
- la acción principal debe estar claramente separada del resto del contenido.

### Regla de jerarquía

Si la placa del vehículo o el resumen compiten visualmente con el stepper, la composición está mal.

### Tamaño objetivo

#### Desktop

- contenedor principal: `min-h` visual suficiente para respiración vertical;
- nodos: aprox. `h-10 w-10` o `h-12 w-12`;
- labels: `text-sm` o `text-base` según espacio;
- frase operativa: `text-base` en el estado actual;
- acción principal: botón mediano o grande.

#### Mobile

- scroll horizontal permitido;
- nodos no deben achicarse por debajo de legibilidad;
- frase operativa puede ir debajo del stepper completo;
- la acción principal queda fija dentro del bloque hero, no perdida abajo.

## 2. Click en step = abrir modal contextual

El stepper se vuelve el disparador principal de herramientas operativas.

### Regla

Clickear un step nunca debe cambiar la pantalla principal a otra sección.

Debe abrir un modal contextual según el step.

### Mapa obligatorio

```typescript
STEP_MODAL = {
  DRAFT: "load",
  LOADING: "load",
  READY_TO_DEPART: "load",
  OUTBOUND: "route",
  RETURNING: "route",
  AWAITING_RECONCILIATION: "reconciliation",
  CLOSED: "reconciliation",
}
```

### Comportamiento esperado

| Step | Acción al click |
|---|---|
| `DRAFT` | abre `LoadModal` |
| `LOADING` | abre `LoadModal` |
| `READY_TO_DEPART` | abre `LoadModal` o modal contextual de salida según CTA principal |
| `OUTBOUND` | abre `RouteModal` |
| `RETURNING` | abre `RouteModal` |
| `AWAITING_RECONCILIATION` | abre `ReconciliationModal` |
| `CLOSED` | abre `ReconciliationModal` en modo lectura |

## 3. Modales operativos

Los panels actuales dejan de sentirse como tabs fijas y pasan a ser contenido de modales amplios.

### Modales requeridos

```text
LoadModal
RouteModal
ReconciliationModal
```

### Regla de tamaño

No deben ser dialogs pequeños de confirmación.

Deben sentirse como workspace operativo:

- ancho amplio (`max-w-4xl` o equivalente según contenido);
- contenido scrolleable;
- header con título, frase corta y estado;
- footer mínimo o inexistente si la acción principal ya vive dentro del contenido;
- cierre explícito y consistente.

### Regla UX crítica

Si la transición automática falla:

- el modal permanece abierto;
- se muestra el error claro dentro del modal;
- el usuario no pierde el contexto;
- la pantalla principal detrás no cambia de estado visualmente hasta el éxito.

## 4. Resumen operativo inline único

El resumen operativo ya no debe renderizarse como múltiples cards ni como un header pesado.

Debe existir un solo resumen operativo inline.

### Contenido mínimo

- placa del vehículo;
- badge de estado;
- conductor;
- almacén origen;
- almacén móvil;
- ruta o ausencia de ruta;
- apertura;
- peso planificado;
- peso confirmado;
- stock móvil resumido;
- última actividad relevante.

### Forma visual

Debe sentirse como una banda contextual o grid inline, no como bloque protagonista.

Ejemplo:

```text
TRK-123 · En ruta · Juan Perez · ALM Central -> MOB-TRK123 · Ruta 09
Apertura 08:10 · Plan 320 kg · Confirmado 310 kg · Stock 5 prod / 28 und
```

### Regla

El resumen informa, pero no compite.

## 5. Eliminar tabs como navegación principal

`Tabs` sale del loop principal.

No debe seguir existiendo como superficie principal de carga, ruta y conciliación.

### Permitido

- tabs internas dentro de un modal si un modal complejo lo necesita;
- tabs secundarias para historial/diferencias solo si no compiten con la acción principal.

### Prohibido

- tabs de nivel página para `summary`, `load`, `route`, `reconciliation`;
- cambiar de herramienta principal como forma de navegar el flujo.

## 6. Nueva arquitectura objetivo

```text
plugins/logistics/frontend/pages/
  VehicleSessionDetailPage.tsx

plugins/logistics/frontend/components/vehicle-sessions/
  VehicleSessionConsole.tsx
  HeroSessionHeader.tsx
  HeroSessionStepper.tsx
  OperationalSummaryInline.tsx
  SessionSecondaryStrip.tsx
  session-ui-map.ts

plugins/logistics/frontend/components/vehicle-sessions/modals/
  LoadModal.tsx
  RouteModal.tsx
  ReconciliationModal.tsx

plugins/logistics/frontend/components/vehicle-sessions/content/
  SessionLoadPanel.tsx
  SessionRoutePanel.tsx
  SessionReconciliationPanel.tsx
  SessionHistoryPanel.tsx
```

## 7. Responsabilidades por componente

### `VehicleSessionDetailPage.tsx`

Hace:

- fetch del snapshot principal;
- orquestación de mutations;
- control del modal activo;
- invalidación de queries;
- bridge entre stepper y modales.

No hace:

- no renderiza tabs principales;
- no contiene layout operativo pesado inline;
- no decide reglas de negocio.

### `VehicleSessionConsole.tsx`

Hace:

- componer la consola completa;
- renderizar header, hero stepper, resumen inline y superficie secundaria;
- mantener consistencia visual de toda la jornada.

### `HeroSessionStepper.tsx`

Hace:

- renderizar el flujo como pieza principal;
- mostrar la frase operativa actual;
- disparar la acción principal cuando aplica;
- abrir el modal contextual del step clickeado.

No hace:

- no abre tabs;
- no carga datasets pesados por sí solo;
- no calcula reglas de negocio.

### `OperationalSummaryInline.tsx`

Hace:

- mostrar una sola banda de contexto operacional;
- condensar la información mínima relevante.

No hace:

- no renderiza como card protagonista;
- no agrega acciones;
- no duplica información del hero.

### `LoadModal`, `RouteModal`, `ReconciliationModal`

Hacen:

- encapsular la herramienta operativa de cada contexto;
- preservar UX de error local;
- cerrar solo en éxito o por acción explícita del usuario.

No hacen:

- no mutan la jerarquía de la pantalla principal;
- no reemplazan al stepper como centro de control.

## 8. Mapa de acción y apertura

Debe existir una fuente única para:

```typescript
STEP_MODAL_BY_STATUS
STEP_LABEL_BY_STATUS
STATUS_PHRASE
MANUAL_ACTION_LABELS
AUTO_ACTION_HINTS
```

No se permite duplicar este mapa en stepper, page y modales.

## 9. Implementación incremental propuesta

### Paso 1 - Extraer consola visual principal

- crear `VehicleSessionConsole.tsx`;
- mover composición principal fuera de `VehicleSessionDetailPage.tsx`.

### Paso 2 - Convertir header card a resumen inline

- reemplazar `SessionWorkspaceHeader.tsx` por `HeroSessionHeader.tsx` + `OperationalSummaryInline.tsx`;
- eliminar card del resumen.

### Paso 3 - Agrandar y recentrar el stepper

- convertir `SessionStepper.tsx` en `HeroSessionStepper.tsx`;
- ajustar nodos, spacing, tipografía y bloque de acción.

### Paso 4 - Sustituir tabs por modal state

- eliminar `Tabs` de nivel página;
- introducir `activeModal: "load" | "route" | "reconciliation" | null`.

### Paso 5 - Reusar panels actuales dentro de modales

- envolver `SessionLoadTab` en `LoadModal`;
- envolver `SessionRouteTab` en `RouteModal`;
- envolver `SessionReconciliationTab` en `ReconciliationModal`.

### Paso 6 - Click en step abre modal

- reemplazar `onNavigateTab` por `onOpenModal`;
- click en step futuro o pasado abre solo contexto, nunca muta estado.

### Paso 7 - Superficie secundaria limpia

- mover historial/resumen extra a una banda secundaria o bloque inferior discreto;
- no competir con el hero.

### Paso 8 - Ajuste embedded mode

- validar que la consola funcione dentro del dialog actual;
- asegurar que los modales internos no rompan el flujo embebido.

## 10. Riesgos reales

### 1. Stepper grande pero vacío

Si se agranda sin mejorar jerarquía, frase y acción, solo será un bloque más grande sin utilidad.

### 2. Modal pequeño o genérico

Si los modales se sienten como dialogs menores, el operador perderá continuidad y contexto.

### 3. Mantener tabs escondidas

Si las tabs siguen siendo la navegación real aunque no se vean, la arquitectura seguirá siendo administrativa.

### 4. Resumen inline demasiado cargado

Si el resumen intenta mostrar todo, vuelve a competir con el stepper.

### 5. Múltiples disparadores para la misma herramienta

Si hay botón aparte, link aparte y step aparte para abrir la misma cosa, reaparece la fricción.

### 6. Fondo principal visualmente ruidoso

Si el header, el resumen y la superficie secundaria usan demasiados bordes o cards, el hero deja de dominar.

## 11. Señales de fallo

- sigue existiendo `Tabs` como navegación principal;
- clickear un step cambia de sección en vez de abrir modal;
- el stepper ocupa visualmente lo mismo que el resumen;
- el resumen sigue siendo una card protagonista;
- el usuario pierde el contexto al abrir carga/ruta/conciliación;
- hay más de una acción primaria visible a la vez;
- el hero no comunica el estado en dos segundos.

## 12. Criterios de aceptación

- [ ] El `SessionStepper` pasa a ser el bloque visual dominante de la jornada
- [ ] El click en un step abre un modal contextual, no tabs
- [ ] `Tabs` dejan de ser navegación principal de la página
- [ ] Existe un solo resumen operativo inline, sin card principal
- [ ] La placa, almacenes, conductor, ruta y pesos siguen visibles en la pantalla base
- [ ] El usuario puede operar carga, ruta y conciliación sin abandonar la consola central
- [ ] Los errores de transición automática permanecen dentro del modal sin cerrarlo
- [ ] El layout funciona en desktop y mobile
- [ ] El modo embebido sigue funcionando
- [ ] La jerarquía visual deja claro que el ciclo operativo es el centro de todo

## 13. Archivos afectados

### Nuevos

- `plugins/logistics/frontend/components/vehicle-sessions/VehicleSessionConsole.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/HeroSessionHeader.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/OperationalSummaryInline.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/modals/LoadModal.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/modals/RouteModal.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/modals/ReconciliationModal.tsx`

### Modificados

- `plugins/logistics/frontend/pages/VehicleSessionDetailPage.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionStepper.tsx` o su reemplazo `HeroSessionStepper.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionWorkspaceHeader.tsx` o su reemplazo
- `plugins/logistics/frontend/components/vehicle-sessions/session-ui-map.ts`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionLoadTab.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionReconciliationTab.tsx`

### Eliminar del flujo principal

- `Tabs` como patrón de navegación principal;
- `summary/load/route/reconciliation` como secciones de página;
- card principal de resumen operativo.

## 14. Nota de vigencia

`SPEC 0024.1` queda superada en arquitectura visual principal.

Sus ideas útiles permanecen, pero esta spec redefine la pantalla objetivo con una prioridad más fuerte:

```text
header compacto -> hero stepper -> resumen inline -> modales contextuales
```

La fuente vigente para la siguiente evolución de `VehicleSession` pasa a ser:

1. `SPEC 0024`
2. `SPEC 0024.0.1`
3. `SPEC 0024.3`
