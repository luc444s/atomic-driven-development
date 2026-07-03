# SPEC 0012 — Logistics: Envase completo + trazabilidad field

## Estado

Implementada

## Contexto

La implementacion actual del plugin `logistics` (SPEC 0011) cubre el state machine, operaciones (pedidos, rutas, carga, movimientos, agenda) y el frontend multi-pantalla. Sin embargo, el modelo del envase (`lg_cylinders`) es esqueletico comparado con el legacy `Producto` que funciona como ficha maestra del cilindro.

El proyecto ya usa y soporta validaciones locales con `pyright` y `ruff` dentro de este repositorio. Ambos deben considerarse herramientas activas del flujo normal de desarrollo y cierre tecnico.

El analisis del legacy revelo:

- `Producto` tiene ~55 columnas de las cuales 25+ son relevantes para el envase y no estan en `lg_cylinders`
- Existen tablas completas no modeladas: retimbrados, custodia, servicios, etiquetas, escaneo movil
- El legacy tiene un sistema de escaneo movil en campo con GPS que valida ADR/PH al entregar/recojer
- La impresion de etiquetas con `barcode2` (matricula) es parte del flujo de alta del cilindro

### Nota de alineación posterior

Esta spec describe el corte implementado de `logistics` al momento de construir el envase completo.

- Las referencias a `lg_gas_products` y `lg_brands` describen el modelo implementado actual.
- No representan el destino final del catálogo maestro de productos.
- Desde ADR 0015 y SPEC 0015, ambos catálogos quedan definidos como transitorios y deberán migrarse a `prod_products` y `prod_brands` del plugin `productos`.
- Esta spec no debe usarse como argumento para volver a centralizar precios, costos o catálogo maestro dentro de `logistics`.

## Objetivo

Completar el modelo de datos del envase para cubrir el equivalente funcional de `frmMovBombonas`/`FrmCatBombonas`, e implementar el sistema de escaneo movil para trazabilidad en campo.

Nota de interpretacion: aunque `lg_cylinders` conserva campos ADR por trazabilidad y snapshot operativo, la configuracion ADR maestra pertenece a `productos`. El alta de envase no debe tratar ADR como entrada manual independiente del catalogo/producto.

## No objetivos

- migracion de datos historicos legacy
- facturacion electronica
- CRM completo
- inventario general (Stock_Actual)
- caja / finanzas / cobranza
- reportes BI
- integracion con hardware de escaneo fisico (solo API para que una app movil consuma)
- firma digital en dispositivo movil

## Alcance

- `plugins/logistics/backend/models.py` — nuevos campos y tablas
- `plugins/logistics/backend/schemas.py` — nuevos schemas
- `plugins/logistics/backend/services/` — cylinders extendido + retimbrados + escaneo + etiquetas
- `plugins/logistics/backend/router.py` — nuevos endpoints
- `plugins/logistics/migrations/004_envase_completo.py`
- `plugins/logistics/frontend/` — formularios y vistas nuevas
- `plugins/logistics/permissions/` — nuevos permisos si aplica
- `plugins/logistics/events/` — nuevos eventos si aplica
- `docs/contracts/logistics-api.md` — ampliar contratos
- `docs/specs/core/0011-logistics-pilot-module.md` — actualizar corte implementado

No debe romper endpoints existentes, el estado actual del plugin ni el kernel.

---

## Modelo de datos: cambios sobre `lg_cylinders`

### Nuevos campos en `lg_cylinders`

