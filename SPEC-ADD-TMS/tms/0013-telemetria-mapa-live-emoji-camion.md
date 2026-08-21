# A.SPEC [TMS-013] — Mapa de jornada con telemetría live y emoji camión (cambio para main)

> Verdicto speccer: `ACCEPT_ONE`. Verdad independiente falsable: cuando una jornada
> materializada (con ruta asignada) se encuentra en estado operativo, el operador ve un
> **mapa** — anclado en la página de la jornada — con la posición del vehículo representada
> por un **emoji 🚚** en tiempo real (refresco periódico del control-state y del historial de
> ubicaciones). El backend de telemetría ya existe en **main** (route-control); esta spec
> agrega la capa de presentación live + captura de ubicación desde navegador. No depende del
> sync legacy: aplica a toda jornada materializada, venga de planificación (main) o de
> integración legacy (TMS).

## WHY

La jornada materializada (activación de planificación en main, o salida legacy sincronizada en
TMS) llega al centro operativo (`VehicleSessionDetailPage`) y hoy el operador NO ve dónde está
el camión:

- `SessionRouteTab` pinta `RouteContextMapLazy`: ruta planificada estática, sin posición del
  vehículo ni telemetría.
- El backend de telemetría está completo y auditado (`lg_vehicle_location_events`,
  `POST /vehicle-sessions/{id}/location`, `GET /location-history`,
  `GET /control-state`, permiso `logistics.session.route_execute`), pero **nada en el
  frontend lo consume**: `RouteControlMapPanel.tsx` está escrito y huérfano (no se monta en
  ninguna página), y no existen fetchers para control-state ni location-history.
- No existe captura de ubicación desde el navegador (para prueba PWA/demo).

El operador necesita ver el camión moviéndose en el mapa: "cuando se materializa una ruta debe
aparecer el mapa con la representación de un emoji de un camión, este mostrará la ubicación en
tiempo real".

## WHAT

Existe un comportamiento observable: en la página de detalle de una jornada con **ruta asignada**
(`route_id != null`) y estado en `READY_TO_DEPART | OUTBOUND | RETURNING`, se muestra un mapa con:

1. La ruta planificada (polyline de paradas) — ya resuelta por `buildRouteControlMapView`.
2. La **posición del vehículo** como marker con **emoji 🚚** (vía `labelVisible` del marker,
   sin tocar `LocationMap` del Core — opción B decidida).
3. La **traza recorrida** (polyline verde) desde el historial de ubicaciones.
4. Refresco automático periódico (~10 s) del `control-state` y del historial reciente; el mapa
   se re-centra cuando la posición cambia.
5. La jornada en modo demo/PWA puede **capturar ubicación desde el navegador**
   (`navigator.geolocation.watchPosition`) y reportarla cada intervalo al backend con
   `source: "WEB"` — para que el mapa muestre movimiento real sin app nativa.

Los endpoints ya existen en main; esta spec NO crea backend nuevo, solo consume el existente.
La captura de navegador tampoco distingue origen de la jornada: el driver reporta contra la
jornada activa que tenga asignada, sin importar cómo se materializó.

## SCOPE

- Frontend logistics: fetchers `getVehicleLocationHistory()`, `getRouteControlState()` (+
  `reportVehicleLocation()` para el sender) en `plugins/logistics/frontend/api/route-control.ts`
  (las keys ya existen en `keys.ts`).
- Frontend logistics: montar `RouteControlMapPanel` en la página de la jornada materializada
  (sustituye/convive con `RouteContextMapLazy`) con polling (`refetchInterval` ~10 s).
- Frontend logistics: en `RouteControlMapPanel`/`route-control-view`, el marker del vehículo
  usa `labelVisible: true` + label `"🚚"` (opción B; sin cambios en `vendor/systutor-shell`).
- Frontend: hook de captura `useVehicleTelemetry(sessionId)` (en `apps/web/src/lib/` como hook
  compartido — regla del repo) que usa `watchPosition`, deduplica localmente y llama
  `reportVehicleLocation()` cada intervalo (default 5 s, `source: "WEB"`).
- Demo/test: en `VehicleSessionDetailPage` un control "Iniciar telemetría (navegador)" que
  arranca/detiene el hook con feedback de estado (posición actual, último reporte, errores de
  permiso). Funciona igual para jornadas de main y de TMS.
- El branch de destino es **main** (los archivos tocados viven en plugins/logistics y
  apps/web, ambos en main); la rama TMS lo absorbirá por rebase/merge posterior.

## OUT OF SCOPE

