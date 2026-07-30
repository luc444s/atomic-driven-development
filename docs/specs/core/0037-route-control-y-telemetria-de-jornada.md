---
id: "0037"
title: "Route Control y Telemetría de Jornada"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0036-evento-de-ruta-unificado-y-contexto-explicito.md
  - docs/specs/core/0033-route-operation-efectos-separados.md
  - docs/specs/core/0024-1-3-4-operational-summary-de-jornada.md
  - docs/specs/core/0014-1-logistics-gap-closure.md
---

# SPEC 0037 - Route Control y Telemetría de Jornada

## Estado

Borrador - v1

## Contexto

`SPEC 0033` dejó firme el control del **qué pasó** en calle:

- `RouteOperation` modela el hecho operativo discreto;
- sus efectos físicos, financieros y documentales no deben mezclarse por comodidad;
- una operación confirmada puede ser válida aunque no proyecte inmediatamente un `Movement` financiero.

`SPEC 0036` endureció el **por qué pasó** y el contexto explícito:

- la incidencia acompaña a la operación y no la reemplaza;
- el hecho físico sigue capturándose una sola vez;
- el usuario ya tiene un workspace operacional más coherente para registrar entregas, recojos, intercambios, correcciones e incidencias.

Sin embargo, aún falta una tercera dimensión operativa crítica:

```text
el sistema sabe qué ocurrió
y por qué ocurrió
pero todavía no sabe de forma confiable dónde está ocurriendo
ni cómo progresa la ejecución real de la ruta planificada
```

Hoy existen piezas parciales:

- `Route` y `RouteStop` como plan operativo base;
- `VehicleSession` como aggregate de ejecución del día;
- endpoints puntuales de GPS (`/routes/{id}/gps-start`, `/routes/{id}/stops/{stop_id}/gps`, `/agenda/tasks/{id}/gps`);
- campos JSON para coordenadas en ruta, parada y tarea;
- soporte frontend de mapa con `Leaflet + OpenStreetMap` vía `LocationPicker`.

Pero esa base aún no constituye un **Route Control System**. Falta una capa propia de telemetría y una capa derivada de control que permitan:

- ver el vehículo en contexto de ruta;
- conocer la siguiente parada y el progreso real;
- detectar llegada sugerida, detenciones prolongadas y desvíos;
- soportar playback y auditoría operacional;
- hacerlo sin contaminar `RouteOperation` ni acoplar GPS a stock.

## Frase guía

**0033 controla qué pasó. 0036 controla por qué pasó. 0037 controla dónde está pasando.**

## Objetivo

Agregar una capa incremental de `Route Control` sobre jornadas y rutas, separando de forma explícita:

1. planificación de ruta;
2. ejecución operativa;
3. telemetría continua de ubicación;
4. estado derivado de control de ruta.

La meta es habilitar un TMS-lite auditable y progresivo, donde el backoffice y el chofer puedan ver la ruta, el avance y la ubicación actual sin reescribir el dominio de `RouteOperation` ni depender ciegamente del GPS.

## No objetivos

- no reemplazar `Route`, `RouteStop` o `VehicleSession` por aggregates nuevos;
- no convertir `RouteOperation` en contenedor de streaming GPS;
- no bloquear entregas, recojos o incidencias por ausencia de GPS o geofence;
- no acoplar telemetría a `stock`, `movements`, `composition/current` o `Carta Porte` como condición de validez;
- no implementar optimización de rutas multi-vehículo en esta spec;
- no exigir en v1 un motor externo de routing vial (`OSRM`, `GraphHopper`, `Valhalla`);
- no prometer experiencia “Uber completa” desde la primera iteración;
- no introducir mobile offline completa en este slice.

## Alcance

Este slice afecta:

- `Route` y `RouteStop` como capa de planificación reutilizada;
- `VehicleSession` como ejecución del día;
- nueva telemetría persistida por jornada/vehículo;
- nuevo estado derivado de control por jornada/ruta;
- mapa de contexto operativo en frontend;
- captura de ubicación periódica desde cliente móvil/web;
- eventos, auditoría y observabilidad relacionados con control de ruta.

Este slice no cambia la semántica de:

- `RouteOperation` como owner del hecho físico;
- `RouteIncident` como contexto complementario;
- `Movement` como consecuencia inventariable/documental cuando corresponda;
- cálculo de composición y carta porte definidos por `0033` y `0036`.

## Capas de dominio

