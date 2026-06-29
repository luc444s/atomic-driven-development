# Avance: Módulo Logistics

## Propósito

Documentar el estado actual del módulo logistics (`plugins/logistics/`) frente al legacy (`modulo_logistica/`), sus capacidades, gaps funcionales y plan de cierre.

## Actualización 2026-06-29

- `SPEC 0014` ya no debe leerse como trabajo pendiente: sus módulos fueron implementados en `plugins/logistics/`.
- Este documento todavía conserva parte del inventario previo a esa implementación y requiere una pasada de normalización posterior para recalcular conteos, endpoints y cobertura exacta.
- Para el estado funcional más reciente, tomar como referencia inmediata `plugins/logistics/README.md` y `docs/specs/core/0014-logistics-complete/index.md`.

## Nota de alineación con `productos`

- `lg_gas_products` y `lg_brands` siguen existiendo en `logistics` porque forman parte del estado implementado actual.
- No son el destino arquitectónico final del catálogo.
- Desde ADR 0015 y SPEC 0015, ambos catálogos quedan definidos como estructuras transitorias de coexistencia.
- El destino final es migrar hacia `prod_products` y `prod_brands` del plugin `productos`.
- Mientras esa migración no ocurra, `logistics` puede seguir operando con `lg_gas_products` y `lg_brands`.
- Cualquier nuevo diseño o cambio relevante en `logistics` debe asumir que:
  - `product_id` será la referencia maestra futura a `prod_products`;
  - `product_name` puede sobrevivir solo como snapshot transaccional de lectura;
  - precios y costos no deben consolidarse en `logistics`, porque su ownership final vive en `productos`.
- `SPEC 0014` fue implementada; esta nota histórica describe el estado anterior del módulo antes de ese cierre.

---

## 1. Estado del módulo actual

### Identidad

| Propiedad | Valor |
|---|---|
| Plugin ID | `logistics` |
| Versión | `0.3.0` |
| Dependencias | `crm` |
| Backend entrypoint | `backend.plugin:register` |
| Frontend entrypoint | `frontend/register.ts` |

### Base de datos: 18 tablas (`lg_*`)

#### Modelos de cilindro

| Tabla | Propósito | Columnas clave |
|---|---|---|
| `lg_cylinder_states` | Catálogo de estados (18) | `code` (PK), `is_final`, `description` |
| `lg_state_transitions` | Transiciones permitidas (31) | `from_state`, `to_state`, `requires_adr`, `requires_hydrotest` |
| `lg_cylinders` | Entidad principal de envase | `serial` (único x tenant), `current_state` (FK), `barcode1`, `barcode2`, `gas_group_id`, `content_kg`, `condition`, `brand_id`, `adr_*` (9 campos), `last_hydrotest_date`, `next_hydrotest_date`, `weight_origin`, `weight_current`, `is_active` |
| `lg_cylinder_state_log` | Trazabilidad de cambios de estado | `cylinder_id`, `from_state`, `to_state`, `movement_id`, `origin`, `reason_code`, `metadata_json` (JSON) |

#### Sub-entidades de cilindro

| Tabla | Propósito | Columnas clave |
|---|---|---|
| `lg_hydrostatic_tests` | Pruebas hidrostáticas (PH) | `cylinder_id`, `test_date`, `previous_test_date`, `status`, `movement_id` |
| `lg_cylinder_warranties` | Garantías comerciales | `cylinder_id`, `customer_id` (FK), `customer_name`, `warranty_type`, `status`, `return_date` |
| `lg_cylinder_retimbrados` | Retimbrados (datos técnicos) | `cylinder_id`, `retimbrado_date`, `manufacture_code`, `weight_origin`, `weight_current`, `service_pressure`, `test_pressure`, `approval_number`, `danger_class`, `marking1`, `marking2`, `package_format`, `transport_code`, `adr_label`, `adr_tunnel`, `un_number`, `food_registry`, `movement_id` |
| `lg_cylinder_ownership` | Historial de propiedad/custodia | `cylinder_id`, `customer_id` (FK), `customer_name`, `movement_id`, `change_date`, `condition` |
| `lg_cylinder_label_history` | Historial de impresión de etiquetas | `cylinder_id`, `origin`, `reason`, `printer_name`, `copies`, `printed_by` |
| `lg_cylinder_services` | Servicios/mantenimiento | `cylinder_id`, `service_type_id`, `status`, `start_date`, `end_date`, `purchase_price`, `sale_price` |

