# Arquitectura de Base de Datos — SYSTUTOR OSS

> Documento generado desde el esquema real de PostgreSQL. 115 tablas, 1420 columnas, 302 foreign keys.

---

## 1. Visión general

La base de datos de SYSTUTOR está organizada en cinco módulos principales de negocio más un núcleo transversal de infraestructura. La separación es limpia: cada módulo tiene su prefijo de tabla y sus propias fronteras de integridad referencial.

| Módulo | Prefijo | Tablas | Rol |
|--------|---------|--------|-----|
| Núcleo | `tenants`, `users`, `roles`, `branches`, `audit_`, `event_`, `plugin_` | ~12 | Multi-tenancy, autenticación, permisos, auditoría, eventos |
| CRM | `crm_` | ~9 | Clientes, contactos, direcciones, sucursales, crédito |
| Productos | `prod_` | ~18 | Catálogo maestro: productos, líneas, marcas, ADR, precios, costos, impuestos |
| Stock | `stk_` | ~4 | Inventario: balance, ledger contable, reservas, configuración |
| Ventas | `ventas_` | ~2 | Cotizaciones |
| Logistics | `lg_` | ~66 | El corazón operativo: cilindros, movimientos, sesiones, rutas, carga, contratos, agenda |

El 57% de las tablas pertenece a Logistics. El módulo más grande y el más interconectado.

---

## 2. Núcleo: multi-tenancy, usuarios y auditoría

Todo arranca con `tenants`. Es la tabla más referenciada del sistema: 69 foreign keys apuntan a ella. Cada tenant es un espacio aislado de negocio — una empresa de gas distinta corriendo sobre la misma instancia.

```
tenants
  └── branches          → sucursales del tenant
        ├── users        → usuarios (pertenecen a un tenant, pueden tener branch)
        ├── roles        → roles con permisos granulares
        ├── role_permissions → asignación rol ↔ permiso
        └── audit_log    → registro de toda acción auditable
```

`users` es la segunda tabla más referenciada (61 FKs). Casi toda acción en el sistema sabe quién la hizo: `created_by`, `updated_by`, `performed_by`, `counted_by`, `selected_by`, `generated_by`, `changed_by`, `closed_by`, `loaded_by`, `unloaded_by`, `released_by`. El modelo de auditoría no es un afterthought — está tejido en cada operación.

`roles` y `permissions` implementan RBAC clásico. `role_branches` permite restringir roles a sucursales específicas.

`plugins` y `plugin_permissions` definen qué módulos están activos y qué permisos exponen. El sistema es extensible por plugins y los permisos se declaran en `plugin.json` + runtime.

`event_store` y `event_subscriptions` son el bus de eventos interno. Cada acción importante (crear cilindro, confirmar movimiento, cambiar estado) emite un evento. Los módulos se suscriben sin acoplarse directamente.

---

## 3. CRM: clientes, contactos y direcciones

El módulo CRM modela la entidad cliente con tres capas:

```
crm_customers                    → ficha maestra del cliente (35 columnas)
  ├── crm_customer_contacts      → personas de contacto (teléfono, email, rol)
  ├── crm_customer_addresses     → direcciones fiscal, comercial, entrega (33 columnas)
  ├── crm_customer_branches      → sucursales del cliente
  ├── crm_customer_bank_accounts → datos bancarios
  ├── crm_customer_credit        → límite de crédito y saldo
  ├── crm_customer_pricing_terms → condiciones comerciales por cliente
  └── crm_customer_commercial_assignments → asignación de comerciales
```

El diseño distingue entre `legal_name` (razón social), `commercial_name` (nombre de negocio) y `display_name` (cómo se muestra en pantalla). `external_code` y `internal_code` mantienen trazabilidad con sistemas legacy. `document_type_code` + `document_number` identifican fiscalmente al cliente.