### 1. Planificación

La planificación ya vive conceptualmente en:

- `Route`
- `RouteStop`

`0037` no crea un `RoutePlan` paralelo. La decisión explícita es reutilizar la capa existente como plan operativo base.

Modelo conceptual de planificación:

```ts
type PlannedRoute = {
  route_id: string
  route_date: string
  vehicle_id?: string | null
  driver_id?: string | null
  stops: PlannedStop[]
}

type PlannedStop = {
  stop_id: string
  order: number
  delivery_point_id: string
  customer_id?: string | null
  lat?: number | null
  lng?: number | null
  time_window?: string | null
}
```

Regla fuerte:

```text
la planificacion sigue siendo la referencia esperada
pero la verdad operacional de ejecucion vive en sesiones + control
```

### Relación obligatoria entre `VehicleSession` y `Route`

`0037` vuelve explícita una regla que antes podía quedar laxa:

1. la telemetría y el control son `session-centric`;
2. una `VehicleSession` asociada a una `Route` no puede ejecutar control con identidad vehicular contradictoria.

Invariante:

```text
si route.vehicle_id existe y difiere de session.vehicle_id -> rechazo
si route.driver_id existe y difiere de session.driver_id -> rechazo
```

Regla adicional de convergencia:

1. `VehicleSession` es el canon runtime para control y telemetría;
2. si `Route.vehicle_id` está vacío al asociar la sesión, debe backfillearse desde `session.vehicle_id` antes de usar la ruta en control;
3. `Route.driver_id` no puede divergir de `session.driver_id` porque la ruta ya exige conductor explícito.

Consecuencia:

```text
control-state y telemetria leen la identidad efectiva desde session
route se sincroniza para no dejar surfaces legacy desalineadas
```

### 2. Ejecución

La ejecución permanece donde ya está madura:

- `VehicleSession`
- `RouteOperation`
- `RouteIncident`

Regla fuerte:

```text
execution = hechos discretos auditablemente confirmados
```

### 2.1 Correlación explícita entre operación y contexto espacial

`0037` no convierte a `RouteOperation` en stream GPS, pero sí exige una correlación espacial opcional y fuerte para trazabilidad y debugging.

Modelo conceptual extendido:

```ts
type RouteOperationLocationSnapshot = {
  location_event_id?: string | null
  lat?: number | null
  lng?: number | null
}
```

Reglas:

1. `location_event_id`, `lat` y `lng` son opcionales;
2. cuando existan, representan snapshot del contexto espacial al momento de confirmar la operación;
3. no reemplazan el historial de `VehicleLocationEvent`;
4. no se actualizan luego como si fueran tracking vivo.

Regla fuerte:

```text
route operation puede guardar una huella espacial
pero nunca se convierte en contenedor del stream de telemetria
```

### 3. Telemetría

`0037` agrega una nueva capa de eventos continuos de ubicación.

Regla fuerte:

```text
GPS es stream continuo
no un detalle embebido dentro de RouteOperation
```

### 4. Control

`0037` agrega una capa derivada de estado actual de ruta.

Regla fuerte:

```text
RouteControlState resume el estado vivo
pero no reemplaza ni la telemetria historica ni la ejecucion operacional
```

### 4.1 Coexistencia obligatoria con `Route` y `RouteStop`

El modelo actual ya usa runtime fields en planificación:

- `lg_routes.status`
- `lg_route_stops.status`
- `lg_route_stops.arrival_time`
- `lg_route_stops.departure_time`

`0037` no crea una segunda verdad paralela para esos campos.

Decisión explícita:

1. `RouteControlState` es un read-model de control y navegación;
2. `Route` y `RouteStop` siguen siendo los owners del estado operacional persistido del plan;
3. `RouteStop.status` no se reinterpreta como estado navegacional fino de GPS;
4. las acciones manuales `arrive/depart` deben mutar `arrival_time/departure_time` y la proyección de control, no convertir `RouteStop.status` en un enum nuevo de navegación;
5. `RouteStop.status` sigue reservado para el cierre operativo grueso/histórico de la parada y su semántica existente;
6. luego de la mutación de timestamps o cierre real, `RouteControlState` y `RouteStopProgress` se recalculan desde la misma base.

Regla fuerte:

```text
route_control no reemplaza route_stop.status
lo interpreta y lo proyecta en tiempo real junto con telemetria
```

Consecuencia:

- si existe conflicto entre `RouteControlState` y `RouteStop.status`, la implementación debe recomputar y reparar el read-model;
- el write canon del progreso de parada no vive en `RouteControlState`.

Tabla de ownership mínima:

| Superficie | Propósito | Owner |
|---|---|---|
| `Route.status` | lifecycle grueso del plan (`PLANIFICADO`, `INICIADO`, etc.) | `Route` runtime actual |
| `RouteStop.status` | cierre operativo/histórico grueso de la parada | `RouteStop` + reglas existentes |
| `RouteStop.arrival_time/departure_time` | timestamps observados de llegada/salida | control manual/telemetría |
| `RouteStopProgress.progress_status` | lectura derivada de progreso real | proyección derivada |
| `RouteControlState.status` | subestado navegacional vivo de ejecución espacial | proyección derivada |

## Decisión de dominio

### 1. `RouteOperation` no absorbe GPS

`RouteOperation` sigue representando:

- entrega;
- recojo;
- intercambio;
- corrección;
- vínculo opcional con incidencia.

No debe crecer con:

- `lat/lng` obligatorios por operación;
- stream de tracking;
- ETA;
- cálculo de desvío;
- geofence.

Regla fuerte:

```text
operacion = discreta
tracking = continuo
no mezclar
```

### 2. La telemetría debe ser append-only

La ubicación del vehículo debe persistirse como historial de eventos, no solo como último punto sobrescrito.

Modelo conceptual:

```ts
type VehicleLocationEvent = {
  id: string
  session_id: string
  route_id?: string | null
  vehicle_id: string
  lat: number
  lng: number
  speed?: number | null
  heading?: number | null
  accuracy_meters?: number | null
  source: "DRIVER_APP" | "WEB" | "IMPORT" | "SYSTEM"
  recorded_at: string
  received_at: string
}
```

Razones:

- playback real;
- auditoría;
- reconstrucción de timeline;
- debugging de ruta;
- soporte futuro para desvíos y detenciones.

### 3. El estado de control debe ser una proyección derivada

Además del historial append-only, el sistema debe mantener un snapshot rápido por sesión/ruta.

Modelo conceptual:

```ts
type RouteControlState = {
  session_id: string
  route_id?: string | null
  vehicle_id: string

  active_stop_id?: string | null
  active_stop_started_at?: string | null

  current_stop_id?: string | null
  current_stop_index?: number | null

  status:
    | "NO_ROUTE_ASSIGNED"
    | "PENDING_START"
    | "EN_RUTA"
    | "EN_PARADA"
    | "DETENIDO"
    | "DESVIADO"
    | "COMPLETADO"

  last_lat?: number | null
  last_lng?: number | null
  last_speed?: number | null
  last_heading?: number | null
  last_recorded_at?: string | null

  completed_stops: number
  total_stops: number
  progress_percent: number

  next_stop_eta_minutes?: number | null
  off_route: boolean
  geofence_state?: "OUTSIDE" | "APPROACHING" | "INSIDE" | null
}
```

Regla fuerte:

```text
RouteControlState se puede recalcular o reparar
VehicleLocationEvent no se reescribe como si nunca hubiera existido
```

Ley explícita de este slice:

```text
RouteControlState = cache invalidable
```

Todo campo persistido en `RouteControlState` debe poder reconstruirse, como mínimo, desde:

- `VehicleLocationEvent`;
- `Route` / `RouteStop`;
- `arrival_time` / `departure_time`;
- acciones manuales de control;
- resultados de parada cuando apliquen.

Si una implementación introduce un dato en `RouteControlState` que no puede recomputarse desde esas fuentes, rompe la spec.

### 3.1 `active_stop` modela intención operativa, no solo inferencia espacial

`current_stop_id` y `current_stop_index` son lectura derivada del punto probable del recorrido.

Pero control de ruta necesita también un concepto explícito de parada activa:

- qué parada está siendo trabajada;
- desde cuándo se está trabajando;
- aunque el vehículo no esté exactamente inmóvil o todavía no exista cierre semántico final.

Regla:

```text
active_stop = intencion operativa actual
current_stop = lectura derivada del recorrido
next_stop = objetivo posterior esperado
```

`active_stop_id` puede activarse por:

1. llegada manual;
2. sugerencia automática aceptada;
3. transición operacional explícita del control.

No debe inferirse solo por “último punto cercano” sin más contexto.