#### Tablas catálogo

| Tabla | Propósito |
|---|---|
| `lg_gas_products` | Productos de gas (GLP10, GLP15, GLP45). Catálogo transitorio; destino final: `productos.prod_products` con `condition_code = 'GAS'` |
| `lg_brands` | Marcas de cilindros (GENERICA, INDURA, SOLYGAS). Catálogo transitorio; destino final: `productos.prod_brands` |
| `lg_cylinder_conditions` | Condiciones (CILPRO, CILCLI, CILPROV, CILGAR) |
| `lg_service_types` | Tipos de servicio (RETIMBRADO, VALVULA, PINTURA, INSPECCION) |
| `lg_movement_types` | Tipos de movimiento (SC, IC, IP, SP, TR, MV) |
| `lg_agenda_task_types` | Tipos de tarea (ENTREGA, RECOJO, SERVICIO, VISITA, COBRO) |

#### Modelos operacionales

| Tabla | Propósito | Columnas clave |
|---|---|---|
| `lg_warehouses` | Almacenes | `name`, `code`, `address`, `is_active` |
| `lg_zones` | Zonas geográficas | `name`, `code`, `is_active` |
| `lg_vehicles` | Vehículos | `plate` (único), `vehicle_type`, `brand`, `model`, `capacity_weight`, `capacity_volume`, `useful_load`, `adr_class`, `status` (default DISPONIBLE), `warehouse_id` |
| `lg_delivery_points` | Puntos de entrega de clientes | `customer_id` (FK crm), `customer_name`, `contact_name`, `contact_email`, `address`, `phone`, `zone_id`, `warehouse_id`, `visit_day`, `time_window`, `instructions`, `delivery_day`, `gps_link` |

#### Modelos de orden, ruta, carga

| Tabla | Propósito | Columnas clave |
|---|---|---|
| `lg_orders` | Pedidos de clientes | `customer_id` (FK), `customer_name`, `movement_type`, `status` (default PENDIENTE) |
| `lg_order_items` | Líneas de pedido | `product_id`, `quantity_requested`, `quantity_planned`, `status` |
| `lg_routes` | Rutas de reparto | `route_date`, `driver_id`, `vehicle_id`, `status` (default PLANIFICADO) |
| `lg_route_stops` | Paradas de ruta | `delivery_point_id`, `stop_order`, `scheduled_time`, `status` (default PENDIENTE), `arrival_time`, `departure_time` |
| `lg_loads` | Carga de cilindros en ruta | `cylinder_id`, `route_id`, `stop_id`, `status` (default ASIGNADO), `loaded_at` |

#### Modelos de movimiento

| Tabla | Propósito | Columnas clave |
|---|---|---|
| `lg_movements` | Movimientos de inventario | `movement_type` (FK), `customer_id` (FK), `customer_name`, `warehouse_id`, `driver_id`, `vehicle_id`, `status`, `order_id`, `route_id`, `parent_movement_id` |
| `lg_movement_items` | Líneas de movimiento | `cylinder_id`, `quantity_in`, `quantity_out`, `state_before`, `state_after` |
| `lg_movement_status_history` | Historial de cambios de estado | `movement_id`, `field_name`, `from_value`, `to_value` |

#### Modelos de agenda y escaneo

| Tabla | Propósito | Columnas clave |
|---|---|---|
| `lg_agenda_tasks` | Tareas diarias | `route_id`, `driver_id`, `customer_id` (FK), `customer_name`, `task_type` (FK), `status` (default PROGRAMADO), `scheduled_date`, `scheduled_time`, `gps_coordinates` (JSON) |
| `lg_scan_log` | Auditoría de escaneo | `movement_id`, `cylinder_id`, `barcode_scanned`, `service_type`, `gps_lat`, `gps_lng`, `result`, `adr_validated`, `hydrotest_validated` |

### API: ~84 endpoints

#### Catálogos (11 endpoints GET)