Las direcciones tienen tipo (`FISCAL`, `COMERCIAL`, `ENTREGA`), coordenadas GPS, persona de contacto in-situ, y flags de `is_default`. Un cliente puede tener múltiples puntos de entrega, cada uno con su propio responsable y teléfono — exactamente lo que Grab2 describe como necesidad operativa real.

---

## 4. Productos: catálogo maestro

`prod_products` es la tabla más interconectada del módulo de negocio (19 FKs entrantes, 12 FKs salientes). Es la fuente de verdad para todo ítem transable en el sistema:

```
prod_products
  ├── prod_lines         → línea de producto (ej: GASES, ENVASES)
  │     └── prod_categories → categoría (ej: INDUSTRIAL, MEDICINAL)
  ├── prod_subline       → sublínea (ej: OXIGENO, NITROGENO, GLP)
  ├── prod_brands        → marca
  ├── prod_groups        → agrupación (ej: bombona 10kg + gas 10kg)
  ├── prod_conditions    → condición (PRODUCTO, CILPRO, CILCLI, CILPROV, CILGAR)
  ├── prod_units         → unidad de medida (KG, UND, M3, L)
  ├── prod_status        → estado del producto en catálogo
  ├── prod_insumo_types  → tipo de insumo
  ├── prod_subcategories → subcategoría
  ├── prod_adr           → ficha ADR (ONU, etiqueta, túnel, puntos, factor)
  ├── prod_barcodes      → códigos de barra
  ├── prod_prices        → precios con vigencia temporal y lista de precios
  ├── prod_costs         → costos con vigencia temporal
  ├── prod_tax_config    → configuración fiscal (exento, IGV, etc.)
  ├── prod_promotions    → promociones (descuento por cantidad, precio caja)
  └── prod_media         → imágenes del producto
```

La separación entre `prod_products` y `prod_adr` es clave: ADR es una ficha técnica de transporte de mercancías peligrosas que puede cambiar en el tiempo (`valid_from` / `valid_to`). Un mismo producto puede tener distintas configuraciones ADR según normativa vigente. Los campos como `un_number`, `cargo_description`, `tunnel_restriction`, `points` y `factor` viven aquí, no en el cilindro — el cilindro hereda ADR del producto que contiene.

`prod_prices` y `prod_costs` tienen vigencia temporal: permiten planificar cambios de precio futuros sin afectar operaciones en curso.

---

## 5. Stock: inventario contable

Cuatro tablas que implementan un sistema de inventario con ledger inmutable:

```
stk_balance         → saldo actual por producto-almacén (quantity, reserved_quantity, total_cost)
stk_ledger          → libro mayor: cada entrada y salida con costo unitario y balance posterior
stk_allocation      → reservas: cantidad separada para un pedido/operación, con vencimiento
stk_config          → reglas por producto-almacén (stock mínimo, máximo, permitir negativo)
```

`stk_ledger` es inmutable. Cada movimiento de stock deja una fila con: operación (IN/OUT), tipo de movimiento, documento origen, parte relacionada, cantidad, costo unitario, costo total y balance resultante. 22 columnas que permiten reconstruir cualquier estado histórico.

La relación con Logistics es a través de `lg_stock_bridge_log`, que registra cada intento de sincronización entre movimientos logísticos y stock contable, con status y mensaje de error si falla.

---

## 6. Ventas: cotizaciones

Módulo mínimo por ahora. Dos tablas:

```
ventas_quote_drafts    → borrador de cotización (cliente, vehículo, fecha entrega, estado)
  └── ventas_quote_items → líneas de cotización (producto, cantidad, peso unitario)
```

La cotización tiene FK a `lg_vehicles` (si aplica transporte) y a `lg_planning_reservations` (si se convierte en una reserva de planificación). El ciclo es: cotización → reserva de planificación → sesión de vehículo.

---

## 7. Logistics: el corazón operativo

66 tablas organizadas en 13 subdominios.

### 7.1 Almacenes y vehículos

