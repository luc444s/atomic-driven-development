# Logistics API Contract

## Estado

Vigente para implementacion actual, incluida la ampliacion de envase completo + escaneo movil.

## Base path

`/api/v1/plugins/logistics`

## Permisos usados hoy

- `logistics.cylinder.read`
- `logistics.cylinder.create`
- `logistics.cylinder.update`
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
- `logistics.retimbrado.read`
- `logistics.retimbrado.manage`
- `logistics.scan.execute`
- `logistics.scan.read`
- `logistics.label.print`
- `logistics.label.read`
- `logistics.ownership.read`
- `logistics.service.read`
- `logistics.service.manage`
- `logistics.gas.read`
- `logistics.brand.read`
- `logistics.session.read`
- `logistics.session.manage`

## Eventos emitidos hoy

- `logistics.cylinder.created`
- `logistics.cylinder.updated`
- `logistics.cylinder.state_changed`
- `logistics.cylinder.hydrotest_registered`
- `logistics.cylinder.retimbrado_registered`
- `logistics.cylinder.label_printed`
- `logistics.cylinder.ownership_changed`
- `logistics.cylinder.scanned`
- `logistics.cylinder.service_registered`
- `logistics.cylinder.service_completed`
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

## Endpoints implementados

### Vehicle Sessions

- `GET /vehicle-sessions`
- `GET /vehicle-sessions/active`
- `GET /vehicle-sessions/{session_id}`
- `GET /vehicle-sessions/{session_id}/history`
- `GET /vehicle-sessions/{session_id}/operational-summary`
- `POST /vehicle-sessions/{session_id}/cancel`
- `GET /vehicle-sessions/{session_id}/load-serials/selected?product_id=...`
- `PUT /vehicle-sessions/{session_id}/load-serials/select`
- `PUT /vehicle-sessions/{session_id}/load-serials/{assignment_id}/release`
- `GET /vehicle-sessions/{session_id}/carta-porte`
- `GET /vehicle-sessions/{session_id}/carta-porte/history`
- `GET /vehicle-sessions/{session_id}/route-operations`
- `GET /vehicle-sessions/{session_id}/route-incidents`
- `GET /vehicle-sessions/{session_id}/route-stop-results`
- `PUT /vehicle-sessions/{session_id}/route-stop-results/{route_stop_id}`
- `GET /vehicle-sessions/{session_id}/route-stop-progress`
- `GET /vehicle-sessions/{session_id}/composition/current`

### GET `/catalog/cylinder-states`

Permiso: `logistics.cylinder.read`

Response:

```json
[
  {
    "code": "CREADO_VACIO",
    "is_final": false,
    "description": "Cilindro nuevo registrado"
  }
]
```

### Catalogos

- `GET /catalog/cylinder-states`
- `GET /catalog/movement-types`
- `GET /catalog/task-types`
- `GET /catalog/warehouses`
- `GET /catalog/vehicles`
- `GET /catalog/delivery-points`
- `GET /catalog/zones`
- `GET /catalog/gas-products`
- `GET /catalog/brands`
- `GET /catalog/service-types`

### GET `/cylinders`

Permiso: `logistics.cylinder.read`

Query params opcionales:

- `search`
- `state`
- `active`

Response:

```json
[
  {
    "id": "uuid",
    "tenant_id": "uuid-string",
    "branch_id": "uuid-string|null",
    "serial": "GL-000001",
    "current_state": "CREADO_VACIO",
    "manufacturer_date": null,
    "manufacturer_code": null,
    "manufacture_year": null,
    "weight_origin": null,
    "weight_current": null,
    "last_hydrotest_date": null,
    "next_hydrotest_date": null,
    "adr_category": null,
    "adr_un_number": null,
    "adr_label": null,
    "location": "Almacen central",
    "is_active": true,
    "created_at": "2026-06-27T00:00:00Z",
    "updated_at": "2026-06-27T00:00:00Z"
  }
]
```

### POST `/cylinders`

Permiso: `logistics.cylinder.create`

Request:

```json
{
  "serial": "GL-000001",
  "location": "Almacen central",
  "next_hydrotest_date": "2027-06-27",
  "adr_category": "2F",
  "adr_un_number": "1047",
  "adr_label": "GLP"
}
```

Response: mismo contrato que `GET /cylinders/{id}`

### GET `/cylinders/summary`

Permiso: `logistics.cylinder.read`

Response:

```json
[
  { "state": "CREADO_VACIO", "count": 3 },
  { "state": "EN_ALMACEN_VACIO", "count": 5 }
]
```

### GET `/cylinders/allowed-transitions/{id}`

Permiso: `logistics.cylinder.read`

