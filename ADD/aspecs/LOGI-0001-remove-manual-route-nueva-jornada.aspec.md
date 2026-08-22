# A.SPEC LOGI-0001 — Remove manual route and redundant cancel from Nueva Jornada modal

> Cambios ya implementados y verificados en esta sesión. Documentados como
> A.SPEC atómica por petición explícita, agrupando la limpieza de la modal
> "Nueva jornada" del módulo Logistics.

## WHY

La modal "Nueva jornada" (logistics) arrastraba dos problemas de superficie:

1. **Ruta manual muerta**: el diálogo permitía seleccionar una ruta existente
   o crear una "ruta manual" (`Crear ruta` / `Crear ruta manual`) a través de
   `CreateRouteFromJornadaDialog`. Esa capacidad de ruta manual quedó
   inútil: el sistema genera la ruta automáticamente desde las direcciones de
   los clientes (`createVehicleSessionWithRoute`). Mantener el selector y el
   diálogo sólo agregaba código muerto y dos botones que no aportaban.

2. **Botón redundante**: cada diálogo de jornada renderizaba un botón
   "Cancelar" en el footer mientras el componente `Dialog` ya muestra un botón
   "Cerrar" en el header. Aparecían los dos al mismo tiempo (cierre + cancelar),
   redundantes y confusos.

## WHAT

- En `CreateJornadaDialog`: se eliminó el bloque de selección de ruta manual
  (selector `Select` + botones `Crear ruta` / `Crear ruta manual`) y sus props
  `routes`, `onOpenCreateRoute`, `setRouteVehicle`. La modal ahora sólo
  informa la generación automática de ruta cuando hay direcciones.
- Se eliminó el botón footer "Cancelar" de `CreateJornadaDialog` y de
  `CreateVehicleFromJornadaDialog`. El cierre queda únicamente en el botón
  "Cerrar" del header del `Dialog`.
- Se borró `CreateRouteFromJornadaDialog.tsx` y todo su cableado en
  `VehicleSessionsPage.tsx` (import, estado `routeForm`/`isRouteOpen`/
  `routeError`, `createRouteMutation`, `onSubmitRoute`, `routesQuery`,
  `routeMap` y estados muertos `isRoutesLibraryOpen`/`routesAutoStart`).

## SCOPE

- `plugins/logistics/frontend/components/vehicle-sessions/CreateJornadaDialog.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/CreateVehicleFromJornadaDialog.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/CreateRouteFromJornadaDialog.tsx` (borrado)
- `plugins/logistics/frontend/pages/VehicleSessionsPage.tsx`

## OUT OF SCOPE

- No se toca la generación automática de ruta (`createVehicleSessionWithRoute`
  + `address_ids`): sigue intacta.
- No se toca el backend (`createVehicleSessionWithRoute`, `createRoute`,
  endpoints de rutas en `api/`).
- No se toca `RoutesPage.tsx` ni los componentes `route-builder/*` (fue
  restaurado por rollback previo y no forma parte de este cambio).
- No se modifica la lógica de vehículos, conductores, almacenes ni mapa de
  direcciones.

## CONTRACT

- Precondición: la creación de jornada con direcciones de clientes debe poder
  generar la ruta automáticamente vía backend.
- Postcondición: al abrir "Nueva jornada" ya NO existe selector de ruta manual
  ni botón "Crear ruta" / "Crear ruta manual"; la única vía de ruta es
  automática por direcciones. Los diálogos de jornada muestran un solo punto
  de cierre ("Cerrar" en header), sin botón "Cancelar" en footer.

## INVARIANTS

```yaml
invariants:
  - La ruta automática por direcciones (createVehicleSessionWithRoute) MUST seguir funcionando.
  - El formulario de jornada sigue enviando route_id (null) y address_ids al backend.
  - El cierre de la modal (onClose) sigue disponible vía el botón "Cerrar" del header.
  - No se rompe la creación de jornada sin ruta manual (ahora requiere direcciones).
```

## VERIFICATION

- `apps/web/package.json` -> `node node_modules/typescript/bin/tsc --noEmit`
  sobre `apps/web`: no hay errores nuevos en los archivos de logistics. El
  único error reportado es pre-existente y ajeno
  (`plugins/logistics/frontend/api/index.ts(32,1): duplicate export
  'VehicleLocationRecordPayload'`), no introducido por este cambio.
- Grep de superficie:
  - `grep -rn "CreateRouteFromJornadaDialog" plugins` -> sin referencias vivas.
  - `grep -n "onOpenCreateRoute\|setRouteVehicle\|routes={routesQuery" plugins/logistics/frontend/pages/VehicleSessionsPage.tsx` -> sin coincidencias.
  - `grep -n "Cancelar" plugins/logistics/frontend/components/vehicle-sessions/CreateJornadaDialog.tsx` -> sin coincidencias (eliminado).

## ROLLBACK

Reversible mediante `git checkout` / `git restore` de los 4 paths afectados
(restaura `CreateRouteFromJornadaDialog.tsx` borrado y revierte las ediciones).
No hay efectos irreversibles (sólo eliminación de UI muerta/redundante, sin
migraciones ni datos).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/frontend/components/vehicle-sessions/CreateJornadaDialog.tsx
    - plugins/logistics/frontend/components/vehicle-sessions/CreateVehicleFromJornadaDialog.tsx
    - plugins/logistics/frontend/components/vehicle-sessions/CreateRouteFromJornadaDialog.tsx
    - plugins/logistics/frontend/pages/VehicleSessionsPage.tsx
  prohibited:
    - plugins/logistics/backend/**
    - plugins/logistics/frontend/api/**
    - plugins/logistics/frontend/pages/RoutesPage.tsx
    - plugins/logistics/frontend/components/route-builder/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - logistics.nueva_jornada.modal
  indirect:
    - logistics.jornada.create (validación ahora require address_ids)
  must_not_affect:
    - logistics.ruta.automatica
    - logistics.vehiculos
    - logistics.almacenes
    - backend
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: []
  systemic_invariants: []
  composition_checks: []
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations: []
```

## Traceability

- Requirement: limpieza de ruta manual muerta + botón cancelar redundante en modal Nueva jornada
- Commit: dedd8c5 — "LOGI-0001: remove manual route + redundant cancel from Nueva Jornada"
- Deployment: n/a

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now
- [x] Invariants preserved
- [x] Verification passed (tsc sin errores nuevos; greps limpios)
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established (commit dedd8c5)
