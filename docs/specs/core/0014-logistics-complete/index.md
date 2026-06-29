# SPEC 0014 — Logistics: Módulos Pendientes (Actualizada)

## Estado

**Versión actualizada** — 2026-06-29. Refleja la existencia de `plugins/stock/`, `plugins/productos/`, claims `warehouse_id` y `lg_warehouses.branch_id`. Pendiente de implementación.

## Contexto

El plugin `logistics` (v0.3.0) implementa el núcleo operativo de logística: gestión de cilindros, movimientos, rutas, carga, agenda, escaneo y catálogos. Sin embargo, el análisis comparativo contra el legacy (`docs/avances/logistics.md`) identificó **15 módulos faltantes** para alcanzar paridad funcional.

El legacy (`modulo_logistica/`) opera sobre SQL Server con 27 tablas, 135 SP, 52 vistas, 24 formularios VB6 y Crystal Reports. El módulo actual corre sobre PostgreSQL con **29 tablas**, **~89 endpoints REST**, **22 eventos** y frontend React.

Esta spec describe **los 15 módulos pendientes** con especificaciones detalladas para cada uno. No son features opcionales — todos son necesarios para reemplazar el legacy en producción.

## Nota de estado

- Esta spec fue actualizada para reflejar el ecosistema actual del proyecto: `plugins/stock/` ya existe, `plugins/productos/` ya existe, claims `warehouse_id` están implementados en core, `lg_warehouses` tiene `branch_id`.
- Cualquier referencia a producto debe usar `prod_products` (`plugins/productos/`), no `lg_gas_products`.
- La planificación debe consumir `stk_balance` del plugin stock, no contar cilindros por estado manualmente.
- Toda operación nueva debe respetar claims `warehouse_id` (alcance por almacén).
- Toda tabla nueva multi-almacén debe considerar `branch_id` derivado.
- Esta spec queda cerrada para implementación con una decisión explícita: `stk_balance` mantiene solo stock real; `StockComprometido` y `StockPlanificado` viven en `logistics` y se derivan por query, no por columnas nuevas en `stock`.
- La integración `logistics` -> `stock` para cambios de stock real se hace por llamada directa de servicio Python con idempotencia, no por subscribers de eventos.

## No objetivos

- Reescribir lógica defectuosa del legacy (bugs R1-R18 documentados); la nueva implementación debe corregir esos problemas.
- Construir UI de reportes imprimibles (el renderizado PDF se define aparte).
- Integración con SUNAT para validación de Carta Porte en tiempo real.
- Módulo de facturación o finanzas (dependen de CRM + logistics pero tienen su propia spec).

---

## 1. Planificación

### 1.1 Objetivo

Implementar el módulo de planificación de operaciones que permita calcular stock disponible (consumiendo `stk_balance` del plugin stock), asignar cantidades planificadas a pedidos, generar precargas y preparar la agenda del repartidor. Es el módulo más crítico del legacy (~20,000 líneas en FrmMovPlanificacionOperaciones).

### 1.2 Alcance

- Cálculo de stock disponible por producto y almacén (desde `stk_balance`)
- Tres modos de planificar: todo, completos, parciales
- Modo overbooking (planificar sin stock suficiente)
- Generación de precarga (cabecera + detalle)
- Aceptar precarga y auto-generar traslado
- Planificación CILPRO vs pedidos normales
- Indicador visual de 3 colores (verde/amarillo/rojo) por nivel de stock
- Respetar claims `warehouse_id` (alcance por almacén)

### 1.3 Riesgos

- El legacy tiene 5 formularios de planificación duplicados; debe consolidarse en uno solo.
- La lógica de stock es sensible: errores causan sobreventa o sub-asignación.
- La generación de precarga debe validar que no exista una precarga activa para la misma fecha/almacén.
- El cálculo de `StockComprometido` y `StockPlanificado` será derivado por query; requiere índices adecuados para no degradar listados masivos.

### 1.4 Reglas de negocio