| columna | tipo | legacy | descripcion |
|---------|------|--------|-------------|
| `description` | VARCHAR(200) | Desc_Producto | descripcion del envase |
| `barcode1` | VARCHAR(150) | barcode1 | codigo de barras primario (producto) |
| `barcode2` | VARCHAR(50) | barcode2 | matricula del cilindro (codigo en etiqueta) |
| `gas_group_id` | VARCHAR(36) FK → lg_gas_products | cod_grupo | que producto gas contiene. FK actual transitoria; destino final: `prod_products` |
| `content_kg` | NUMERIC(10, 2) | Cont | capacidad en kg de gas |
| `volume_m3` | NUMERIC(10, 4) | M3 | volumen en metros cubicos |
| `condition` | VARCHAR(50) | condicion | NUEVO, USADO |
| `brand_id` | VARCHAR(36) FK → lg_brands | Marca_Producto | marca del envase. FK actual transitoria; destino final: `prod_brands` |
| `cost` | NUMERIC(19, 4) | Costo_Producto | costo capturado en el corte legacy del envase. No debe convertirse en fuente maestra de costos frente al plugin `productos` |
| `price` | NUMERIC(19, 4) | Precio_Producto | precio capturado en el corte legacy del envase. No debe convertirse en fuente maestra de precios frente al plugin `productos` |
| `country_code` | CHAR(2) | PaisCodigo | pais de origen |
| `box_number` | VARCHAR(50) | Nro_cja | numero de caja/lote |
| `is_service` | BOOLEAN | servicio | true si es servicio, false si es fisico |

### Campos ADR completos en `lg_cylinders`

Actualmente existen 3 campos ADR. Se agregan los 9 restantes:

| columna | tipo | legacy |
|---------|------|--------|
| `adr_category` | VARCHAR(50) | ADR_Categoria (existente) |
| `adr_un_number` | VARCHAR(10) | ADR_UN (existente) |
| `adr_label` | VARCHAR(50) | ADR_Etiqueta (existente) |
| `adr_package_type` | VARCHAR(50) | ADR_TipoBulto (nuevo) |
| `adr_weight_kg` | NUMERIC(10, 2) | ADR_PesoKg (nuevo) |
| `adr_merchandise` | VARCHAR(200) | ADR_Mercancia (nuevo) |
| `adr_tunnel` | VARCHAR(10) | ADR_Tunel (nuevo) |
| `adr_subline` | VARCHAR(50) | ADR_Sublinea (nuevo) |
| `adr_factor` | NUMERIC(10, 2) | ADR_Factor (nuevo) |
| `adr_points` | INTEGER | ADR_Puntos (nuevo) |
| `adr_unit_measure` | VARCHAR(20) | ADR_UnidadMedida (nuevo) |

---

## Nuevas tablas

### `lg_gas_products` — catalogo transitorio de productos gas (cod_grupo legacy)

Cada envase contiene un tipo de gas (GLP, propano, butano, etc). En legacy `Producto.cod_grupo` se refiere a otro `Producto` que es el gas "padre".

Este catálogo queda como compatibilidad transitoria en `logistics`. El destino final es `prod_products` con `condition_code = 'GAS'`.

| columna | tipo | descripcion |
|---------|------|-------------|
| id | VARCHAR(36) PK | |
| tenant_id | VARCHAR(36) FK | |
| name | VARCHAR(120) | nombre del gas |
| code | VARCHAR(20) | codigo interno |
| content_kg | NUMERIC(10, 2) | contenido tipico en kg |
| unit | VARCHAR(20) | unidad de medida |
| is_active | BOOLEAN | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### `lg_brands` — catálogo transitorio de marcas de envase

Este catálogo queda como compatibilidad transitoria en `logistics`. El destino final es `prod_brands` del plugin `productos`.

| columna | tipo | descripcion |
|---------|------|-------------|
| id | VARCHAR(36) PK | |
| tenant_id | VARCHAR(36) FK | |
| name | VARCHAR(100) | nombre de marca |
| code | VARCHAR(20) | codigo interno |
| is_active | BOOLEAN | |
| created_at | TIMESTAMP | |

### `lg_cylinder_retimbrados` — retimbrado / reestampado

Equivalente a `Edetalle_retimbrado`. Datos tecnicos del retimbrado de un cilindro.