```
lg_warehouses       → almacenes (físicos y móviles)
  ├── lg_zones       → zonas geográficas de operación
  └── lg_vehicles    → vehículos (placa, tipo, capacidades, clase ADR)
        ├── lg_vehicle_delivery_points → puntos de entrega asignados al vehículo
        └── lg_vehicle_route_restrictions → restricciones de ruta por vehículo
```

`lg_warehouses` tiene un campo `warehouse_type` que distingue entre `FIXED` (almacén físico) y `MOBILE` (camión). Un mismo vehículo puede ser tratado como almacén móvil — el inventario que lleva encima es stock real, no solo carga. Esto es fundamental para el modelo de custodio en tránsito.

### 7.2 Sesiones de vehículo

Este es uno de los mejores diseños del sistema:

```
lg_vehicle_sessions       → la cápsula operativa del día
  ├── lg_vehicle_location_events → tracking GPS en tiempo real
  ├── lg_session_waybill_versions → versiones de carta porte (con hash operacional e idempotencia)
  └── lg_session_reconciliations  → conciliación de cierre (lo cargado vs lo devuelto)
```

Una `VehicleSession` representa una salida real de un vehículo en una fecha concreta. Agrupa: el vehículo, el chofer, el almacén de origen, el almacén móvil asociado, la ruta planificada, y todo lo que ocurrió durante esa salida. No depende del vehículo (el mismo camión puede hacer otra ruta mañana), no depende del chofer (es asignación temporal), no depende de la ruta (es una plantilla que se materializa en la sesión).

Los estados de la sesión: `DRAFT → READY → IN_PROGRESS → COMPLETED`. Con timestamps para cada transición: `opened_at`, `ready_at`, `departed_at`, `returned_at`, `closed_at`.

`lg_session_waybill_versions` implementa versionado de carta porte. Cada cambio en la carga genera una nueva versión con: snapshot del contenido, hash operacional, motivo del cambio, evento disparador, contexto regulatorio. Las versiones se encadenan por `previous_version_id`. Idempotencia por `session_id + idempotency_key`.

`lg_session_reconciliations` registra la conciliación al cierre: ¿coincide lo que salió con lo que volvió? Con quien contó, quien cerró y el resultado (`MATCHED`, `DISCREPANCY`).

### 7.3 Envases / Cilindros

El subdominio más grande de Logistics:

```
lg_cylinder_states          → catálogo de estados (18 estados: CREADO_VACIO, EN_ALMACEN_VACIO, LLENADO_OK, etc.)
lg_state_transitions        → transiciones permitidas entre estados (31 transiciones)
lg_cylinders                → ficha maestra del cilindro (44 columnas)
  ├── lg_cylinder_state_log     → trazabilidad de cambios de estado (origen, motivo, metadata JSON)
  ├── lg_cylinder_ownership     → custodia/posesión (quién tiene el cilindro y desde cuándo)
  ├── lg_cylinder_retimbrados   → ficha técnica de reestampado (25 columnas, pesos, presiones, ADR)
  ├── lg_hydrostatic_tests      → pruebas hidrostáticas (fecha, estado, notas)
  ├── lg_cylinder_warranties    → garantías (cliente, tipo, estado, fecha devolución)
  ├── lg_cylinder_services      → servicios (tipo, precios, descuentos, estado - 21 columnas)
  ├── lg_cylinder_label_history → historial de impresión de etiquetas
  ├── lg_cylinder_events        → eventos del ciclo de vida
  ├── lg_customer_cylinder_ledger → libro de posesión por cliente
  └── lg_scan_log               → registro de escaneos operativos (barcode, GPS, validación ADR/PH)
```

`lg_cylinders` con 44 columnas es la tabla más ancha del sistema. Pero su diseño es intencionalmente completo: serial único, barcode1 (producto), barcode2 (etiqueta física pegada al cilindro), gas/producto asociado, contenido en kg, volumen en m3, condición (propio/cliente/proveedor/garantía), marca, pesos, fechas de fabricación y PH. Cada cilindro es un activo trazable individualmente.

