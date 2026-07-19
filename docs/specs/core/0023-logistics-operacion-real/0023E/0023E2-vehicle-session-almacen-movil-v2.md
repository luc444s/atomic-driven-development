# SPEC 0023E2 — VehicleSession y warehouse MOBILE: alineacion operativa V2

## Estado

Propuesta posterior a V1 — 2026-07-14

## Depende de

- `0023E1-vehicle-session-almacen-movil-v1.md`

`0023E2` no reemplaza a `0023E1`.

`0023E1` define la primera version util y estable.

`0023E2` define lo que falta para alinear completamente el modelo con Grab2 y con la operacion madura del legacy.

## Objetivo

Completar la distancia entre:

- una V1 util y segura
- la operacion real descrita en Grab2
- los comportamientos finos que el legacy ya absorbia en calle

## Regla de alcance

`0023E2` solo entra cuando `0023E1` ya resuelve correctamente y sin regresiones este ciclo:

```text
abrir jornada
-> preparar carga
-> confirmar carga
-> salir
-> retornar
-> conciliar
-> cerrar
```

Si ese ciclo no esta estable, `0023E2` no debe empezar.

## Gap exacto respecto a Grab2 y legacy

La nueva arquitectura ya corrige el problema central del intento anterior:

```text
no hay dos fuentes de verdad para inventario
```

Pero Grab2 y legacy todavia piden una capa mas de alineacion operativa.

Lo que falta no es inventario base.

Lo que falta es operacion de calle.

## Lo que V1 ya resuelve bien

- warehouse MOBILE como ubicacion real reutilizando `lg_warehouses`
- `VehicleSession` como aggregate root
- carga actual derivada siempre desde Stock
- carga y retorno como movimientos reales de inventario
- conciliacion obligatoria antes del cierre
- lifecycle operativo limpio
- fleet monitor como lectura derivada

## Lo que V2 debe terminar de alinear

### 1. Ruta viva y no solo `route_id`

En V1 la ruta existe, pero la jornada todavia no opera plenamente por paradas reales.

V2 debe cerrar:

- secuencia real de paradas
- orden previsto vs orden ejecutado
- estado por parada
- inicio/cierre de parada
- evidencia por parada

#### Resultado esperado

```text
VehicleSession
  -> Route
      -> Stops
          -> Delivery / Pickup / Exchange
```

### 2. Entrega, recojo e intercambio en calle

V1 deja previstas estas operaciones.

V2 debe implementarlas completamente:

- `DELIVERY`
- `PICKUP`
- `EXCHANGE`

#### Regla fuerte

`EXCHANGE` no es una mutacion magica unica.

Debe modelarse como:

```text
DELIVERY
+
PICKUP
```

Aunque la UI lo muestre como una accion sola.

### 3. Aceptacion real del conductor

Grab2 y la operacion real sugieren que no basta con que la carga exista.

Debe haber aceptacion explicita de quien sale con el vehiculo.

V2 debe agregar:

- aceptacion de carga por conductor
- evidencia o confirmacion de salida
- trazabilidad de quien asumio la jornada

### 4. Operacion en ruta con cantidades reales

El modelo V1 deja listo el historial y la sesion.

V2 debe soportar:

- cantidades esperadas
- cantidades realmente entregadas
- cantidades realmente recogidas
- diferencias registradas en el momento de calle
- cierre parcial o fallido de parada

### 5. Excepciones operativas e incidencias

En V1 los incidentes quedan fuera a proposito.

V2 debe incorporar como minimo:

- parada fallida
- cliente ausente
- diferencia fisica detectada en calle
- evidencia adjunta
- motivo de devolucion o no entrega

No hace falta un mega modulo de incidencias, pero si una trazabilidad operativa minima real.

### 6. Stock libre en reparto

Grab2 y la operacion legacy describen que el camion puede salir con:

- carga comprometida
- stock extra no comprometido

V1 solo necesita carga/retorno.

V2 debe cerrar:

- producto planificado para ruta
- producto libre adicional
- visibilidad separada en UI
- conciliacion que no mezcle ambas cosas de forma opaca

### 7. Escaneo al cargar y operar

El sistema actual tiene infraestructura de scan pero no un flujo unificado de jornada.

V2 debe alinear:

- escaneo durante carga
- escaneo durante entrega/recojo
- validacion contra session + stop + operation
- evidencia operativa derivada del scan

### 8. Carta porte viva ligada a la jornada y ruta

`0023J` sigue siendo la spec documental de carta porte.

Pero `0023E2` debe asegurar que la jornada soporte la informacion necesaria para que luego `0023J` pueda mutar correctamente en ruta.

Eso incluye:

- cantidades reales de entrega y recojo
- orden real de operacion
- conductor real que asumio la carga
- version operativa de lo que salio y volvio

### 9. Timeline operativo fino

En V1 el historial es suficiente como timeline derivado simple.

V2 debe enriquecerlo con eventos de calle como:

```text
08:00  carga iniciada
08:12  carga terminada
08:40  salida
09:15  entrega cliente A
09:42  entrega cliente B
10:20  recojo cliente C
12:10  retorno
12:45  conciliacion
13:00  cierre
```

