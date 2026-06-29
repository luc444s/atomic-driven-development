# logistics

Plugin piloto de negocio de SYSTUTOR OSS.

Version actual: `0.4.0`

## Alcance implementado

### Envases

- alta, edicion y trazabilidad de cilindros;
- validacion de transiciones;
- PH, garantias, retimbrados, servicios y etiquetas;
- escaneo con validacion ADR/PH;
- historial de propiedad y custodia.

### Operacion base

- almacenes, zonas, vehiculos y puntos de entrega;
- pedidos con lineas;
- rutas con paradas;
- carga por ruta;
- movimientos con confirmacion y cancelacion;
- agenda manual y agenda generada desde ruta.

### SPEC 0014 implementada

- planificacion de pedidos contra `stk_balance`;
- precargas por almacen y fecha;
- aceptacion/cancelacion de precargas;
- recepcion con faltantes e incidencias;
- despacho con guia y cierre idempotente;
- retorno de vehiculo;
- carta porte y reportes JSON estructurados;
- equipos por movimiento;
- restricciones vehiculo-ruta;
- parametros por repartidor;
- vinculacion vehiculo-punto de entrega;
- resumen diario de agenda;
- schedule semanal de rutas;
- control de peso de carga;
- ADR por producto, incompatibilidades y elegibilidad de vehiculos;
- tracking GPS en ruta, parada y agenda;
- consultas de peso y contenido.

## Integraciones

### Productos

- las nuevas funciones operan con `prod_products` como catalogo maestro;
- `lg_movement_items` materializa `product_id` y `product_name` como snapshot transaccional.

### Stock

- planificacion lee stock real desde `stk_balance`;
- recepcion incrementa stock real por producto;
- `close-dispatch` descuenta stock real por producto;
- la integracion con stock se hace por llamada directa de servicio Python con idempotencia;
- una linea logistica solo afecta stock real si existe `stk_config` activo para `(tenant_id, warehouse_id, product_id)`.

## Endpoints principales

### Planning

- `GET /api/v1/plugins/logistics/planning/stock`
- `POST /api/v1/plugins/logistics/planning/stock/summary`
- `GET /api/v1/plugins/logistics/planning/pending-orders`
- `POST /api/v1/plugins/logistics/planning/plan-order/{order_id}`
- `POST /api/v1/plugins/logistics/planning/generate-preload`
- `GET /api/v1/plugins/logistics/planning/preloads`
- `GET /api/v1/plugins/logistics/planning/preloads/{preload_id}`
- `POST /api/v1/plugins/logistics/planning/preloads/{preload_id}/accept`
- `POST /api/v1/plugins/logistics/planning/preloads/{preload_id}/cancel`

### Reception y despacho

- `GET /api/v1/plugins/logistics/reception/pending`
- `GET /api/v1/plugins/logistics/reception/{movement_id}`
- `POST /api/v1/plugins/logistics/reception/{movement_id}/receive`
- `POST /api/v1/plugins/logistics/reception/{movement_id}/incident`
- `GET /api/v1/plugins/logistics/reception/incident-reasons`
- `PATCH /api/v1/plugins/logistics/movements/{movement_id}/guide`
- `POST /api/v1/plugins/logistics/movements/{movement_id}/close-dispatch`
- `GET /api/v1/plugins/logistics/movements/{movement_id}/dispatch-receipt`
- `POST /api/v1/plugins/logistics/movements/{movement_id}/vehicle-return`

### Documentos y reportes

- `GET /api/v1/plugins/logistics/waybill/{movement_id}`
- `GET /api/v1/plugins/logistics/waybill/{movement_id}/summary`
- `GET /api/v1/plugins/logistics/reports/route-agenda/{route_id}`
- `GET /api/v1/plugins/logistics/reports/dispatch-ticket/{movement_id}`
- `GET /api/v1/plugins/logistics/reports/transfer-albaran/{movement_id}`
- `GET /api/v1/plugins/logistics/reports/load-summary/{route_id}`
- `GET /api/v1/plugins/logistics/reports/adr-summary/{movement_id}`

### Modulos auxiliares

- `GET|POST /api/v1/plugins/logistics/equipment`
- `GET|POST|PATCH /api/v1/plugins/logistics/movements/{movement_id}/equipment`
- `GET|POST /api/v1/plugins/logistics/vehicles/{vehicle_id}/route-restrictions`
- `GET /api/v1/plugins/logistics/routes/{route_id}/eligible-vehicles`
- `GET|PUT /api/v1/plugins/logistics/drivers/{driver_id}/parameters`
- `GET|POST|DELETE /api/v1/plugins/logistics/vehicles/{vehicle_id}/delivery-points`
- `GET /api/v1/plugins/logistics/agenda/daily-summary`
- `PATCH /api/v1/plugins/logistics/routes/{route_id}/weekly-schedule`
- `GET /api/v1/plugins/logistics/loads/weight-summary`
- `GET|PUT /api/v1/plugins/logistics/adr/product-config/{product_id}`
- `GET|POST|DELETE /api/v1/plugins/logistics/adr/incompatibilities`
- `GET /api/v1/plugins/logistics/adr/points/{movement_id}`
- `GET /api/v1/plugins/logistics/adr/eligible-vehicles/{movement_id}`
- `PATCH /api/v1/plugins/logistics/routes/{route_id}/gps-start`
- `PATCH /api/v1/plugins/logistics/routes/{route_id}/stops/{stop_id}/gps`
- `PATCH /api/v1/plugins/logistics/agenda/tasks/{task_id}/gps`
- `GET /api/v1/plugins/logistics/cylinders/available-with-weight`
- `GET /api/v1/plugins/logistics/cylinders/{cylinder_id}/weight`
- `GET /api/v1/plugins/logistics/products/{product_id}/content`

## Permisos

El plugin sigue reutilizando el set actual de permisos:

- `logistics.cylinder.*`
- `logistics.order.*`
- `logistics.route.*`
- `logistics.load.manage`
- `logistics.movement.read`
- `logistics.movement.create`
- `logistics.movement.confirm`
- `logistics.warehouse.*`
- `logistics.vehicle.*`
- `logistics.agenda.*`
- `logistics.maintenance.*`
- `logistics.retimbrado.*`
- `logistics.scan.*`
- `logistics.label.*`
- `logistics.ownership.read`
- `logistics.service.*`
- `logistics.gas.read`
- `logistics.brand.read`

Los endpoints nuevos respetan `warehouse_id` como claim contextual cuando operan contra almacenes.

## Eventos principales

- `logistics.planning.preload_generated`
- `logistics.planning.preload_accepted`
- `logistics.reception.completed`
- `logistics.dispatch.completed`
- `logistics.dispatch.returned`
- `logistics.route.created`
- `logistics.route.started`
- `logistics.route.completed`
- `logistics.movement.created`
- `logistics.movement.completed`
- `logistics.movement.cancelled`
- `logistics.agenda.task_completed`

## Notas operativas

- los reportes y carta porte exponen datos estructurados en JSON; el renderizado PDF queda fuera del plugin;
- `close-dispatch` es el momento en que se descuenta stock real;
- `vehicle-return` solo mueve estado fisico y prepara la recepcion;
- recepcion crea lineas `FALTANTE NO TRANSFERIDO` cuando aplica;
- la precarga activa es unica por tenant + almacen + fecha en estado `PENDIENTE`/`ACEPTADA`.
