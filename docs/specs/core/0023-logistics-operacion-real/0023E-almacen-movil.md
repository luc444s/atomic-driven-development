# SPEC 0023E — Almacen movil: integración con Stock y Logistics

> **Estado de vigencia:** `historica / deprecada en runtime`
>
> La implementacion runtime de `almacen movil` y `flota` fue retirada del producto por inconsistencia operativa y tecnica.
> Esta spec **no debe tomarse como feature activa ni como roadmap inmediato de implementacion**.
> Se conserva como baseline de diseno para una reconstruccion futura del dominio, no como contrato vigente del sistema actual.
>
> La spec vigente que reemplaza este intento es: `0023E1-vehicle-session-almacen-movil-v1.md`.

## Estado

Version 2 — 2026-07-09 — Reemplaza a la version anterior de 0023E

> Esta spec reescribe completamente `0023E-almacen-movil.md` para resolver la contradiccion con el motor de stock. Ya no se mantiene la clausula "no crear warehouse en stock". Por el contrario, esta spec establece que **todo almacen movil debe ser un warehouse real** con `warehouse_type = MOBILE` para que el motor de inventario unificado pueda operar sin excepciones.

## Problema

El sistema nuevo ya modela almacenes fijos (`lg_warehouses`) y almacenes moviles (`lg_mobile_warehouses`), pero ambos estan desconectados:

1. `transfer_stock` en `stock` solo transfiere entre registros de `lg_warehouses`. No sabe que existe un almacen movil.
2. `lg_mobile_warehouse` tiene `warehouse_id` (origen fijo) pero no es en si mismo un warehouse con balance.
3. Cargar un vehiculo no impacta `stk_balance`. Entregar a cliente tampoco. No hay trazabilidad de inventario real entre almacen fijo, vehiculo y cliente.
4. El repartidor no puede consultar "que tengo en el coche" desde el sistema.
5. Los eventos no pueden expresar movimientos entre fijo y movil porque el movil no existe como warehouse.

Sin esta integracion, `0023F` (agenda a carga), `0023G` (stock libre en reparto), `0023H` (escaneo de carga) y `0023J` (carta porte viva) operan sobre un modelo incompleto.

## Evidencia

### Grab2

`Grabación28ENE2025_transcripcion.txt` y `Bogdan 30 abril 2024_fix_transcripcion.txt` confirman que el camion se trata operativamente como un almacen:

- "... agregar un almacen que seria el almacen movil ..."
- "... al cargar esta haciendo el traspaso al almacen movil ..."
- "... todo lo que se traslada va al almacen movil ..."
- "... mientras que no se pica sigue siendolo dentro de ese coche ..."
- "... yo me puedo ver desde aqui que es lo que tiene en el coche ..."

### Legacy

`FrmCargaRepartidor`, `AGENDA_PREPARACION_CARGA` y `sp_CargaRepartidor_Insertar` confirman que el legacy ya modelaba carga de vehiculo como operacion de inventario, no como simple estado.

### Codigo existente

- `plugins/logistics/backend/models/mobile.py` — `LogisticsMobileWarehouse` e `Items` existen pero sin conexion a stock.
- `plugins/stock/backend/services/operations.py:258-406` — `transfer_stock` solo maneja FIXED → FIXED.
- `plugins/logistics/backend/services/stock_bridge.py` — existe como puente pero sin integracion real de warehouse movil.
- `plugins/stock/backend/models.py:66-90` — `stk_balance` por `product_id + warehouse_id`, listo para recibir warehouses moviles.

## Objetivo

Integrar los almacenes moviles con el motor de inventario de `stock` para que:

1. Cargar un vehiculo = transferencia `FIXED → MOBILE` con decremento/incremento de `stk_balance`.
2. Entregar a cliente = salida `MOBILE → CUSTOMER` via `issue_stock`.
3. Recoger envase = entrada `CUSTOMER → MOBILE` via `receive_stock`.
4. Devolver a almacen = transferencia `MOBILE → FIXED`.
5. El repartidor puede ver la composicion actual de su vehiculo en tiempo real.
6. El ledger registra toda transicion sin depender del modelo movil.
7. El sistema valida peso, capacidad y ADR durante carga y entrega.

