---
id: "0024.1.3.1"
title: "RouteOperation y Composición Vigente"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-1-3-carta-porte-operativa-en-jornada.md
  - docs/specs/core/0024-3-vehicle-session-hero-console.md
  - docs/specs/core/0023-logistics-operacion-real/0023E/0023E2-vehicle-session-almacen-movil-v2.md
---

# SPEC 0024.1.3.1 — RouteOperation y Composición Vigente

## Contexto

## Nota de vigencia

`SPEC 0033 - RouteOperation con Efectos Separados` ajusta esta spec en dos puntos no opcionales:

1. una `RouteOperation` confirmada ya no requiere siempre `Movement` derivado;
2. `composition/current` debe leerse como verdad fisica de la jornada, no como mera proyeccion financiera.

Esta spec se conserva como base historica del modelo, pero sus reglas sobre `PICKUP -> IC` y `cada operacion confirmada -> uno o mas movements` quedan superadas por `0033`.

`SPEC 0024.1.3` definió correctamente a `Carta Porte` como una proyección documental versionada de la jornada en movimiento.

Sin embargo, esa spec todavía depende de una capa operativa que hoy no está cerrada en el sistema:

- la operación real de calle durante `OUTBOUND`;
- la composición transportada vigente del vehículo;
- la diferencia entre saldo móvil y verdad operacional.

Hoy el `stepper` y la consola pueden verse maduros desde UX, pero el backend aún no modela completamente lo que pasa cuando el conductor entrega, recoge, intercambia o corrige en ruta.

Eso genera una tensión peligrosa:

```text
el flujo visual puede verse verde
sin que la verdad operacional de calle exista todavía
```

## Frase guía

**Antes de cerrar carta porte, la jornada debe saber qué pasó realmente en la calle.**

## Objetivo

Definir la capa operacional mínima que vuelve confiable a `OUTBOUND`, modelando:

1. `RouteOperation` como hecho operativo de calle;
2. `MobileStock` como proyección derivada, no persistida;
3. la `Composición Vigente` del vehículo como resultado de carga confirmada + operaciones confirmadas;
4. la base real sobre la que después `Carta Porte` se vuelve una proyección casi trivial.

## No objetivos

- no rediseñar el stepper de `0024.3`;
- no reemplazar `VehicleSession` como aggregate root;
- no crear una segunda fuente de verdad de stock;
- no persistir un modelo paralelo de `MobileStock`;
- no permitir editar libremente operaciones ya confirmadas;
- no cerrar todavía todos los documentos derivados de ruta.

## Problema exacto

Hoy existe una base valiosa:

- `VehicleSession` como ejecución del día;
- `mobile_warehouse_id` como almacén móvil real;
- balances de stock del almacén móvil;
- carga confirmada (`TRANSFER_OUT`) y retorno (`TRANSFER_IN`);
- `Carta Porte` ya visible dentro de `RouteModal`.

Pero todavía faltan tres piezas críticas:

1. no existe una entidad explícita para las operaciones de calle (`DELIVERY`, `PICKUP`, `EXCHANGE`);
2. no existe una composición transportada vigente derivada formalmente desde esas operaciones;
3. `Carta Porte` todavía depende de una base parcial, no de la calle real.

## Decisión de dominio

### 1. `RouteOperation` es el owner de la operación de calle

`RouteOperation` representa un hecho operativo confirmado de ruta.

Ejemplos:

- entregar producto al cliente;
- recoger vacíos;
- hacer un intercambio;
- registrar una corrección posterior como nueva operación.

### 2. `Movement` sigue siendo la vía obligatoria para tocar stock

`RouteOperation` **no actualiza stock directamente**.

Toda mutación de stock derivada de calle debe confirmarse vía `Movement`.

Regla fuerte:

```text
RouteOperation describe la operación
Movement ejecuta el efecto inventariable
Stock sigue siendo la fuente de verdad de balance
```

### 3. `MobileStock` no se persiste

`MobileStock` es una proyección derivada del estado operativo y del stock real.

No se crea una tabla propia como segunda verdad.

### 4. `Composición Vigente` es la fuente para carta porte

La carta porte no debe intentar inferir calle por sí sola.

Debe proyectarse desde una composición vigente calculada a partir de:

- carga confirmada inicial;
- operaciones de ruta confirmadas;
- remanente actual del vehículo;
- metadata material de vehículo, conductor y destino.

## Invariantes obligatorios

