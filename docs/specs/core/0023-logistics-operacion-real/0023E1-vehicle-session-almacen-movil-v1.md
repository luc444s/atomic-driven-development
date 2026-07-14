# SPEC 0023E1 — VehicleSession y warehouse MOBILE dentro de Logistics

## Estado

Vigente propuesta de reconstruccion — 2026-07-14

## Reemplaza a

- `0023E-almacen-movil.md` como spec activa de implementacion

`0023E` queda historica porque describia un intento runtime que fue retirado por inconsistencia operativa y tecnica.

## Continuacion prevista

La ampliacion posterior a esta V1 queda descrita en:

- `0023E2-vehicle-session-almacen-movil-v2.md`

## Principio rector

```text
VehicleSession NO representa inventario.
VehicleSession representa una operacion logistica.
Todo inventario pertenece a Stock.
```

Y ademas:

```text
Logistics orquesta la operacion fisica.
Stock es la unica fuente de verdad para las existencias.
Todo almacen movil es un Warehouse(type=MOBILE)
cuya utilizacion se gestiona mediante una VehicleSession.
```

## Problema

La implementacion retirada de almacen movil cometio el error principal que esta spec viene a prohibir:

1. duplico la idea de inventario entre Logistics y Stock;
2. mezclo historial operativo con carga actual;
3. introdujo tablas vivas que pretendian describir el estado del vehiculo en paralelo al saldo real;
4. acoplo excesivamente UI, backend y stock a una feature inestable;
5. hizo que una misma pregunta tuviera dos respuestas distintas:

```text
"que tiene hoy el vehiculo?"
```

Esta spec define una reconstruccion donde:

- la jornada operativa vive en Logistics;
- las existencias viven en Stock;
- la carga actual siempre se lee desde Stock;
- la vista de flota es solo una proyeccion de lectura.

## Objetivo de V1

Resolver bien este ciclo, y nada mas:

```text
abrir jornada
-> preparar carga
-> confirmar carga
-> salir
-> retornar
-> conciliar
-> cerrar
```

## No objetivos de V1

- no implementar GPS en tiempo real
- no implementar geofencing
- no implementar app offline
- no implementar dashboard visual avanzado de flota
- no implementar incidentes complejos
- no implementar tablas materializadas de fleet monitor
- no implementar un segundo ledger para inventario movil
- no implementar microservicios ni event sourcing
- no reintroducir `mobile_warehouses` como tabla o agregado

## Decision de dominio

### 1. Delimitacion de ownership

#### Logistics es dueño de

- vehiculos
- asignacion operativa de vehiculo + conductor + warehouse + fecha
- jornadas operativas
- rutas asociadas a la jornada
- carga planificada
- operaciones logisticas historicas
- conciliacion operativa
- reglas de capacidad
- lifecycle de la jornada
- historial de lo ocurrido durante la jornada
- proyeccion de lectura para flota activa

#### Stock es dueño de

- warehouses
- productos inventariables
- balances
- ledger
- transferencias
- entradas
- salidas
- ajustes
- validacion de disponibilidad
- idempotencia del movimiento de stock

#### Fleet Monitor no es dueño de datos

Fleet Monitor es una consulta derivada dentro de Logistics.

No tendra:

- tablas propias
- ledger propio
- scheduler propio
- modulo independiente de persistencia

### 2. Warehouse no se mueve

`lg_warehouses` permanece como catalogo unico de ubicaciones del sistema.

```text
lg_warehouses
  - FIXED
  - MOBILE
  - TRANSIT
  - QUARANTINE
  - ...
```

No se crea otra entidad para reemplazar `warehouse`.

### 3. VehicleSession es el Aggregate Root

Todo el lifecycle operacional gira alrededor de `VehicleSession`.

```text
Vehicle
   |
   v
VehicleSession
   |
   +-- route_id
   +-- origin_warehouse_id
   +-- mobile_warehouse_id -> lg_warehouses(type=MOBILE)
   +-- load plan
   +-- logistics operations
   +-- reconciliation
   +-- derived history
```

No gira alrededor de:

- Vehicle
- Warehouse
- Route
- Stock
- Fleet Monitor

### 4. La carga actual del vehiculo siempre sale de Stock

Esta es una regla inviolable.

```text
La carga actual del vehiculo siempre sale de Stock.
Nunca de una tabla viva de Logistics.
```