## No objetivos

- No crear un warehouse de tipo `CLIENT`. El cliente es una entidad externa, no un almacen.
- No implementar kardex valorizado (costo promedio, FIFO). Sigue diferido a contabilidad futura.
- No implementar facturacion, cobros o CxC desde esta spec.
- No reemplazar `lg_vehicles` ni `lg_equipment`. El vehiculo sigue siendo entidad propia en logistics.
- No implementar el flujo completo de agenda a carga (0023F) ni escaneo de carga (0023H). Esta spec es prerequisito para esas specs.

## Decision de arquitectura

### 1. El almacen movil es un warehouse real

Cada `lg_mobile_warehouse` activo debe tener un registro en `lg_warehouses` con `warehouse_type = MOBILE`. Ese warehouse tendra balance en `stk_balance` como cualquier almacen fijo.

El motor de stock no necesita logica diferente para calcular existencias moviles.

### 2. Tres servicios, un motor

Se separa la semantica en tres servicios que comparten un motor interno comun (`post_stock_movement`):

| Servicio | Uso | Operaciones |
|---|---|---|
| `transfer_stock` | Entre warehouses | `INTERNAL_TRANSFER`, `LOAD`, `RETURN_TO_WAREHOUSE` |
| `issue_stock` | Salida a externo | `DELIVERY`, `CONSUMPTION`, `SCRAP`, `LOSS` |
| `receive_stock` | Entrada desde externo | `PICKUP`, `PURCHASE_RECEIPT`, `CUSTOMER_RETURN`, `ADJUSTMENT_IN` |

El motor comun es responsable de: bloquear balances con `SELECT FOR UPDATE`, validar stock, registrar ledger, actualizar balances, crear eventos moviles y garantizar idempotencia. Todo en una sola transaccion.

### 3. Clasificacion de movimientos a dos ejes

| movement_type | Naturaleza contable | operation_type | Operacion logistica |
|---|---|---|---|
| `TRANSFER` | Movimiento entre warehouses | `INTERNAL_TRANSFER` | Fijo → Fijo |
| `TRANSFER` | Movimiento entre warehouses | `LOAD` | Fijo → Movil |
| `TRANSFER` | Movimiento entre warehouses | `RETURN_TO_WAREHOUSE` | Movil → Fijo |
| `SALE` | Salida por venta/entrega | `DELIVERY` | Movil → Cliente |
| `CUSTOMER_RETURN` | Entrada por devolucion | `PICKUP` | Cliente → Movil |
| `ADJUSTMENT` | Correccion de inventario | `RECONCILIATION` | Ajuste en movil |
| `SCRAP` | Baja por perdida | `UNLOAD` | Baja desde movil |

### 4. Identidad persistente por vehiculo

El warehouse movil se asocia al vehiculo, no al conductor. El conductor puede cambiar entre jornadas.

Esto evita crear warehouses huerfanos por cambio de repartidor.

### 5. Cliente NO es warehouse

El cliente no mantiene inventario interno. Una entrega a cliente es una salida de stock (`issue_stock`). Un recojo es una entrada (`receive_stock`). En ningun caso se crea un warehouse para el cliente.

## Modelo de datos

### `lg_warehouses` — nuevo campo

```sql
ALTER TABLE lg_warehouses ADD COLUMN warehouse_type VARCHAR(20) NOT NULL DEFAULT 'FIXED';
```

Restriccion:

```sql
CHECK (warehouse_type IN ('FIXED', 'MOBILE', 'TRANSIT', 'QUARANTINE'))
```

### `lg_mobile_warehouses` — nuevo campo

```sql
ALTER TABLE lg_mobile_warehouses ADD COLUMN warehouse_id VARCHAR(36) NOT NULL;
ALTER TABLE lg_mobile_warehouses ADD CONSTRAINT fk_mw_warehouse FOREIGN KEY (warehouse_id) REFERENCES lg_warehouses(id);
```