La máquina de estados (`lg_cylinder_states` + `lg_state_transitions`) gobierna el ciclo de vida. Un cilindro no puede saltar de cualquier estado a cualquier otro — solo por las transiciones declaradas. Algunas transiciones exigen validación ADR o PH vigente.

`lg_cylinder_ownership` responde "quién tiene este cilindro ahora mismo". Es la capa de custodia que permite saber si un cilindro está en almacén, en cliente, en ruta o en garantía. El ownership vigente debe ser consistente con el estado del cilindro.

`lg_customer_cylinder_ledger` es el libro de entradas y salidas de cilindros por cliente — análogo al `stk_ledger` pero para activos físicos en vez de stock.

### 7.4 Movimientos

El sistema de movimientos es el motor transaccional:

```
lg_movement_types            → catálogo de tipos (IC, IP, SC, SP, IFP, etc.)
lg_movements                 → cabecera del movimiento (33 columnas, 10 FKs)
  ├── lg_movement_items       → líneas del movimiento (producto, cilindro, cantidades, precios)
  ├── lg_movement_equipment   → equipos asociados al movimiento
  └── lg_movement_status_history → historial de cambios de estado del movimiento
```

`lg_movements` es la tercera tabla con más FKs (10). Conecta con: tenant, branch, tipo de movimiento, orden de trabajo, ruta, almacén, chofer, vehículo, cliente, movimiento padre. Un movimiento puede tener movimiento padre (para anulaciones, correcciones, devoluciones). El campo `full_document` unifica serie+número para referencia rápida.

`lg_movement_items` maneja cantidades de entrada y salida por separado (`quantity_in`, `quantity_out`), más `quantity_planned` y `quantity`. Captura el estado del cilindro antes y después del movimiento (`state_before`, `state_after`). Esto permite auditoría completa: qué cilindro, en qué estado estaba, a qué estado pasó, con qué producto y cantidades.

`lg_movement_types` define la semántica de cada tipo: ¿mueve cilindros? ¿cuál es el estado origen y destino? ¿a qué categoría pertenece? Los tipos se usan como discriminantes para validar transiciones de estado y generar efectos colaterales (stock, ownership).

### 7.5 Rutas y paradas

```
lg_routes                   → ruta planificada (fecha, vehículo, chofer, sucursal)
  ├── lg_route_stops         → paradas de la ruta (orden, cliente, punto de entrega, hora programada)
  │     └── lg_delivery_points → puntos de entrega (dirección, GPS, contacto, frecuencia)
  └── lg_route_weekdays      → días de operación de la ruta semanal
```

Las rutas son plantillas que se materializan en sesiones. `lg_route_stops` tiene orden secuencial (`stop_order`), tiempos programados, reales de llegada y salida, y GPS. El estado de cada parada evoluciona: `PENDING → IN_PROGRESS → COMPLETED → SKIPPED`.

`lg_delivery_points` (28 columnas) es una tabla rica: dirección completa, coordenadas, persona de contacto in-situ con teléfono y email, frecuencia de visita (día de semana), ventana horaria, instrucciones especiales, tipo de acceso. Referencia al cliente via `customer_id` y a la dirección del CRM via `address_id`.

### 7.6 Operaciones en ruta

Aquí es donde ocurre la acción real en la calle:

```
lg_route_operations         → operación en una parada (21 columnas, 7 FKs)
  ├── lg_route_operation_items → líneas de la operación (producto, cantidad, dirección)
  ├── lg_route_stop_results    → resultado de la parada (completada, parcial, fallida)
  └── lg_route_incidents       → incidentes (tipo, operación relacionada, operación correctiva)

lg_logistics_operations     → envoltura operativa de un movimiento (sesión, parada, tipo)
  └── lg_logistics_operation_items → líneas del movimiento operativo
```