Sigue siendo derivado. No implica persistir una tabla propia si no hace falta.

## Cambios de frontend esperados en V2

La V1 ya deja la pantalla central correcta:

```text
VehicleSessionDetail
  [Resumen] [Carga] [Ruta] [Conciliacion] [Historial]
```

V2 expande principalmente la pestaña `Ruta`.

### VehicleSessionDetail V2

```text
+============================================================================+
| Jornada TRK-001                                                            |
| Estado: OUTBOUND                                                           |
+============================================================================+
| Tabs: [Resumen] [Carga] [Ruta] [Conciliacion] [Historial]                  |
+============================================================================+
```

### Tab Ruta V2

```text
+--------------------------------------------------------------------------------+
| Ruta                                                                           |
+--------------------------------------------------------------------------------+
| Parada | Tipo       | Cliente        | Estado              | Hora   | Accion    |
|--------+------------+----------------+---------------------+--------+-----------|
| 1      | DELIVERY   | Cliente A      | COMPLETED           | 09:15  | Ver       |
| 2      | EXCHANGE   | Cliente B      | PARTIALLY_COMPLETED | 09:42  | Continuar |
| 3      | PICKUP     | Cliente C      | PENDING             | --     | Iniciar   |
+--------------------------------------------------------------------------------+
```

### Drawer o panel de parada

```text
+----------------------------------------------------------------------------+
| Parada 2 - Cliente B                                                       |
+----------------------------------------------------------------------------+
| Operacion esperada: EXCHANGE                                               |
| Esperado: 2 llenas / 2 vacias                                              |
| Real:     [2] entregadas / [1] recogida                                    |
| Motivo diferencia: [________________________]                              |
| Evidencia: [Adjuntar]                                                      |
+----------------------------------------------------------------------------+
| [Confirmar entrega] [Confirmar recojo] [Registrar incidencia]              |
+----------------------------------------------------------------------------+
```

### Fleet Monitor V2

Sigue siendo lectura, pero mejora el nivel de detalle:

```text
+--------------------------------------------------------------------------------+
| Vehiculo | Estado      | Ruta | Paradas | Entregas | Recojos | Ultima accion |
|----------+-------------+------+---------+----------+---------+---------------|
| TRK-001  | OUTBOUND    | R-08 | 2/8     | 3        | 1       | Entrega 09:42 |
| TRK-002  | RETURNING   | R-12 | 8/8     | 10       | 4       | Retorno 11:05 |
+--------------------------------------------------------------------------------+
```

No se convierte en dashboard autonomo de storage.

## Cambios de backend esperados en V2

### Nuevos conceptos que se activan realmente

- RouteStop operativo
- DELIVERY
- PICKUP
- EXCHANGE
- incidentes minimos de calle
- confirmacion de conductor
- timeline enriquecido derivado

### Endpoints esperados

#### Ruta y paradas

```text
GET    /vehicle-sessions/{id}/route
GET    /vehicle-sessions/{id}/stops
POST   /vehicle-sessions/{id}/stops/{stop_id}/arrive
POST   /vehicle-sessions/{id}/stops/{stop_id}/start
POST   /vehicle-sessions/{id}/stops/{stop_id}/complete
POST   /vehicle-sessions/{id}/stops/{stop_id}/fail
```

#### Operacion de calle

```text
POST   /vehicle-sessions/{id}/deliver
POST   /vehicle-sessions/{id}/pickup
POST   /vehicle-sessions/{id}/exchange
```

#### Conductor

```text
POST   /vehicle-sessions/{id}/driver-ack
```

#### Historial enriquecido

```text
GET    /vehicle-sessions/{id}/history
```

## Reglas adicionales de V2

### 1. Una parada no se puede cerrar si quedan operaciones obligatorias sin resolver

### 2. `EXCHANGE` siempre conserva semanticamente dos movimientos

### 3. La diferencia entre esperado y real en calle se registra antes del cierre de parada

### 4. La aceptacion del conductor queda auditada y asociada a la jornada

### 5. El scan nunca reemplaza la operacion; la respalda

## Criterios de aceptacion de V2

### Operacion

- la jornada puede ejecutar entregas reales
- la jornada puede ejecutar recojos reales
- el intercambio conserva entrega + recojo como movimientos separados
- se puede cerrar o fallar una parada con estado explicito
- el conductor puede aceptar la salida con trazabilidad

### Trazabilidad

- el historial de jornada ya refleja eventos de calle
- fleet monitor muestra avance real por jornada
- una diferencia de operacion en parada no desaparece al conciliar despues

### Inventario

- la carga actual sigue saliendo exclusivamente de Stock
- ninguna operacion de V2 crea tablas paralelas de saldo vivo
- las mutaciones de inventario siguen pasando por la integracion con Stock

## Regla final

`0023E2` no existe para rehacer el inventario movil.

Existe para completar la operacion de calle que V1 deja preparada:

```text
salir
-> entregar / recoger / intercambiar
-> volver
-> conciliar
```

Si una decision de V2 vuelve a introducir dos fuentes de verdad para existencias, contradice esta spec.