- `StockDisponible = stk_balance.quantity - StockComprometido - StockPlanificado`
- `StockComprometido` = suma de `lg_order_items.quantity_planned` donde order.status en (`PENDIENTE`, `PLANIFICADO`) y la línea aún no fue consumida por despacho
- `StockPlanificado` = suma de `lg_plan_preload_items.quantity_planned` donde preload.status = `PENDIENTE`
- `CantPlanificada` no puede exceder `CantPendiente` (salvo overbooking explícito)
- Overbooking requiere flag explícito (`permitir_sin_stock`)
- Solo una precarga activa por fecha y almacén
- Precarga tiene estados: `PENDIENTE`, `ACEPTADA`, `CANCELADA`
- Al aceptar precarga, auto-generar movimiento de traslado si aplica
- Aceptar una precarga no modifica `stk_balance`; solo crea el movimiento logístico y reserva operativa en `logistics`
- Todos los endpoints filtran por `allowed_warehouse_ids` del usuario autenticado

### 1.5 API endpoints propuestos

| Método | Path | Descripción | Claims |
|---|---|---|---|
| `GET` | `/planning/stock?warehouse_id=&product_id=` | Stock disponible (desde `stk_balance`) | Filtra por warehouse scope |
| `POST` | `/planning/stock/summary` | Resumen de stock para múltiples productos | Filtra por warehouse scope |
| `GET` | `/planning/pending-orders` | Pedidos pendientes con semáforo de stock | Filtra por warehouse scope |
| `POST` | `/planning/plan-order/{order_id}` | Planificar cantidades para un pedido | Valida warehouse scope |
| `POST` | `/planning/generate-preload` | Generar precarga | Valida warehouse scope |
| `GET` | `/planning/preloads` | Listar precargas | Filtra por warehouse scope |
| `GET` | `/planning/preloads/{id}` | Detalle de precarga | Valida warehouse scope |
| `POST` | `/planning/preloads/{id}/accept` | Aceptar precarga y generar traslado | Valida warehouse scope |
| `POST` | `/planning/preloads/{id}/cancel` | Cancelar precarga | Valida warehouse scope |

### 1.6 Tablas afectadas

- `lg_order_items` — campo `quantity_planned` (ya existe)
- Nueva `lg_plan_preloads` — cabecera de precarga:
  - `id`, `tenant_id`, `warehouse_id` (FK), **`branch_id`** (derivado del almacén), `date`, `status`, `created_by`, `created_at`
- Nueva `lg_plan_preload_items` — detalle de precarga:
  - `id`, `preload_id`, `order_item_id`, **`product_id` (FK a `prod_products.id`)**, `quantity_planned`, `quantity_loaded`

### 1.7 Decisiones de implementación

- `stk_balance` no recibe columnas `quantity_compromised` ni `quantity_planned`
- `StockComprometido` y `StockPlanificado` se calculan en queries SQL agregadas dentro de `services/planning.py`
- Crear índices para soportar esos agregados:
  - `lg_order_items (product_id, order_id)`
  - `lg_orders (warehouse_id, status)`
  - `lg_plan_preloads (warehouse_id, status, date)`
  - `lg_plan_preload_items (product_id, preload_id)`
- Crear constraint de unicidad para impedir más de una precarga activa por almacén/fecha:
  - unique parcial sobre `lg_plan_preloads (tenant_id, warehouse_id, date)` donde `status in ('PENDIENTE', 'ACEPTADA')`
- Si la migración no puede expresar ese índice parcial con el helper actual, validar también dentro de una transacción con `SELECT ... FOR UPDATE`
- La aceptación de precarga genera `lg_movements` y `lg_movement_items`, pero no toca stock real todavía

### 1.8 Eventos

- `logistics.planning.preload_generated` — emitido al crear precarga.
- `logistics.planning.preload_accepted` — emitido al aceptar precarga (incluye movimiento generado).

### 1.9 Criterios de aceptación