| Path | Permiso |
|---|---|
| `/catalog/cylinder-states` | `logistics.cylinder.read` |
| `/catalog/movement-types` | `logistics.movement.read` |
| `/catalog/task-types` | `logistics.agenda.read` |
| `/catalog/warehouses` | `logistics.warehouse.read` |
| `/catalog/vehicles` | `logistics.vehicle.read` |
| `/catalog/delivery-points` | `logistics.route.read` |
| `/catalog/zones` | `logistics.warehouse.read` |
| `/catalog/conditions` | `logistics.cylinder.read` |
| `/catalog/gas-products` | `logistics.gas.read` |
| `/catalog/brands` | `logistics.brand.read` |
| `/catalog/service-types` | `logistics.service.read` |

#### Cilindros (21 endpoints)

| Método | Path | Permiso | Descripción |
|---|---|---|---|
| GET | `/cylinders` | cylinder.read | Listar con filtros (search, state, active) |
| POST | `/cylinders` | cylinder.create | Crear (201) |
| GET | `/cylinders/summary` | cylinder.read | Conteo por estado |
| GET | `/cylinders/allowed-transitions/{id}` | cylinder.read | Transiciones permitidas |
| GET | `/cylinders/by-serial/{serial}` | cylinder.read | Búsqueda por serial/barcode |
| GET | `/cylinders/{id}` | cylinder.read | Detalle |
| PATCH | `/cylinders/{id}` | cylinder.update | Actualizar |
| GET | `/cylinders/{id}/trace` | cylinder.trace | Trazabilidad de estado |
| GET | `/cylinders/{id}/label-data` | label.read | Datos para etiqueta |
| GET | `/cylinders/{id}/retimbrados` | retimbrado.read | Listar retimbrados |
| POST | `/cylinders/{id}/retimbrados` | retimbrado.manage | Crear retimbrado (201) |
| GET | `/cylinders/{id}/ownership` | ownership.read | Historial de propiedad |
| GET | `/cylinders/{id}/label-history` | label.read | Historial de etiquetas |
| POST | `/cylinders/{id}/print-label` | label.print | Registrar impresión (201) |
| GET | `/cylinders/{id}/services` | service.read | Listar servicios |
| POST | `/cylinders/{id}/services` | service.manage | Crear servicio (201) |
| PATCH | `/cylinders/{id}/services/{sid}` | service.manage | Actualizar servicio |
| DELETE | `/cylinders/{id}/services/{sid}` | service.manage | Eliminar servicio (204) |
| GET | `/cylinders/{id}/hydrotests` | maintenance.read | Listar hidrotests |
| POST | `/cylinders/{id}/hydrotests` | maintenance.manage | Crear hidrotest (201) |
| GET | `/cylinders/{id}/warranties` | maintenance.read | Listar garantías |
| POST | `/cylinders/{id}/warranties` | maintenance.manage | Crear garantía (201) |
| POST | `/cylinders/{id}/transition` | cylinder.transition | Cambio de estado |

#### Almacenes, Zonas, Vehículos, Puntos de Entrega (11 endpoints)

| Método | Path | Permiso | Descripción |
|---|---|---|---|
| GET/POST | `/warehouses` | warehouse.read/manage | CRUD |
| PATCH | `/warehouses/{id}` | warehouse.manage | Actualizar |
| GET/POST | `/zones` | warehouse.read/manage | CRUD |
| GET/POST | `/vehicles` | vehicle.read/manage | CRUD |
| PATCH | `/vehicles/{id}` | vehicle.manage | Actualizar |
| GET/POST | `/delivery-points` | route.read/manage | CRUD |
| PATCH | `/delivery-points/{id}` | route.manage | Actualizar |

#### Órdenes (9 endpoints)

| Método | Path | Permiso |
|---|---|---|
| GET | `/orders` | order.read |
| GET | `/orders/pending` | order.read |
| GET | `/orders/{id}` | order.read |
| GET | `/orders/{id}/items` | order.read |
| POST | `/orders` | order.create |
| PATCH | `/orders/{id}` | order.manage |
| POST | `/orders/{id}/items` | order.manage |
| PATCH | `/orders/{id}/items/{item_id}` | order.manage |
| DELETE | `/orders/{id}/items/{item_id}` | order.manage |

