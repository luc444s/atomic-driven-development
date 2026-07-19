---
id: "0024.1.3.2"
title: "Exchange Guiado, Incidencias y Progreso Real de Stop"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-1-3-1-route-operation-y-composicion-vigente.md
  - docs/specs/core/0024-1-3-carta-porte-operativa-en-jornada.md
---

# SPEC 0024.1.3.2 — Exchange Guiado, Incidencias y Progreso Real de Stop

## Contexto

`SPEC 0024.1.3.1` ya cerró la base correcta:

- `RouteOperation` como owner de la calle;
- `Movement` como vía obligatoria para tocar stock;
- `MobileStock` derivado;
- `Composición Vigente` como fuente downstream de `Carta Porte`.

Ese slice ya permite registrar operación real y volver `Carta Porte` sensible a la calle.

Pero todavía quedan tres endurecimientos clave para que la verdad operacional no se quede en un nivel “solo suficiente”:

1. `EXCHANGE` todavía puede sentirse demasiado libre si el operador elige direcciones línea por línea;
2. las incidencias y correcciones todavía no tienen contrato de dominio explícito;
3. `RouteStop` todavía no expresa formalmente el progreso real derivado de operaciones confirmadas.

## Frase guía

**La ruta no solo necesita operaciones. Necesita operaciones correctas, trazables y visibles como progreso real.**

## Objetivo

Endurecer la capa operacional de `OUTBOUND` en tres frentes:

1. convertir `EXCHANGE` en un flujo guiado y semánticamente explícito;
2. formalizar incidencias y correcciones sin romper la inmutabilidad de operaciones confirmadas;
3. hacer que cada `RouteStop` refleje progreso operativo real derivado de la calle.

## No objetivos

- no reemplazar `RouteOperation` por otro aggregate;
- no volver a permitir edición de operaciones `CONFIRMED`;
- no mover stock fuera de `Movement`;
- no cerrar todavía toda la UI handheld avanzada;
- no rediseñar el stepper fuera de lo necesario para reflejar progreso real.

## Problema exacto

### 1. `EXCHANGE` demasiado genérico

En `0024.1.3.1`, `EXCHANGE = DELIVERY + PICKUP` quedó correctamente fijado.

Pero si la UX deja al operador armarlo como un conjunto arbitrario de líneas `IN/OUT`, el sistema conserva consistencia técnica pero pierde claridad operativa.

### 2. Incidencias no formalizadas

La calle no solo entrega o recoge.

También produce:

- cliente ausente;
- entrega parcial;
- retiro parcial;
- diferencia física;
- no entrega;
- devolución no planificada.

Si esto no tiene modelo, la operación queda “confirmada” o “no confirmada” de forma demasiado binaria.

### 3. `RouteStop` sin progreso semántico fuerte

Hoy una parada puede existir en ruta, pero todavía falta una regla fuerte que diga:

- cuándo una parada empezó realmente;
- cuándo quedó parcial;
- cuándo quedó completada;
- cuándo quedó fallida;
- qué evidencia operacional la llevó a ese estado.

## Decisión de dominio

## 1. `EXCHANGE` pasa a ser un flujo guiado

`EXCHANGE` sigue significando:

```text
DELIVERY + PICKUP
```

Pero desde esta spec deja de tratarse solo como “operación con líneas mixtas”.

La UX y el backend deben reconocer explícitamente dos mitades del intercambio:

- `delivered_lines`
- `picked_up_lines`

### Regla fuerte

El usuario puede ver una sola acción “Intercambio”,
pero el sistema debe validar ambas mitades por separado.

### Beneficio

Esto evita ambigüedades como:

- intercambio con salida sin retiro;
- intercambio con retiro sin salida;
- mezcla opaca de líneas sin lectura operacional clara.

## 2. Incidencia no reemplaza operación

Una incidencia no debe editar una operación confirmada.

Debe vivir como hecho complementario.

### Regla fuerte

```text
operación confirmada = inmutable
incidencia = explicación o desvío
corrección = nueva operación
```

## 3. Corrección siempre como nueva operación

Si una `DELIVERY`, `PICKUP` o `EXCHANGE` fue confirmada con error, no se edita.

Se crea una nueva operación de corrección o compensación.

Ejemplos:

- se entregaron 3 y debían ser 2 -> nueva `PICKUP` correctiva de 1;
- se retiraron 2 vacíos y era 1 -> nueva `DELIVERY` o corrección equivalente según caso real.

## 4. `RouteStop` pasa a tener progreso derivado real

La parada deja de depender solo de una marca manual o un botón suelto.

Su estado debe derivarse de las operaciones confirmadas e incidencias registradas.

## Invariantes obligatorios

1. `EXCHANGE` debe ser legible como salida + ingreso, aunque la UI lo presente unido.
2. Una incidencia no altera stock por sí sola.
3. Una corrección nunca modifica una operación confirmada previa.
4. El progreso de `RouteStop` debe poder reconstruirse a partir de operaciones e incidencias.
5. `Carta Porte` sigue siendo downstream de composición; no absorbe la lógica de incidencias.

## Modelo conceptual

### Exchange guiado