El `warehouse_id` debe apuntar a un registro con `warehouse_type = MOBILE`.

### `stk_ledger` — nuevos campos

```sql
ALTER TABLE stk_ledger ADD COLUMN movement_type VARCHAR(30);
ALTER TABLE stk_ledger ADD COLUMN operation_type VARCHAR(30);
ALTER TABLE stk_ledger ADD COLUMN document_type VARCHAR(50);
ALTER TABLE stk_ledger ADD COLUMN document_id VARCHAR(36);
ALTER TABLE stk_ledger ADD COLUMN related_party_type VARCHAR(20);
ALTER TABLE stk_ledger ADD COLUMN related_party_id VARCHAR(36);
```

### `lg_mobile_warehouse_items` — nuevos campos

```sql
ALTER TABLE lg_mobile_warehouse_items ADD COLUMN serial_id VARCHAR(36);
ALTER TABLE lg_mobile_warehouse_items ADD COLUMN condition VARCHAR(20);
ALTER TABLE lg_mobile_warehouse_items ADD COLUMN source_ledger_entry_id VARCHAR(36);
ALTER TABLE lg_mobile_warehouse_items ADD COLUMN last_ledger_entry_id VARCHAR(36);
ALTER TABLE lg_mobile_warehouse_items ADD COLUMN customer_id VARCHAR(36);
```

### Nuevas tablas de eventos por item

```sql
CREATE TABLE lg_mobile_warehouse_item_events (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    mobile_warehouse_item_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    ledger_entry_id VARCHAR(36),
    movement_id VARCHAR(36),
    customer_id VARCHAR(36),
    occurred_at TIMESTAMP NOT NULL,
    created_by VARCHAR(36),
    metadata JSONB,
    FOREIGN KEY (mobile_warehouse_item_id) REFERENCES lg_mobile_warehouse_items(id),
    FOREIGN KEY (ledger_entry_id) REFERENCES stk_ledger(id)
);
```

### Nuevas tablas de snapshot de jornada

```sql
CREATE TABLE lg_mobile_warehouse_snapshots (
    id VARCHAR(36) PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL,
    mobile_warehouse_id VARCHAR(36) NOT NULL,
    snapshot_type VARCHAR(30) NOT NULL,
    captured_at TIMESTAMP NOT NULL,
    captured_by VARCHAR(36),
    total_units NUMERIC(18, 4) NOT NULL DEFAULT 0,
    total_weight_kg NUMERIC(18, 4) NOT NULL DEFAULT 0,
    metadata JSONB,
    FOREIGN KEY (mobile_warehouse_id) REFERENCES lg_mobile_warehouses(id)
);

CREATE TABLE lg_mobile_warehouse_snapshot_items (
    id VARCHAR(36) PRIMARY KEY,
    snapshot_id VARCHAR(36) NOT NULL,
    product_id VARCHAR(36) NOT NULL,
    condition VARCHAR(20),
    quantity NUMERIC(18, 4) NOT NULL,
    weight_kg NUMERIC(18, 4) NOT NULL DEFAULT 0,
    FOREIGN KEY (snapshot_id) REFERENCES lg_mobile_warehouse_snapshots(id)
);
```

> **Regla critica: `lg_mobile_warehouse_items` NO compite con `stk_balance`.** `stk_balance` es la fuente de verdad de inventario. `lg_mobile_warehouse_items` es una vista operacional para tracking de unidades en jornada. Si en algun momento `SUM(mobile_items) != stk_balance` para un warehouse movil, hay un bug. Nunca debe usarse `mobile_items` para calcular stock disponible.

## Estados de jornada movil

Se reemplaza el binomio `OPEN/CLOSED` por estados operativos explícitos:

| Estado | Descripcion | Operaciones permitidas |
|---|---|---|
| `PLANNED` | Jornada planificada, sin carga real | Planificar carga, cambiar vehiculo/conductor |
| `LOADING` | En proceso de carga | `LOAD`, escaneo de items |
| `READY` | Carga concluida, pendiente de salida | Solo lectura; cambios requieren reapertura |
| `IN_ROUTE` | En ruta de reparto | `DELIVERY`, `PICKUP` |
| `RETURNING` | Retornando al almacen. Solo operaciones de devolucion de stock. | `PICKUP` pendientes, `RETURN_TO_WAREHOUSE` |
| `RECONCILING` | Conteo final y auditoria. No entran ni salen unidades. | Registro de diferencias, snapshot final, ajustes compensatorios |
| `CLOSED` | Jornada cerrada | Solo lectura |
| `CANCELLED` | Jornada cancelada antes de salir | Solo si no hay carga confirmada; requiere movimientos compensatorios |

> **Separacion RETURNING vs RECONCILING es deliberada.** RETURNING mueve stock (devolucion fisica al almacen). RECONCILING no mueve stock — solo audita, cuenta y ajusta diferencias. Mezclarlas introduciria bugs de conciliacion donde no se sabe si falta stock o falta registro.

Transiciones permitidas:

```
PLANNED → LOADING → READY → IN_ROUTE → RETURNING → RECONCILING → CLOSED
                                      ↘            ↙
                                   CANCELLED
```

## Flujos funcionales

### Carga (FIXED → MOBILE)

```
oficina/repartidor escanea items → transfer_stock(type=LOAD)
  → decrementa stk_balance del fijo
  → incrementa stk_balance del movil
  → registra ledger con movement_type=TRANSFER, operation_type=LOAD
  → crea/actualiza lg_mobile_warehouse_items con status=LOADED
  → valida peso contra lg_vehicles.useful_load
  → valida ADR contra lg_vehicles.adr_class
  → emite evento stock.transfer.completed
  → emite evento logistics.mobile_item.loaded (por item)
```

### Entrega (MOBILE → CUSTOMER)

```
repartidor escanea items + selecciona cliente → issue_stock(type=DELIVERY)
  → decrementa stk_balance del movil
  → registra ledger con movement_type=SALE, operation_type=DELIVERY
  → registra related_party_type=CUSTOMER, related_party_id
  → actualiza lg_mobile_warehouse_items.status=DELIVERED
  → emite evento stock.issue.completed
  → emite evento logistics.mobile_item.delivered (por item)
```

### Recojo (CUSTOMER → MOBILE)

```
repartidor escanea items + selecciona cliente → receive_stock(type=PICKUP)
  → incrementa stk_balance del movil
  → registra ledger con movement_type=CUSTOMER_RETURN, operation_type=PICKUP
  → registra related_party_type=CUSTOMER
  → crea/actualiza lg_mobile_warehouse_items con status=PICKED_UP
  → valida peso contra lg_vehicles.useful_load
  → emite evento stock.receive.completed
  → emite evento logistics.mobile_item.picked_up (por item)
```

### Devolucion (MOBILE → FIXED)

```
repartidor/almacen escanea items → transfer_stock(type=RETURN_TO_WAREHOUSE)
  → decrementa stk_balance del movil
  → incrementa stk_balance del fijo
  → registra ledger con movement_type=TRANSFER, operation_type=RETURN_TO_WAREHOUSE
  → actualiza lg_mobile_warehouse_items.status=RETURNED
  → emite evento stock.transfer.completed
  → emite evento logistics.mobile_item.returned (por item)
```

## Eventos

Conforme a ADR 0005 (`<module>.<resource>.<past_action>`):

### Stock (motor de inventario)

| Evento | Cuando |
|---|---|
| `stock.transfer.completed` | Transferencia entre warehouses ejecutada |
| `stock.transfer.failed` | Transferencia rechazada |
| `stock.issue.completed` | Salida a externo ejecutada |
| `stock.issue.failed` | Salida rechazada |
| `stock.receive.completed` | Entrada desde externo ejecutada |
| `stock.receive.failed` | Entrada rechazada |

> **stock.balance.updated queda excluido deliberadamente.** Emitirlo en cada operacion genera ruido masivo sin consumidores reales. Cualquier proyeccion de balance se deriva de `stock.transfer.completed`, `stock.issue.completed` y `stock.receive.completed`.

### Logistics (operacion de vehiculos)

