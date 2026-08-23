# A.SPEC LOGI-0032 — Mapa de contexto de jornada dibuja ruta OSRM asignada y almacén origen

## WHY

El mapa en vivo de control de jornada (`RouteControlMapPanel`, título "Mapa de contexto")
dibujaba la ruta planificada como una **línea recta** entre los puntos de entrega, sin
consumir la geometría vial que OSRM ya generó y persistió en `lg_route_calculations.polyline`.
Además omitía el almacén origen (`lg_routes.gps_start_coordinates`), por lo que el operador
veía "solo direcciones" flotando sin recorrido real.

La feature existía en el mapa estático (`RouteContextMap`, commit `78b9eac` "use assigned
route snapshot") pero nunca fue portada al panel en vivo creado después (commit `33d5c85`,
TMS-013). Adicionalmente, `buildRouteControlMapView` filtraba cualquier parada sin
delivery point vinculado (`delivery_point_id` NULL), aunque la parada tuviera sus propias
coordenadas en `lg_route_stops.gps_coordinates`.

## WHAT

Una sola transición observable: el "Mapa de contexto" de una jornada activa muestra

1. la **ruta vial asignada** (polyline encoded decodificada de `assigned_route.polyline`,
   ~11.500 puntos reales siguiendo calles) como línea sólida;
2. el **marcador del almacén origen** ("A", verde) cuando la ruta tiene
   `gps_start_coordinates`;
3. las paradas con coordenadas aunque **no tengan delivery point** — usando como fallback
   `lg_route_stops.gps_coordinates`;
4. línea punteada recta (almacén → paradas) únicamente como fallback cuando no existe
   polyline asignada.

## SCOPE

- `route-control-view.ts`: `buildRouteControlMapView` acepta `assignedPolyline` y
  `startPoint`; decodifica polyline; fallback a `stop.gps_coordinates`; incluye marcador
  de origen en `plannedPath`.
- `RouteControlMapPanel.tsx`: nuevas props `assignedPolyline` / `startPoint`; dibuja
  polylines (asignada sólida, fallback punteada, recorrida verde) y marcador origen;
  `autoFit` para encuadrar todos los markers.
- `SessionRouteTab.tsx`: pasa `assignedRoute?.polyline` y `startPoint` al panel.
- `route-polyline.ts` (nuevo): util compartido `decodePolyline` (Google precision-5).

## OUT OF SCOPE

- Telemetría en vivo del vehículo (ya existente, intacta).
- El mapa estático `RouteContextMap` (ya soportaba polyline).
- Recálculo u optimización de rutas.
- Detección de desvío de ruta (`off_route`), geofences, ETA.
- Migraciones de DB: no aplica, los datos ya existen.

## CONTRACT

Precondiciones:

- La sesión tiene `route_id` con ruta existente.
- `lg_route_calculations` tiene snapshot asignado para la ruta (o se cae a fallback).
- Las paradas tienen coordenadas en `gps_coordinates` propio o vía delivery point.

Postcondiciones:

- Con polyline asignada: la polilínea dibujada sigue geometría vial (>2 puntos) y comienza
  en las cercanías del almacén origen.
- Sin polyline asignada: se dibuja línea punteada almacén→paradas (nunca nada roto).
- Paradas sin `delivery_point_id` pero con `gps_coordinates` propio aparecen en el mapa.

## INVARIANTS

```yaml
invariants:
  - El resto del tab "Ruta" (carta porte, operaciones, botones llegada/salida) no cambia.
  - RouteContextMap (mapa estático) no se modifica.
  - Si decodePolyline falla o la polyline es inválida, el mapa NO debe crashear:
    cae a línea punteada planificada.
  - El orden de render en LocationMap se preserva: ChangeView primero, FitMarkers después.
  - No se tocan endpoints backend ni schemas.
```

## VERIFICATION

- `cd apps/web && npx tsc --noEmit` — sin errores nuevos (existe uno preexistente,
  `VehicleLocationRecordPayload` duplicado, fuera de superficie).
- Endpoint real: `GET /api/v1/plugins/logistics/routing/assigned-route/{route_id}`
  devuelve `polyline` de 31.079 chars; decodificación manual produce 11.594 puntos,
  primero ≈ (-8.098, -79.007) [almacén OXIPUR], último ≈ (-7.720, -77.664) [entrega final].
- Endpoint real: `GET .../vehicle-sessions/{id}/route-context` devuelve 2 stops con
  `gps_coordinates` dict y `delivery_point_id` null.
- Simulación Node de `buildRouteControlMapView` con esos datos: 2 stops mapeados,
  polyline >1 punto → se dibuja.
- Visual: jornada RAM/BEI-793 OUTBOUND muestra ruta vial + almacén A + 2 paradas.

## ROLLBACK

Reversible: revertir los 4 archivos tocados
(`git checkout -- plugins/logistics/frontend/components/vehicle-sessions/{route-control-view.ts,RouteControlMapPanel.tsx,SessionRouteTab.tsx}` y borrar `route-polyline.ts`).
Sin efecto irreversible: solo lectura de datos existentes, sin escrituras.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/frontend/components/vehicle-sessions/route-control-view.ts
    - plugins/logistics/frontend/components/vehicle-sessions/RouteControlMapPanel.tsx
    - plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx
    - plugins/logistics/frontend/components/vehicle-sessions/route-polyline.ts
  prohibited:
    - vendor/systutor-shell/**
    - plugins/logistics/backend/**
    - plugins/logistics/frontend/api/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - vehicle-sessions.SessionRouteTab.mapa_de_contexto
  indirect:
    - vehicle-sessions.VehicleJornadasDialog # usa RouteContextMap, no tocado; verificación visual
  must_not_affect:
    - route-builder.RouteBuilderMap
    - planning
    - carta porte / waybills
    - backend routing service
```

## Composition

```yaml
composition:
  requires_aspecs:
    - LOGI-0001 # flujo jornada sin ruta manual, contexto de sesión
  must_compose_with:
    - TMS-013 # mapa de jornada en vivo con telemetría
  systemic_invariants:
    - Un mismo route_id produce la misma geometría en mapa estático y dinámico.
  composition_checks:
    - Abrir jornada OUTBOUND con ruta asignada: ambos mapas muestran trazado vial coherente.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: route-control-view.ts sigue siendo el único constructor del view del mapa vivo
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - vehicle-sessions/route-polyline.ts # decoder aislado, reutilizable
```

## Traceability

- Requirement: reporte del usuario — "la línea no debe ser recta, debe ser la ruta
  asignada; falta la ubicación del almacén" (vehículo RAM/BEI-793).
- Commit: pendente de integración (ver mensaje LOGI-0032).
- Deployment: frontend Vite dev / build web; sin backend deploy.

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now
- [x] Invariants preserved
- [x] Verification passed
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [ ] Traceability established (commit pendiente)
