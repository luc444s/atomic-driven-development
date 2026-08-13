---
id: "0047"
title: "Creación atómica de jornada con ruta asignada"
domain: logistics
module: jornadas
status: propuesta
extends:
  - docs/specs/core/0046-motor-de-calculo-rutas-osrm-vroom.md
  - docs/specs/core/0025-planificacion-calendar-first-y-reserva-de-capacidad.md
  - docs/specs/core/0037-route-control-y-telemetria-de-jornada.md
---

# SPEC 0047 — Creación atómica de jornada con ruta asignada

## Estado

Propuesta — v1

## Frase guía

**Sin ruta asignada real, no nace la jornada.**

## Contexto

Después de `0046`, el sistema ya puede:

- calcular preview de ruta con `OSRM + VROOM`;
- persistir snapshot de ruta asignada con `commit-order`;
- mostrar en `Jornadas` la ruta asignada persistida.

Pero la creación de jornada todavía puede quedar repartida entre varios pasos del frontend:

- crear `Route`;
- crear `RouteStop`;
- calcular/aceptar propuesta;
- crear `VehicleSession`.

Eso deja riesgo de estados parciales y contradice la necesidad operativa nueva:

```text
click crear jornada
-> ruta lista
-> snapshot listo
-> jornada lista
```

## Decisión

La creación de jornada con ruta dinámica pasa a ser **atómica**.

Regla fuerte:

```text
si no existe cálculo aceptado y snapshot de ruta asignada
la jornada no se crea
```

## Objetivo

Agregar un flujo backend único para `Crear jornada` que:

1. cree ruta base si aún no existe;
2. cree stops si vienen desde clientes/direcciones;
3. calcule orden y geometría con `0046`;
4. persista snapshot asignado con `commit-order`;
5. cree la `VehicleSession` solo después de todo lo anterior;
6. haga rollback completo si cualquiera de esos pasos falla.

## No objetivos

- no recalcular automáticamente la ruta después de creada la jornada;
- no permitir fallback silencioso a línea genérica cuando el cálculo falle;
- no reemplazar `Planning`;
- no alterar ownership de `VehicleSession` como aggregate runtime;
- no introducir multi-vehículo en esta spec.

## Política de fallo

Se elige **ruta A / hard fail**.

### Si falla el motor de rutas

- no se crea la jornada;
- no se deja `VehicleSession` huérfana;
- no se confirma una ruta parcial sin snapshot asignado;
- el usuario recibe error claro.

### Mensaje mínimo esperado

```text
No se pudo crear la jornada: el motor de rutas no pudo generar la ruta asignada.
```

Mensajes más específicos aceptables:

- falta origen con GPS;
- faltan direcciones con GPS;
- `OSRM` no disponible;
- `VROOM` no disponible;
- no se pudo persistir snapshot.

## Flujo oficial

### Caso 1 — Jornada con clientes/direcciones

```text
Crear jornada
-> validar vehículo/conductor/almacén
-> crear Route
-> crear RouteStop desde direcciones seleccionadas
-> optimize/preview routing
-> commit-order
-> crear VehicleSession ligada a route_id
-> devolver jornada lista
```

### Caso 2 — Jornada con `route_id` ya existente

```text
Crear jornada
-> validar ruta existente
-> si no hay snapshot asignado: calcular + commit-order
-> crear VehicleSession
-> devolver jornada lista
```

## Regla de atomicidad

Todos los pasos viven en una sola operación de aplicación.

Si uno falla:

- rollback de route/stop si fueron creados en la misma operación;
- rollback de snapshot;
- rollback de session.

## Contrato backend nuevo

### Endpoint

`POST /vehicle-sessions/create-with-route`

### Request

```python
class CreateVehicleSessionWithRouteRequest(BaseModel):
    vehicle_id: str
    driver_id: str
    origin_warehouse_id: str | None = None
    route_id: str | None = None
    customer_ids: list[str] = []
    address_ids: list[str] = []
    route_date: date | None = None
```