| Evento | Cuando |
|---|---|
| `logistics.mobile_warehouse.created` | Jornada creada |
| `logistics.mobile_warehouse.opened` | Jornada abierta operativamente |
| `logistics.mobile_warehouse.load_started` | Inicio de carga |
| `logistics.mobile_warehouse.loaded` | Carga completada |
| `logistics.mobile_warehouse.departed` | Vehiculo inicia ruta |
| `logistics.mobile_warehouse.in_route` | En ruta |
| `logistics.mobile_warehouse.returning` | Inicia retorno |
| `logistics.mobile_warehouse.closed` | Jornada cerrada |
| `logistics.mobile_warehouse.cancelled` | Jornada cancelada |
| `logistics.delivery.completed` | Entrega a cliente ejecutada |
| `logistics.delivery.failed` | Entrega rechazada |
| `logistics.pickup.completed` | Recojo ejecutado |
| `logistics.pickup.failed` | Recojo rechazado |
| `logistics.return.completed` | Devolucion ejecutada |
| `logistics.return.failed` | Devolucion rechazada |
| `logistics.reconciliation.started` | Inicia conciliacion |
| `logistics.reconciliation.completed` | Conciliacion completada |
| `logistics.reconciliation.failed` | Conciliacion con diferencias no resueltas |

### Por item (trazabilidad fina)

| Evento | Cuando |
|---|---|
| `logistics.mobile_item.loaded` | Item cargado al vehiculo |
| `logistics.mobile_item.delivered` | Item entregado a cliente |
| `logistics.mobile_item.picked_up` | Item recogido de cliente |
| `logistics.mobile_item.returned` | Item devuelto al almacen |
| `logistics.mobile_item.damaged` | Item marcado como danado |
| `logistics.mobile_item.missing` | Item marcado como faltante |
| `logistics.mobile_item.reconciled` | Item conciliado en cierre |

Payload base de todo evento (ADR 0005):

```json
{
  "event_id": "uuid",
  "event_name": "stock.transfer.completed",
  "version": "1",
  "occurred_at": "2026-07-09T19:00:00Z",
  "module": "stock",
  "tenant_id": "uuid",
  "branch_id": "uuid",
  "actor_type": "user",
  "actor_id": "uuid",
  "entity_type": "mobile_warehouse",
  "entity_id": "uuid",
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "payload": {},
  "metadata": {}
}
```

## Permisos

Se crean los siguientes permisos nuevos (formato ADR 0003 `<module>.<resource>.<action>`):

| Permiso | Descripcion |
|---|---|
| `stock.transfer.internal` | Transferir entre almacenes fijos |
| `stock.mobile.load` | Cargar a almacen movil |
| `stock.mobile.return` | Devolver desde almacen movil |
| `stock.mobile.deliver` | Entregar desde almacen movil |
| `stock.mobile.pickup` | Recoger desde/hacia almacen movil |
| `stock.mobile.reconcile` | Conciliar inventario movil |
| `stock.mobile.close` | Cerrar jornada movil |
| `stock.mobile.override_capacity` | Sobrepasar limite de capacidad |
| `stock.mobile.resolve_difference` | Resolver diferencias de conciliacion |

El repartidor solo debe poder operar sobre su jornada activa, su vehiculo asignado y los movimientos/clientes incluidos en su ruta.

## Auditoria minima

Toda operacion debe registrar auditoria con:

- `action`: nombre de la accion (`mobile_warehouse.load`, `stock.delivery`, etc.)
- `entity_type`: `mobile_warehouse`, `mobile_item`, `stock_movement`
- `entity_id`: id del recurso afectado
- `details`: vehicle_id, warehouse_id, product_id, quantity, peso, etc.

## Control de peso y capacidad

Cada operacion que afecte la carga del vehiculo debe recalcular y validar:

```
current_load_weight + incoming_weight <= useful_load
```

El backend debe recalcular desde datos confiables, no desde el frontend.

Validaciones adicionales:
- Incompatibilidad de productos (ADR)
- Clasificacion ADR del vehiculo
- Restricciones de ruta
- Cantidad maxima por tipo de envase