### 3.2 `RouteControlState` no crea un workflow paralelo a `VehicleSession`

`VehicleSession.status` sigue siendo el owner del lifecycle grueso de la jornada:

- `DRAFT`
- `LOADING`
- `READY_TO_DEPART`
- `OUTBOUND`
- `RETURNING`
- `AWAITING_RECONCILIATION`
- `CLOSED`
- `CANCELLED`
- equivalentes vigentes del modelo real

`RouteControlState.status` no reemplaza ese lifecycle.

Su semántica correcta es:

- `NO_ROUTE_ASSIGNED`: la jornada existe, pero no tiene ruta asociada para control;
- `PENDING_START`: existe ruta, pero el tracking de ejecución aún no arrancó;
- `EN_RUTA | EN_PARADA | DETENIDO | DESVIADO | COMPLETADO`: subestado navegacional de una jornada ya en ejecución.

Regla fuerte:

```text
session.status responde en que etapa de jornada esta el aggregate
route_control.status responde como va la ejecucion espacial de esa jornada
```

Relación mínima obligatoria:

1. si la sesión no tiene `route_id`, `route_control.status = NO_ROUTE_ASSIGNED`;
2. si la sesión tiene ruta pero está en `DRAFT | LOADING | READY_TO_DEPART`, `route_control.status = PENDING_START`;
3. `RouteControlState` solo puede entrar a `EN_RUTA | EN_PARADA | DETENIDO | DESVIADO` cuando `session.status` está en `OUTBOUND | RETURNING`;
4. si `session.status` está en `AWAITING_RECONCILIATION | CLOSED`, el control de ruta ya no avanza y debe quedar congelado en `COMPLETADO` si hubo ruta ejecutada;
5. si `session.status = CANCELLED`, la telemetría de control deja de aceptarse salvo decisión posterior explícita;
6. `COMPLETADO` no cierra la sesión por sí solo; solo expresa cierre espacial/control de la ruta.

Tabla mínima de mapeo:

| `VehicleSession.status` | `RouteControlState.status` permitido |
|---|---|
| `DRAFT` | `NO_ROUTE_ASSIGNED` o `PENDING_START` |
| `LOADING` | `NO_ROUTE_ASSIGNED` o `PENDING_START` |
| `READY_TO_DEPART` | `NO_ROUTE_ASSIGNED` o `PENDING_START` |
| `OUTBOUND` | `EN_RUTA`, `EN_PARADA`, `DETENIDO`, `DESVIADO` |
| `RETURNING` | `EN_RUTA`, `DETENIDO`, `DESVIADO` |
| `AWAITING_RECONCILIATION` | `COMPLETADO` |
| `CLOSED` | `COMPLETADO` |
| `CANCELLED` | terminal sin tracking activo |

### 4. La llegada automática sugiere; no impone

Si el vehículo entra en geofence de la siguiente parada, el sistema puede sugerir:

- `ARRIVED_SUGGESTED`
- cambio derivado a `EN_PARADA`
- destaque visual de “llegó / cerca de destino”

Pero no puede convertir eso en bloqueo duro.

Regla fuerte:

```text
el GPS asiste el control
no reemplaza el criterio operativo humano
```

### 5. Siempre existe fallback manual

El chofer y el backoffice deben poder operar aunque:

- no haya señal;
- la precisión GPS sea mala;
- el equipo no reporte temporalmente;
- la ruta esté en interior o sombra satelital.

Por eso deben existir acciones manuales equivalentes al menos para:

- `Llegué a parada`
- `Salí de parada`
- continuar registrando `RouteOperation`
- continuar registrando `RouteIncident`

### 6. GPS no toca stock ni invalida composición

La telemetría no debe afectar por sí sola:

- balances de stock;
- seriales;
- `movement_ids`;
- `composition/current`;
- `Carta Porte`.

La relación correcta es:

```text
RouteOperation cambia la realidad fisica/documental
VehicleLocation explica donde iba ocurriendo
```

### 6.1 Distinción mínima entre `DETENIDO` y `EN_PARADA`

`DETENIDO` y `EN_PARADA` no pueden ser sinónimos.

Regla mínima de interpretación:

- `DETENIDO` = velocidad cercana a cero y fuera de geofence operativa activa;
- `EN_PARADA` = dentro de geofence de parada y con intención operativa (`active_stop_id`) o llegada manual/aceptada.

Consecuencia:

- tráfico, semáforo o detención casual no equivalen a trabajo de parada;
- presencia en geofence sin intención aceptada puede disparar sugerencia, no cambio duro obligatorio.

## Invariantes obligatorios

1. `VehicleLocationEvent` es append-only y auditable.
2. `RouteControlState` es una proyección derivada, no la fuente primaria de verdad operativa.
3. Ninguna operación de calle depende obligatoriamente de GPS para ser válida.
4. Ningún geofence puede impedir registrar `RouteOperation` o `RouteIncident`.
5. Debe existir fallback manual para llegada/salida de parada.
6. La ausencia de telemetría no debe mutar stock ni romper composición.
7. La ruta planificada (`Route` + `RouteStop`) sigue siendo la referencia esperada contra la cual se compara la ejecución.
8. Los cálculos de ETA, desvío y llegada deben declararse como derivados y revisables.
9. Todo dato de telemetría debe respetar `tenant_id` y alcance de permisos.
10. La captura de ubicación debe poder limitarse por frecuencia y precisión para evitar ruido excesivo.
11. `active_stop_id` no puede inferirse de forma ciega solo por cercanía geográfica.
12. Toda operación puede capturar snapshot espacial opcional sin volver obligatoria la telemetría para operar.

## Modelo de datos

### Nuevas entidades mínimas

#### `lg_vehicle_location_events`

Campos mínimos:

- `id`
- `tenant_id`
- `branch_id`
- `session_id`
- `route_id`
- `vehicle_id`
- `driver_id`
- `lat`
- `lng`
- `speed`
- `heading`
- `accuracy_meters`
- `source`
- `recorded_at`
- `received_at`
- `metadata_json`
- `created_at`

Índices mínimos:

- `(tenant_id, session_id, recorded_at desc)`
- `(tenant_id, vehicle_id, recorded_at desc)`
- `(tenant_id, route_id, recorded_at desc)`

Política mínima de volumen para v1:

- cliente de chofer: cada `10-15s` cuando hay movimiento;
- cliente de chofer: cada `60s` cuando el vehículo está detenido;
- umbral de distancia recomendado para emitir nuevo punto: `20-30m`;
- backend: deduplicación básica cuando el nuevo punto no cambia materialmente posición, tiempo o estado.

Regla fuerte:

```text
0037 no admite telemetria sin politica explicita de frecuencia
```

#### `lg_route_control_states`

Campos mínimos:

- `session_id` (PK lógica o unique)
- `tenant_id`
- `route_id` (nullable cuando la jornada aún no tiene ruta)
- `vehicle_id`
- `active_stop_id`
- `active_stop_started_at`
- `current_stop_id`
- `current_stop_index`
- `status`
- `last_lat`
- `last_lng`
- `last_speed`
- `last_heading`
- `last_recorded_at`
- `completed_stops`
- `total_stops`
- `progress_percent`
- `off_route`
- `next_stop_eta_minutes`
- `geofence_state`
- `updated_at`

Regla importante:

- `completed_stops`, `total_stops` y `progress_percent` no son una segunda verdad autónoma;
- si se persisten aquí, funcionan como cache derivado alineado con la misma lógica base de `RouteStopProgress`.

### Datos existentes reutilizados

Se reutilizan sin duplicarlos:

- `lg_routes`
- `lg_route_stops`
- `lg_vehicle_sessions`
- `lg_route_operations`
- `lg_route_incidents`

### Normalización obligatoria de coordenadas

Para que el mapa y el control de ruta sean confiables, los puntos de entrega deben converger a coordenadas estructuradas.

Regla obligatoria de este slice:

- `gps_link` puede sobrevivir como dato heredado o auxiliar;
- la planificación y el control no deben depender de parsear URLs libres;
- `delivery_point` debe incorporar `gps_coordinates` o `lat/lng` normalizados como parte de `0037`.

Canon explícito para este slice:

1. las coordenadas **planificadas** para geofence y control de siguiente parada deben salir de `delivery_point` normalizado;
2. `route_stop.gps_coordinates` y `route.gps_start_coordinates` se interpretan como coordenadas **observadas** o registradas durante ejecución, no como fuente primaria del plan;
3. `gps_link` no es fuente canónica de cálculo, solo soporte heredado o auxiliar de migración/UI.

Esta normalización puede entrar en la misma implementación si el costo es pequeño, o como sub-slice previo si el impacto es mayor.
No queda diferida fuera de `0037`.

Regla de implementación:

1. Fase 1 de `0037` incluye contrato backend/frontend para capturar y leer coordenadas estructuradas de `delivery_point`;
2. las rutas o paradas sin coordenadas estructuradas no pueden participar en geofence ni ETA hasta quedar normalizadas;
3. la spec puede aceptar degradación temporal de visualización para datos legacy incompletos, pero no permite usar `gps_link` como canon definitivo de cálculo.

## APIs y contratos

### Nuevos endpoints mínimos

#### Ingesta de telemetría

`POST /vehicle-sessions/{session_id}/location`

Payload conceptual:

```json
{
  "lat": -12.0464,
  "lng": -77.0428,
  "speed": 22.5,
  "heading": 180,
  "accuracy_meters": 12,
  "recorded_at": "2026-07-30T19:20:00Z",
  "source": "DRIVER_APP"
}
```

Comportamiento:

- persiste `VehicleLocationEvent`;
- recalcula o actualiza `RouteControlState` de la sesión cuando exista contexto de ruta controlable;
- no toca `RouteOperation`;
- no toca `stock`.

Caso sin ruta asignada:

- el endpoint no se rechaza solo porque `session.route_id` sea `null`;
- la ubicación puede persistirse igual como telemetría de sesión;
- el estado derivado debe quedar en `NO_ROUTE_ASSIGNED` y no intentar ETA, geofence ni “siguiente parada”.

#### Estado actual de control

`GET /vehicle-sessions/{session_id}/control-state`

Devuelve snapshot derivado para UI de backoffice y chofer.

Debe soportar dos modos:

1. `NO_ROUTE_ASSIGNED` para jornadas sin ruta;
2. snapshot completo de control cuando la jornada sí está asociada a una ruta.

#### Historial / playback

`GET /vehicle-sessions/{session_id}/location-history?from=&to=&limit=`

Devuelve puntos ordenados por tiempo para playback o troubleshooting.

#### Llegada manual

`POST /vehicle-sessions/{session_id}/stops/{stop_id}/arrive`

#### Salida manual

`POST /vehicle-sessions/{session_id}/stops/{stop_id}/depart`

Estos endpoints actualizan control de ruta y auditoría, pero no crean por sí solos una `RouteOperation` falsa.

### Endpoints existentes que se preservan

Se conservan como baseline o compatibilidad funcional:

- `PATCH /routes/{id}/gps-start`
- `PATCH /routes/{id}/stops/{stop_id}/gps`
- `PATCH /agenda/tasks/{id}/gps`

Regla de transición:

```text
los endpoints actuales de GPS puntual no se borran por esta spec
pero la telemetria continua de jornada pasa a ser el contrato principal de control
```

## Reglas de negocio

1. Una jornada con ruta activa puede recibir telemetría incluso si no se registraron operaciones todavía.
2. Una jornada sin ruta asignada puede recibir telemetría, pero solo en modo `NO_ROUTE_ASSIGNED`.
3. Una jornada sin telemetría sigue pudiendo registrar operaciones e incidencias.
4. La siguiente parada se deriva desde `RouteStop` pendiente más cercana al progreso esperado, no desde la última operación a secas.
5. `completed_stops / total_stops` debe derivarse desde la misma lógica base que alimenta `RouteStopProgress` y `OperationalSummary`, no desde un contador paralelo inventado dentro de `RouteControlState`.
6. Las acciones manuales `arrive/depart` y las sugerencias automáticas de llegada deben converger sobre la misma proyección de progreso de parada para evitar dos verdades.
7. Un vehículo dentro del radio de parada puede disparar sugerencia de llegada; la confirmación manual sigue disponible.
8. Un desvío no invalida la jornada; genera estado de atención y trazabilidad.
9. ETA es una estimación; nunca una fuente normativa de cumplimiento.
10. Playback debe reflejar puntos históricos realmente recibidos, no interpolaciones inventadas como verdad auditable.
11. La UI de control puede mostrar ruta planificada y puntos recorridos aunque no exista motor de routing vial.
12. El sistema debe tolerar muestreo irregular de telemetría.
13. `DETENIDO` y `EN_PARADA` deben resolverse con reglas distintas; detenerse fuera de cliente no equivale a trabajar una parada.
14. `active_stop_id` debe poder fijarse manualmente o por aceptación explícita de llegada sugerida.

## UX objetivo

### Backoffice

El backoffice de control debe mostrar:

- mapa de ruta con paradas planificadas;
- posición actual del vehículo;
- estado de control (`EN_RUTA`, `EN_PARADA`, `DETENIDO`, `DESVIADO`, `COMPLETADO`);
- siguiente parada;
- progreso;
- acceso a playback;
- alertas visibles, no bloqueantes.

### Chofer / operación de campo

La superficie de chofer o consola operativa debe permitir:

- ver la ruta y la siguiente parada;
- ver ubicación actual en contexto;
- marcar manualmente llegada/salida;
- seguir usando `RouteOperation` y `RouteIncident` sin fricción extra;
- seguir operando si el GPS falla.

### Relación con el mapa

En v1/v2 el mapa debe usar `Leaflet + OpenStreetMap` como base visual.

Regla importante:

```text
OpenStreetMap resuelve visualizacion y contexto
no obliga en esta spec a calcular route-by-road real desde el dia uno
```

Si más adelante se desea ruta vial real, deberá integrarse un motor adicional y documentarse en una spec o ADR posterior.

## Implementación incremental

### Fase 1 - Telemetría básica y mapa vivo

Incluye:

- normalización estructurada de coordenadas en `delivery_point`;
- persistir ubicación periódica por `session_id`;
- endpoint de ingesta de ubicación;
- endpoint de lectura de `control-state`;
- mapa básico en contexto de ruta;
- visualización de vehículo y paradas;
- snapshot espacial opcional en operaciones nuevas cuando exista punto cercano disponible;
- sin ETA ni desvío sofisticado.

### Fase 2 - Estado de ruta y llegada sugerida

Incluye:

- `RouteControlState` completo;
- geofence simple por parada;
- llegada sugerida automática;
- acciones manuales `arrive/depart`;
- `active_stop_id` y `active_stop_started_at`;
- progreso operativo visible;
- playback básico.

### Fase 3 - Alertas y derivación avanzada

Incluye:

- ETA derivado;
- alertas de desvío y detención prolongada;
- estado `DESVIADO` más confiable;
- posible consumo de routing vial externo;
- refinamientos de backoffice tipo torre de control.

## Permisos

Permisos base de v1:

- `logistics.session.read`
- `logistics.session.manage`

Aplicación mínima:

- lectura de `control-state` e historial: `logistics.session.read`;
- ingesta de telemetría y acciones manuales `arrive/depart`: `logistics.session.manage`.

Nota:

- si en una fase posterior se necesita aislar telemetría y control de ruta con permisos propios (`logistics.route_control.*`, `logistics.telemetry.*`), eso debe abrirse como ajuste explícito del manifiesto y del runtime, no asumirse de manera silenciosa en esta v1.

## Eventos

Eventos nuevos sugeridos:

- `logistics.vehicle_location.recorded`
- `logistics.route_control.status_changed`
- `logistics.route_control.stop_arrival_suggested`
- `logistics.route_control.stop_arrived_manually`
- `logistics.route_control.stop_departed_manually`
- `logistics.route_control.deviation_detected`

Reglas:

- no emitir eventos antes de persistir el dato principal;
- `VehicleLocationEvent` puede producir eventos livianos o agregados, pero sin convertir el bus en spam opaco;
- si el volumen de telemetría vuelve inviable emitir un evento por punto, la implementación puede limitar eventos a cambios relevantes de estado derivado.

## Auditoría y observabilidad

Debe registrarse al menos:

- ingesta de telemetría relevante con `session_id`, `vehicle_id`, `tenant_id`, `source`, `correlation_id`;
- cambios de `RouteControlState` significativos;
- confirmaciones manuales de llegada/salida;
- desvíos detectados;
- errores de ingestión o payload inválido;
- playback consultado no requiere auditoría funcional fuerte, salvo necesidad futura.

Reglas:

1. el historial de telemetría no reemplaza audit log;
2. la auditoría debe distinguir entre cambio automático y acción humana;
3. los cálculos derivados deben poder explicarse con datos reconstruibles.

## Migraciones

Sí requiere migraciones de base de datos.

Mínimo:

1. nueva tabla `lg_vehicle_location_events`;
2. nueva tabla `lg_route_control_states`;
3. índices por sesión, vehículo y tiempo;
4. migración obligatoria para coordenadas estructuradas en `delivery_points`.

Regla:

```text
la normalizacion de coordenadas en delivery points es parte de 0037
y puede ejecutarse de forma incremental sin volverse una migracion gigante
```