```ts
type ExchangeOperationDraft = {
  route_stop_id?: string | null
  delivered_lines: Array<{
    product_id: string
    product_name: string
    quantity: number
  }>
  picked_up_lines: Array<{
    product_id: string
    product_name: string
    quantity: number
  }>
  notes?: string | null
}
```

### Incidencia operacional

```ts
type RouteIncident = {
  id: string
  session_id: string
  route_stop_id?: string | null
  related_route_operation_id?: string | null

  incident_type:
    | "CUSTOMER_ABSENT"
    | "PARTIAL_DELIVERY"
    | "PARTIAL_PICKUP"
    | "PHYSICAL_DIFFERENCE"
    | "FAILED_DELIVERY"
    | "UNPLANNED_RETURN"

  status: "OPEN" | "RESOLVED"
  notes?: string | null
  created_by: string
  created_at: string
}
```

### Estado derivado de parada

```ts
type RouteStopProgress = {
  route_stop_id: string
  progress_status:
    | "PENDING"
    | "IN_PROGRESS"
    | "PARTIAL"
    | "COMPLETED"
    | "FAILED"
  last_operation_at?: string | null
  open_incidents: number
}
```

## Reglas de `EXCHANGE`

1. `EXCHANGE` requiere al menos una línea entregada y una recogida.
2. La UI debe separar visualmente ambas mitades.
3. El backend debe materializarlo como dos `movements` distintos cuando corresponda.
4. En auditoría debe quedar claro qué salió y qué entró.

## Reglas de incidencias

1. una incidencia puede abrirse sobre una parada o una operación concreta;
2. una incidencia no cambia stock por sí sola;
3. una incidencia puede explicar por qué una parada queda `PARTIAL` o `FAILED`;
4. si una incidencia exige corrección inventariable, la corrección debe emitirse como nueva `RouteOperation`.

## Reglas de progreso real de `RouteStop`

### `PENDING`

No hay operación confirmada ni inicio operativo visible.

### `IN_PROGRESS`

Existe actividad operativa sobre la parada, pero todavía no hay cierre semántico suficiente.

### `PARTIAL`

Hubo cumplimiento parcial o incidencia abierta relevante.

### `COMPLETED`

La parada alcanzó su resultado esperado o aceptado, sin hueco operacional pendiente.

### `FAILED`

La parada no pudo ejecutarse y quedó documentada como fallida.

## Relación con composición vigente

`Composición Vigente` sigue saliendo de operaciones confirmadas.

Las incidencias la afectan solo indirectamente:

- si una incidencia abre una corrección,
- y esa corrección se confirma como nueva operación,
- entonces la composición cambia.

## Relación con carta porte

`Carta Porte` no modela incidencias.

Solo reacciona cuando la composición vigente cambia realmente.

Consecuencia:

- una incidencia sin corrección inventariable no cambia carta porte;
- una corrección confirmada sí puede volverla `OUTDATED`.

## Frontend esperado

`RouteModal` debe endurecerse para:

1. mostrar `EXCHANGE` en dos bloques explícitos;
2. permitir registrar incidencias sobre la parada o la operación;
3. mostrar progreso real de cada stop;
4. distinguir operación confirmada de incidente abierto;
5. impedir la ilusión de “todo verde” si la parada está parcial o fallida.

## Backend esperado

Se requiere soporte explícito para:

1. confirmar `EXCHANGE` como flujo guiado de dos mitades;
2. registrar incidencias sin mutar stock;
3. derivar progreso de stop desde operaciones + incidencias;
4. mantener corrección como nueva operación y no como edición.

## Endpoints mínimos sugeridos

- `POST /vehicle-sessions/{id}/route-operations/exchange`
- `POST /vehicle-sessions/{id}/route-incidents`
- `POST /vehicle-sessions/{id}/route-incidents/{incident_id}/resolve`
- `GET /vehicle-sessions/{id}/route-stop-progress`

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| `EXCHANGE` demasiado libre en UI | alto | separar `delivered_lines` y `picked_up_lines` |
| usar incidencia para corregir stock | crítico | corrección solo como nueva operación |
| marcar stop completado con incidente abierto | alto | progreso derivado con estado `PARTIAL` o `FAILED` |
| volver a editar confirmados | crítico | mantener confirmados inmutables |

## Criterios de aceptación

1. existe una spec explícita para endurecer `EXCHANGE` como flujo guiado;
2. existe una spec explícita para incidencias sin tocar stock directo;
3. existe una spec explícita para correcciones vía nueva operación;
4. existe una spec explícita para progreso real derivado de `RouteStop`;
5. queda explícito que `Carta Porte` sigue siendo downstream y no absorbe esta lógica.

## Dependencias

- `docs/specs/core/0024-1-3-1-route-operation-y-composicion-vigente.md`
- `docs/specs/core/0024-1-3-carta-porte-operativa-en-jornada.md`
- `plugins/logistics/backend/services/route_operations.py`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx`

## Archivos candidatos

- `plugins/logistics/backend/models/route_operations.py`
- `plugins/logistics/backend/services/route_operations.py`
- `plugins/logistics/backend/routers/route_operations.py`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/modals/RouteModal.tsx`