| columna | tipo | legacy | descripcion |
|---------|------|--------|-------------|
| id | VARCHAR(36) PK | | |
| cylinder_id | VARCHAR(36) FK | Cod_producto | |
| retimbrado_date | DATE | | fecha del retimbrado |
| manufacture_code | VARCHAR(50) | Codigo_fabricacion | codigo de fabricacion |
| manufacture_year | INTEGER | Anio_fabricacion | año de fabricacion |
| serial_number | VARCHAR(50) | Nro_Bombona | numero de bombona |
| weight_origin | NUMERIC(10, 2) | Peso_origen | peso original |
| weight_current | NUMERIC(10, 2) | Peso_actual | peso actual |
| service_pressure | NUMERIC(10, 2) | Presion_servicio | presion de servicio |
| test_pressure | NUMERIC(10, 2) | Presion_prueba | presion de prueba |
| approval_number | VARCHAR(50) | Nro_aprobacion | numero de aprobacion |
| danger_class | VARCHAR(50) | Clase_peligro | clase de peligro |
| marking1 | VARCHAR(50) | Marcado1 | marcado 1 |
| marking2 | VARCHAR(50) | Marcado2 | marcado 2 |
| package_format | VARCHAR(50) | Formato_Bulto | formato del bulto |
| transport_code | INTEGER | Transporte | codigo de transporte (nuevo vs mapeo) |
| adr_label | VARCHAR(50) | Etiqueta | etiqueta ADR |
| adr_tunnel | VARCHAR(10) | Tuneles | restriccion de tunel ADR |
| un_number | VARCHAR(10) | Nro_ONU | numero ONU |
| food_registry | VARCHAR(50) | Regist_Alimentario | registro alimentario (nuevo vs mapeo) |
| movement_id | VARCHAR(36) | | FK opcional al movimiento que origino el retimbrado |
| notes | TEXT | | |
| created_by | VARCHAR(36) FK | | |
| created_at | TIMESTAMP | | |
| updated_at | TIMESTAMP | | |

### `lg_cylinder_ownership` — historial de custodia

Equivalente a `Ecil_duenio`. Registra cambios de propiedad/custodia del cilindro.

| columna | tipo | descripcion |
|---------|------|-------------|
| id | VARCHAR(36) PK | |
| cylinder_id | VARCHAR(36) FK | |
| customer_id | VARCHAR(36) | persona/cliente |
| customer_name | VARCHAR(120) | |
| movement_id | VARCHAR(36) | FK al movimiento que causo el cambio |
| change_date | TIMESTAMP | fecha del cambio |
| condition | VARCHAR(50) | condicion al momento del cambio |
| notes | TEXT | |
| created_by | VARCHAR(36) FK | |
| created_at | TIMESTAMP | |

### `lg_cylinder_label_history` — historial de impresion de etiquetas

Equivalente a `ECilindroEtiquetaHistorial`.

| columna | tipo | descripcion |
|---------|------|-------------|
| id | VARCHAR(36) PK | |
| cylinder_id | VARCHAR(36) FK | |
| origin | VARCHAR(50) | ALTA, REIMPRESION, PLUS |
| reason | VARCHAR(200) | motivo (obligatorio en reimpresion) |
| printer_name | VARCHAR(150) | nombre de impresora |
| copies | INTEGER | numero de copias |
| printed_by | VARCHAR(36) FK | |
| printed_at | TIMESTAMP | |
| created_at | TIMESTAMP | |

### `lg_scan_log` — registro de escaneo movil

Equivalente a `LogEscaneo`. Registra cada escaneo de cilindro en campo.

| columna | tipo | descripcion |
|---------|------|-------------|
| id | VARCHAR(36) PK | |
| tenant_id | VARCHAR(36) FK | |
| movement_id | VARCHAR(36) FK | movimiento asociado |
| cylinder_id | VARCHAR(36) FK | cilindro escaneado |
| barcode_scanned | VARCHAR(150) | codigo de barras leido |
| service_type | VARCHAR(20) | VENTA, CANJE_ENTREGA, CANJE_RECOJO, ALQUILER, DEVOLUCION, RECHAZO, SPOT |
| user_id | VARCHAR(36) FK | quien escaneo |
| gps_lat | NUMERIC(10, 7) | latitud GPS |
| gps_lng | NUMERIC(10, 7) | longitud GPS |
| result | VARCHAR(20) | OK, ERROR |
| error_reason | TEXT | motivo de error si lo hubo |
| adr_validated | BOOLEAN | resultado validacion ADR |
| hydrotest_validated | BOOLEAN | resultado validacion PH |
| scanned_at | TIMESTAMP | |
| created_at | TIMESTAMP | |