## Creacion automatica del warehouse movil

Al crear un `lg_mobile_warehouse`:

1. Validar vehiculo y conductor.
2. Buscar warehouse movil reutilizable asociado al vehiculo (`warehouse_type = MOBILE`, activo).
3. Si no existe, crear nuevo registro en `lg_warehouses` con `warehouse_type = MOBILE`.
4. Asignar `lg_mobile_warehouses.warehouse_id` al warehouse creado/reutilizado.
5. No es necesario insertar filas vacias en `stk_balance`. El balance se crea bajo demanda al primer movimiento.

## Concurrencia e idempotencia

Toda operacion debe aceptar `idempotency_key`.

Formato sugerido:
- Carga: `load:{mobile_warehouse_id}:{serial_id}`
- Entrega: `delivery:{movement_id}:{serial_id}`
- Recojo: `pickup:{movement_id}:{serial_id}`
- Devolucion: `return:{mobile_warehouse_id}:{serial_id}`

Los balances deben bloquearse con `SELECT ... FOR UPDATE` (ya implementado en `_lock_balance_row`).

Si la clave ya fue procesada, devolver resultado anterior sin duplicar.

## Snapshots de jornada

Cada jornada debe registrar:

| Snapshot | Momento |
|---|---|
| `OPENING` | Al abrir la jornada |
| `PRE_DEPARTURE` | Antes de salir a ruta, carga final confirmada |
| `CLOSING` | Al cerrar la jornada, despues de conciliacion |
| `RECONCILIATION` | Si hubo diferencias que requirieron ajuste |

El snapshot captura `total_units`, `total_weight_kg` y detalle por producto. No sustituye al ledger. Sirve para conciliacion rapida y auditoria de cierre.

## Vistas operativas

### Composicion actual del vehiculo

```sql
CREATE VIEW v_mobile_warehouse_load AS
SELECT
    mw.id AS mobile_warehouse_id,
    mw.warehouse_id,
    mw.vehicle_id,
    v.plate,
    mw.driver_id,
    mw.status,
    mw.opened_at,
    mwi.product_id,
    mwi.condition,
    SUM(mwi.quantity) AS quantity,
    SUM(mwi.weight_kg) AS weight_kg
FROM lg_mobile_warehouses mw
JOIN lg_vehicles v ON v.id = mw.vehicle_id
LEFT JOIN lg_mobile_warehouse_items mwi
    ON mwi.mobile_warehouse_id = mw.id
    AND mwi.status NOT IN ('DELIVERED', 'RETURNED', 'CANCELLED')
WHERE mw.status NOT IN ('CLOSED', 'CANCELLED')
GROUP BY mw.id, mw.warehouse_id, mw.vehicle_id, v.plate,
         mw.driver_id, mw.status, mw.opened_at,
         mwi.product_id, mwi.condition;
```

### Dashboard de flota activa

Debe exponer por vehiculo activo:
- Placa, conductor, estado, ruta
- Almacen de origen, carga actual (peso y unidades)
- Capacidad utilizada (%)
- Entregado, recogido, pendiente
- Incidencias
- Ultima sincronizacion

## Integracion con legacy

| Legacy | OSS |
|---|---|
| `EEquipos.IdEquipo` | `lg_vehicles.id` |
| `EEquipos.NombreEquipo` | `lg_vehicles.plate` |
| `EEquipos.TipoEquipo` | `lg_vehicles.vehicle_type` |
| `EEquiposPorMovimiento` | `lg_movement_equipment` |
| Carga transportada | `lg_mobile_warehouse_items` |
| Parametros del repartidor | `lg_driver_parameters` |
| Peso maximo | `lg_vehicles.useful_load` |
| Capacidad tecnica | `lg_vehicles.capacity_weight` |

## Plan de migracion

### Fase 1: modelo base

- Agregar `warehouse_type` a `lg_warehouses`.
- Agregar `warehouse_id` a `lg_mobile_warehouses`.
- Crear warehouse movil por vehiculo (automatico).
- Conectar `stk_balance` a warehouses moviles.
- Agregar `movement_type` y `operation_type` a `stk_ledger`.
- Mantener compatibilidad con `transfer_stock` actual.

