# SPEC 0014 — Logistics: Módulos Pendientes

## Estado

Borrador

## Contexto

El plugin `logistics` (v0.3.0) implementa el núcleo operativo de logística: gestión de cilindros, movimientos, rutas, carga, agenda, escaneo y 6 catálogos. Sin embargo, el análisis comparativo contra el legacy (`docs/avances/logistics.md`) identificó **15 módulos faltantes** para alcanzar paridad funcional.

El legacy (`modulo_logistica/`) opera sobre SQL Server con 27 tablas, 135 SP, 52 vistas, 24 formularios VB6 y Crystal Reports. El módulo actual corre sobre PostgreSQL con 18 tablas, ~84 endpoints REST, 22 eventos y frontend React.

Esta spec describe **los 15 módulos pendientes** con especificaciones detalladas para cada uno. No son features opcionales — todos son necesarios para reemplazar el legacy en producción.

## Nota de estado

- Esta spec sigue en borrador y no representa trabajo ya implementado.
- Los módulos aquí descritos no deben asumirse como avanzados ni alineados automáticamente con decisiones arquitectónicas posteriores.
- Antes de implementar cualquiera de estos módulos, hay que revalidarlos contra ADR 0015 y SPEC 0015 del plugin `productos`.
- En particular, cualquier referencia a producto, marca, ADR de producto transportado o pricing debe considerar que el catálogo maestro futuro vive en `productos`, no en `logistics`.

## No objetivos

- Reescribir lógica defectuosa del legacy (bugs R1-R18 documentados); la nueva implementación debe corregir esos problemas.
- Construir UI de reportes imprimibles (el renderizado PDF se define aparte).
- Integración con SUNAT para validación de Carta Porte en tiempo real.
- Módulo de facturación o finanzas (dependen de CRM + logistics pero tienen su propia spec).

---

## 1. Planificación

### 1.1 Objetivo

Implementar el módulo de planificación de operaciones que permita calcular stock disponible, asignar cantidades planificadas a pedidos, generar precargas y preparar la agenda del repartidor. Es el módulo más crítico del legacy (~20,000 líneas en FrmMovPlanificacionOperaciones).

### 1.2 Alcance

- Cálculo de stock disponible por producto y almacén
- Tres modos de planificar: todo, completos, parciales
- Modo overbooking (planificar sin stock suficiente)
- Generación de precarga (PLAN_PREPARACION_CARGA + PLAN_PREPARACION_DETALLE)
- Aceptar precarga y auto-generar traslado
- Planificación CILPRO vs pedidos normales
- Indicador visual de 3 colores (verde/amarillo/rojo) por nivel de stock

### 1.3 Riesgos

- El legacy tiene 5 formularios de planificación duplicados; debe consolidarse en uno solo.
- La lógica de stock es sensible: errores causan sobreventa o sub-asignación.
- La generación de precarga debe validar que no exista una precarga activa para la misma fecha/almacén.

### 1.4 Reglas de negocio

- Stock disponible = `StockActual - StockComprometido - StockPlanificado`
- `CantPlanificada` no puede exceder `CantPendiente` (salvo overbooking explícito)
- Overbooking requiere flag explícito (`permitir_sin_stock`)
- Solo una precarga activa por fecha y almacén
- Precarga tiene estados: `PENDIENTE`, `ACEPTADA`, `CANCELADA`
- Al aceptar precarga, auto-generar movimiento de traslado si aplica

### 1.5 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/planning/stock?warehouse_id=&product_id=` | Stock disponible por almacén/producto |
| `POST` | `/planning/stock/summary` | Resumen de stock para múltiples productos |
| `GET` | `/planning/pending-orders` | Pedidos pendientes con estado de stock (verde/amarillo/rojo) |
| `POST` | `/planning/plan-order/{order_id}` | Planificar cantidades para un pedido |
| `POST` | `/planning/generate-preload` | Generar precarga a partir de pedidos planificados |
| `GET` | `/planning/preloads` | Listar precargas (filtro por fecha, almacén, estado) |
| `GET` | `/planning/preloads/{id}` | Detalle de precarga |
| `POST` | `/planning/preloads/{id}/accept` | Aceptar precarga y generar traslado |
| `POST` | `/planning/preloads/{id}/cancel` | Cancelar precarga |

### 1.6 Tablas afectadas

- `lg_order_items` — se agrega `quantity_planned` (ya existe), manejo de modos
- Nueva `lg_plan_preloads` — cabecera de precarga (id, tenant_id, warehouse_id, date, status, created_by)
- Nueva `lg_plan_preload_items` — detalle de precarga (id, preload_id, order_item_id, product_id, quantity_planned, quantity_loaded)

### 1.7 Criterios de aceptación

- [ ] Stock disponible se calcula correctamente considerando cilindros por estado y almacén
- [ ] Modo completos solo planifica pedidos con stock total suficiente
- [ ] Modo parciales planifica hasta agotar stock
- [ ] Overbooking permite planificar más allá del stock disponible
- [ ] Generar precarga crea registro con estado PENDIENTE
- [ ] Aceptar precarga cambia estado a ACEPTADA y genera movimiento de traslado si aplica
- [ ] No se puede crear segunda precarga activa para misma fecha/almacén
- [ ] Indicador de 3 colores refleja correctamente el nivel de cobertura

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