- [ ] Stock disponible se calcula desde `stk_balance` correctamente
- [ ] Modo completos solo planifica pedidos con stock total suficiente
- [ ] Modo parciales planifica hasta agotar stock
- [ ] Overbooking permite planificar más allá del stock disponible
- [ ] Generar precarga crea registro con estado PENDIENTE
- [ ] Aceptar precarga cambia estado a ACEPTADA y genera movimiento de traslado si aplica
- [ ] No se puede crear segunda precarga activa para misma fecha/almacén
- [ ] Indicador de 3 colores refleja correctamente el nivel de cobertura
- [ ] Endpoints filtran por warehouse scope del usuario
- [ ] Eventos emitidos incluyen `branch_id` derivado del almacén
- [ ] La planificación no modifica `stk_balance`

---

## 2. Recepción

### 2.1 Objetivo

Implementar el proceso de recepción de movimientos: confirmar recepción de cilindros, detectar faltantes, registrar incidencias y actualizar estados.

### 2.2 Alcance

- Listar movimientos pendientes de recepción por almacén destino
- Procesar recepción: cilindros recibidos vs esperados
- Detección y registro automático de faltantes
- Actualización de estado del movimiento a `RECEPCIONADO`
- Transición de cilindros de `DESCARGADO_POR_RECEPCIONAR` a `EN_ALMACEN_VACIO`
- Registro de incidencias con catálogo de motivos
- Historial de estado de traslado
- Actualización de stock real por producto en almacén destino

### 2.3 Riesgos

- El legacy hace SQL directo sobre `ECilindroEstadoLog` y `ECilindroEstadoActual` (bug R3). La nueva implementación debe usar el state machine existente.
- Los faltantes mal manejados causan discrepancias de inventario.
- La recepción parcial debe ser soportada (recibir menos de lo esperado).
- Al recepcionar, debe actualizarse `stk_balance` del almacén destino con idempotencia por movimiento/etapa.

### 2.4 Reglas de negocio

- Solo movimientos en estado `DESCARGADO_POR_RECEPCIONAR` pueden ser recepcionados
- Si `cantidadRecibida < cantidadEsperada`, crear línea "FALTANTE NO TRANSFERIDO"
- Los cilindros recibidos transicionan a `EN_ALMACEN_VACIO`
- El movimiento cambia a estado `RECEPCIONADO`
- Las incidencias registradas transicionan cilindros a `OBSERVADO` o `PARA_REPARACION` según el motivo
- El delta de stock real se calcula agregando `lg_movement_items.quantity_in` por `product_id`
- `lg_movement_items` debe conservar `product_id` como snapshot transaccional para evitar recalcular desde el cilindro en documentos y stock
- La recepción ejecuta una llamada directa al servicio de stock con `idempotency_key = movement_id + ':reception'`

### 2.5 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/reception/pending?warehouse_id=` | Movimientos pendientes de recepción |
| `GET` | `/reception/{movement_id}` | Detalle del movimiento para recepción |
| `POST` | `/reception/{movement_id}/receive` | Procesar recepción (lista de cilindros recibidos) |
| `POST` | `/reception/{movement_id}/incident` | Registrar incidencia durante recepción |
| `GET` | `/reception/incident-reasons` | Catálogo de motivos de incidencia |

### 2.6 Tablas afectadas

- `lg_movements` — actualizar estado a `RECEPCIONADO`
- `lg_movement_items` — agregar soporte para ítems "FALTANTE NO TRANSFERIDO" y snapshot `product_id` / `product_name`
- `lg_cylinder_state_log` — transiciones de estado
- `stk_balance` — incrementar stock del almacén destino al recepcionar (llamada directa idempotente)
- Nueva `lg_reception_incidents` — incidencias de recepción (id, movement_id, cylinder_id, reason_code, description, created_by)

### 2.7 Eventos

- `logistics.reception.completed` — emitido al recepcionar un movimiento. Payload: `{movement_id, warehouse_id, items_received, items_short, branch_id}`.

### 2.8 Decisiones de implementación

