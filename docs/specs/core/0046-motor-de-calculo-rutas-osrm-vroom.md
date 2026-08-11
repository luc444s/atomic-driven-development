---
id: "0046"
title: "Motor de cálculo de rutas con OSRM + VROOM"
domain: logistics
module: routing
status: propuesta
extends:
  - docs/specs/core/0025-planificacion-calendar-first-y-reserva-de-capacidad.md
  - docs/specs/core/0036.1-route-builder-visual.md
  - docs/specs/core/0036.2-customer-address-gps.md
  - docs/specs/core/0037-route-control-y-telemetria-de-jornada.md
---

# SPEC 0046 — Motor de cálculo de rutas con OSRM + VROOM

## Estado

Propuesta — v1

## Frase guía

**`Jornadas` ejecuta. El motor calcula. El usuario decide aceptar.**

## Contexto

El sistema ya tiene base operativa suficiente para rutas y jornadas:

- `Jornadas` es el aggregate runtime y owner de la ejecución real;
- `Route` y `RouteStop` ya existen como plan operativo persistido;
- `Planning` ya modela reserva de capacidad futura;
- existe `Route Builder` visual y contexto de mapa;
- existe `Route Control` como dirección para telemetría y progreso real.

Lo que falta no es otro aggregate ni otra UI principal. Falta una **capa de cálculo** que resuelva:

- orden sugerido de paradas;
- tiempo y distancia entre stops;
- ETA estimada;
- geometría/polyline de ruta sugerida;
- conflictos de capacidad, ventanas horarias y restricciones básicas.

La necesidad actual no es “Uber completo” ni optimización autónoma en tiempo real. La necesidad actual es un motor auditable y reutilizable para cálculo y preview de ruta sobre datos que ya viven en `logistics`.

## Relación con specs existentes

### `0025` — Planificación

`Planning` sigue siendo owner de reserva de capacidad futura. Esta spec no traslada ownership de planificación al motor. El motor solo calcula una propuesta usable por `Planning`, `Route Builder` o `Jornadas`.

### `0036.1` — Route Builder Map First

`0036.1` declaró explícitamente que el constructor visual no hacía ruteo automático en esa iteración. Esta spec no contradice eso: agrega una nueva capa posterior al constructor para cálculo sugerido de orden y geometría.

### `0037` — Route Control y Telemetría

`0037` explicitó que en ese slice no se exigiría motor externo vial (`OSRM`, `GraphHopper`, `Valhalla`). Esa restricción aplicaba a `0037`, no al sistema para siempre. Con `v1` ya cerrada, `0046` abre el siguiente slice post-`v1`: agregar el motor externo de cálculo sin cambiar ownership de `Route Control` ni de `Jornadas`.

## Objetivo

Agregar un motor de cálculo de rutas basado en **OSRM + VROOM** que permita:

1. construir matriz tiempo/distancia real sobre red vial;
2. optimizar orden de stops para una jornada o ruta;
3. estimar ETA por parada;
4. devolver polyline/geometría de la ruta sugerida;
5. detectar violaciones de ventanas horarias, capacidad y ADR básico;
6. exponer preview de cálculo antes de persistir cambios en `RouteStop.stop_order` o activar jornada.

## No objetivos

- no reemplazar `Jornadas` como owner del runtime;
- no reemplazar `Route` ni `RouteStop` como owner del plan persistido;
- no introducir optimización automática continua durante la ejecución en calle;
- no bloquear `RouteOperation`, `RouteIncident` ni movimientos por fallas del motor;
- no acoplar el cálculo a `stock` como condición de validez;
- no introducir en esta iteración optimización multi-depósito compleja;
- no convertir el constructor visual del mapa en solver;
- no persistir resultados automáticamente sin aceptación explícita del usuario;
- no hacer mobile offline ni recalculo autónomo por GPS en esta spec.

## Alcance

### Incluye