1. `RouteOperation` confirmada es inmutable.
2. Una corrección no edita una operación confirmada: crea una nueva operación compensatoria o correctiva.
3. `RouteOperation` nunca ajusta stock directo.
4. `MobileStock` nunca se persiste como fuente propia de verdad.
5. `Composición Vigente` siempre se deriva; no se edita a mano.
6. `Carta Porte` solo se considera confiable si sale de la composición vigente.

## Modelo conceptual

```ts
type RouteOperation = {
  id: string
  session_id: string
  route_stop_id?: string | null
  movement_ids: string[]

  operation_type: "DELIVERY" | "PICKUP" | "EXCHANGE"
  status: "DRAFT" | "CONFIRMED" | "CANCELLED"

  performed_by?: string | null
  performed_at?: string | null
  notes?: string | null
  idempotency_key: string
}

type RouteOperationItem = {
  id: string
  route_operation_id: string
  product_id: string
  product_name: string
  quantity: number
  direction: "OUT" | "IN"
}
```

## Significado de cada operación

### `DELIVERY`

Producto que sale realmente del camión hacia un cliente o destino de ruta.

Mapa natural a inventario:

- `Movement` tipo `SC` cuando aplique como salida a cliente.

### `PICKUP`

Producto o envase que entra realmente al camión desde cliente o punto de ruta.

Mapa natural a inventario:

- `Movement` tipo `IC` cuando aplique como ingreso desde cliente.

### `EXCHANGE`

No es una mutación mágica única.

Regla obligatoria:

```text
EXCHANGE = DELIVERY + PICKUP
```

La UI puede presentarlo como una sola acción, pero el modelo debe poder reconstruir ambas direcciones por separado.

## Relación con `Movement`

### Regla principal

`RouteOperation` no reemplaza a `Movement`.

Lo orquesta o lo referencia.

### Regla mínima esperada

Lectura histórica original:

```text
cada operacion confirmada debe quedar asociada a uno o mas movements reales
```

Lectura vigente desde `SPEC 0033`:

```text
una RouteOperation confirmada puede no tener Movement
si su efecto es fisico/documental y no financiero
```

Regla complementaria:

1. `movement_ids` debe admitir múltiples movements por operación;
2. en especial, `EXCHANGE` necesita poder apuntar a los dos movements que lo materializan.

Ejemplos históricos de esta spec:

- `DELIVERY` -> `SC`
- `PICKUP` -> `IC`
- `EXCHANGE` -> `SC + IC`

Lectura vigente desde `SPEC 0033`:

- `DELIVERY` -> `SC` cuando exista efecto financiero;
- `PICKUP` -> efecto fisico obligatorio, `IC` solo si hay devolucion financiera real;
- `EXCHANGE` -> separar parte `OUT` y parte `IN` por efecto.

### Regla de trazabilidad

Debe poder responderse:

1. qué operación de ruta ocurrió;
2. qué movement(s) la materializaron;
3. qué efecto tuvo sobre la composición del camión.

## MobileStock derivado

### Lo que ya existe y se conserva

La jornada ya cuenta con:

- `mobile_warehouse_id`;
- balances desde stock;
- resumen `current_stock`;
- visualización inline del almacén móvil.

### Lo que esta spec agrega

La semántica operacional del stock móvil.

`MobileStock` debe leerse como:

```text
qué lleva realmente el vehículo ahora
por qué lo lleva
qué salió
qué entró
qué quedó remanente
```

No es una tabla nueva.

Es una proyección derivada de:

- verdad fisica de cilindros presentes en sesion;
- saldo del almacén móvil cuando aplique para productos no serializados o agregados;
- carga inicial confirmada;
- operaciones de ruta confirmadas.

## Composición vigente

Se introduce explícitamente el concepto de `Composición Vigente`.

### Definición

Es la fotografía operativa actual de lo que el vehículo transporta en este momento.

### Entradas mínimas

1. carga confirmada inicial;
2. operaciones `DELIVERY` confirmadas;
3. operaciones `PICKUP` confirmadas;
4. operaciones `EXCHANGE` descompuestas en sus dos direcciones;
5. metadata material de vehículo, conductor y destino.

### Salida mínima

```ts
type CurrentComposition = {
  session_id: string
  composition_version?: number
  product_lines: Array<{
    product_id: string
    product_name: string
    quantity: number
    weight_kg?: number | null
    adr_points?: number | null
  }>
  totals: {
    total_packages: number
    total_weight_kg: number
    total_adr_points: number
  }
}
```