La pregunta:

```text
"que tiene hoy el vehiculo?"
```

se responde asi:

```text
warehouse MOBILE asociado al vehiculo
-> saldo real en Stock
```

Nunca:

```text
tabla de items vivos en Logistics
```

## Modelo de datos

### 1. Vehicle

Se reutiliza `lg_vehicles`.

Se agrega o formaliza:

```text
mobile_warehouse_id
```

El vehiculo no necesita un estado persistente `IN_OPERATION` si este puede derivarse de la existencia de una sesion activa.

### 2. VehicleAssignment como concepto

No requiere tabla propia en V1.

Existe como concepto de negocio dentro de la creacion de la jornada:

```text
VehicleAssignment =
vehicle
+ driver
+ mobile_warehouse
+ origin_warehouse
+ date
```

### 3. `lg_vehicle_sessions`

```text
id
tenant_id
branch_id
vehicle_id
driver_id
origin_warehouse_id
mobile_warehouse_id
route_id NULL
status
opened_at
ready_at NULL
departed_at NULL
returned_at NULL
closed_at NULL
planned_weight_kg NULL
loaded_weight_kg NULL
closing_notes NULL
created_by
updated_by
created_at
updated_at
```

#### Estados

```text
DRAFT
LOADING
READY_TO_DEPART
OUTBOUND
RETURNING
AWAITING_RECONCILIATION
CLOSED
CANCELLED
```

#### Reglas

- un vehiculo no puede tener mas de una sesion activa
- una sesion `CLOSED` o `CANCELLED` no se edita
- no se puede salir si no esta `READY_TO_DEPART`
- no se puede cerrar con discrepancias abiertas
- la jornada solo termina cuando queda conciliada contra Stock

### 4. `lg_load_plans`

`LoadPlan` existe. `Dispatch` no existe como entidad persistente.

```text
id
session_id
status
notes
created_by
created_at
updated_at
```

### 5. `lg_load_plan_items`

```text
id
load_plan_id
product_id
planned_quantity
planned_weight_kg NULL
source_warehouse_id
notes NULL
```

#### Significado

```text
LoadPlan = intencion logistica
No inventario
No saldo
No ledger
```

### 6. `lg_logistics_operations`

Representa historial operativo. No representa carga actual.

```text
id
session_id
route_stop_id NULL
movement_type
status
external_movement_id NULL
idempotency_key
performed_by
performed_at NULL
notes NULL
evidence_json NULL
created_at
updated_at
```

### 7. `lg_logistics_operation_items`

```text
id
operation_id
product_id
quantity
weight_kg NULL
notes NULL
```

#### movement_type

```text
TRANSFER_OUT
TRANSFER_IN
DELIVERY
PICKUP
EXCHANGE
```

#### status

```text
DRAFT
PENDING_STOCK
CONFIRMED
FAILED
REVERSED
```

#### V1 real implementa solo

- `TRANSFER_OUT`
- `TRANSFER_IN`

`DELIVERY`, `PICKUP` y `EXCHANGE` quedan reservados para V1.1.

### 8. `lg_session_reconciliations`

```text
id
session_id
status
counted_by
counted_at NULL
closed_by NULL
closed_at NULL
notes NULL
created_at
updated_at
```

#### status

```text
MATCHED
HAS_DIFF
UNDER_REVIEW
CLOSED
```

### 9. `lg_inventory_discrepancies`

```text
id
reconciliation_id
product_id
expected_quantity
counted_quantity
difference_quantity
status
resolution_notes NULL
resolved_by NULL
resolved_at NULL
created_at
updated_at
```

#### status

```text
OPEN
UNDER_REVIEW
APPROVED_FOR_ADJUSTMENT
ADJUSTED
REJECTED
```

### 10. Modelos que NO existen en V1

- `mobile_warehouses`
- `dispatch`
- `fleet_monitor`
- `session_timeline`

## Integracion con Stock

### Ubicacion

```text
plugins/logistics/backend/integrations/stock.py
```

No vive en `services/` porque no es logica del dominio logistico. Es integracion con otro bounded context.

### Cadena de integracion

```text
Logistics
   -> integrations/stock.py
      -> Core Internal API
         -> Stock Plugin
```

### Operaciones disponibles

```python
transfer(...)
issue(...)
receive(...)
adjust(...)
get_balance(...)
get_movement(...)
```