### `lg_cylinder_services` — servicios sobre envase

Equivalente a `ECilindros_Servicios`.

| columna | tipo | descripcion |
|---------|------|-------------|
| id | VARCHAR(36) PK | |
| cylinder_id | VARCHAR(36) FK | |
| order_id | VARCHAR(36) FK | pedido asociado |
| order_item_id | VARCHAR(36) FK | detalle del pedido asociado |
| movement_id | VARCHAR(36) FK | movimiento asociado |
| service_type_id | VARCHAR(36) FK | tipo de servicio |
| status | VARCHAR(50) | PENDIENTE, REALIZADO, CANCELADO |
| start_date | TIMESTAMP | |
| end_date | TIMESTAMP | |
| notes | TEXT | |
| purchase_price | NUMERIC(19, 4) | precio de compra del servicio |
| sale_price | NUMERIC(19, 4) | precio de venta del servicio |
| stock_in | NUMERIC(19, 4) | stock de ingreso |
| stock_out | NUMERIC(19, 4) | stock de egreso |
| group_code | VARCHAR(50) | codigo de grupo de servicio |
| discount_pct | NUMERIC(5, 2) | porcentaje de descuento |
| discount_amount | NUMERIC(19, 4) | monto de descuento |
| total_amount | NUMERIC(19, 4) | total del servicio |
| created_by | VARCHAR(36) FK | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

### `lg_service_types` — catalogo de tipos de servicio

| columna | tipo | descripcion |
|---------|------|-------------|
| id | VARCHAR(36) PK | |
| tenant_id | VARCHAR(36) FK | |
| code | VARCHAR(50) | codigo interno |
| name | VARCHAR(120) | nombre del servicio |
| is_active | BOOLEAN | |
| created_at | TIMESTAMP | |

---

## Nuevos endpoints

### Catalogos extendidos

```
GET /catalog/gas-products     → lg_gas_products
GET /catalog/brands           → lg_brands
GET /catalog/service-types    → lg_service_types
```

### Cilindros extendidos

```
PATCH /cylinders/{id}               → actualizar campos nuevos (barcode, gas, ADR, precio, etc)
GET   /cylinders/by-serial/{serial} → busqueda por serial
GET   /cylinders/{id}/label-data    → datos para imprimir etiqueta
POST  /cylinders/{id}/retimbrados
GET   /cylinders/{id}/retimbrados
POST  /cylinders/{id}/retimbrados/{retimbrado_id}/validate → validar datos retimbrado
GET   /cylinders/{id}/ownership     → historial de custodia
POST  /cylinders/{id}/print-label   → registrar impresion de etiqueta
GET   /cylinders/{id}/label-history → historial de impresiones
      (los endpoints existentes de hydrotests y warranties se mantienen)
```

### Escaneo movil

```
POST /scan                       → procesar escaneo desde campo
                                 body: { movement_id, barcode_serial, service_type,
                                         gps_lat, gps_lng, user_id }
                                 valida ADR, PH, ejecuta transicion de estado
                                 registra en lg_scan_log
                                 retorna: { result, cylinder_id, state_before, state_after }
GET  /scan/log                   → historial de escaneos
GET  /scan/log/{movement_id}     → escaneos de un movimiento
```

### Servicios (envase)

```
POST /cylinders/{id}/services
GET  /cylinders/{id}/services
PATCH /cylinders/{id}/services/{service_id}
DELETE /cylinders/{id}/services/{service_id}
```

---

## Efecto del escaneo en el state machine