Reglas complementarias de composición:

1. `product_lines` debe salir en orden determinista, como mínimo `product_id ASC`;
2. ese orden estable forma parte de la consistencia del hash y evita diferencias falsas sin cambio real;
3. `composition_version` queda reservado como soporte futuro para debug y auditoría operacional.
4. si `stock` y presencia fisica divergen, la composición vigente debe reflejar la presencia fisica.

## Regla sobre el stepper

`0024.3` no se invalida, pero esta sub-spec fija un límite de interpretación:

```text
un stepper visualmente avanzado no equivale a una verdad operacional cerrada
```

Consecuencia:

- `OUTBOUND` no debe tratarse como dominio resuelto solo porque el modal y el estado existen;
- la verdad de `OUTBOUND` depende de `RouteOperation + Composición Vigente`, y `Movement` solo cuando exista consecuencia financiera/documental derivada.

### Evolución opcional futura

Si luego hace falta una UX más fina, puede introducirse un estado intermedio como `PENDING_CONFIRMATION` para operaciones de ruta todavía no confirmadas.

No es obligatorio en este slice.

## Carta porte como downstream

Una vez exista `Composición Vigente`, la complejidad de carta porte baja drásticamente.

Nuevo flujo correcto:

```text
RouteOperation confirmada
-> Movement confirmado
-> MobileStock derivado cambia
-> Composición Vigente cambia
-> operational_hash cambia
-> Carta Porte queda OUTDATED
-> regeneración crea nueva versión
```

## Frontend esperado

`RouteModal` deja de ser solo un contenedor de ruta y pasa a ser workspace operativo real.

Debe evolucionar para permitir:

- ver la lista de operaciones de ruta;
- confirmar `DELIVERY`, `PICKUP` y `EXCHANGE`;
- ver impacto sobre la composición vigente;
- mostrar `Carta Porte` como proyección de esa composición;
- no editar manualmente el documento.

## Backend esperado

Se requiere una capa explícita de servicios para:

1. crear operación de ruta en `DRAFT`;
2. confirmar operación de ruta;
3. generar o asociar `Movement` correcto;
4. derivar la composición vigente;
5. exponerla al frontend y a `Carta Porte`.

## Endpoints mínimos sugeridos

- `GET /vehicle-sessions/{id}/route-operations`
- `POST /vehicle-sessions/{id}/route-operations`
- `POST /vehicle-sessions/{id}/route-operations/{operation_id}/confirm`
- `GET /vehicle-sessions/{id}/mobile-stock/current`
- `GET /vehicle-sessions/{id}/composition/current`

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Actualizar stock directo desde RouteOperation | crítico | obligar paso por `Movement` |
| Persistir MobileStock como verdad propia | alto | dejarlo derivado |
| Permitir editar operaciones confirmadas | crítico | `CONFIRMED` inmutable, corrección = nueva operación |
| Mezclar UX verde con dominio resuelto | alto | explicitar que `OUTBOUND` depende de esta capa |
| Hacer que carta porte siga inventando composición | alto | consumir solo `Composición Vigente` |

## Criterios de aceptación

1. existe una spec explícita que modela `RouteOperation` como owner de la calle;
2. queda fijado que `Movement` sigue siendo la vía obligatoria para mutar stock;
3. queda fijado que `MobileStock` es derivado y no persistido;
4. queda definido que `EXCHANGE` se reconstruye como `DELIVERY + PICKUP`;
5. queda definido el concepto de `Composición Vigente` como fuente de carta porte;
6. queda explicitado que el stepper actual no basta por sí solo para considerar cerrada la verdad operacional de `OUTBOUND`.

## Dependencias

- `docs/specs/core/0024-1-3-carta-porte-operativa-en-jornada.md`
- `docs/specs/core/0024-3-vehicle-session-hero-console.md`
- `docs/specs/core/0023-logistics-operacion-real/0023E/0023E2-vehicle-session-almacen-movil-v2.md`
- `plugins/logistics/backend/models/movements.py`
- `plugins/logistics/backend/models/session_operations.py`
- `plugins/logistics/backend/services/movements.py`
- `plugins/logistics/backend/services/operations.py`

## Archivos candidatos

- `plugins/logistics/backend/models/session_operations.py` o su evolución
- `plugins/logistics/backend/services/operations.py`
- `plugins/logistics/backend/services/movements.py`
- `plugins/logistics/backend/routers/operations.py`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/modals/RouteModal.tsx`