#### Rutas (13 endpoints)

| Método | Path | Permiso |
|---|---|---|
| GET | `/routes` | route.read |
| GET | `/routes/{id}` | route.read |
| GET | `/routes/{id}/stops` | route.read |
| POST | `/routes` | route.manage |
| PATCH | `/routes/{id}` | route.manage |
| POST | `/routes/{id}/start` | route.manage |
| POST | `/routes/{id}/complete` | route.manage |
| POST | `/routes/{id}/cancel` | route.manage |
| POST | `/routes/{id}/stops` | route.manage |
| PATCH | `/routes/{id}/stops/{stop_id}` | route.manage |
| DELETE | `/routes/{id}/stops/{stop_id}` | route.manage |
| POST | `/routes/{id}/stops/{stop_id}/deliver` | route.manage |
| POST | `/routes/{id}/agenda-tasks` | agenda.manage |

#### Carga (5 endpoints)

| Método | Path | Permiso |
|---|---|---|
| GET | `/loads` | load.manage |
| POST | `/loads` | load.manage |
| POST | `/loads/bulk` | load.manage |
| POST | `/loads/confirm` | load.manage |
| DELETE | `/loads/{id}` | load.manage |

#### Movimientos (8 endpoints)

| Método | Path | Permiso |
|---|---|---|
| GET | `/movements` | movement.read |
| GET | `/movements/{id}` | movement.read |
| GET | `/movements/{id}/items` | movement.read |
| GET | `/movements/{id}/history` | movement.read |
| POST | `/movements` | movement.create |
| PATCH | `/movements/{id}` | movement.create |
| POST | `/movements/{id}/confirm` | movement.confirm |
| POST | `/movements/{id}/cancel` | movement.confirm |

#### Escaneo (3 endpoints)

| Método | Path | Permiso |
|---|---|---|
| POST | `/scan` | scan.execute |
| GET | `/scan/log` | scan.read |
| GET | `/scan/log/{movement_id}` | scan.read |

#### Agenda (7 endpoints)

| Método | Path | Permiso |
|---|---|---|
| GET | `/agenda/tasks` | agenda.read |
| GET | `/agenda/tasks/by-driver/{driver_id}` | agenda.read |
| GET | `/agenda/tasks/{id}` | agenda.read |
| POST | `/agenda/tasks` | agenda.manage |
| PATCH | `/agenda/tasks/{id}` | agenda.manage |
| POST | `/agenda/tasks/{id}/complete` | agenda.manage |
| POST | `/agenda/tasks/{id}/cancel` | agenda.manage |

### Frontend: 10 páginas, 1 widget

| Ruta | Página | Funcionalidad |
|---|---|---|
| `/logistics` | `LogisticsPage.tsx` (1575 líneas) | Panel principal de cilindros: resumen por estado, tabla de cilindros, búsqueda, detalle con 10 sub-secciones, formularios CRUD |
| `/logistics/orders` | `OrdersPage.tsx` (306 l) | Lista de pedidos + detalle con líneas, crear pedido con búsqueda de cliente CRM |
| `/logistics/routes` | `RoutesPage.tsx` (308 l) | Lista de rutas + detalle con paradas, crear/iniciar/completar ruta |
| `/logistics/loads` | `LoadsPage.tsx` (179 l) | Asignación de cilindros a ruta, confirmar carga |
| `/logistics/movements` | `MovementsPage.tsx` (302 l) | Lista de movimientos + items + historial, crear/confirmar/cancelar |
| `/logistics/agenda` | `AgendaPage.tsx` (174 l) | Tareas de agenda, crear/completar con búsqueda de cliente CRM |
| `/logistics/delivery-points` | `DeliveryPointsPage.tsx` (261 l) | Puntos de entrega con búsqueda de cliente CRM |
| `/logistics/vehicles` | `VehiclesPage.tsx` (190 l) | CRUD de vehículos |
| `/logistics/warehouses` | `WarehousesPage.tsx` (218 l) | CRUD de almacenes + zonas |
| Dashboard | `LogisticsSummaryWidget.tsx` (36 l) | Widget de resumen de estados en dashboard principal |

### Alineación documental pendiente