- capa backend de cálculo en `plugins/logistics/backend/services/routing/`;
- integración con proveedor vial `OSRM`;
- integración con optimizador `VROOM`;
- endpoints backend de preview/optimize/commit;
- validaciones de datos mínimos de parada/vehículo;
- snapshot opcional de cálculo para auditoría/debug;
- consumo inicial desde `Route Builder`, `Planning` o `Jornadas` mediante llamada explícita.

### No incluye

- rediseño completo del frontend de rutas;
- tracking en tiempo real;
- replay histórico;
- asignación automática multi-flota no asistida;
- cambios de dominio en `RouteOperation`;
- cambios de ownership entre `Planning`, `Route`, `VehicleSession`.

## Stack elegido

### OSRM

Se adopta **OSRM** como motor vial para:

- `table` → matriz tiempo/distancia entre coordenadas;
- `route` → geometría/polyline de la ruta final;
- `nearest` → snap de coordenadas a red vial.

### VROOM

Se adopta **VROOM** como optimizador para:

- single-vehicle routing inicial;
- secuencia óptima/sugerida de jobs;
- soporte futuro de multi-vehículo, time windows y capacidades;
- integración con matriz y geometría servida por `OSRM`.

### Motivo de la combinación

- `OSRM` simplifica el cálculo vial y es self-hosted;
- `VROOM` simplifica la optimización sin obligar a desarrollar heurísticas complejas desde cero;
- ambos pueden vivir como servicios de infraestructura laterales, consumidos por `logistics` sin mover lógica de negocio al core.

## Arquitectura propuesta

```text
plugins/logistics/backend/services/routing/
├── models.py
├── provider.py
├── matrix.py
├── optimizer.py
├── geometry.py
├── service.py
├── constraints.py
├── cache.py
└── providers/
    ├── osrm.py
    └── vroom.py
```

## Regla arquitectónica fuerte

```text
el motor de cálculo vive en logistics
el kernel no conoce OSRM ni VROOM
el core no absorbe reglas de ruteo de negocio
```

## Responsabilidades por capa

### `provider.py`

Contratos de acceso a motores externos.

### `matrix.py`

Normaliza coordenadas y construye matriz tiempo/distancia.

### `optimizer.py`

Arma payload de optimización y resuelve secuencia sugerida.

### `geometry.py`

Obtiene polyline, legs, resumen de distancia y tiempo.

### `service.py`

Orquesta validación, cálculo, optimización y shape del response final.

### `cache.py`

Cachea matrices y cálculos repetidos cuando el `input_hash` sea equivalente.

## Modelo de entrada

### `RoutingStopInput`

```python
class RoutingStopInput(BaseModel):
    stop_id: str
    customer_id: str | None = None
    customer_name: str | None = None
    address_id: str | None = None
    address_label: str | None = None
    lat: float
    lng: float
    service_minutes: int = 0
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    demand_units: float = 0
    demand_weight_kg: float = 0
    demand_volume_m3: float = 0
    adr_required: bool = False
    priority: int | None = None
```

### `RoutingVehicleInput`

```python
class RoutingVehicleInput(BaseModel):
    vehicle_id: str
    start_warehouse_id: str | None = None
    end_warehouse_id: str | None = None
    start_lat: float
    start_lng: float
    end_lat: float | None = None
    end_lng: float | None = None
    capacity_units: float | None = None
    capacity_weight_kg: float | None = None
    capacity_volume_m3: float | None = None
    adr_capable: bool = False
```

### `RoutingCalculationRequest`

```python
class RoutingCalculationRequest(BaseModel):
    route_id: str | None = None
    session_id: str | None = None
    planning_reservation_id: str | None = None
    vehicle: RoutingVehicleInput
    stops: list[RoutingStopInput]
    departure_at: datetime | None = None
    mode: Literal["preview", "optimize"] = "preview"
    commit_order: bool = False
```

## Modelo de salida