- App nativa Android / Capacitor / Tauri (el sender navegador es para prueba PWA; la app
  nativa es otra spec).
- Endpoints backend: NO se modifican (ya existen, auditados, con dedup).
- Cambios al modelo `LogisticsVehicleLocationEvent`.
- Notificaciones push, WebSocket/SSE (el polling cubre el realismo para esta spec; el canal
  push es una mejora posterior con ADR).
- Geocercas y estados `geofence_state` (ya vienen en control-state; solo se muestran si
  existen).
- Cambios de stock, waybill, conciliación.

## CONTRACT

- **Precondición**: jornada materializada con `route_id != null` y estado ∈ {`READY_TO_DEPART`,
  `OUTBOUND`, `RETURNING`}; permiso `logistics.session.read` para ver el mapa;
  `logistics.session.route_execute` para reportar ubicaciones. Aplica a jornadas de cualquier
  origen (planificación main o sync legacy).
- **Postcondición (lectura)**: el mapa muestra polyline planificada, polyline recorrida (si hay
  historial) y marker 🚚 en `controlState.last_lat/last_lng` (o último evento de historial si el
  control-state no tiene posición).
- **Postcondición (escritura demo)**: tras habilitar la telemetría, el navegador reporta
  `{lat, lng, speed, heading, accuracy_meters, recorded_at, source:"WEB"}` a
  `POST /vehicle-sessions/{id}/location`; el backend respeta su dedup y sus gates de estado.
- **Filtros de historial**: `getVehicleLocationHistory(sessionId, {from, to, limit})` —
  `limit` default 200, máximo 1000 (igual al DTO existente).
- `RouteControlMapPanel` recibe `history`, `controlState`, `deliveryPoints`, `stops`,
  `sessionStatus` — contrato ya definido por sus props actuales; no cambia su API externa.

## INVARIANTS

```yaml
invariants:
  - "el backend de telemetría NO cambia (endpoints, DTOs, dedup, gates de estado)"
  - "LocationMap del Core NO cambia (emoji camión vía labelVisible, opción B)"
  - "el mapa aparece SOLO con ruta asignada y estado operativo (READY_TO_DEPART/OUTBOUND/RETURNING)"
  - "reportar ubicaciones exige permiso logistics.session.route_execute (403 si falta)"
  - "la captura de navegador es opt-in y reversible (iniciar/detener sin recargar)"
  - "el reporte con source WEB no rompe la compatibilidad del DTO (campo default WEB ya existe)"
```

## VERIFICATION

- Frontend (Vitest, lógica pura): `buildRouteControlMapView` con historia + control-state →
  `vehiclePosition` = última posición y marker 🚚 en `labelVisible`; sin historial y sin
  `last_lat/last_lng` → `vehiclePosition = null` (sin marker de vehículo).
- Frontend (Vitest): fetchers `getVehicleLocationHistory`/`getRouteControlState` pegan a los
  paths correctos con query params (`from`, `to`, `limit`).
- E2E manual: jornada materializada con ruta (creada por activación de planificación en main,
  o por sync legacy en TMS) → el mapa aparece con polyline y 🚚 estático (sin telemetría
  muestra "Sin telemetría reciente"); al habilitar telemetría navegador y moverse, el 🚚 se
  mueve en ≤2 ciclos de polling (~20 s).
- Negativo (I3): jornada sin ruta o en DRAFT/LOADING/CLOSED → el mapa de telemetría live NO se
  monta (se mantiene la vista actual de ruta planificada si existe).
- Negativo (I4): reporte con usuario sin `logistics.session.route_execute` → 403.
- Backend (regresión): suite `route_control` existente se mantiene verde (no se toca backend).

## DECISIONES REGISTRADAS

- **D-TMS-013-1**: emoji camión vía `labelVisible` del marker existente (opción B). Cero cambios
  en `vendor/systutor-shell`. El marker 🚚 acompaña al pin del vehículo (pin de color + label
  emoji visible). Un mapa "camión como icono puro" sería extender `LocationMap` del Core
  (submodule) — se pospone.
- **D-TMS-013-2**: canal de tiempo real = polling (`refetchInterval` ~10 s), no WebSocket/SSE.
  Suficiente para la demo y alineado con la infra actual; push real queda como ADR/spec aparte.
- **D-TMS-013-3**: sender navegador en `apps/web/src/lib/` como hook compartido (regla del
  repo: hooks de infra en lib, no en el plugin).

## ROLLBACK