- `SPEC 0012` describe el estado implementado del envase completo y por eso todavía referencia `lg_gas_products` y `lg_brands` como FKs actuales.
- Esa referencia describe el presente técnico, no el destino final del dominio de productos.
- `SPEC 0014` documenta trabajo pendiente y no iniciado; cuando se retome, debe rebastarse contra ADR 0015 y SPEC 0015 de `productos` antes de implementarse.

### Máquina de estados: 18 estados, 31 transiciones

#### Estados finales (bloqueados)
`BLOQUEADO`, `OBSERVADO`, `DE_BAJA`, `PERDIDO`

#### Todos los estados
| Código | Etiqueta | Final |
|---|---|---|
| `CREADO_VACIO` | Nuevo | No |
| `EN_ALMACEN_VACIO` | Disponible | No |
| `EN_LLENADO` | En llenado | No |
| `LLENADO_OK` | Listo | No |
| `CARGA_EN_VEHICULO` | Cargado | No |
| `EN_RUTA` | En camino | No |
| `EN_CLIENTE_LLENO` | En cliente | No |
| `EN_CLIENTE_VACIO` | Por devolver | No |
| `VACIO_EN_ALMACEN` | Devuelto | No |
| `DESCARGADO_POR_RECEPCIONAR` | Pendiente | No |
| `RECEPCIONADO` | Recibido | No |
| `EN_MANTENIMIENTO` | Mantenimiento | No |
| `PARA_REPARACION` | Reparacion | No |
| `PARA_TRASLADO` | Traslado | No |
| `BLOQUEADO` | Bloqueado | Sí |
| `OBSERVADO` | Observado | Sí |
| `DE_BAJA` | Baja | Sí |
| `PERDIDO` | Perdido | Sí |

#### Reglas de transición
- **ADR required**: `EN_ALMACEN_VACIO -> LLENADO_OK` (requiere `adr_category`, `adr_un_number`, `adr_label`)
- **Hydrotest required**: `EN_ALMACEN_VACIO -> LLENADO_OK` (requiere `next_hydrotest_date >= today`)
- **Estados finales**: no permiten transiciones salientes
- **Auto-transición**: no permitida (mismo estado)

### Eventos del sistema: 22 eventos emitidos

| Evento | Disparador |
|---|---|
| `logistics.cylinder.created` | Creación de cilindro |
| `logistics.cylinder.updated` | Actualización de cilindro |
| `logistics.cylinder.state_changed` | Transición de estado |
| `logistics.cylinder.hydrotest_registered` | Registro de PH |
| `logistics.cylinder.retimbrado_registered` | Registro de retimbrado |
| `logistics.cylinder.label_printed` | Impresión de etiqueta |
| `logistics.cylinder.ownership_changed` | Cambio de propiedad |
| `logistics.cylinder.scanned` | Escaneo de código |
| `logistics.cylinder.service_registered` | Creación de servicio |
| `logistics.cylinder.service_completed` | Servicio completado |
| `logistics.order.created` | Creación de pedido |
| `logistics.order.updated` | Actualización de pedido |
| `logistics.route.created` | Creación de ruta |
| `logistics.route.started` | Inicio de ruta |
| `logistics.route.completed` | Finalización de ruta |
| `logistics.load.assigned` | Asignación de carga |
| `logistics.load.prepared` | Confirmación de carga |
| `logistics.movement.created` | Creación de movimiento |
| `logistics.movement.completed` | Confirmación de movimiento |
| `logistics.movement.cancelled` | Cancelación de movimiento |
| `logistics.agenda.task_completed` | Tarea de agenda completada |
| `logistics.warranty.created` | Creación de garantía |

### Permisos: 31 permisos

