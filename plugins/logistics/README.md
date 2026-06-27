# logistics

Plugin piloto real de negocio para SYSTUTOR OSS.

## Alcance implementado

### Cilindros

- catalogo de estados de cilindro;
- transiciones validas;
- alta de envases;
- trazabilidad de cambios de estado;
- validacion ADR/PH para carga a estado `LLENADO_OK`;
- registro de revisiones PH;
- registro de garantias.

### Operacion

- almacenes;
- zonas;
- vehiculos;
- puntos de entrega;
- pedidos con lineas;
- rutas con paradas;
- carga por ruta;
- movimientos con confirmacion;
- agenda manual y agenda generada desde ruta.

### Frontend

- panel principal de envases;
- paginas separadas para pedidos, rutas, carga, movimientos, agenda, almacenes, vehiculos y entregas;
- widget de resumen en dashboard del sistema;
- UI sobre componentes compartidos del shell (estilo shadcn/base del proyecto).

## Endpoints disponibles

### Catalogos

- `GET /api/v1/plugins/logistics/catalog/cylinder-states`
- `GET /api/v1/plugins/logistics/catalog/movement-types`
- `GET /api/v1/plugins/logistics/catalog/task-types`
- `GET /api/v1/plugins/logistics/catalog/warehouses`
- `GET /api/v1/plugins/logistics/catalog/vehicles`
- `GET /api/v1/plugins/logistics/catalog/delivery-points`
- `GET /api/v1/plugins/logistics/catalog/zones`

### Cilindros

- `GET /api/v1/plugins/logistics/cylinders`
- `POST /api/v1/plugins/logistics/cylinders`
- `GET /api/v1/plugins/logistics/cylinders/summary`
- `GET /api/v1/plugins/logistics/cylinders/allowed-transitions/{id}`
- `GET /api/v1/plugins/logistics/cylinders/{id}`
- `GET /api/v1/plugins/logistics/cylinders/{id}/trace`
- `POST /api/v1/plugins/logistics/cylinders/{id}/transition`
- `GET /api/v1/plugins/logistics/cylinders/{id}/hydrotests`
- `POST /api/v1/plugins/logistics/cylinders/{id}/hydrotests`
- `GET /api/v1/plugins/logistics/cylinders/{id}/warranties`
- `POST /api/v1/plugins/logistics/cylinders/{id}/warranties`

### Recursos operativos

- `GET|POST|PATCH /api/v1/plugins/logistics/warehouses`
- `GET|POST /api/v1/plugins/logistics/zones`
- `GET|POST|PATCH /api/v1/plugins/logistics/vehicles`
- `GET|POST|PATCH /api/v1/plugins/logistics/delivery-points`

### Pedidos

- `GET|POST /api/v1/plugins/logistics/orders`
- `GET|PATCH /api/v1/plugins/logistics/orders/{id}`
- `GET /api/v1/plugins/logistics/orders/pending`
- `GET|POST /api/v1/plugins/logistics/orders/{id}/items`
- `PATCH|DELETE /api/v1/plugins/logistics/orders/{id}/items/{item_id}`

### Rutas y carga

- `GET|POST /api/v1/plugins/logistics/routes`
- `GET|PATCH /api/v1/plugins/logistics/routes/{id}`
- `POST /api/v1/plugins/logistics/routes/{id}/start`
- `POST /api/v1/plugins/logistics/routes/{id}/complete`
- `POST /api/v1/plugins/logistics/routes/{id}/cancel`
- `GET|POST /api/v1/plugins/logistics/routes/{id}/stops`
- `PATCH|DELETE /api/v1/plugins/logistics/routes/{id}/stops/{stop_id}`
- `POST /api/v1/plugins/logistics/routes/{id}/stops/{stop_id}/deliver`
- `POST /api/v1/plugins/logistics/routes/{id}/agenda-tasks`
- `GET|POST /api/v1/plugins/logistics/loads`
- `POST /api/v1/plugins/logistics/loads/bulk`
- `POST /api/v1/plugins/logistics/loads/confirm`
- `DELETE /api/v1/plugins/logistics/loads/{id}`

### Movimientos y agenda

- `GET|POST /api/v1/plugins/logistics/movements`
- `GET|PATCH /api/v1/plugins/logistics/movements/{id}`
- `POST /api/v1/plugins/logistics/movements/{id}/confirm`
- `POST /api/v1/plugins/logistics/movements/{id}/cancel`
- `GET /api/v1/plugins/logistics/movements/{id}/items`
- `GET /api/v1/plugins/logistics/movements/{id}/history`
- `GET|POST /api/v1/plugins/logistics/agenda/tasks`
- `GET /api/v1/plugins/logistics/agenda/tasks/by-driver/{driver_id}`
- `GET|PATCH /api/v1/plugins/logistics/agenda/tasks/{id}`
- `POST /api/v1/plugins/logistics/agenda/tasks/{id}/complete`
- `POST /api/v1/plugins/logistics/agenda/tasks/{id}/cancel`

## Permisos

- `logistics.cylinder.read`
- `logistics.cylinder.create`
- `logistics.cylinder.transition`
- `logistics.cylinder.trace`
- `logistics.order.read`
- `logistics.order.create`
- `logistics.order.manage`
- `logistics.route.read`
- `logistics.route.manage`
- `logistics.load.manage`
- `logistics.movement.read`
- `logistics.movement.create`
- `logistics.movement.confirm`
- `logistics.warehouse.read`
- `logistics.warehouse.manage`
- `logistics.vehicle.read`
- `logistics.vehicle.manage`
- `logistics.agenda.read`
- `logistics.agenda.manage`
- `logistics.maintenance.read`
- `logistics.maintenance.manage`

## Eventos principales

- `logistics.cylinder.created`
- `logistics.cylinder.state_changed`
- `logistics.cylinder.hydrotest_registered`
- `logistics.order.created`
- `logistics.order.updated`
- `logistics.route.created`
- `logistics.route.started`
- `logistics.route.completed`
- `logistics.load.assigned`
- `logistics.load.prepared`
- `logistics.movement.created`
- `logistics.movement.completed`
- `logistics.movement.cancelled`
- `logistics.agenda.task_completed`
- `logistics.warranty.created`