`lg_route_operations` registra qué pasó en cada parada: tipo de operación (`DELIVERY`, `PICKUP`, `EXCHANGE`, `EMERGENCY`), con quién (`customer_id` o `warehouse_id`), dónde (GPS), qué movimientos se generaron (`movement_ids_json`), y estado (`DRAFT → CONFIRMED`). La idempotencia por `session_id + idempotency_key` evita duplicados.

El campo `context_type` distingue explícitamente si la operación fue con un cliente (`customer`) o en un almacén (`warehouse`). Esto resuelve el problema de "el cilindro está en cliente, ¿pero en cuál?" — la operación declara el contexto sin ambigüedad.

`lg_logistics_operations` es una capa más técnica: envuelve un movimiento con su contexto de sesión y parada, agrega evidencia (`evidence_json`) y referencia externa (`external_movement_id`). Es el puente entre el mundo de movimientos y el mundo de operaciones en ruta.

`lg_route_incidents` captura eventos anómalos: tipo de incidente, operación donde ocurrió, operación correctiva aplicada. Estados: `OPEN → IN_PROGRESS → RESOLVED`. Los incidentes pueden referenciar tanto la operación que los causó como la operación que los corrigió — doble trazabilidad.

`lg_reception_incidents` es similar pero para recepción en almacén (no en ruta).

### 7.7 Carga y planificación

```
lg_planning_reservations    → reserva de vehículo/chofer/ruta (28 columnas, 10 FKs)
lg_load_plans               → plan de carga de una sesión
  └── lg_load_serial_assignments → asignación de cilindros al plan de carga
lg_plan_preloads            → precarga planificada
  └── lg_plan_preload_items  → ítems de precarga
lg_loads                    → carga/descarga de cilindros en ruta (por parada)
```

`lg_planning_reservations` es la tabla de planificación táctica: reserva un vehículo, un chofer y una ruta para una ventana temporal. Conecta con `ventas_quote_drafts` (si viene de una cotización) y con `lg_vehicle_sessions` (cuando se materializa). Tiene resumen de carga esperado y real, flags de ADR requerido, y permitir overrides.

`lg_load_serial_assignments` es la tabla que responde "qué cilindros van en este camión". Cada asignación tiene: cilindro, producto, serial, quien lo seleccionó, estado (`PENDING → LOADED → CONFIRMED → UNLOADED`), y referencia a la operación que confirmó la carga. Es el puente entre el plan de carga y la operación real.

`lg_loads` maneja el ciclo de carga/descarga por cilindro individual en cada parada de ruta: `loaded_at`, `unloaded_at`, parada donde se cargó/descargó.

### 7.8 Almacén móvil

```
lg_mobile_warehouses            → el camión como almacén (14 columnas, 6 FKs)
  ├── lg_mobile_warehouse_items  → inventario a bordo (producto, cilindro, cantidades, pesos)
  │     └── lg_mobile_warehouse_item_events → eventos del ítem (carga, descarga, transferencia)
  └── lg_mobile_warehouse_snapshots → foto del inventario en un momento dado
        └── lg_mobile_warehouse_snapshot_items → detalle de la foto
```

Este subdominio modela el camión como un almacén que se mueve. `lg_mobile_warehouses` tiene: vehículo, chofer, almacén base, almacén de stock vinculado, estado (`ACTIVE`, `CLOSED`), y timestamps de apertura/cierre.

`lg_mobile_warehouse_items` rastrea cada ítem a bordo: producto y/o cilindro, cantidades, pesos, cliente destino, almacenes origen/destino, quien cargó y descargó, movimiento asociado. Con 8 FKs, es una de las tablas más interconectadas del módulo.

`lg_mobile_warehouse_snapshots` es una foto del inventario en un instante: tipo de snapshot, total de unidades y peso, metadata JSON. Sirve para verificaciones de carga, conciliaciones y auditorías. El detalle está en `lg_mobile_warehouse_snapshot_items`.

El gap identificado: `lg_mobile_warehouse_snapshots` no tiene FK a `lg_vehicle_sessions`. Para saber qué snapshot corresponde a qué sesión hay que cruzar por timestamps.

### 7.9 Contratos de envases