| Permiso | Uso |
|---|---|
| `logistics.cylinder.read` | Ver cilindros, estados, transiciones |
| `logistics.cylinder.create` | Crear cilindros |
| `logistics.cylinder.update` | Actualizar cilindros |
| `logistics.cylinder.transition` | Cambiar estado |
| `logistics.cylinder.trace` | Ver trazabilidad |
| `logistics.order.read` | Ver pedidos |
| `logistics.order.create` | Crear pedidos |
| `logistics.order.manage` | Gestionar pedidos |
| `logistics.route.read` | Ver rutas, puntos de entrega |
| `logistics.route.manage` | CRUD rutas, iniciar/completar |
| `logistics.load.manage` | Gestionar cargas |
| `logistics.movement.read` | Ver movimientos |
| `logistics.movement.create` | Crear movimientos |
| `logistics.movement.confirm` | Confirmar/cancelar movimientos |
| `logistics.warehouse.read` | Ver almacenes, zonas |
| `logistics.warehouse.manage` | CRUD almacenes, zonas |
| `logistics.vehicle.read` | Ver vehículos |
| `logistics.vehicle.manage` | CRUD vehículos |
| `logistics.agenda.read` | Ver tareas de agenda |
| `logistics.agenda.manage` | CRUD/completar/cancelar tareas |
| `logistics.maintenance.read` | Ver hidrotests, garantías |
| `logistics.maintenance.manage` | Crear hidrotests, garantías |
| `logistics.retimbrado.read` | Ver retimbrados |
| `logistics.retimbrado.manage` | Crear retimbrados |
| `logistics.scan.execute` | Ejecutar escaneos |
| `logistics.scan.read` | Ver logs de escaneo |
| `logistics.label.print` | Imprimir etiquetas |
| `logistics.label.read` | Ver datos/historial de etiquetas |
| `logistics.ownership.read` | Ver historial de propiedad |
| `logistics.service.read` | Ver servicios |
| `logistics.service.manage` | CRUD servicios |
| `logistics.gas.read` | Ver catálogo de productos de gas |
| `logistics.brand.read` | Ver catálogo de marcas |

### Migraciones ejecutadas (6)

| Migración | Descripción |
|---|---|
| `001_initial.py` | Crea tablas base de cilindros + estados + transiciones + seed data |
| `002_phase_2_3.py` | Crea 14 tablas operacionales + seed de tipos de movimiento/tarea |
| `003_direct_return_transition.py` | Agrega transición EN_CLIENTE_VACIO -> EN_ALMACEN_VACIO |
| `004_envase_completo.py` | Agrega 22 columnas a cilindros + 8 tablas nuevas |
| `005_cylinder_conditions.py` | Crea lg_cylinder_conditions + migra columna condition a FK |
| `006_customer_refs.py` | Agrega 12 columnas a lg_delivery_points |

### Servicios backend (12 archivos)

| Archivo | Responsabilidad |
|---|---|
| `state_machine.py` | Validación de transiciones (ADR, PH, estados finales) |
| `cylinders.py` | CRUD de cilindros + cambios de estado |
| `catalog.py` | Catálogos + auto-seed por tenant |
| `movements.py` | Movimientos de inventario + confirmación + cancelación |
| `orders.py` | Pedidos + líneas de pedido |
| `routes.py` | Rutas + paradas + inicio/completar/entregar + generación de agenda |
| `loads.py` | Carga de cilindros en rutas |
| `resources.py` | CRUD almacenes, zonas, vehículos, puntos de entrega |
| `envase.py` | Retimbrados, propiedad, etiquetas, servicios de cilindro |
| `extras.py` | Hidrotests (+5 años), garantías |
| `scan.py` | Escaneo con validación (ADR, PH, duplicados) |
| `agenda.py` | CRUD de tareas de agenda |
| `common.py` | Contexto de acción, auditoría, eventos |

---

## 2. Análisis del legacy (`modulo_logistica/`)

### Fuente
- **Base de datos**: SQL Server (`ACONCAGUA.Sys_GMS_ES`)
- **Cliente**: VB6 WinForms
- **Reportes**: Crystal Reports (.rpt)
- **Capa de datos**: Clases DAL VB6 con ADO.NET
- **Alcance del análisis**: 12 documentos, 27 tablas, 4 triggers, 52 vistas, 135 SP, 14 funciones escalares, 6 TVP, ~24 formularios VB, ~9 clases DAL

### Dominios funcionales