- `lg_movement_items.product_id` referencia `prod_products.id`
- `lg_movement_items.product_name` queda como snapshot de lectura para documentos
- Recepción actualiza stock real agregando por `product_id` y ejecutando ajustes idempotentes en stock
- Se considera "stock controlado" a todo producto con registro activo en `stk_config` para el `warehouse_id` afectado
- Si no existe `stk_config` para ese producto/almacén, recepción no altera `stk_balance` para esa línea
- Los movimientos de solo vacíos no incrementan stock vendible; solo incrementan para productos configurados como stock controlado en `stock`

### 2.9 Criterios de aceptación

- [ ] Lista solo movimientos pendientes de recepción para el almacén destino
- [ ] Recepción exitosa cambia estado del movimiento a RECEPCIONADO
- [ ] Cilindros recibidos transicionan a EN_ALMACEN_VACIO
- [ ] Si hay faltantes, se crean líneas "FALTANTE NO TRANSFERIDO" automáticamente
- [ ] Recepción parcial funciona correctamente
- [ ] Incidencias se registran con motivo del catálogo
- [ ] Historial de estado se actualiza en cada paso
- [ ] `stk_balance` se actualiza al recepcionar (incremento en almacén destino)
- [ ] Evento `logistics.reception.completed` emitido con `branch_id` derivado
- [ ] La operación es idempotente si se reintenta la misma recepción

---

## 3. Carta Porte

### 3.1 Objetivo

Implementar la generación del documento Carta Porte, requisito legal para el transporte terrestre de mercancías en Perú. El documento debe contener cabecera, detalle de productos y resumen con datos del remitente, destinatario y transportista.

### 3.2 Alcance

- Generar datos estructurados de Carta Porte a partir de un movimiento
- Cabecera: datos del movimiento, cliente, transportista, ruta, fechas
- Detalle: productos (desde `prod_products`), cantidades, pesos, bultos
- Resumen: totales, peso bruto, puntos ADR
- Endpoint que devuelve datos listos para renderizar (PDF u otro formato)
- Respetar claims `warehouse_id` (solo movimientos de almacenes permitidos)

### 3.3 Riesgos

- La Carta Porte tiene implicaciones legales y fiscales; los datos deben ser precisos.
- El renderizado a PDF está fuera del alcance de esta spec (se define aparte).
- Depende de datos de cliente (CRM) y transportista/vehículo (logistics).

### 3.4 Reglas de negocio

- Una Carta Porte se genera por movimiento de tipo SALIDA (SC, SP)
- Los datos del remitente son el almacén origen
- Los datos del destinatario son el cliente (desde CRM)
- Los datos del transportista son el chofer/vehículo asignado al movimiento
- El detalle incluye cada producto con cantidad, peso unitario y peso total
- El detalle se genera desde `lg_movement_items.product_id` + `product_name` snapshot, no recalculando desde cilindros en tiempo de lectura
- El resumen incluye total de bultos, peso bruto total y puntos ADR si aplica

### 3.5 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/waybill/{movement_id}` | Datos estructurados de Carta Porte para un movimiento |
| `GET` | `/waybill/{movement_id}/summary` | Resumen de Carta Porte |

### 3.6 Tablas afectadas

- `lg_movements` — datos del movimiento
- `lg_movement_items` — detalle de productos con snapshot `product_id` / `product_name`
- `crm_customers` — datos del cliente
- `lg_warehouses` — datos del almacén origen
- `lg_vehicles` — datos del vehículo/transportista
- Ninguna tabla nueva; endpoint de solo lectura

### 3.7 Decisiones de implementación

- Si un movimiento se crea desde cilindros, al persistir sus items se debe materializar `product_id` y `product_name`
- Carta Porte y reportes consumen ese snapshot transaccional para evitar inconsistencias futuras si cambia el catálogo
- El peso unitario se obtiene de `prod_products`; el nombre mostrado sale del snapshot del movimiento

### 3.8 Criterios de aceptación

- [ ] Carta Porte se genera para movimientos de tipo SC y SP
- [ ] Cabecera contiene remitente, destinatario, transportista correctos
- [ ] Detalle lista cada producto con cantidades y pesos
- [ ] Resumen calcula totales correctamente (bultos, peso bruto, ADR)
- [ ] Datos estructurados listos para renderizar
- [ ] El detalle no depende de recalcular cilindro -> producto en tiempo de consulta