### 2.3 Riesgos

- El legacy hace SQL directo sobre `ECilindroEstadoLog` y `ECilindroEstadoActual` (bug R3). La nueva implementación debe usar el state machine existente.
- Los faltantes mal manejados causan discrepancias de inventario.
- La recepción parcial debe ser soportada (recibir menos de lo esperado).

### 2.4 Reglas de negocio

- Solo movimientos en estado `DESCARGADO_POR_RECEPCIONAR` pueden ser recepcionados
- Si `cantidadRecibida < cantidadEsperada`, crear línea "FALTANTE NO TRANSFERIDO"
- Los cilindros recibidos transicionan a `EN_ALMACEN_VACIO`
- El movimiento cambia a estado `RECEPCIONADO`
- Las incidencias registradas transicionan cilindros a `OBSERVADO` o `PARA_REPARACION` según el motivo

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
- `lg_movement_items` — agregar soporte para ítems "FALTANTE NO TRANSFERIDO"
- `lg_cylinder_state_log` — transiciones de estado
- Nueva `lg_reception_incidents` — incidencias de recepción (id, movement_id, cylinder_id, reason_code, description, created_by)

### 2.7 Criterios de aceptación

- [ ] Lista solo movimientos pendientes de recepción para el almacén destino
- [ ] Recepción exitosa cambia estado del movimiento a RECEPCIONADO
- [ ] Cilindros recibidos transicionan a EN_ALMACEN_VACIO
- [ ] Si hay faltantes, se crean líneas "FALTANTE NO TRANSFERIDO" automáticamente
- [ ] Recepción parcial funciona correctamente
- [ ] Incidencias se registran con motivo del catálogo
- [ ] Historial de estado se actualiza en cada paso

---

## 3. Carta Porte

### 3.1 Objetivo

Implementar la generación del documento Carta Porte, requisito legal para el transporte terrestre de mercancías en Perú. El documento debe contener cabecera, detalle de productos y resumen con datos del remitente, destinatario y transportista.

### 3.2 Alcance

- Generar datos estructurados de Carta Porte a partir de un movimiento
- Cabecera: datos del movimiento, cliente, transportista, ruta, fechas
- Detalle: productos, cantidades, pesos, bultos
- Resumen: totales, peso bruto, puntos ADR
- Endpoint que devuelve datos listos para renderizar (PDF u otro formato)

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
- El resumen incluye total de bultos, peso bruto total y puntos ADR si aplica

### 3.5 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/waybill/{movement_id}` | Datos estructurados de Carta Porte para un movimiento |
| `GET` | `/waybill/{movement_id}/summary` | Resumen de Carta Porte |

### 3.6 Tablas afectadas

- `lg_movements` — datos del movimiento
- `lg_movement_items` — detalle de productos
- `crm_customers` — datos del cliente
- `lg_warehouses` — datos del almacén origen
- `lg_vehicles` — datos del vehículo/transportista
- Ninguna tabla nueva; endpoint de solo lectura

### 3.7 Criterios de aceptación

- [ ] Carta Porte se genera para movimientos de tipo SC y SP
- [ ] Cabecera contiene remitente, destinatario, transportista correctos
- [ ] Detalle lista cada producto con cantidades y pesos
- [ ] Resumen calcula totales correctamente (bultos, peso bruto, ADR)
- [ ] Datos estructurados listos para renderizar

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

### 5.5 API endpoints propuestos

| Método | Path | Descripción |
|---|---|---|
| `PATCH` | `/movements/{id}/guide` | Asignar número de guía |
| `POST` | `/movements/{id}/close-dispatch` | Cerrar despacho |
| `GET` | `/movements/{id}/dispatch-receipt` | Vista de despacho recibido |
| `POST` | `/movements/{id}/vehicle-return` | Retorno de vehículo con carga masiva |

### 5.6 Tablas afectadas

- `lg_movements` — campos `document_series`, `document_number` (ya existen), nuevo campo `dispatched_at`

### 5.7 Criterios de aceptación

- [ ] Número de guía se asigna correctamente (serie + correlativo)
- [ ] Despacho cerrado no puede modificarse
- [ ] Retorno de vehículo transiciona cilindros a DESCARGADO_POR_RECEPCIONAR
- [ ] Carga masiva con escáner no permite duplicados

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

- Configuración ADR por producto (clase, puntos, túnel, cantidad máxima)
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

- `lg_adr_product_config` (product_id, adr_class, adr_points, adr_tunnel, max_quantity, valid_from, valid_to)
- `lg_adr_incompatibilities` (product_id_1, product_id_2)

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

## Historial de cambios

| Fecha | Cambio |
|---|---|
| 2026-06-28 | Creación del documento con los 15 módulos pendientes de logistics |