| Dominio | Descripción | Estado en módulo actual |
|---|---|---|
| Planificación | Cálculo de stock, modos de planificar (todo/completo/parcial), generar precarga | ❌ No existe |
| Agenda Repartidor | Tareas con estados (Programado/EnCurso/Realizado/Cancelado), reprogramación, marcar cargado, resumen diario | ✅ Completo |
| Rutas | CRUD, schedule semanal, paradas ordenadas, restricciones vehículo | ⚠️ Parcial (sin schedule semanal, sin restricciones) |
| Carga Repartidor | Asignación de cilindros, validación de peso (5,000 kg máx), resumen de peso | ⚠️ Parcial (sin validación de peso) |
| Movimientos/Traslados | Transferencia entre almacenes, separación lleno/vacío, guías, despacho, recepción | ⚠️ Parcial (sin recepción con faltantes, sin guías) |
| Despacho | Registro, cierre, número de guía, retorno de vehículo con escáner | ⚠️ Parcial |
| Recepción | Procesar recepción, detección de faltantes (crea "FALTANTE NO TRANSFERIDO") | ❌ No existe |
| Ciclo de vida del cilindro | Trazabilidad de estados, PH, contenido/peso, consultas de disponibles | ✅ Completo |
| Incidencias | Registro con catálogo de motivos, transiciones a OBSERVADO/PARA_REPARACION | ⚠️ Básico (vía transiciones) |
| Vehículos y equipos | CRUD, restricciones por ruta, equipos por movimiento, choferes, parámetros de repartidor | ⚠️ Parcial (sin equipos, sin parámetros) |
| ADR (Mercancías Peligrosas) | Configuración de producto, cálculo de puntos, selección de vehículo, incompatibilidades | ⚠️ Básico (solo campos + validación PH) |
| Carta Porte | Generación de documento legal de transporte (cabecera, detalle, resumen) | ❌ No existe |
| Reportes | Crystal Reports: agenda de ruta, guía de despacho, albarán de traslado, carta porte, ADR | ❌ No existe |

### Bugs y riesgos conocidos del legacy (18 documentados)

| ID | Riesgo | Gravedad |
|---|---|---|
| R1 | Recursión infinita en `ExisteAgendaAbierta()` | Crítico |
| R2 | Credenciales `sa`/`password` hardcodeadas en todos los .rpt | Crítico |
| R3 | SQL directo sobre ECilindroEstadoLog/Actual en FrmRecepcion | Crítico |
| R4 | GPS siempre (0,0) — implementación stub | Crítico |
| R5 | `sp_CargaRepartidor_Eliminar` no existe en BD | Crítico |
| R6 | UPDATE directo en DetalleMovimiento desde forms | Alto |
| R7 | Sin transacción en btnGenerarAgenda | Alto |
| R8 | Criterios de listado de choferes inconsistentes | Alto |
| R9 | Conexiones SQL sin cerrar en GetADRInfo | Alto |
| R10 | 5 formularios de planificación duplicados | Alto |
| R11 | 17 consultas SQL inline en FrmAgendaRepartidor | Medio |
| R12 | cboAlmacen_SelectedIndexChanged vacío | Medio |
| R13 | FrmRepartoSuc accede a controles de otro form | Medio |
| R14 | ~30-40% código comentado | Medio |
| R15 | Sin logging centralizado (MsgBox everywhere) | Medio |
| R16 | Label7 muestra texto de SP al usuario | Bajo |
| R17 | ComboBox items hardcodeados luego sobrescritos | Bajo |
| R18 | Variable global `objcn` — riesgo de acceso concurrente | Bajo |

---

## 3. Comparativa: Módulo actual vs Legacy

### Lo que el módulo actual tiene y el legacy no

- Integración con CRM (FK reales a `crm_customers`)
- API REST moderna con 31 permisos granulares
- Arquitectura de eventos (22 eventos)
- Auditoría completa por operación
- Multi-tenancy nativo (`tenant_id` en todas las tablas)
- Historial de retimbrados con 18 campos técnicos
- Servicios de cilindro (mantenimiento, reparaciones)
- Historial de impresión de etiquetas
- Catálogo de marcas, productos de gas, condiciones, tipos de servicio
- Escaneo con validación de ADR + PH + duplicados
- Frontend moderno (React + TypeScript + TanStack Query + shadcn/ui)

### Gaps funcionales