```
lg_cylinder_contracts      → contrato de alquiler/cesión de envases (34 columnas)
  ├── lg_cylinder_contract_items → ítems del contrato (producto, cantidad, precio)
  ├── lg_cylinder_contract_history → historial de cambios del contrato
  └── lg_contract_types     → tipos de contrato (duración, unidad)
```

Implementación completa del flujo descrito en Grab2: los contratos se atan a tipo de cilindro (`cylinder_type_id` → `prod_products`), no a seriales concretos. Tienen cliente, condición del cilindro, cantidad, precio unitario, fechas de inicio y fin, tipo de renovación, y estado (`DRAFT → ACTIVE → TERMINATED`). Workflow con validaciones: no se puede activar sin cliente y cantidad > 0, un cilindro no puede estar en dos contratos activos, terminar el contrato libera los cilindros. Firma digital pendiente (spec `0023AE`).

### 7.10 Agenda y tareas

```
lg_agenda_tasks            → tareas programadas (25 columnas, 6 FKs)
lg_agenda_task_types       → tipos de tarea
lg_agenda_task_status      → estados de tarea
```

Sistema de agenda para programar operaciones recurrentes o puntuales: tipo de tarea, responsable, ventana temporal, prioridad, recurrencia, cliente o almacén destino.

### 7.11 Órdenes de trabajo

```
lg_orders                  → orden de trabajo (documento, cliente, almacén, tipo, fechas)
  └── lg_order_items        → líneas de la orden (producto, cantidades, condición, ubicación)
```

Las órdenes son el paso previo a los movimientos. Una orden se convierte en uno o varios movimientos. El flujo: orden → movimiento → operación en ruta. Tienen número de documento, serie, tipo de movimiento asociado, ventana de compromiso.

### 7.12 Equipos

```
lg_equipment               → equipos (tipo, código, estado)
  └── lg_equipment_assignments → asignación de equipo a movimiento o sesión
```

Equipamiento auxiliar: bombas, mangueras, carretillas. Se pueden asignar a movimientos o sesiones.

### 7.13 Catálogos y utilidades

```
lg_cylinder_states         → estados de cilindro (18 códigos)
lg_state_transitions       → transiciones permitidas (31 registros)
lg_movement_types          → tipos de movimiento
lg_service_types           → tipos de servicio para cilindros
lg_contract_types          → tipos de contrato
lg_stock_bridge_log        → log de sincronización logistics ↔ stock
```

---

## 8. Estadísticas del esquema

| Métrica | Valor |
|---------|-------|
| Total tablas | 115 |
| Total columnas | 1420 |
| Foreign keys | 302 |
| Índices | 709 |
| Check constraints | 5 |
| Tabla más ancha | `lg_cylinders` (44 columnas) |
| Tabla con más FKs salientes | `prod_products` (12 FKs) |
| Tabla más referenciada | `tenants` (69 FKs entrantes) |
| Tabla con más índices | `lg_cylinders` (17 índices) |

Distribución de tipos de datos:
- `varchar`: 880 columnas (62%)
- `timestamp/timestamptz`: 220 columnas
- `numeric`: 105 columnas
- `boolean`: 71 columnas
- `text`: 56 columnas
- `integer`: 36 columnas
- `date`: 25 columnas
- `json/jsonb`: 18 columnas

---

## 9. Decisiones de diseño visibles en el esquema

### 9.1 UUIDs como claves primarias

Todas las tablas de negocio usan `id VARCHAR(36)` con UUIDs generados en aplicación. Esto permite: generación offline (sin secuencia de BD), merge de datos entre entornos, y evita enumerabilidad de recursos en APIs.

### 9.2 Timestamps universales

Prácticamente toda tabla tiene `created_at` y `updated_at` con `timezone`. Las tablas operativas añaden timestamps de negocio: `performed_at`, `departed_at`, `returned_at`, `closed_at`, `loaded_at`, `unloaded_at`, `signed_at`, `terminated_at`. Esto permite reconstruir la línea de tiempo real de cada operación.