```python
class RoutingCalculatedStop(BaseModel):
    stop_id: str
    sequence: int
    eta_at: datetime | None = None
    etd_at: datetime | None = None
    distance_from_prev_m: int | None = None
    travel_seconds_from_prev: int | None = None
    service_minutes: int = 0
    violation_codes: list[str] = []


class RoutingTotals(BaseModel):
    distance_m: int
    travel_seconds: int
    service_seconds: int
    total_seconds: int


class RoutingCalculationResponse(BaseModel):
    provider_stack: str  # "osrm+vroom"
    route_id: str | None = None
    session_id: str | None = None
    ordered_stops: list[RoutingCalculatedStop]
    totals: RoutingTotals
    polyline: str | None = None
    violations: list[str] = []
    committed: bool = False
```

## Regla de snapshot único de ruta asignada

Cuando un cálculo es aceptado para una `Route` o una `Jornada`, el resultado deja de ser preview y pasa a ser **ruta asignada**.

Esa ruta asignada debe cumplir estas reglas:

1. se genera **una sola vez** por aceptación explícita;
2. su `polyline`, orden de stops, ETA base y totales quedan congelados como snapshot operativo;
3. `Jornadas` ejecuta sobre ese snapshot, no sobre un cálculo vivo que cambie en cada apertura;
4. no existe recálculo automático silencioso al abrir el mapa, al refrescar la página o al recibir nueva telemetría;
5. si el usuario desea cambiar la ruta asignada, debe disparar una acción explícita de **recalcular** que produce una nueva propuesta separada;
6. la nueva propuesta no pisa la ruta asignada actual hasta que el usuario la acepte de nuevo.

Consecuencia visual en `Jornadas`:

- si existe snapshot aceptado, el mapa de ruta muestra esa geometría asignada;
- la línea simple entre stops deja de ser la fuente principal y queda solo como fallback cuando aún no existe `polyline` persistida;
- la jornada no “redibuja” otra ruta automáticamente durante la ejecución.

## Reglas de negocio

1. El motor nunca persiste cambios por defecto; el resultado inicial es preview.
2. `Jornadas` sigue siendo owner del flujo vivo. El motor solo sugiere orden y ETA.
3. `RouteStop.stop_order` solo se actualiza mediante aceptación explícita (`commit`).
4. Si faltan coordenadas estructuradas en un stop, ese stop no puede entrar al cálculo vial y debe devolverse error claro.
5. Si faltan capacidades del vehículo, el motor puede calcular secuencia y ETA, pero no debe declarar `capacity_validated=true`.
6. Si hay ventanas horarias, el motor debe devolver violaciones explícitas; no debe ignorarlas silenciosamente.
7. Si hay ADR básico, el motor debe devolver incompatibilidad explícita si el vehículo no lo soporta.
8. Una falla de `OSRM` o `VROOM` no invalida la jornada ni la ruta existente; solo invalida el cálculo sugerido.
9. `Planning` puede usar el motor antes de materializar ruta o jornada; `Jornadas` puede usarlo sobre una ruta ya existente.
10. El cálculo debe ser determinista para el mismo payload y configuración, salvo cambios externos del proveedor.
11. Una vez aceptada la ruta asignada, el sistema no debe recalcularla automáticamente durante la jornada.
12. El mapa de `Jornadas` debe priorizar la geometría persistida de la ruta asignada sobre cualquier línea derivada simple entre stops.

## Fases operativas

### Fase 1 — Single vehicle preview

Objetivo:

- una ruta o jornada;
- un vehículo;
- lista de stops ya conocidos;
- optimización de secuencia;
- ETA y polyline;
- sin persistencia automática.

### Fase 2 — Commit de orden

Objetivo:

- aceptar propuesta;
- actualizar `RouteStop.stop_order`;
- guardar snapshot de cálculo;
- congelar la ruta asignada para que `Jornadas` la use sin recálculo automático.

### Fase 3 — Multi-vehículo asistido

Fuera de esta spec principal, pero habilitado por diseño:

- varias rutas candidatas;
- varios vehículos;
- reparto sugerido por capacidad y ventanas.

## Endpoints propuestos

### `POST /routing/preview`

Calcula y devuelve preview. No persiste.

### `POST /routing/optimize`

Alias semántico para cálculo explícito con optimización de secuencia. No persiste.

### `POST /routing/commit-order`