---

## 4. Reportes

### 4.1 Objetivo

Crear endpoints que devuelvan datos estructurados para los reportes operativos del legacy. El renderizado a PDF se maneja aparte (frontend o servicio de reportes).

### 4.2 Alcance

- Reporte de agenda de ruta: paradas, cliente, producto, cantidad
- Ticket de guía de despacho
- Albarán de traslado entre almacenes
- Reporte de carga de repartidor
- Resumen de puntos ADR por movimiento

### 4.3 Riesgos

- El renderizado PDF está fuera del alcance; los endpoints devuelven JSON estructurado.
- Los formatos de reporte deben ser validados con usuarios operativos.

### 4.4 Reglas de negocio

- Reporte de agenda: agrupa por ruta, ordena por secuencia de parada
- Ticket de guía: datos del movimiento, cliente, productos, cantidades
- Albarán de traslado: almacén origen, destino, productos, cantidades
- Reporte de carga: cilindros asignados por repartidor, peso total
- ADR: cálculo de puntos por producto, suma por movimiento

### 4.5 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/reports/route-agenda/{route_id}` | Datos de agenda de ruta para impresión |
| `GET` | `/reports/dispatch-ticket/{movement_id}` | Ticket de guía de despacho |
| `GET` | `/reports/transfer-albaran/{movement_id}` | Albarán de traslado |
| `GET` | `/reports/load-summary/{route_id}` | Resumen de carga de repartidor |
| `GET` | `/reports/adr-summary/{movement_id}` | Resumen de puntos ADR |

### 4.6 Tablas afectadas

- Ninguna tabla nueva. Endpoints de solo lectura sobre tablas existentes.

### 4.7 Criterios de aceptación

- [ ] Todos los endpoints devuelven datos estructurados y completos
- [ ] Reporte de agenda ordena paradas por secuencia
- [ ] Ticket de guía incluye todos los datos del despacho
- [ ] Albarán de traslado muestra origen y destino correctos
- [ ] Resumen de carga calcula peso total por repartidor
- [ ] ADR calcula puntos correctamente

---

## 5. Guía de Despacho

### 5.1 Objetivo

Implementar el flujo de despacho: asignación de número de guía, cierre de despacho, recepción de despacho (vista de solo lectura) y retorno de vehículo.

### 5.2 Alcance

- Asignar número de guía a un movimiento
- Cerrar despacho (marcar como atendido)
- Vista de solo lectura de despacho recibido
- Retorno de vehículo con recepción de carga (escáner + carga masiva)

### 5.3 Riesgos

- La guía es un documento legal; la numeración debe ser secuencial y no reutilizable.
- El retorno de vehículo con escáner requiere soporte para carga masiva (TVP).

### 5.4 Reglas de negocio

- El número de guía se compone de serie + número correlativo por almacén/año
- Una vez cerrado, un despacho no puede modificarse
- El retorno de vehículo recibe cilindros y los transiciona a `DESCARGADO_POR_RECEPCIONAR`
- El escáner debe soportar carga masiva sin duplicados
- El descuento de stock real ocurre en `close-dispatch`, no en `vehicle-return`
- El delta de stock de despacho se calcula agregando `lg_movement_items.quantity_out` por `product_id`
- `vehicle-return` solo procesa retorno físico y estados de cilindros; no descuenta stock vendible adicional

### 5.5 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `PATCH` | `/movements/{id}/guide` | Asignar número de guía |
| `POST` | `/movements/{id}/close-dispatch` | Cerrar despacho |
| `GET` | `/movements/{id}/dispatch-receipt` | Vista de despacho recibido |
| `POST` | `/movements/{id}/vehicle-return` | Retorno de vehículo con carga masiva |

### 5.6 Tablas afectadas

- `lg_movements` — campos `document_series`, `document_number` (ya existen), nuevo campo `dispatched_at`
- `lg_movement_items` — requiere snapshot `product_id` / `product_name` para descuento y documentos