### 9.3 Snapshots de nombres

Campos como `customer_name_snapshot`, `warehouse_name_snapshot`, `product_name` aparecen en tablas operativas (route_operations, movements, loads). Esto es una decisión deliberada: aunque exista la FK a la entidad maestra, se guarda una copia del nombre en el momento de la operación. Si el cliente cambia de nombre mañana, los documentos de hoy siguen siendo legibles.

### 9.4 Idempotencia

`lg_route_operations`, `lg_logistics_operations`, `lg_session_waybill_versions` tienen `idempotency_key` con constraint UNIQUE compuesto por sesión. Esto permite reintentos seguros en operaciones de campo con conectividad intermitente.

### 9.5 JSON para datos flexibles

18 columnas `json/jsonb` en todo el esquema: `metadata_json` en state_log, `evidence_json` en logistics_operations, `movement_ids_json` en route_operations, `gps_coordinates` en route_stops, `snapshot_json` en waybill_versions. Se usa para datos que varían por contexto sin necesidad de migraciones de esquema.

### 9.6 Separación de movimientos y operaciones

El sistema distingue entre `lg_movements` (transacción contable/logística) y `lg_route_operations` / `lg_logistics_operations` (contexto operativo en calle). Un movimiento puede existir sin operación en ruta (movimiento de almacén), y una operación en ruta puede generar múltiples movimientos. Esta separación evita el acoplamiento que el legacy tenía al mezclar todo en `ECabeceraPedido`/`EDetallePedido`.

---

## 10. Conexiones clave entre módulos

```
Productos ──→ Stock ──→ Logistics
    │                        │
    ├── prod_products ───────┤ (FK en lg_cylinders, lg_movement_items, etc.)
    ├── prod_adr ────────────┤ (ADR se lee desde producto al cilindro)
    ├── prod_prices ─────────┤ (precios en movimientos y contratos)
    └── prod_conditions ─────┤ (condición del cilindro)

CRM ────────→ Logistics
    ├── crm_customers ───────┤ (cliente en movimientos, operaciones, contratos)
    └── crm_customer_addresses┤ (puntos de entrega)

Ventas ─────→ Logistics
    └── ventas_quote_drafts ─→ lg_planning_reservations (cotización → reserva)

Stock ←─────→ Logistics
    └── stk_ledger ←────────── lg_stock_bridge_log (sincronización)
```

---

## 11. Lo que el esquema revela sobre el modelo de negocio

1. **El cilindro es el activo central**: 44 columnas, 13 FKs entrantes, 17 índices. Todo gira alrededor del envase.

2. **La sesión de vehículo es la unidad de trabajo**: 13 FKs entrantes. Carga, ruta, operaciones, incidentes, GPS, carta porte, conciliación — todo cuelga de la sesión.

3. **La trazabilidad es ubicua**: state_log, ownership, scan_log, movement_status_history, contract_history, waybill_versions, customer_cylinder_ledger, stock_bridge_log. Cada acción deja rastro.

4. **El modelo distingue entre planificado y real**: planned vs actual en planning_reservations, quantity_planned vs quantity en movement_items, scheduled vs arrival en route_stops. La diferencia entre lo que se planeó y lo que realmente pasó es un dato de negocio de primera clase.

5. **ADR es del producto, no del cilindro**: `prod_adr` es una entidad independiente con vigencia temporal. El cilindro hereda ADR del producto que contiene en ese momento.

6. **El camión es un almacén**: `lg_mobile_warehouses` y sus items/snapshots tratan al vehículo como una ubicación de inventario real, con su propio ledger de eventos.

7. **Los contratos son sobre tipos, no sobre seriales**: `lg_cylinder_contracts.cylinder_type_id` apunta a `prod_products`, no a `lg_cylinders`. Coincide exactamente con lo que Grab2 describe: "el contrato no amarra a número de cilindro, se amarra a tipo de cilindro".