Persiste el orden aceptado sobre `RouteStop.stop_order` y registra snapshot.

### `POST /routing/snap-stops`

Normaliza coordenadas vía `OSRM nearest` antes de optimizar.

## Persistencia opcional de auditoría

Tabla sugerida:

```text
lg_route_calculations
- id
- tenant_id
- route_id nullable
- session_id nullable
- planning_reservation_id nullable
- provider_stack
- input_hash
- ordered_stop_ids_json
- totals_json
- violations_json
- polyline
- created_at
- created_by
```

Uso:

- auditoría;
- debugging;
- comparación entre recalculos;
- soporte de UI “aceptar último cálculo”.

## Configuración

Settings sugeridos:

```python
logistics_routing_enabled: bool = False
logistics_osrm_base_url: str | None = None
logistics_vroom_base_url: str | None = None
logistics_routing_request_timeout_seconds: int = 10
logistics_routing_cache_ttl_seconds: int = 300
```

## Infraestructura

### Entorno local

Como Termux es entorno primario, el sistema debe soportar dos modos:

1. servicios externos/remotos configurados por URL;
2. servicios locales auxiliares cuando el entorno lo permita.

No se debe acoplar el desarrollo a Docker obligatorio.

### Disponibilidad degradada

Si `OSRM` o `VROOM` no están configurados:

- los endpoints de cálculo deben responder error claro de capability no disponible;
- el resto de `logistics` debe seguir funcionando.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Datos de stops sin `lat/lng` confiables | alto | validación temprana + `snap-stops` |
| Time windows incompletas o irreales | medio | violaciones explícitas, no aceptación automática |
| Dependencia excesiva de proveedor externo | medio | adapters propios + capability flag |
| Latencia alta en matrices grandes | medio | cache + límites de stops por request |
| Mezclar cálculo con ownership de `Jornadas` | alto | commit explícito y preview por defecto |
| Intentar VRP complejo demasiado pronto | alto | limitar esta spec a single-vehicle preview + commit |

## Límites iniciales

Para esta iteración:

- máximo recomendado: `40` stops por cálculo;
- foco principal: `single-vehicle same-day routing`;
- no se garantiza multi-flota en esta spec;
- no se garantiza recalculo autónomo durante ejecución.

## Pruebas requeridas

### Unitarias

- normalización de payloads;
- validación de coordenadas y capacidades;
- mapeo `OSRM/VROOM -> DTO interno`;
- cálculo de ETA y totales;
- commit de orden sobre `RouteStop.stop_order`.

### Integración

- `preview` con provider mock;
- `optimize` con provider mock;
- `commit-order` persistiendo secuencia;
- degradación correcta cuando `OSRM/VROOM` no están configurados.

### Manuales

- cálculo desde `Route Builder`;
- cálculo desde `Planning`;
- aceptación y persistencia del orden sugerido;
- visualización de ETA/polyline;
- errores claros por coordenadas faltantes.

## Criterios de aceptación

1. Existe capa backend `routing/` dentro de `logistics`.
2. `POST /routing/preview` devuelve secuencia, ETA, totales y polyline sin persistir.
3. `POST /routing/commit-order` actualiza `RouteStop.stop_order` solo tras aceptación explícita.
4. El cálculo usa `OSRM + VROOM` detrás de adapters propios del proyecto.
5. Una jornada o ruta existente puede consumir el motor sin perder ownership del aggregate.
6. El kernel no importa servicios de routing ni proveedores viales.
7. Las fallas de proveedor externo no rompen el resto de `logistics`.
8. Los tests unitarios e integración con mock provider pasan.
9. La UI puede mostrar cálculo sugerido sin comprometer cambios automáticamente.
10. Tras aceptar una propuesta, `Jornadas` muestra la ruta asignada persistida y no recalcula automáticamente otra geometría.

## Archivos esperados

### Backend