Al procesar un escaneo (`POST /scan`), el sistema debe:

1. Resolver el cilindro por `barcode_serial` (busca en `serial`, `barcode1` o `barcode2`)
2. Resolver el movimiento asociado
3. Validar ADR del cilindro segun tipo de movimiento
4. Validar PH vigente segun tipo de movimiento
5. Ejecutar la transicion de estado correspondiente:

| service_type | transicion |
|-------------|------------|
| VENTA | segun movement_type.target_state |
| CANJE_ENTREGA | segun movement_type.target_state |
| CANJE_RECOJO | EN_CLIENTE_VACIO → VACIO_EN_ALMACEN |
| DEVOLUCION | EN_CLIENTE_LLENO → EN_ALMACEN_VACIO |
| RECHAZO | estado actual → OBSERVADO |
| ALQUILER | segun movement_type.target_state |
| SPOT | segun movement_type.target_state |

6. Registrar en `lg_scan_log` con GPS, resultado validaciones, estado anterior y nuevo
7. Emitir evento `logistics.cylinder.scanned`

---

## Nuevos permisos

| permiso | descripcion |
|---------|-------------|
| `logistics.cylinder.update` | Editar datos del envase |
| `logistics.cylinder.delete` | Eliminacion logica de envase |
| `logistics.retimbrado.read` | Ver retimbrados |
| `logistics.retimbrado.manage` | Registrar/editar retimbrados |
| `logistics.scan.execute` | Ejecutar escaneo movil |
| `logistics.scan.read` | Ver historial de escaneos |
| `logistics.label.print` | Imprimir etiquetas |
| `logistics.label.read` | Ver historial de impresion |
| `logistics.ownership.read` | Ver historial de custodia |
| `logistics.service.read` | Ver servicios de envase |
| `logistics.service.manage` | Gestionar servicios de envase |
| `logistics.gas.read` | Ver catalogo de gases |
| `logistics.brand.read` | Ver catalogo de marcas |

---

## Nuevos eventos

| evento | cuando |
|--------|--------|
| `logistics.cylinder.updated` | Datos del cilindro modificados |
| `logistics.cylinder.retimbrado_registered` | Retimbrado registrado |
| `logistics.cylinder.scanned` | Cilindro escaneado en campo |
| `logistics.cylinder.label_printed` | Etiqueta impresa |
| `logistics.cylinder.ownership_changed` | Cambio de custodia registrado |
| `logistics.cylinder.service_registered` | Servicio registrado en envase |
| `logistics.cylinder.service_completed` | Servicio completado |

---

## Frontend

### Paginas existentes a modificar

- **CylinderDetailPage**: agregar pestanas o secciones para:
  - Datos generales (campos nuevos: gas, marca, barcode, ADR completo)
  - Retimbrados (tabla + formulario)
  - Servicios (tabla + formulario)
  - Custodia (historial de duenio)
  - Etiquetas (historial de impresion + boton imprimir)
  - Escaneos (historial si los hay)

### Formularios nuevos

- **RetimbradoForm**: fecha, codigo fabricacion, peso, presiones, nº aprobacion, clase peligro, marcados, ADR, ONU, registro alimentario
- **ServiceForm**: tipo servicio, fechas, precios, descuentos, notas
- **PrintLabelDialog**: seleccionar impresora, copias, motivo (si reimpresion)

### Widgets nuevos

- Ultimos escaneos en dashboard del plugin
- Alertas: cilindros con PH proximo a vencer, cilindros observados en campo

---

## Pruebas

- El modulo no se considera cerrado sin esta bateria minima de pruebas.

### Backend unitarias