| # | Funcionalidad Legacy | Impacto | Estado |
|---|---|---|---|
| 1 | **Planificación** — cálculo de stock disponible, modos de planificar (todo/completo/parcial), generar precarga | **Alto** — operación diaria crítica | ❌ No existe |
| 2 | **Recepción** — procesar recepción con detección de faltantes (crea línea "FALTANTE NO TRANSFERIDO") | **Alto** — operación diaria crítica | ❌ No existe |
| 3 | **Carta Porte** — documento legal para transporte terrestre | **Alto** — requisito legal/fiscal en Perú | ❌ No existe |
| 4 | **Reportes imprimibles** — agenda de ruta, guía de despacho, albarán de traslado, carta porte | **Alto** — necesario para operación diaria | ❌ No existe |
| 5 | **Equipos por movimiento** — bombas, mangueras, etc. asignados a movimientos | **Medio** | ❌ No existe |
| 6 | **Restricciones vehículo-ruta** | **Medio** | ❌ No existe |
| 7 | **Parámetros de repartidor** — configuración por chofer | **Bajo** | ❌ No existe |
| 8 | **Vinculación vehículo-cliente** — puntos de entrega por vehículo | **Bajo** | ❌ No existe |
| 9 | **Resumen diario de agenda** | **Bajo** | ❌ No existe |
| 10 | **Módulo ADR completo** — cálculo de puntos, selección de vehículo, incompatibilidades | **Bajo** (depende del negocio) | ❌ No existe |
| 11 | **GPS** — registro de coordenadas en ruta (aunque legacy es un stub) | **Bajo** | ❌ No existe |

### Conclusión: ~75% del legacy cubierto

El módulo actual es funcional y operativo para el núcleo de logística:

- ✅ Gestión de cilindros (CRUD + trazabilidad + PH + retimbrados + servicios + etiquetas)
- ✅ Movimientos de inventario (ingreso/salida/traslado con confirmación)
- ✅ Pedidos (creación + líneas + planificación de cantidades)
- ✅ Rutas (creación + paradas + carga + inicio + entrega + completado)
- ✅ Agenda (tareas + tipos + completado + cancelación)
- ✅ Escaneo (validación ADR + PH + duplicados + GPS)
- ✅ Puntos de entrega (CRUD con integración CRM)
- ✅ Almacenes, Zonas, Vehículos (CRUD)

Los gaps más críticos son **4 módulos** que requieren construcción:

| Módulo | ¿Dónde va? | ¿Qué hace? |
|---|---|---|
| **Planificación** | `logistics/services/planning.py` | Calcula stock disponible, modos de planificar genera precarga |
| **Recepción** | `logistics/services/reception.py` | Procesa recepción, detecta faltantes, completa el ciclo de movimiento |
| **Carta Porte** | `logistics/services/waybill.py` | Genera documento legal con datos de movimiento + cliente + ruta |
| **Reportes** | `logistics/services/reports.py` | Endpoints que devuelven datos estructurados para impresión |

Todos deben implementarse **dentro del plugin logistics** como submódulos, no como plugins separados, por el alto acoplamiento de datos con las tablas existentes.

---

## 4. Plan de acción propuesto

### Prioridad 1: Planificación
- Crear `services/planning.py`
- Endpoints: cálculo de stock, modos de planificar, generar precarga
- Usa `lg_order_items.quantity_planned`, catálogo de productos, stock por almacén

### Prioridad 2: Recepción
- Crear `services/reception.py`
- Extiende flujo de confirmación de movimiento
- Detecta faltantes y crea líneas de "NO TRANSFERIDO"
- Actualiza estado de movimiento a RECEPCIONADO

### Prioridad 3: Carta Porte
- Crear `services/waybill.py`
- Endpoint que genera datos estructurados (cabecera + detalle + resumen)
- Usa datos de `lg_movements` + `crm_customers` + `lg_routes`

### Prioridad 4: Reportes
- Crear `services/reports.py`
- Endpoints que devuelven datos para impresión (agenda de ruta, guía de despacho, albarán, carta porte)
- El renderizado a PDF se hace desde el frontend o servicio externo

---

## 5. Historial de cambios

| Fecha | Cambio |
|---|---|
| 2026-06-28 | Creación del documento con análisis completo del módulo logistics actual vs legacy |