- `plugins/logistics/backend/services/routing/models.py`
- `plugins/logistics/backend/services/routing/provider.py`
- `plugins/logistics/backend/services/routing/providers/osrm.py`
- `plugins/logistics/backend/services/routing/providers/vroom.py`
- `plugins/logistics/backend/services/routing/matrix.py`
- `plugins/logistics/backend/services/routing/optimizer.py`
- `plugins/logistics/backend/services/routing/geometry.py`
- `plugins/logistics/backend/services/routing/service.py`
- `plugins/logistics/backend/routers/routing.py`
- `plugins/logistics/backend/plugin.py` (registro de subrouter)

### Frontend

- `plugins/logistics/frontend/routes/` o `planning/` para preview y aceptación
- integración mínima desde `Route Builder`, `Planning` o `SessionRouteTab`

## Plan de implementación por PRs

Esta spec no debe ejecutarse en un PR único. La implementación oficial queda cortada en PRs explícitos, secuenciales y reviewables.

### PR1 — Infraestructura routing base

Alcance:

- settings `OSRM`/`VROOM`;
- carpeta `services/routing/`;
- `models.py`, `provider.py`, `service.py`, `cache.py`;
- adapters `providers/osrm.py` y `providers/vroom.py`;
- tests unitarios de shape y provider mock.

No incluye:

- endpoints públicos;
- persistencia;
- frontend.

Resultado esperado:

- base backend viva;
- capability flag;
- cero impacto visible en `Jornadas`.

### PR2 — Preview de cálculo

Alcance:

- `POST /routing/preview`;
- validación de stops/vehicle;
- cálculo de secuencia, ETA, totales y polyline;
- errores claros cuando faltan coordenadas o provider no está disponible.

No incluye:

- persistencia;
- cambios en `RouteStop.stop_order`;
- snapshot congelado.

Resultado esperado:

- `Route Builder`, `Planning` o `Jornadas` pueden pedir preview sin mutar estado.

### PR3 — Commit y snapshot congelado

Alcance:

- tabla `lg_route_calculations`;
- `POST /routing/commit-order`;
- persistencia de `RouteStop.stop_order`;
- persistencia de `polyline`, totales, violaciones e `input_hash`;
- congelamiento de ruta asignada tras aceptación.

Resultado esperado:

- ruta asignada generada una vez;
- snapshot persistido;
- base lista para consumo desde `Jornadas`.

### PR4 — `Jornadas` consume ruta asignada

Alcance:

- mapa de `Jornadas` prioriza `polyline` persistida;
- fallback a línea simple solo si no existe snapshot;
- visualización de ETA/progreso base por stop;
- sin recálculo automático.

Resultado esperado:

- `Jornadas` muestra la ruta asignada real;
- ejecución sobre snapshot, no sobre cálculo vivo.

### PR5 — Recalcular explícito

Alcance:

- `POST /routing/optimize`;
- acción UI `Recalcular ruta`;
- diff entre snapshot actual y propuesta nueva;
- aceptación explícita para reemplazar snapshot.

Resultado esperado:

- no mutación silenciosa;
- recalculo manual, auditable y reversible a nivel de propuesta.

### PR6 — Integración upstream

Alcance:

- preview desde `Planning`;
- preview desde `Route Builder`;
- warnings de `TIME_WINDOW`, `CAPACITY`, `ADR`;
- consumo seguro antes de activación de jornada.

Resultado esperado:

- cálculo útil antes de runtime;
- mejor preparación de la jornada.

### PR7 — Hardening

Alcance:

- cache;
- retry/timeout;
- auditoría;
- observabilidad;
- límites de stops;
- tests de degradación y documentación operativa.

Resultado esperado:

- slice listo para uso serio post-`v1`.

## Orden obligatorio

```text
PR1 -> PR2 -> PR3 -> PR4 -> PR5 -> PR6 -> PR7
```

Regla fuerte:

```text
ningún PR posterior salta a Jornadas o Planning
sin que preview y snapshot ya existan
```

## Nota final

Esta spec no redefine el sistema alrededor del motor. Hace lo contrario: agrega el motor como pieza subordinada a un dominio que ya existe.

Regla final:

```text
si el motor no está disponible
la operación sigue existiendo
solo desaparece la ayuda de cálculo
```