## Riesgos

1. mezclar control de ruta con `session.status` y terminar creando dos workflows paralelos;
2. sobreacoplar GPS a validez operativa;
3. inundar el sistema con telemetría sin estrategia de frecuencia o retención;
4. asumir precisión falsa del GPS y generar llegadas/desvíos incorrectos;
5. depender de `gps_link` legacy sin converger a coordenadas estructuradas;
6. intentar meter ETA/routing vial avanzado demasiado pronto;
7. convertir `RouteControlState` en segunda fuente de verdad de ejecución;
8. generar demasiados eventos por punto de ubicación y degradar observabilidad.

## Criterios de aceptación

1. Existe persistencia append-only de ubicaciones por jornada/vehículo.
2. Los `delivery_points` usados por control de ruta ya exponen coordenadas estructuradas sin depender de `gps_link` como fuente primaria.
3. Existe endpoint para registrar ubicación periódica de una jornada activa.
4. Existe endpoint para consultar el estado derivado de control de una jornada.
5. La jornada puede mostrar un mapa de contexto con vehículo y paradas sin romper `RouteOperation` ni `RouteIncident`.
6. Una jornada sin `route_id` puede persistir telemetría sin romperse, quedando explícitamente en `NO_ROUTE_ASSIGNED`.
7. La falta de GPS no impide registrar operaciones o incidencias.
8. Existen acciones manuales de llegada y salida de parada.
9. El sistema puede reconstruir historial reciente de ubicación para playback básico.
10. La telemetría no altera stock, seriales, composición ni carta porte por sí sola.
11. Los cambios importantes de control quedan observables y auditables.
12. Los datos de progreso de control y los contadores mostrados en `OperationalSummary` no divergen porque comparten la misma base de derivación.
13. Si la sesión se asocia a una ruta, no puede existir mismatch silencioso de `vehicle_id` o `driver_id` entre sesión y ruta.
14. La implementación respeta tenancy, permisos y trazabilidad.
15. Una `RouteOperation` puede, cuando exista contexto disponible, guardar referencia opcional a `location_event_id` y snapshot `lat/lng` sin depender del stream completo.
16. La política de muestreo mínima de telemetría queda implementada o explícitamente parametrizada.
17. El sistema distingue `DETENIDO` de `EN_PARADA` y expone `active_stop_id` cuando una parada está realmente en trabajo.

## Pruebas requeridas

### Backend

1. tests de ingestión de ubicación válida;
2. tests de rechazo por permiso o tenant incorrecto;
3. tests de actualización de `RouteControlState`;
4. tests de llegada manual y salida manual;
5. tests de no regresión: telemetría no crea ni modifica `RouteOperation` ni `Movement`;
6. tests de playback / consulta histórica básica.

### Frontend

1. tests de rendering del mapa/contexto cuando hay telemetría;
2. tests de estados sin telemetría;
3. tests de acciones manuales de control;
4. tests de no bloqueo del composer operacional cuando falta GPS.

### Manuales

1. jornada en ruta reporta ubicación periódica y se refleja en mapa;
2. el operador puede marcar llegada/salida manualmente;
3. el sistema sigue permitiendo registrar entrega o incidencia con GPS ausente;
4. playback básico refleja puntos persistidos en orden temporal.

## Notas para agentes

1. No meter telemetría dentro de `RouteOperation` por “comodidad”.
2. No bloquear operaciones por geofence.
3. No conectar GPS directamente a stock o movimientos.
4. Reusar `Route` y `RouteStop` como capa de planificación en vez de crear un aggregate paralelo.
5. Si aparece necesidad de routing vial real, abrir sub-spec o ADR en vez de inflar esta spec silenciosamente.
6. Priorizar fase 1 implementable antes de perseguir experiencia tipo Uber completa.

## Referencias

- `docs/specs/core/0033-route-operation-efectos-separados.md`
- `docs/specs/core/0036-evento-de-ruta-unificado-y-contexto-explicito.md`
- `docs/specs/core/0024-1-3-4-operational-summary-de-jornada.md`
- `docs/specs/core/0014-1-logistics-gap-closure.md`
- `docs/specs/core/0014-logistics-complete/index.md`
- `plugins/logistics/backend/models/operations.py`
- `plugins/logistics/backend/router.py`
- `plugins/logistics/frontend/pages/RoutesPage.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx`
- `apps/web/src/shared/ui/location-picker.tsx`