Response:

```json
[
  {
    "id": "uuid",
    "from_state": "CREADO_VACIO",
    "to_state": "EN_ALMACEN_VACIO",
    "requires_adr": false,
    "requires_hydrotest": false,
    "description": "Alta inicial"
  }
]
```

### GET `/cylinders/{id}`

Permiso: `logistics.cylinder.read`

Response: mismo contrato que el item de `GET /cylinders`

### GET `/cylinders/{id}/trace`

Permiso: `logistics.cylinder.trace`

Response:

```json
[
  {
    "id": 1,
    "tenant_id": "uuid-string",
    "cylinder_id": "uuid-string",
    "from_state": null,
    "to_state": "CREADO_VACIO",
    "changed_by": "uuid-string",
    "movement_id": null,
    "origin": "PLUGIN_CREATE",
    "reason_code": null,
    "notes": "Initial cylinder registration",
    "metadata_json": {},
    "created_at": "2026-06-27T00:00:00Z"
  }
]
```

### POST `/cylinders/{id}/transition`

Permiso: `logistics.cylinder.transition`

Request:

```json
{
  "to_state": "EN_ALMACEN_VACIO",
  "origin": "ALTA",
  "reason_code": null,
  "notes": "Ingreso a inventario",
  "metadata_json": {}
}
```

Errores de negocio:

- `400` si la transicion no existe
- `400` si el cilindro esta en estado final
- `400` si falta ADR cuando el destino lo requiere
- `400` si falta o vencio `next_hydrotest_date` cuando el destino lo requiere
- `404` si el cilindro no existe en el tenant actual

Response: mismo contrato que `GET /cylinders/{id}`

### GET/POST `/cylinders/{id}/hydrotests`

Permisos:

- lectura: `logistics.maintenance.read`
- escritura: `logistics.maintenance.manage`

`POST` actualiza `last_hydrotest_date` y `next_hydrotest_date` del cilindro.

### GET/POST `/cylinders/{id}/warranties`

Permisos:

- lectura: `logistics.maintenance.read`
- escritura: `logistics.maintenance.manage`

### Envase extendido

- `GET /cylinders/by-serial/{serial}`
- `PATCH /cylinders/{id}`
- `GET /cylinders/{id}/label-data`
- `GET|POST /cylinders/{id}/retimbrados`
- `GET /cylinders/{id}/ownership`
- `GET /cylinders/{id}/label-history`
- `POST /cylinders/{id}/print-label`
- `GET|POST /cylinders/{id}/services`
- `PATCH|DELETE /cylinders/{id}/services/{service_id}`

### Recursos operativos

- `GET|POST|PATCH /warehouses`
- `GET|POST /zones`
- `GET|POST|PATCH /vehicles`
- `GET|POST|PATCH /delivery-points`

### Pedidos

- `GET|POST /orders`
- `GET /orders/pending`
- `GET|PATCH /orders/{id}`
- `GET|POST /orders/{id}/items`
- `PATCH|DELETE /orders/{id}/items/{item_id}`

### Rutas y carga

- `GET|POST /routes`
- `GET|PATCH /routes/{id}`
- `POST /routes/{id}/start`
- `POST /routes/{id}/complete`
- `POST /routes/{id}/cancel`
- `GET|POST /routes/{id}/stops`
- `PATCH|DELETE /routes/{id}/stops/{stop_id}`
- `POST /routes/{id}/stops/{stop_id}/deliver`
- `POST /routes/{id}/agenda-tasks`
- `GET /loads?route_id={id}`
- `POST /loads`
- `POST /loads/bulk`
- `POST /loads/confirm`
- `DELETE /loads/{id}`

### Movimientos

- `GET|POST /movements`
- `GET|PATCH /movements/{id}`
- `POST /movements/{id}/confirm`
- `POST /movements/{id}/cancel`
- `GET /movements/{id}/items`
- `GET /movements/{id}/history`

### Agenda

- `GET|POST /agenda/tasks`
- `GET /agenda/tasks/by-driver/{driver_id}`
- `GET|PATCH /agenda/tasks/{id}`
- `POST /agenda/tasks/{id}/complete`
- `POST /agenda/tasks/{id}/cancel`

### Escaneo movil

- `POST /scan`
- `GET /scan/log`
- `GET /scan/log/{movement_id}`

## Notas

- todos los endpoints son tenant-aware;
- todas las acciones relevantes generan auditoria en `audit_logs`;
- todos los eventos del plugin se persisten via `event_log` y `event_outbox`;
- este contrato ya cubre el corte actual de `cylinders + envase completo + resources + orders + routes + loads + movements + agenda + scan`.