### Fase 2: carga y retorno

- Implementar `operation_type = LOAD` y `RETURN_TO_WAREHOUSE` en `transfer_stock`.
- Validar peso en carga.
- Integrar con `lg_mobile_warehouse_items`.
- Eventos por item (`logistics.mobile_item.loaded`, `returned`).

### Fase 3: entrega y recojo

- Implementar `issue_stock` y `receive_stock`.
- Conectar cliente como `related_party`.
- Eventos `logistics.mobile_item.delivered`, `picked_up`.
- Integrar con movimientos logisticos existentes.

### Fase 4: jornada y conciliacion

- Estados completos de jornada.
- Snapshots.
- Cierre de jornada con deteccion de diferencias.
- Incidencias y resolucion.

### Fase 5: optimizacion

- Idempotencia completa.
- Soporte offline para app movil.
- Operaciones masivas por lote.
- Dashboard de flota en tiempo real.
- Outbox transaccional para eventos.

## Endpoints esperados

### Lectura

- `GET /mobile-warehouses` — listar jornadas activas
- `GET /mobile-warehouses/{id}` — detalle de jornada
- `GET /mobile-warehouses/{id}/load` — composicion actual del vehiculo
- `GET /mobile-warehouses/{id}/snapshots` — snapshots de la jornada
- `GET /mobile-warehouses/by-vehicle/{vehicle_id}` — jornada activa por vehiculo

### Operacion

- `POST /mobile-warehouses` — crear/abrir jornada
- `POST /mobile-warehouses/{id}/load` — cargar items
- `POST /mobile-warehouses/{id}/deliver` — entregar items a cliente
- `POST /mobile-warehouses/{id}/pickup` — recoger items de cliente
- `POST /mobile-warehouses/{id}/return` — devolver items al almacen
- `POST /mobile-warehouses/{id}/close` — cerrar jornada
- `POST /mobile-warehouses/{id}/cancel` — cancelar jornada

### Stock (desde el motor de inventario)

- `POST /stock/transfer` — transferencia entre warehouses
- `POST /stock/issue` — salida a externo
- `POST /stock/receive` — entrada desde externo

## Criterios de aceptacion

1. Al crear una jornada se crea o reutiliza un warehouse movil con `type = MOBILE`.
2. Una carga `FIXED → MOBILE` reduce el `stk_balance` del fijo y aumenta el del movil.
3. Una entrega `MOBILE → CUSTOMER` reduce el `stk_balance` del movil sin crear balance para el cliente.
4. Un recojo `CUSTOMER → MOBILE` aumenta el `stk_balance` del movil.
5. Una devolucion `MOBILE → FIXED` reduce el movil y aumenta el fijo.
6. El repartidor puede ver la composicion actual de su vehiculo via API.
7. Cargar mas alla del `useful_load` es rechazado.
8. Cerrar una jornada con diferencias no resueltas es rechazado.
9. Toda operacion deja rastro en `stk_ledger` con `movement_type` y `operation_type`.
10. Toda operacion movil emite evento conforme a ADR 0005.
11. Toda operacion movil acepta `idempotency_key` y es segura ante reintentos.
12. El warehouse movil reutiliza la identidad del vehiculo entre jornadas.

## Reglas de integridad

1. Un warehouse movil debe pertenecer al mismo tenant que el vehiculo y la jornada.
2. Un vehiculo no puede tener dos jornadas activas simultaneamente.
3. Un cilindro serializado no puede existir en dos almacenes al mismo tiempo.
4. Un item entregado no puede continuar en balance movil.
5. Un item recogido debe ingresar al balance movil antes de ser devuelto.
6. Una jornada cerrada no puede recibir movimientos nuevos.
7. Toda modificacion de balance debe tener ledger asociado.
8. El ledger no se edita ni se elimina. Las correcciones se realizan mediante movimientos compensatorios.
9. Todo movimiento debe registrar actor, fecha, tenant y documento relacionado.