### Response

Debe devolver la misma forma base de `VehicleSessionDetail`, pero garantizando que:

- `route_id` no es nulo;
- existe snapshot asignado para esa ruta;
- la jornada ya puede abrir mapa con polyline persistida.

## Reglas de negocio

1. `VehicleSession` no se crea sin `route_id` válido en este flujo.
2. `VehicleSession` no se crea sin snapshot asignado persistido.
3. Si se usan `address_ids`, la ruta se genera automáticamente.
4. Si se usa `route_id` existente, debe tener stops suficientes para cálculo.
5. Si faltan coordenadas del origen o de los stops, el flujo falla completo.
6. El cálculo aceptado del motor se hace exactamente una vez antes de crear la jornada.
7. La jornada creada abre directamente con mapa de ruta real, no con fallback manual, salvo lectura de snapshots históricos ya válidos.

## Frontend

### `CreateJornadaDialog`

Sigue siendo punto de entrada principal.

No debe orquestar localmente:

- `createRoute`;
- `createRouteStop`;
- `optimize`;
- `commit-order`;
- `createVehicleSession`.

Debe hacer una sola llamada al endpoint atómico.

### `VehicleSessionsPage`

Debe:

- reemplazar la mutación actual de creación fragmentada;
- usar la mutación `create-with-route`;
- abrir la jornada resultante inmediatamente.

## Auditoría

Debe quedar registro al menos de:

- `routing.commit_order` ya existente;
- nueva acción `session.create_with_route`;
- `route.create_auto_from_jornada` cuando aplique.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| crear demasiada lógica en frontend | alto | mover orquestación al backend |
| rollback incompleto | alto | operación transaccional única |
| datos GPS incompletos | alto | validación fuerte antes de crear session |
| dependencia dura de routing | medio | error explícito, no fallback silencioso |

## Criterios de aceptación

1. Existe endpoint backend atómico `create-with-route`.
2. Si el cálculo falla, no se crea `VehicleSession`.
3. Si el cálculo y commit funcionan, se crea `VehicleSession` con `route_id` listo.
4. Al abrir la jornada recién creada, el mapa usa snapshot persistido de ruta asignada.
5. El frontend ya no crea ruta/stops/session por pasos sueltos para este flujo.
6. Los tests cubren éxito y rollback.

## Plan de implementación por PRs

### PR8 — Backend atómico

Alcance:

- servicio `create_vehicle_session_with_route`;
- endpoint `POST /vehicle-sessions/create-with-route`;
- integración con `0046` preview + commit-order;
- rollback total.

Resultado:

- backend dueño del flujo completo.

### PR9 — Frontend crea jornada con flujo único

Alcance:

- `CreateJornadaDialog` y `VehicleSessionsPage` usan endpoint atómico;
- apertura inmediata de la jornada creada;
- eliminación de orquestación fragmentada en frontend para este caso.

Resultado:

- click `Crear jornada` = jornada real con ruta asignada.

### PR10 — Hardening UX

Alcance:

- mensajes claros de fallo de routing;
- loading states;
- bloqueo de submit mientras se calcula;
- feedback de ruta creada correctamente.

Resultado:

- flujo usable sin ambigüedad operativa.

### PR11 — Mapa embedded de jornada activa en vista por vehículo

Alcance:

- `VehicleJornadasDialog` muestra mapa completo si existe `active_session` con `route_id`;
- consulta `route detail`, `route stops`, `assigned-route snapshot` y `route-stop-progress`;
- usa `RouteContextMap` con prioridad de `polyline` persistida y fallback a línea simple.

Resultado:

- al abrir un vehículo con jornada activa, la ruta asignada queda visible inmediatamente;
- no hace falta entrar primero al contexto completo de la jornada para ver el mapa.

## Orden obligatorio

```text
PR8 -> PR9 -> PR10 -> PR11
```