### Payload minimo hacia Stock

```text
source_warehouse_id
destination_warehouse_id
product_id
quantity
movement_type
external_reference
idempotency_key
```

Stock no debe recibir:

- `vehicle_id`
- `driver_id`
- `route_id`
- `customer_id`
- `stop_id`

Eso permanece en Logistics.

## Reglas compartidas

Existe un unico archivo transversal:

```text
plugins/logistics/backend/services/rules.py
```

Internamente se organiza por bloques conceptuales, pero permanece en un solo archivo en V1.

### Bloques internos

- Session Rules
- Transition Rules
- Load Rules
- Reconciliation Rules

### Reglas minimas

- `ensure_single_active_session(vehicle_id)`
- `ensure_session_editable(session)`
- `ensure_session_can_start_loading(session)`
- `ensure_session_can_be_ready(session)`
- `ensure_session_can_depart(session)`
- `ensure_session_can_mark_returning(session)`
- `ensure_session_can_close(session)`
- `ensure_capacity_not_exceeded(vehicle, planned_weight, loaded_weight)`
- `ensure_stock_result_confirmed(result)`
- `ensure_no_open_discrepancies(session_id)`

## Servicios backend V1

### `services/sessions.py`

Responsable de:

- abrir jornada
- asignar conductor
- pasar a `LOADING`
- pasar a `READY_TO_DEPART`
- marcar salida (`OUTBOUND`)
- marcar retorno (`RETURNING`)
- cancelar jornada
- listar activas
- obtener detalle

### `services/load_plans.py`

Responsable de:

- crear o editar `LoadPlan`
- consultar disponibilidad en origen
- preparar la confirmacion de carga

### `services/operations.py`

Responsable de:

- crear operacion `TRANSFER_OUT`
- crear operacion `TRANSFER_IN`
- llamar a Stock
- persistir resultado
- dejar traza historica

Internamente todos los flujos comparten la misma secuencia:

```text
validar
-> llamar Stock
-> persistir
-> auditar
```

### `services/reconciliation.py`

Responsable de:

- consultar saldo real del warehouse MOBILE en Stock
- registrar conteo fisico
- comparar esperado vs contado
- crear discrepancias
- solicitar ajuste autorizado
- cerrar jornada

### `services/snapshots.py`

Responsable de construir un objeto derivado, no persistente:

```text
SessionSnapshot
```

## SessionSnapshot

No es tabla. No es modelo persistente. Es un DTO interno derivado.

```text
VehicleSession
-> build_session_snapshot()
-> {
     session_id,
     vehicle,
     driver,
     route,
     status,
     occupancy_percent,
     current_stock_summary,
     last_activity,
     alerts,
     can_depart,
     can_close
   }
```

Se usa para:

- resumen de jornada
- fleet monitor
- posibles clientes moviles futuros
- lecturas consolidadas del frontend

## Routers backend V1

### `routers/sessions.py`

```text
POST   /vehicle-sessions
GET    /vehicle-sessions
GET    /vehicle-sessions/active
GET    /vehicle-sessions/{id}
POST   /vehicle-sessions/{id}/start-loading
POST   /vehicle-sessions/{id}/ready
POST   /vehicle-sessions/{id}/depart
POST   /vehicle-sessions/{id}/mark-returning
POST   /vehicle-sessions/{id}/cancel
GET    /vehicle-sessions/{id}/history
```

### `routers/load_plans.py`

```text
GET    /vehicle-sessions/{id}/load-plan
PUT    /vehicle-sessions/{id}/load-plan
GET    /vehicle-sessions/{id}/origin-availability
POST   /vehicle-sessions/{id}/confirm-load
POST   /vehicle-sessions/{id}/return-remaining
```

### `routers/operations.py`

V1 minima:

```text
GET    /vehicle-sessions/{id}/operations
```

V1.1 ampliara:

```text
POST   /vehicle-sessions/{id}/deliver
POST   /vehicle-sessions/{id}/pickup
POST   /vehicle-sessions/{id}/exchange
```

### `routers/reconciliation.py`

```text
GET    /vehicle-sessions/{id}/reconciliation
POST   /vehicle-sessions/{id}/reconciliation/count
POST   /vehicle-sessions/{id}/reconciliation/request-adjustment
POST   /vehicle-sessions/{id}/close
```

### Fleet Monitor en V1