### 5.7 Decisiones de implementación

- `close-dispatch` ejecuta llamada directa al servicio de stock con `idempotency_key = movement_id + ':dispatch'`
- El descuento se hace por `product_id`, agregando `quantity_out` de las líneas del movimiento
- Solo participan líneas cuyo producto tenga configuración de stock controlado activa en `stk_config`
- Reintentar `close-dispatch` no debe duplicar el descuento de stock

### 5.8 Criterios de aceptación

- [ ] Número de guía se asigna correctamente (serie + correlativo)
- [ ] Despacho cerrado no puede modificarse
- [ ] Retorno de vehículo transiciona cilindros a DESCARGADO_POR_RECEPCIONAR
- [ ] Carga masiva con escáner no permite duplicados
- [ ] Endpoints validan warehouse scope del usuario
- [ ] `close-dispatch` descuenta stock real una sola vez por movimiento
- [ ] `vehicle-return` no altera stock vendible

---

## 6. Equipos por Movimiento

### 6.1 Objetivo

Implementar el catálogo de equipos (bombas, mangueras, etc.) y su asignación a movimientos, con control de devolución.

### 6.2 Alcance

- Catálogo de equipos
- Asignar equipos a movimientos
- Marcar devolución de equipos

### 6.3 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/equipment` | Listar catálogo de equipos |
| `POST` | `/equipment` | Crear equipo |
| `GET` | `/movements/{id}/equipment` | Equipos asignados a un movimiento |
| `POST` | `/movements/{id}/equipment` | Asignar equipo a movimiento |
| `PATCH` | `/movements/{id}/equipment/{eq_id}/return` | Marcar devolución de equipo |

### 6.4 Tablas nuevas

- `lg_equipment` — catálogo (id, tenant_id, name, equipment_type, is_active)
- `lg_movement_equipment` — asignación (id, movement_id, equipment_id, assigned_at, returned_at, notes)

### 6.5 Criterios de aceptación

- [ ] Catálogo de equipos CRUD funcional
- [ ] Asignación de equipos a movimientos
- [ ] Devolución registrada con fecha

---

## 7. Restricciones Vehículo-Ruta

### 7.1 Objetivo

Implementar restricciones que impidan asignar un vehículo a una ruta no autorizada.

### 7.2 Alcance

- Tabla de restricciones vehículo ↔ ruta
- Validación al asignar vehículo a ruta
- Mantenimiento de restricciones desde frontend

### 7.3 Reglas de negocio

- Por defecto, un vehículo puede servir cualquier ruta (lista blanca o negra)
- La restricción puede ser inclusiva (solo estas rutas) o exclusiva (todas excepto estas)

### 7.4 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/vehicles/{id}/route-restrictions` | Restricciones de un vehículo |
| `POST` | `/vehicles/{id}/route-restrictions` | Actualizar restricciones |
| `GET` | `/routes/{id}/eligible-vehicles` | Vehículos elegibles para una ruta |

### 7.5 Tablas nuevas

- `lg_vehicle_route_restrictions` (id, vehicle_id, route_id, restriction_type: ALLOW/DENY)

### 7.6 Criterios de aceptación

- [ ] Al asignar vehículo a ruta, se valida restricción
- [ ] API devuelve error si el vehículo no puede servir la ruta

---

## 8. Parámetros de Repartidor

### 8.1 Objetivo

Implementar configuración clave-valor por chofer/repartidor.

### 8.2 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/drivers/{id}/parameters` | Parámetros del repartidor |
| `PUT` | `/drivers/{id}/parameters` | Guardar parámetros |

### 8.3 Tablas nuevas

- `lg_driver_parameters` (id, driver_id, param_key, param_value)

### 8.4 Criterios de aceptación

- [ ] Guardar y leer parámetros por repartidor

---

## 9. Vinculación Vehículo-Cliente

### 9.1 Objetivo

Implementar la vinculación directa entre vehículos y puntos de entrega de clientes.

