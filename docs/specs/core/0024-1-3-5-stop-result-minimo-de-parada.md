---
id: "0024.1.3.5"
title: "Stop Result Minimo de Parada"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-1-3-4-operational-summary-de-jornada.md
  - docs/specs/core/0024-1-3-3-reconciliacion-controlada-sobre-incidencias-de-ruta.md
  - docs/specs/core/0024-1-3-2-exchange-incidencias-y-progreso-real-de-stop.md
---

# SPEC 0024.1.3.5 - Stop Result Minimo de Parada

## Contexto

`RouteOperation` ya modela la verdad de calle.

`RouteIncident` ya modela desvíos e incidencias, incluidas reconciliaciones inventariables.

`Operational Summary` ya hace visible la salud general de la jornada.

Pero todavía queda un hueco semántico:

- una operación no siempre explica cómo terminó la parada;
- una incidencia no siempre equivale al resultado operativo final;
- el usuario necesita poder dejar constancia explícita de cuánto se completó una parada y qué pasó allí.

Ejemplos:

- se atendió solo el 60% de la parada;
- el cliente estuvo ausente;
- hubo retorno no planificado;
- el conductor debe dejar una nota operativa explícita del resultado.

## Frase guia

**La operación dice qué se hizo. El stop result dice cómo terminó la parada.**

## Objetivo

Agregar un `StopResult` mínimo por parada que permita:

1. registrar el resultado operativo explícito de una parada;
2. capturar porcentaje de cumplimiento;
3. capturar nota del conductor;
4. mejorar la lectura de progreso y summary sin rediseñar todavía todo el modelo completo de `stop result`.

## No objetivos

- no reemplazar `RouteIncident`;
- no reemplazar `RouteOperation`;
- no cerrar todavía una taxonomía completa de outcomes de parada;
- no convertir este slice en rediseño completo de `RouteStop`;
- no mover inventario fuera de `Movement`.

## Decisión de dominio

## 1. `StopResult` es una capa semántica mínima adicional

`StopResult` no reemplaza la calle.

La cadena sigue siendo:

```text
RouteOperation -> verdad
RouteIncident -> desvío
StopResult -> cierre operativo de parada
```

## 2. Cada parada puede tener a lo sumo un resultado vigente por jornada

El resultado es propio del par:

```text
session_id + route_stop_id
```

## 3. El porcentaje importa

No toda parada termina binariamente.

Debe poder expresarse:

- `0%`
- `60%`
- `100%`

sin forzar a que todo pase por incidencias o notas libres.

## 4. La nota del conductor es parte del resultado

El sistema debe permitir una nota operativa humana breve para explicar el resultado de la parada.

Eso no reemplaza auditoría ni incidencias, pero sí agrega contexto operativo directo.

## Invariantes obligatorios

1. `StopResult` no altera inventario por sí solo.
2. `StopResult` no crea `Movement` por sí solo.
3. `StopResult` no reemplaza una incidencia reconciliable.
4. `StopResult` puede coexistir con `RouteIncident` y `RouteOperation` sobre la misma parada.
5. Solo puede existir un `StopResult` vigente por `session_id + route_stop_id`.

## Modelo conceptual

```ts
type RouteStopResult = {
  id: string
  session_id: string
  route_stop_id: string

  status:
    | "PENDING"
    | "IN_PROGRESS"
    | "PARTIAL"
    | "COMPLETED"
    | "FAILED"

  completion_percent: number

  outcome_type:
    | "NORMAL"
    | "CUSTOMER_ABSENT"
    | "FAILED_DELIVERY"
    | "PARTIAL_ATTENDED"
    | "UNPLANNED_RETURN"
    | "OTHER"

  driver_note?: string | null
  created_at: string
  updated_at: string
}
```

## Reglas mínimas de validación

1. `completion_percent` debe estar entre `0` y `100`.
2. `COMPLETED` exige `100`.
3. `PENDING` exige `0`.
4. `PARTIAL` exige un valor intermedio (`1..99`).
5. `IN_PROGRESS` exige un valor intermedio (`1..99`).
6. `FAILED` no puede ser `100`.

## Relación con `RouteIncident`

`RouteIncident` sigue siendo necesario para desvíos y reconciliación.

Ejemplos:

- faltó un balón en el recojo -> puede existir incidencia;
- cliente ausente -> puede expresarse como `StopResult` aunque no abra reconciliación inventariable.

## Relación con `RouteStopProgress`

`RouteStopProgress` debe poder enriquecerse con `StopResult`.

Regla mínima:

1. si existe `StopResult`, su `status` tiene prioridad semántica para lectura de progreso;
2. si no existe, sigue aplicando la derivación actual desde operaciones e incidencias.

## Relación con `Operational Summary`

`Operational Summary` debe poder leer:

- porcentaje de cumplimiento;
- tipo de outcome;
- nota humana relevante;

sin depender solo de incidencias abiertas.

## Backend esperado

1. nueva entidad persistente `RouteStopResult`;
2. endpoint para listar resultados de parada de una jornada;
3. endpoint `upsert` para crear o actualizar resultado por parada;
4. integración del resultado en `route-stop-progress` y `operational-summary`.

## Frontend esperado

1. panel mínimo en `SessionRouteTab` para registrar `StopResult`;
2. mostrar porcentaje / outcome / nota en la lectura de progreso;
3. no esconderlo en un flujo complejo.

## Permisos

Hereda `logistics.session.manage` para escritura y `logistics.session.read` para lectura.

## Migraciones

Sí requiere migración nueva para la tabla de resultados de parada.

## Riesgos

1. usar `StopResult` como sustituto de incidencias reconciliables;
2. duplicar lógica semántica si no se define prioridad clara con `RouteStopProgress`;
3. volver demasiado complejo este slice mínimo.

## Criterios de aceptación

1. existe una entidad mínima de `StopResult` por parada;
2. se puede registrar `status`, `completion_percent`, `outcome_type` y `driver_note`;
3. el resultado puede editarse sin rediseñar todavía todo `RouteStop`;
4. `RouteStopProgress` expone ese resultado cuando existe;
5. `Operational Summary` puede consumir el resultado mínimo para hacer la jornada más legible.

## Pruebas requeridas

1. integración backend de `upsert` y lectura;
2. pruebas de validación de `completion_percent` por `status`;
3. prueba de que `route-stop-progress` refleja el `StopResult` cuando existe;
4. prueba de que `operational-summary` lo incorpora.

## Notas para agentes

1. Mantener esto como slice mínimo; no abrir todavía el rediseño completo de `StopResult`.
2. No reubicar la verdad de inventario ni la reconciliación fuera de `RouteOperation`/`RouteIncident`.