No existe router propio.

Fleet Monitor se alimenta con:

```text
GET /vehicle-sessions/active
GET /vehicle-sessions/{id}
GET /vehicle-sessions/{id}/history
```

## Lifecycle oficial

```text
                +-----------+
                |   DRAFT   |
                +-----------+
                      |
                      v
                +-----------+
                |  LOADING  |
                +-----------+
                      |
                      v
           +----------------------+
           | READY_TO_DEPART      |
           +----------------------+
                      |
                      v
                +-----------+
                | OUTBOUND  |
                +-----------+
                      |
                      v
                +-----------+
                | RETURNING |
                +-----------+
                      |
                      v
      +----------------------------------+
      | AWAITING_RECONCILIATION          |
      +----------------------------------+
                      |
                      v
                +-----------+
                |  CLOSED   |
                +-----------+

Exceptional:
DRAFT / LOADING / READY_TO_DEPART -> CANCELLED
```

## Frontend V1 real

### Distribucion

```text
plugins/logistics/frontend/
|
|-- api/
|   |-- sessions.ts
|   |-- load_plans.ts
|   |-- operations.ts
|   `-- reconciliation.ts
|
|-- pages/
|   |-- VehicleSessionsPage.tsx
|   `-- VehicleSessionDetailPage.tsx
|
|-- components/
|   |-- sessions/
|   |   |-- SessionTable.tsx
|   |   |-- SessionHeader.tsx
|   |   |-- SessionStatusBadge.tsx
|   |   `-- SessionPrimaryActions.tsx
|   |
|   |-- load_plans/
|   |   |-- LoadPlanTable.tsx
|   |   |-- ConfirmLoadPanel.tsx
|   |   |-- CapacitySummary.tsx
|   |   `-- OriginAvailabilityTable.tsx
|   |
|   |-- operations/
|   |   `-- OperationHistoryTable.tsx
|   |
|   `-- reconciliation/
|       |-- ReconciliationSummary.tsx
|       |-- PhysicalCountTable.tsx
|       |-- DiscrepancyTable.tsx
|       `-- CloseSessionPanel.tsx
|
`-- register.ts
```

## UX principal

La jornada es el centro absoluto.

No existen paginas-isla de dispatch o conciliacion.

```text
VehicleSessionsPage
   |
   v
VehicleSessionDetailPage
   |
   +-- [Resumen]
   +-- [Carga]
   +-- [Ruta]
   +-- [Conciliacion]
   `-- [Historial]