### 9.2 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/vehicles/{id}/delivery-points` | Puntos de entrega vinculados al vehículo |
| `POST` | `/vehicles/{id}/delivery-points` | Vincular punto de entrega |
| `DELETE` | `/vehicles/{id}/delivery-points/{dp_id}` | Desvincular |

### 9.3 Tablas nuevas

- `lg_vehicle_delivery_points` (id, vehicle_id, delivery_point_id)

### 9.4 Criterios de aceptación

- [ ] Vincular y desvincular puntos de entrega a vehículos

---

## 10. Resumen Diario de Agenda

### 10.1 Objetivo

Endpoint que devuelva el resumen diario de tareas de agenda agrupadas por estado y chofer.

### 10.2 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/agenda/daily-summary?date=` | Resumen diario (por defecto hoy) |

### 10.3 Criterios de aceptación

- [ ] Resumen agrupa por estado y chofer
- [ ] Totaliza correctamente

---

## 11. Schedule Semanal de Rutas

### 11.1 Objetivo

Agregar días de la semana a las rutas (1=lunes .. 7=domingo) para filtrar rutas disponibles al planificar.

### 11.2 Reglas de negocio

- Una ruta puede tener múltiples días
- Al planificar, solo mostrar rutas que correspondan al día seleccionado

### 11.3 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `PATCH` | `/routes/{id}/weekly-schedule` | Actualizar días de la semana |
| `GET` | `/routes?weekday=` | Filtrar rutas por día |

### 11.4 Tablas nuevas

- `lg_route_weekdays` (id, route_id, weekday: 1-7)

### 11.5 Criterios de aceptación

- [ ] Ruta puede tener múltiples días asignados
- [ ] Filtro por día funciona correctamente

---

## 12. Validación de Peso en Carga

### 12.1 Objetivo

Validar que la carga asignada a un repartidor no exceda el límite de peso máximo.

### 12.2 Reglas de negocio

- Límite máximo: 5,000 kg por repartidor (configurable por tenant)
- Al asignar cilindros a carga, calcular peso total y rechazar si excede
- Mostrar resumen de peso al asignar

### 12.3 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/loads/weight-summary?route_id=` | Resumen de peso por ruta |

### 12.4 Criterios de aceptación

- [ ] Peso total se calcula correctamente
- [ ] Asignación rechazada si excede el límite

---

## 13. Módulo ADR Completo

### 13.1 Objetivo

Implementar el módulo de Mercancías Peligrosas (ADR) completo: configuración por producto, cálculo de puntos, selección de vehículo, incompatibilidades.

### 13.2 Alcance

- Configuración ADR por producto (clase, puntos, túnel, cantidad máxima) — sobre `prod_products`
- Cálculo de puntos ADR por movimiento/documento
- Validación de incompatibilidades entre productos
- Selección de vehículo con capacidad ADR suficiente

### 13.3 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/adr/product-config/{product_id}` | Configuración ADR de un producto |
| `PUT` | `/adr/product-config/{product_id}` | Actualizar configuración ADR |
| `GET` | `/adr/points/{movement_id}` | Calcular puntos ADR del movimiento |
| `GET` | `/adr/incompatibilities` | Listar incompatibilidades |
| `POST` | `/adr/incompatibilities` | Agregar incompatibilidad |
| `DELETE` | `/adr/incompatibilities/{id}` | Eliminar incompatibilidad |
| `GET` | `/adr/eligible-vehicles/{movement_id}` | Vehículos con capacidad ADR suficiente |

### 13.4 Tablas nuevas

- `lg_adr_product_config` (**product_id** FK a `prod_products.id`, adr_class, adr_points, adr_tunnel, max_quantity, valid_from, valid_to)
- `lg_adr_incompatibilities` (**product_id_1**, **product_id_2** FK a `prod_products.id`)

### 13.5 Criterios de aceptación

- [ ] Configuración ADR por producto con fechas de vigencia
- [ ] Cálculo de puntos ADR por movimiento
- [ ] Validación de incompatibilidades al cargar
- [ ] Selección de vehículo con capacidad ADR disponible

---

## 14. GPS Tracking

### 14.1 Objetivo