- `CylinderService`: crear y actualizar cilindro con campos nuevos (`barcode1`, `barcode2`, gas, marca, ADR completo, condicion)
- `CylinderService`: unicidad de `serial`, `barcode1` y `barcode2` por tenant
- `CylinderService`: busqueda por `serial`, `barcode1` y `barcode2`
- `StateMachineService`: transiciones via escaneo para cada `service_type`
- `ScanService`: validacion ADR/PH, resolucion por `barcode1`/`barcode2`/`serial`, rechazo de doble escaneo
- `RetimbradoService`: CRUD, validacion de fechas, presiones y consistencia de datos tecnicos
- `OwnershipService`: registro automatico al confirmar movimiento
- `LabelService`: registro de impresion, obligar motivo en reimpresion
- `CylinderServiceService`: alta/edicion/cierre de servicios sobre el envase
- `pyright`: sin errores de tipos en backend del plugin y tests tocados
- `ruff check`: sin errores de lint en backend y tests tocados

### Backend integracion

- crear cilindro completo y consultar detalle expandido
- registrar PH y retimbrado, luego validar transicion que lo requiera
- registrar garantia y consultar historial combinado del envase
- crear movimiento con item de cilindro, escanearlo y verificar `lg_scan_log` + `lg_cylinder_state_log`
- confirmar movimiento y verificar registro de custodia
- imprimir etiqueta y verificar `lg_cylinder_label_history`
- crear servicio de envase y completarlo
- aislamiento por tenant en todos los endpoints nuevos
- permisos: cada nuevo endpoint retorna `403` sin permiso
- eventos: cada accion emite el evento esperado

### Frontend

- render de `CylinderDetailPage` con secciones nuevas
- formulario de retimbrado con validacion basica
- formulario de servicio con validacion basica
- dialogo de impresion de etiqueta con motivo obligatorio en reimpresion
- vistas de historial (custodia, etiquetas, escaneos) con estado vacio y estado con datos
- `pnpm build`: sin errores de tipos ni build roto por el frontend nuevo

---

## Orden de implementacion

```
Semana 1:
  - Migracion 004: campos nuevos en lg_cylinders + tablas nuevas
  - Seed de gas_products, brands, service_types
  - Extender schemas y service de cilindros (create/update con campos nuevos)
  - PATCH /cylinders/{id} + GET /cylinders/by-serial/{serial}
  - Tests de migracion y CRUD extendido

Semana 2:
  - Retimbrados: modelo, service, endpoints, frontend
  - Ownership: modelo, service, registro automatico en movimientos
  - Label history: modelo, endpoint, frontend
  - CylinderDetailPage renovada con pestanas
  - Tests de retimbrados, ownership y label history

Semana 3:
  - Escaneo: lg_scan_log, ScanService, POST /scan + GET /scan/log
  - Validacion ADR/PH en escaneo
  - Ejecucion de transiciones via escaneo
  - Frontend: historial de escaneos, alertas en dashboard
  - Servicios de envase: lg_cylinder_services + lg_service_types
  - Tests de escaneo, servicios y frontend
  - Bug fixing + ajustes de UX
  - corrida final completa: pytest + vitest + build + pyright + ruff check
```

---

## Criterios de aceptacion

1. Usuario puede crear cilindro con todos los campos del legacy relevantes al envase fisico (barcode, gas, ADR completo, etc.)
2. Usuario puede registrar retimbrados con datos tecnicos completos
3. Usuario puede ver historial de custodia del cilindro
4. Usuario puede imprimir etiqueta y registrar la impresion
5. Sistema procesa escaneo movil con validacion ADR y PH
6. Escaneo ejecuta transicion de estado correspondiente al service_type
7. Cada escaneo se registra con GPS, usuario, resultado y validaciones
8. Usuario puede ver historial de escaneos por movimiento
9. Usuario puede registrar servicios sobre el envase
10. Todo es tenant-scoped
11. Todos los endpoints retornan 403 sin permiso
12. Cada accion emite su evento en `event_log`
13. Frontend muestra datos completos del envase en CylinderDetailPage
14. No se rompen endpoints ni frontend existentes
15. Existe cobertura de pruebas suficiente para CRUD extendido, retimbrados, custodia, etiquetas, escaneo y servicios
16. `pytest`, `vitest`, `build`, `pyright` y `ruff check` pasan al cierre del trabajo