- Reversible UI-only: quitar el montaje de `RouteControlMapPanel` en `VehicleSessionDetailPage`
  (vuelve `RouteContextMapLazy`) y borrar `api/route-control.ts` + `lib/use-vehicle-telemetry.*`.
  No hay migración, ni datos nuevos, ni cambios de backend/Core que deshacer.

## Change Surface

```yaml
change_surface:
  allowed:
    - "crear plugins/logistics/frontend/api/route-control.ts (fetchers)"
    - "crear apps/web/src/lib/use-vehicle-telemetry.ts (+ test Vitest)"
    - "editar plugins/logistics/frontend/components/vehicle-sessions/RouteControlMapPanel.tsx (marker 🚚 labelVisible)"
    - "editar plugins/logistics/frontend/components/vehicle-sessions/route-control-view.ts (si hace falta tipo marker)"
    - "editar plugins/logistics/frontend/pages/VehicleSessionDetailPage.tsx (montar panel + control demo)"
  prohibited:
    - "tocar backend de telemetría (routers/dto/services route_control)"
    - "tocar vendor/systutor-shell (LocationMap)"
    - "cambiar modelo LogisticsVehicleLocationEvent ni stock"
    - "agregar dependencias nuevas"
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - "página de detalle de jornada (VehicleSessionDetailPage)"
    - "nuevo hook compartido useVehicleTelemetry en apps/web/src/lib/"
  indirect:
    - "todas las jornadas con ruta asignada de cualquier tenant del plugin logistics"
  must_not_affect:
    - "endpoints telemetría y su dedup/gates de estado"
    - "ruta planificada estática (RouteContextMap) para jornadas sin ruta"
    - "stock OSS y legacy"
```

## Composition

```yaml
composition:
  requires_aspecs:
    - "TMS-012 (telemetría backend route-control ya en main)"   # backend consumido, no se modifica
  must_compose_with:
    - "logistics route_control (POST location, GET control-state/location-history)"
  systemic_invariants:
    - "el backend de telemetría y sus permisos no cambian"
    - "el mapa solo aparece con ruta asignada y estado operativo"
  composition_checks:
    - "al reportar con source WEB, el backend acepta y persiste (dedup respetado)"
    - "el mapa refleja el últim control-state tras ≤2 ciclos de polling"
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility (ver jornada viva en mapa) y un solo motivo de cambio
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/logistics/frontend/api/route-control.ts"
    - "apps/web/src/lib/use-vehicle-telemetry.ts"
```

## Traceability

- Requirement: mapa con 🚚 en tiempo real cuando la jornada está materializada (main)
- Commit: pendiente
- Deployment: rama main (afecta plugin logistics + apps/web); TMS lo absorbe por rebase/merge

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now (mapa 🚚 + polling + reporte navegador)
- [x] Invariants preserved
- [x] Verification passed (verifier ADD run)
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established

## Verifier ADD — coverage map

```
contract.lectura-vehiclePosition   -> test route-control-view (3, passed)
contract.lectura-fallback-historial-> test route-control-view "último evento" (passed)
contract.lectura-sin-telemetria    -> test route-control-view "sin vehículo" (passed)
contract.escritura-payload         -> test use-vehicle-telemetry buildVehicleLocationPayload (3, passed)
contract.escritura-dedup           -> test use-vehicle-telemetry positionsDiffer (3, passed)
contract.fetchers-control-state    -> test route-control-api "lee control-state" (passed)
contract.fetchers-history-params   -> test route-control-api "query params"/"omite vacío" (2, passed)
contract.fetchers-report           -> test route-control-api "reporta por POST" (passed)
contract.fetchers-arrive-depart    -> test route-control-api "arrive y depart" (passed)
invariant.backend-no-cambia        -> git diff: solo frontend/logistics + lib (sin backend/Core)
invariant.core-no-cambia           -> git diff: vendor/systutor-shell sin cambios
invariant.mapa-solo-ruta-estado    -> showLiveMap gate en SessionRouteTab (code)
invariant.permiso-route_execute    -> backend existente (no tocado)
invariant.captura-opt-in           -> start/stop en SessionRouteTab, stop() en unmount (code)
invariant.source-WEB-compat        -> test payload fuente WEB (passed)
composition.check-reporte-accepta  -> backend route_control existente (regresión no tocada)
composition.check-polling-refleja  -> refetchInterval 10s control-state + history (code)

VERDICT: PASS
Nota: 4 fallos de suite pre-existentes (badge "Listo", cryogenic, shell, core-management)
confirmados idénticos con git stash (no causados por TMS-013).
```