```

## Pantalla 1: VehicleSessionsPage

```text
+--------------------------------------------------------------------------------+
| Jornadas de Vehiculo                                                           |
+--------------------------------------------------------------------------------+
| [Nueva jornada]   [Estado: Activas v]   [Fecha]   [Vehiculo]   [Conductor]    |
+--------------------------------------------------------------------------------+
| Vehiculo   | Conductor   | Base Origen    | Estado       | Ruta  | Apertura   |
|------------+-------------+----------------+--------------+-------+------------|
| TRK-001    | Juan Perez  | Almacen Centro | LOADING      | --    | 08:05      |
| TRK-002    | Ana Lopez   | Almacen Norte  | OUTBOUND     | R-08  | 07:40      |
| TRK-003    | Luis Rojas  | Almacen Sur    | CLOSED       | R-12  | 06:50      |
+--------------------------------------------------------------------------------+
| [Ver jornada]                                                                   |
+--------------------------------------------------------------------------------+
```

### Acciones

- crear jornada
- filtrar activas/cerradas
- abrir detalle

No se opera stock desde aqui.

## Pantalla 2: VehicleSessionDetailPage

```text
+============================================================================+
| Jornada TRK-001                                                            |
| Estado: READY_TO_DEPART                                                    |
+============================================================================+
| Vehiculo: TRK-001      Conductor: Juan Perez                               |
| Warehouse MOBILE: MOB-TRK001                                               |
| Base origen: Almacen Central                                               |
| Ruta: R-08                                                                 |
| Apertura: 08:05                                                            |
| Peso planificado: 1800 kg                                                  |
| Peso confirmado: 1760 kg                                                   |
| Ocupacion: 88%                                                             |
+----------------------------------------------------------------------------+
| [Iniciar carga] [Lista para salir] [Marcar salida] [Retorno] [Cerrar]      |
+----------------------------------------------------------------------------+
| Tabs: [Resumen] [Carga] [Ruta] [Conciliacion] [Historial]                  |
+============================================================================+
```

### Tab Resumen

```text
+----------------------------------------------------------------------------+
| Resumen operativo                                                          |
+----------------------------------------------------------------------------+
| Estado actual: READY_TO_DEPART                                             |
| Ultima actividad: Carga confirmada 08:34                                   |
| Capacidad ocupada: 88%                                                     |
| Saldo actual warehouse MOBILE: 58 unidades / 1760 kg                       |
| Alertas: ninguna                                                           |
| Puede salir: si                                                            |
| Puede cerrar: no                                                           |
+----------------------------------------------------------------------------+
```

### Tab Carga

```text
+----------------------------------------------------------------------------+
| Carga                                                                      |
+----------------------------------------------------------------------------+
| Producto              Planificado    Disponible    Confirmado              |
|--------------------- +------------- +------------ +----------------------  |
| Bombona 10kg          50             120           [ 50 ]                  |
| Bombona 15kg          20             60            [ 18 ]                  |
| Regulador             10             30            [ 10 ]                  |
+----------------------------------------------------------------------------+
| Peso planificado: 1800 kg                                                  |
| Peso confirmado: 1760 kg                                                   |
| Capacidad maxima vehiculo: 2000 kg                                         |
| Ocupacion resultante: 88%                                                  |
+----------------------------------------------------------------------------+
| [Guardar plan] [Confirmar carga]                                           |
+----------------------------------------------------------------------------+
```

### Tab Ruta

En V1 aun no ejecuta entregas/recojos, pero la pestaña existe desde el principio para no romper la navegacion futura.

```text
+----------------------------------------------------------------------------+
| Ruta                                                                       |
+----------------------------------------------------------------------------+
| Ruta asignada: R-08                                                        |
| Estado de ruta: no iniciada                                                |
| Paradas: 0                                                                 |
| Operaciones en ruta: no habilitadas en V1                                  |
+----------------------------------------------------------------------------+
| Esta pestaña evolucionara en V1.1 para soportar:                           |
| - Deliver                                                                  |
| - Pickup                                                                   |
| - Exchange                                                                 |
+----------------------------------------------------------------------------+
```

### Tab Conciliacion

```text
+----------------------------------------------------------------------------+
| Conciliacion                                                               |
+----------------------------------------------------------------------------+
| Estado: AWAITING_RECONCILIATION                                            |
+----------------------------------------------------------------------------+
| Producto              Esperado Stock    Conteo Fisico    Diferencia        |
|--------------------- +---------------- +--------------- +----------------  |
| Bombona 10kg          5                 [ 5 ]            0                 |
| Bombona 15kg          2                 [ 1 ]           -1                 |
+----------------------------------------------------------------------------+
| Discrepancias                                                               |
| Producto        Dif.    Estado         Accion                               |
| Bombona 15kg    -1      UNDER_REVIEW   [Solicitar ajuste]                  |
+----------------------------------------------------------------------------+
| [Guardar conteo] [Solicitar ajuste] [Cerrar jornada]                       |
+----------------------------------------------------------------------------+
```

### Tab Historial

```text
+----------------------------------------------------------------------------+
| Historial de Jornada                                                       |
+----------------------------------------------------------------------------+
| 08:05  Jornada creada                                                      |
| 08:10  Carga iniciada                                                      |
| 08:34  Carga confirmada                                                    |
| 08:45  Jornada lista para salir                                            |
| 08:52  Vehiculo salio                                                      |
| 12:10  Vehiculo retorno                                                    |
| 12:20  Remanente transferido a almacen base                                |
| 13:05  Conteo fisico registrado                                            |
| 13:25  Jornada cerrada                                                     |
+----------------------------------------------------------------------------+
```

Este historial es derivado. No se persiste como tabla propia.

## Fleet Monitor V1

No existe dashboard complejo en V1.

Fleet Monitor es una tabla de lectura construida desde sesiones activas y snapshots.

```text
+----------------------------------------------------------------------------+
| Fleet Monitor                                                              |
+----------------------------------------------------------------------------+
| Vehiculo | Estado      | Conductor   | Ruta  | Carga | Ocup. | Ultima      |
|----------+-------------+-------------+-------+-------+-------+-------------|
| TRK-001  | OUTBOUND    | Juan Perez  | R-08  | 320kg | 16%   | 09:20       |
| TRK-002  | LOADING     | Ana Lopez   | --    | 1200kg| 60%   | 08:41       |
| TRK-003  | RETURNING   | Luis Rojas  | R-12  | 90kg  | 4%    | 11:02       |
+----------------------------------------------------------------------------+
```

Abrir una fila manda al detalle de la jornada.

## Flujo V1 oficial

```text
[1] Crear jornada
    -> VehicleSession(status=DRAFT)