Registrar coordenadas GPS durante la ejecución de rutas y tareas de agenda.

### 14.2 Alcance

- Registrar coordenadas al iniciar ruta
- Registrar coordenadas al completar tarea/parada
- Almacenar coordenadas en tareas de agenda (campo `gps_coordinates` ya existe como JSON)

### 14.3 Riesgos

- El legacy tiene GPS stub siempre (0,0). La nueva implementación debe funcionar con coordenadas reales desde el frontend móvil.
- El geocoding inverso (coordenadas → dirección) es opcional.

### 14.4 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `PATCH` | `/routes/{id}/gps-start` | Registrar GPS al iniciar ruta |
| `PATCH` | `/routes/{id}/stops/{stop_id}/gps` | Registrar GPS en parada |
| `PATCH` | `/agenda/tasks/{id}/gps` | Registrar GPS en tarea |

### 14.5 Criterios de aceptación

- [ ] Coordenadas se registran al iniciar ruta
- [ ] Coordenadas se registran al completar parada/tarea
- [ ] Datos almacenados en campo gps_coordinates (JSON)

---

## 15. Peso y Contenido de Cilindro

### 15.1 Objetivo

Implementar funciones de consulta de peso y contenido de cilindros: contenido en kg por producto, peso por cilindro (tara, capacidad, contenido), consulta de cilindros disponibles con datos de peso.

### 15.2 Alcance

- Función de contenido por producto (kg)
- Vista de peso por cilindro (tara, capacidad, contenido neto)
- Endpoint de cilindros disponibles con peso

### 15.3 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/cylinders/available-with-weight?warehouse_id=` | Cilindros disponibles con datos de peso |
| `GET` | `/cylinders/{id}/weight` | Datos de peso de un cilindro |
| `GET` | `/products/{id}/content` | Contenido en kg de un producto |

### 15.4 Criterios de aceptación

- [ ] Contenido por producto se calcula correctamente
- [ ] Peso por cilindro muestra tara, capacidad y contenido neto
- [ ] Consulta de disponibles incluye peso total

---

## Consideraciones transversales

### Claims `warehouse_id`

Todos los endpoints nuevos deben respetar el alcance por almacén del usuario autenticado (`TenantContext.current_warehouse_ids`). La validación sigue el mismo patrón que `plugins/stock/`:
- Lectura (`GET`): filtrar resultados por `allowed_warehouse_ids`
- Escritura (`POST`, `PATCH`): rechazar con 403 si el warehouse_id no está en el scope del usuario

### `branch_id` derivado

Toda tabla nueva que incluya `warehouse_id` debe también incluir `branch_id` derivado del almacén (`lg_warehouses.branch_id`). Esto garantiza trazabilidad de sucursal en eventos y auditoría.

### Integración con stock

Los módulos que afectan inventario deben integrarse con `plugins/stock/` por llamada directa de servicio Python, usando idempotencia:
- **Planificación**: no modifica stock real; solo calcula contra `stk_balance`
- **Recepción**: actualiza stock real con `idempotency_key = movement_id + ':reception'`
- **Despacho**: descuenta stock real con `idempotency_key = movement_id + ':dispatch'`

Los eventos se mantienen para auditoría e integración futura, pero no son el mecanismo primario de consistencia entre plugins.

### Producto con stock controlado

La condición para que una línea logística afecte stock real es:
- existe `stk_config` activo para `(tenant_id, warehouse_id, product_id)`
- la línea del movimiento tiene `product_id` materializado

Esto evita que líneas no inventariables o productos sin configuración operativa alteren `stk_balance`.

### Productos

Toda referencia a producto (id, nombre, ADR, peso) debe usar `prod_products` del plugin `plugins/productos/`. Las tablas `lg_gas_products` y `lg_brands` son transitorias y no deben usarse en módulos nuevos.

---

## Historial de cambios

| Fecha | Cambio |
|---|---|
| 2026-06-29 | Actualización mayor: stock, productos, claims, branch_id, eventos integrados |
| 2026-06-28 | Creación del documento con los 15 módulos pendientes de logistics |