[2] Iniciar carga
    -> status=LOADING

[3] Preparar plan
    -> LoadPlan + items

[4] Confirmar carga
    -> LogisticsOperation(TRANSFER_OUT, PENDING_STOCK)
    -> integrations/stock.transfer(...)
    -> LogisticsOperation(CONFIRMED)
    -> VehicleSession(status=READY_TO_DEPART)

[5] Marcar salida
    -> VehicleSession(status=OUTBOUND)

[6] Marcar retorno
    -> VehicleSession(status=RETURNING)

[7] Transferir remanente a base
    -> LogisticsOperation(TRANSFER_IN)
    -> integrations/stock.transfer(...)
    -> VehicleSession(status=AWAITING_RECONCILIATION)

[8] Conciliar
    -> comparar saldo stock vs conteo fisico
    -> si coincide: cierre
    -> si no coincide: discrepancy + ajuste autorizado
```

## Reglas criticas de negocio

1. un vehiculo no puede tener mas de una sesion activa
2. la carga actual del vehiculo siempre sale de Stock
3. Logistics nunca escribe `stk_balance` ni `stk_ledger`
4. no se sale sin carga confirmada
5. no se cierra con discrepancias abiertas
6. todo movimiento hacia Stock lleva `idempotency_key` estable
7. el warehouse MOBILE es persistente por vehiculo
8. Fleet Monitor no es owner de datos

## Idempotencia

La clave debe ser estable.

### Formato sugerido

```text
session_id:operation_id:item_id
```

No incluye `attempt`.

### Motivo

Si hay reintento de red o doble click, la operacion debe consultarse o confirmarse, nunca duplicarse.

## Permisos V1

### Planificador

- crear jornadas
- asignar vehiculo y conductor
- editar plan de carga

### Almacenero

- iniciar carga
- confirmar carga
- registrar retorno
- registrar conteo fisico

### Supervisor

- revisar discrepancias
- solicitar ajustes
- cerrar jornadas
- cancelar jornadas excepcionales

### Administrador

- configurar vehiculos
- asociar `mobile_warehouse_id`
- administrar permisos

## Criterios de aceptacion V1

### Backend

- se puede abrir una sesion
- se puede preparar un plan de carga
- se puede confirmar una carga real
- la confirmacion de carga genera movimientos reales en Stock
- se puede marcar salida
- se puede retornar remanente
- la conciliacion compara contra saldo real de Stock
- no se puede cerrar con discrepancias abiertas
- la idempotencia evita duplicados

### Frontend

- existe listado de jornadas
- la jornada se opera desde una sola pantalla central con tabs
- la pestaña `Carga` permite planificar y confirmar
- la pestaña `Conciliacion` permite conteo y cierre
- la pestaña `Historial` refleja el lifecycle sin salir de la jornada
- Fleet Monitor muestra sesiones activas en tabla simple

## Orden oficial de implementacion

### Fase 1

- `mobile_warehouse_id` en Vehicle
- `VehicleSession`
- lifecycle de la sesion

### Fase 2

- `integrations/stock.py`
- prueba real de comunicacion Logistics -> Stock

### Fase 3

- `LoadPlan`
- `TRANSFER_OUT`
- `TRANSFER_IN`

### Fase 4

- conciliacion
- discrepancias
- cierre seguro

### Fase 5

- `DELIVERY`
- `PICKUP`
- `EXCHANGE`

### Fase 6

- Fleet Monitor refinado
- incidentes
- mejoras UX

## Decision final

```text
Logistics es dueño de la jornada y la operacion.
Stock es dueño de las existencias y movimientos.
Fleet Monitor es una proyeccion de lectura.
VehicleSession es el Aggregate Root.
La carga actual del vehiculo siempre sale de Stock.
La UI gira completamente alrededor de VehicleSessionDetail.
```
