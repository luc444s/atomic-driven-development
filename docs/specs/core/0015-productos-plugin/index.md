# SPEC 0015 — Plugin productos: Catálogo Maestro

## Estado

Aceptado

## Contexto

SYSTUTOR OSS maneja productos de forma fragmentada. `plugins/logistics/` tiene `lg_gas_products` y `lg_brands` como catálogos propios de gas, pero no existe un catálogo maestro. El análisis del legacy (`docs/database/modulo_productos/`) revela que la tabla `Producto` (~70 columnas, 0 FKs) es la entidad más referenciada del sistema legacy: ~100+ SPs, ~30 formularios, dependencias de stock, logística, ventas, compras, contabilidad y escaneo. Está acoplada a un solo formulario VB de 5,773 líneas (`FrmCatProductos.vb`) con bugs confirmados (IGV invertido, ADR no guardado, 38 parámetros inconsistentes, sin transacciones).

Esta spec describe la construcción del plugin `productos` como catálogo maestro normalizado, siguiendo el mismo patrón arquitectónico que `plugins/crm/`.

## Objetivo

Construir el plugin `productos` que gestione el catálogo completo de productos con:

- **Catálogos base**: línea, sublínea, marca, categoría/rubro, tipo de insumo, unidad de medida (con factores m3, litros, kg), condición del producto, subcategoría, grupo logístico, estado del producto.
- **Producto**: CRUD maestro con SKU, nombre, descripción, multi-unidad, multi-código de barras, imágenes.
- **Precios**: 4+ niveles de precio (unitario, intermedio, caja, lista2, lista3, lista4) historificados por vigencia.
- **Costos**: 5 tipos de costo (actual, reposición, anterior, CGI, total) historificados.
- **ADR**: configuración de mercancías peligrosas con vigencias (reemplaza `Edetalle_Producto_Bombona` y corrige el bug legacy).
- **Impuestos**: IGV (exonerado/gravado), percepción, comisión externa por producto.
- **Media**: imágenes de producto y códigos de barras (filesystem local, preparado para Cloudflare R2).
- **Promociones**: promociones simples por producto (minimal, extraíble a plugin independiente).

## No objetivos

- Stock actual, stock mínimo/máximo por almacén (va en módulo Stock futuro).
- Retimbrado de bombonas (pertenece al ciclo de vida del envase en logistics).
- Estado de cilindros / trazabilidad de cilindros (pertenece a logistics).
- Precios especiales por cliente (`Tarifa_cliente`) — van en CRM (ADR 0012).
- Descuentos por cliente o línea — van en CRM (futuro).
- Migración de datos legacy (se hará desde `tools/migrator/` con CSV + manifest).
- Facturación electrónica, contabilidad o cálculo de impuestos en tiempo real.
- Generación de códigos de barras en imagen (se externaliza a librería JS/Python).

## Alcance

El plugin toca exclusivamente:

- `plugins/productos/` — plugin completo (backend + frontend + migraciones + permisos + eventos).
- `plugins/logistics/` — Fase 2: agregar FKs opcionales hacia `prod_products` y `prod_brands`.
- `plugins/logistics/plugin.json` — Fase 3: agregar `"requires": ["productos"]`.

---

## 1. Modelo de datos

### Convenciones generales

- **IDs**: UUID string (PK), generados con `uuid4()`.
- **Tenant**: todas las tablas con datos por tenant tienen `tenant_id` FK a `tenants.id`.
- **Auditoría**: `created_at`, `updated_at` en todas las tablas; `created_by` solo en tablas críticas.
- **Soft delete**: `is_active = False`, no se eliminan registros físicamente.
- **Nombres**: prefijo `prod_` para tablas del plugin.

### 1.1 Catálogos base

#### prod_lines (línea)

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| code | String(20) | NN |
| name | String(100) | NN |
| category_id | String(36) | FK → prod_categories (rubro), NULL |
| description | String(200) | NULL |
| is_active | Boolean | NN, default TRUE |
| created_at | DateTime(tz) | NN |
| updated_at | DateTime(tz) | NN |

UK: `(tenant_id, code)`

#### prod_subline (sublínea)

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| code | String(20) | NN |
| name | String(100) | NN |
| line_id | String(36) | FK → prod_lines, NN |
| is_active | Boolean | NN, default TRUE |
| created_at | DateTime(tz) | NN |
| updated_at | DateTime(tz) | NN |

UK: `(tenant_id, code, line_id)`

#### prod_brands (marca — reemplaza `lg_brands`)

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| code | String(20) | NN |
| name | String(100) | NN |
| description | String(200) | NULL |
| is_active | Boolean | NN, default TRUE |
| created_at | DateTime(tz) | NN |
| updated_at | DateTime(tz) | NN |

UK: `(tenant_id, code)`

#### prod_categories (rubro/categoría)

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| code | String(20) | NN |
| name | String(100) | NN |
| is_active | Boolean | NN, default TRUE |
| created_at | DateTime(tz) | NN |
| updated_at | DateTime(tz) | NN |

#### prod_insumo_types (tipo de insumo)

Mismas columnas que `prod_categories`.

#### prod_units (unidad de medida)

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| code | String(20) | NN |
| name | String(50) | NN |
| equivalencia | Integer | NULL (1 = unidad base) |
| m3_factor | Float | NULL |
| liter_factor | Float | NULL |
| kg_factor | Float | NULL |
| is_active | Boolean | NN, default TRUE |
| created_at | DateTime(tz) | NN |
| updated_at | DateTime(tz) | NN |

#### prod_conditions (condición del producto)

Tabla de catálogo fijo (seeded). Reemplaza valores hardcodeados `CILPRO/CILCLI/…`.

| Columna | Tipo | Constraint |
|---------|------|------------|
| code | String(20) | PK (PRODUCTO, GAS, CILPRO, CILCLI, CILPROV, CILGAR, SERVICIO) |
| name | String(100) | NN |
| description | String(200) | NULL |
| is_active | Boolean | NN, default TRUE |

#### prod_subcategories (subcategoría)

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| code | String(20) | NN (GAS, BOMBONAS, PRODUCTOS, SERVICIOS) |
| name | String(50) | NN |
| is_active | Boolean | NN, default TRUE |

#### prod_groups (grupo logístico — reemplaza `Grupo` legacy)

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| code | String(20) | NN |
| name | String(50) | NN |
| gas_product_id | String(36) | FK → prod_products, NULL |
| line_id | String(36) | FK → prod_lines, NULL |
| subline_id | String(36) | FK → prod_subline, NULL |
| unit_id | String(36) | FK → prod_units, NULL |
| is_active | Boolean | NN, default TRUE |

UK: `(tenant_id, code)`

`prod_groups` es un catálogo de clasificación logística/comercial. No almacena precios operativos.

#### prod_status (estado del producto)

| Columna | Tipo | Constraint |
|---------|------|------------|
| code | String(20) | PK |
| name | String(50) | NN |
| is_active | Boolean | NN, default TRUE |

### 1.2 Tabla principal

#### prod_products (núcleo del producto)

| Columna | Tipo | Constraint | Notas |
|---------|------|------------|-------|
| id | String(36) | PK | |
| tenant_id | String(36) | FK → tenants, NN | |
| legacy_id | Integer | NULL | Trazabilidad migración |
| sku | String(30) | NN | Código propio / `Nro_Producto` legacy |
| name | String(200) | NN | `Desc_Producto` legacy |
| description | Text | NULL | |
| short_description | String(500) | NULL | `Nro_cja` legacy (descripción corta con metadata) |
| line_id | String(36) | FK → prod_lines, NN | |
| subline_id | String(36) | FK → prod_subline, NULL | |
| brand_id | String(36) | FK → prod_brands, NULL | `Marca_Producto` legacy |
| insumo_type_id | String(36) | FK → prod_insumo_types, NULL | |
| unit_id | String(36) | FK → prod_units, NN | Unidad principal |
| box_unit_id | String(36) | FK → prod_units, NULL | Unidad de caja |
| qty_per_box | Numeric(10,2) | NULL | `cant` legacy (cantidad por caja) |
| subcategory_id | String(36) | FK → prod_subcategories, NULL | |
| group_id | String(36) | FK → prod_groups, NULL | |
| status_code | String(20) | FK → prod_status, NN | |
| condition_code | String(20) | FK → prod_conditions, NN | PRODUCTO, GAS, CILPRO… |
| weight_kg | Numeric(10,3) | NULL | `peso_producto` legacy |
| content_m3 | Numeric(10,4) | NULL | `M3` legacy |
| country_code | String(5) | NULL, default NULL | Solo informativo, sin lógica de país |
| delivery_time | Eliminado | — | No vive en productos; corresponde al dominio de envases/logistics |
| is_service | Boolean | NN, default FALSE | `servicio` legacy |
| is_active | Boolean | NN, default TRUE | |
| created_by | String(36) | FK → users, NN | |
| created_at | DateTime(tz) | NN | |
| updated_at | DateTime(tz) | NN | |

UK: `(tenant_id, sku)`
Index: `(tenant_id, name)` para búsqueda ILIKE
Index: `(tenant_id, line_id)`
Index: `(tenant_id, condition_code)`
Index: `(tenant_id, is_active)`

### 1.3 Tablas hijas

#### prod_barcodes

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| product_id | String(36) | FK → prod_products, NN |
| barcode_type | String(20) | NN (CABYS, MATRICULA, GS1, INTERNAL) |
| barcode | String(150) | NN |
| is_primary | Boolean | NN, default FALSE |
| is_active | Boolean | NN, default TRUE |
| created_at | DateTime(tz) | NN |
| updated_at | DateTime(tz) | NN |

UK: `(tenant_id, barcode_type, barcode)`

Regla: `is_primary` es la unica forma de marcar el codigo principal.

#### prod_prices

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| product_id | String(36) | FK → prod_products, NN |
| price_list | String(20) | NN (UNITARIO, INTERMEDIO, CAJA, LISTA2, LISTA3, LISTA4) |
| amount | Numeric(12,2) | NN |
| currency | String(3) | NN |
| valid_from | Date | NN |
| valid_to | Date | NULL (NULL = vigente actual) |
| created_by | String(36) | FK → users, NN |
| created_at | DateTime(tz) | NN |

Index: `(product_id, price_list, valid_from DESC)`

#### prod_costs

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| product_id | String(36) | FK → prod_products, NN |
| cost_type | String(20) | NN (ACTUAL, REPOSICION, ANTERIOR, CGI, TOTAL) |
| amount | Numeric(12,2) | NN |
| currency | String(3) | NN |
| valid_from | Date | NN |
| valid_to | Date | NULL |
| created_by | String(36) | FK → users, NN |
| created_at | DateTime(tz) | NN |

Index: `(product_id, cost_type, valid_from DESC)`

#### prod_tax_config

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| product_id | String(36) | FK → prod_products, NN |
| tax_type | String(20) | NN (IGV, PERCEPCION, COMISION_EXT) |
| value | Numeric(5,2) | NULL |
| is_exempt | Boolean | NN, default FALSE |
| valid_from | Date | NN |
| valid_to | Date | NULL |
| created_at | DateTime(tz) | NN |

#### prod_adr (reemplaza ADR_* en Producto + Edetalle_Producto_Bombona)

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| product_id | String(36) | FK → prod_products, NN |
| category | String(50) | NULL | `ADR_Categoria` legacy |
| packaging_type | String(50) | NULL | `ADR_TipoBulto` legacy |
| net_weight_kg | Numeric(10,2) | NULL | `ADR_PesoKg` legacy |
| net_volume_m3 | Numeric(10,4) | NULL | `ADR_M3` legacy |
| un_number | String(10) | NULL | `ADR_UN` legacy |
| cargo_description | Text | NULL | `ADR_Mercancia` legacy |
| label | String(50) | NULL | `ADR_Etiqueta` legacy |
| tunnel_restriction | String(10) | NULL | `ADR_Tunel` legacy |
| subline_id | String(36) | FK → prod_subline, NULL | `ADR_Sublinea` legacy |
| factor | Integer | NULL | `ADR_Factor` legacy |
| points | Integer | NULL | `ADR_Puntos` legacy |
| unit_measure | String(20) | NULL | `ADR_UnidadMedida` legacy |
| valid_from | Date | NN |
| valid_to | Date | NULL (NULL = vigente actual) |
| created_by | String(36) | FK → users, NN |
| created_at | DateTime(tz) | NN |

Index: `(product_id, valid_from DESC)`

#### prod_media

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| product_id | String(36) | FK → prod_products, NN |
| media_type | String(20) | NN (PHOTO, BARCODE_IMAGE, DOC) |
| url | String(500) | NN |
| is_primary | Boolean | NN, default FALSE |
| created_at | DateTime(tz) | NN |

#### prod_promotions

| Columna | Tipo | Constraint |
|---------|------|------------|
| id | String(36) | PK |
| tenant_id | String(36) | FK → tenants, NN |
| product_id | String(36) | FK → prod_products, NN |
| name | String(200) | NULL |
| condition | String(20) | NN (CANTIDAD, PORCENTAJE, OFERTA) |
| qty_required | Integer | NULL |
| discount_percent | Numeric(5,2) | NULL |
| unit_price | Numeric(12,2) | NULL |
| box_price | Numeric(12,2) | NULL |
| valid_from | Date | NN |
| valid_to | Date | NULL |
| is_active | Boolean | NN, default TRUE |
| created_by | String(36) | FK → users, NN |
| created_at | DateTime(tz) | NN |
| updated_at | DateTime(tz) | NN |

---

## 2. API endpoints

### 2.1 Catálogos base

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/catalog/lines` | Listar líneas |
| `POST` | `/catalog/lines` | Crear línea |
| `PUT` | `/catalog/lines/{id}` | Actualizar línea |
| `GET` | `/catalog/subline` | Listar sublíneas |
| `POST` | `/catalog/subline` | Crear sublínea |
| `PUT` | `/catalog/subline/{id}` | Actualizar sublínea |
| `GET` | `/catalog/brands` | Listar marcas |
| `POST` | `/catalog/brands` | Crear marca |
| `PUT` | `/catalog/brands/{id}` | Actualizar marca |
| `GET` | `/catalog/categories` | Listar categorías/rubros |
| `POST` | `/catalog/categories` | Crear categoría |
| `PUT` | `/catalog/categories/{id}` | Actualizar categoría |
| `GET` | `/catalog/insumo-types` | Listar tipos de insumo |
| `POST` | `/catalog/insumo-types` | Crear tipo de insumo |
| `PUT` | `/catalog/insumo-types/{id}` | Actualizar tipo de insumo |
| `GET` | `/catalog/units` | Listar unidades |
| `POST` | `/catalog/units` | Crear unidad |
| `PUT` | `/catalog/units/{id}` | Actualizar unidad |
| `GET` | `/catalog/conditions` | Listar condiciones |
| `GET` | `/catalog/subcategories` | Listar subcategorías |
| `GET` | `/catalog/groups` | Listar grupos |
| `POST` | `/catalog/groups` | Crear grupo |
| `PUT` | `/catalog/groups/{id}` | Actualizar grupo |

### 2.2 Productos

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/products` | Listar productos (paginado, filtros: sku, name, line_id, brand_id, condition_code, is_active) |
| `GET` | `/products/{id}` | Obtener producto completo (precios, costos, barcodes, ADR, taxes, media, promotion activa) |
| `POST` | `/products` | Crear producto |
| `PUT` | `/products/{id}` | Actualizar producto (cabecera) |
| `PATCH` | `/products/{id}/status` | Cambiar estado (activo/inactivo) |
| `GET` | `/products/search?q=` | Búsqueda rápida por texto (sku, name, barcode) — para autocomplete/combobox |

### 2.3 Precios

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/products/{id}/prices` | Histórico de precios del producto |
| `POST` | `/products/{id}/prices` | Agregar nuevo precio (vigente desde hoy) |
| `POST` | `/products/{id}/prices/{price_id}/supersede` | Cerrar vigencia actual y crear nueva versión |
| `POST` | `/products/{id}/prices/update-all` | Crear nueva versión vigente para múltiples listas de precio en un solo call |

### 2.4 Costos

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/products/{id}/costs` | Histórico de costos |
| `POST` | `/products/{id}/costs` | Agregar nuevo costo |
| `POST` | `/products/{id}/costs/{cost_id}/supersede` | Cerrar vigencia actual y crear nueva versión |

### 2.5 Códigos de barras

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/products/{id}/barcodes` | Listar códigos de barras |
| `POST` | `/products/{id}/barcodes` | Agregar código de barras |
| `PUT` | `/products/{id}/barcodes/{barcode_id}` | Actualizar código |
| `DELETE` | `/products/{id}/barcodes/{barcode_id}` | Eliminar código |
| `POST` | `/products/{id}/barcodes/{barcode_id}/set-primary` | Marcar como principal |

### 2.6 ADR

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/products/{id}/adr` | Listar configuraciones ADR (histórico) |
| `POST` | `/products/{id}/adr` | Crear/actualizar ADR vigente |
| `PUT` | `/products/{id}/adr/{adr_id}` | Actualizar configuración ADR |
| `POST` | `/products/{id}/adr/{adr_id}/expire` | Cerrar vigencia (set valid_to = today) |

### 2.7 Impuestos

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/products/{id}/tax` | Configuración de impuestos |
| `PUT` | `/products/{id}/tax` | Actualizar impuestos del producto |

### 2.8 Media

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/products/{id}/media` | Listar media |
| `POST` | `/products/{id}/media` | Subir archivo (multipart) |
| `DELETE` | `/products/{id}/media/{media_id}` | Eliminar archivo |
| `POST` | `/products/{id}/media/{media_id}/set-primary` | Marcar como principal |

### 2.9 Promociones

| Método | Path | Descripción |
|--------|------|-------------|
| `GET` | `/products/{id}/promotions` | Listar promociones del producto |
| `POST` | `/products/{id}/promotions` | Crear promoción |
| `PUT` | `/promotions/{promotion_id}` | Actualizar promoción |
| `DELETE` | `/promotions/{promotion_id}` | Eliminar promoción |

---

## 3. Permisos

```
productos.catalog.read        — Ver catálogos (líneas, marcas, unidades, etc.)
productos.catalog.manage      — CRUD de catálogos base
productos.product.read        — Ver productos
productos.product.create      — Crear productos
productos.product.update      — Actualizar productos
productos.product.delete      — Desactivar productos
productos.price.read          — Ver precios
productos.price.manage        — Actualizar precios
productos.cost.read           — Ver costos
productos.cost.manage         — Actualizar costos
productos.adr.read            — Ver ADR
productos.adr.manage          — Gestionar ADR
productos.media.manage        — Gestionar imágenes
productos.promotion.read      — Ver promociones
productos.promotion.manage    — Gestionar promociones
```

Nota: el runtime actual del core exige permisos con formato exacto `<module>.<resource>.<action>` (ADR 0003). Por eso la implementación final usa `productos.price.read` y no permisos de cuatro segmentos.

---

## 4. Eventos

```
productos.product.created
productos.product.updated
productos.product.status_changed
productos.product.price_changed
productos.product.cost_changed
productos.product.adr_updated
productos.product.barcode_added
productos.brand.created
productos.brand.updated
productos.line.created
productos.line.updated
productos.promotion.created
productos.promotion.updated
productos.promotion.expired
```

---

## 5. Reglas de negocio

### 5.1 SKU único por tenant
El campo `sku` debe ser único dentro del tenant. Se valida al insertar y al modificar.

### 5.2 Código de barras principal
Cada producto puede tener múltiples códigos de barras, pero exactamente uno debe ser `is_primary = TRUE`. Al marcar uno como principal, los demás pasan a `is_primary = FALSE`.

### 5.3 Precios historificados
Los precios no se actualizan in-place. Cada cambio inserta una nueva fila y cierra la anterior (`valid_to = today`). El precio vigente es el que tiene `valid_to IS NULL`.

`prod_groups` no puede almacenar listas de precio ni valores derivados de precio.

### 5.4 Costos historificados
Misma regla que precios. `valid_to IS NULL` = costo vigente.

### 5.5 ADR con vigencias
Misma regla. Solo una fila ADR puede tener `valid_to IS NULL` por producto. Al crear una nueva, se cierra la anterior.

### 5.6 IGV exonerado explícito
`is_exempt = TRUE` en `prod_tax_config` para `tax_type = 'IGV'` significa producto exonerado. No hay lógica inversa como en el legacy.

### 5.7 Condiciones de producto
Los valores `PRODUCTO`, `GAS`, `CILPRO`, `CILCLI`, `CILPROV`, `CILGAR`, `SERVICIO` son catálogo en BD, no strings hardcodeados. Un producto puede cambiar de condición (ej. bombona que pasa de CILPRO a CILCLI).

### 5.8 Promociones
Una promoción `condition = 'CANTIDAD'` aplica descuento cuando se compran `qty_required` unidades. `condition = 'PORCENTAJE'` aplica `discount_percent`. `condition = 'OFERTA'` establece `unit_price` / `box_price` fijo.

### 5.9 Precedencia de precio efectivo
Cuando otro módulo necesite resolver el precio efectivo de venta, la precedencia es:

1. tarifa especial por cliente en CRM (`Tarifa_cliente` migrada);
2. promoción activa del producto en `prod_promotions`;
3. precio vigente base del producto en `prod_prices`.

`productos` no resuelve overrides por cliente. Ese ownership vive en CRM.

### 5.10 Moneda explícita
`currency` debe enviarse explícitamente al crear precios y costos. El plugin no asume una moneda país por defecto.

### 5.11 Snapshots transaccionales
Los módulos consumidores pueden conservar `product_name` como snapshot histórico de lectura en tablas transaccionales, pero la relación maestra debe ser `product_id` con FK a `prod_products`.

---

## 6. Frontend

### 6.1 Páginas

- **`ProductListPage.tsx`** — Tabla con filtros (nombre, SKU, línea, marca, condición, activo/inactivo) + paginación.
- **`ProductFormPage.tsx`** — Formulario multi-pestaña:
  - Datos generales (nombre, SKU, línea, marca, subcategoría, condición, unidad, peso)
  - Precios y costos (tabla de niveles con histórico)
  - Códigos de barras (lista con tipo y selector de principal)
  - ADR (formulario con vigencias)
  - Impuestos (IGV, percepción, comisión)
  - Media (upload de imágenes)
  - Promociones (tabla simple)
- **`ProductDetailPage.tsx`** — Vista de solo lectura con todos los datos.
- **`CatalogManagerPage.tsx`** — Gestión de catálogos base (líneas, marcas, unidades, etc.) con tabla CRUD simple.

### 6.2 Componentes reutilizables

- **`ProductSearchDialog.tsx`** — Modal de búsqueda de productos para usar desde otros plugins (logistics, ventas, compras). Soportes: búsqueda por texto, selección única, callback onSelect, muestra SKU + nombre + marca.

---

## 7. Migración desde logistics (Fases)

### Fase 1 — Plugin nuevo (esta spec)

- Se crea `plugins/productos/` con todos los modelos, endpoints, frontend.
- Logistics sigue usando `lg_gas_products` y `lg_brands`.
- No hay FKs cruzadas todavía.

### Fase 2 — Punto de integración

- Se agregan columnas opcionales en logistics:
  - `lg_orders.product_id` FK opcional → `prod_products.id`
  - `lg_movements.product_id` FK opcional → `prod_products.id`
  - `lg_gas_products.product_id` FK opcional → `prod_products.id`
  - `lg_brands.product_id` FK opcional → `prod_brands.id` (o se migra directo)
- Los servicios de logistics pueden leer de ambas tablas.
- Las tablas transaccionales pueden mantener `product_name` como snapshot histórico, pero toda nueva relación debe capturar `product_id` cuando ya exista en `productos`.

### Fase 3 — Corte

- Se migran datos de `lg_gas_products` → `prod_products` con `condition_code = 'GAS'`.
- Se migran datos de `lg_brands` → `prod_brands`.
- Las FKs opcionales pasan a obligatorias.
- Se eliminan `lg_gas_products` y `lg_brands`.
- Logistics declara `"requires": ["productos"]`.

---

## 8. Criterios de aceptación

### 8.1 Funcionales

1. Crear un producto completo con: datos generales, 3 códigos de barras, 4 niveles de precio, 2 costos, IGV exonerado, ADR vigente y una imagen. → El producto se guarda y se recupera completo.
2. Modificar el precio de un producto. → El precio anterior queda con `valid_to` y el nuevo con `valid_to IS NULL`.
3. Buscar productos por SKU, nombre y código de barras. → Los 3 métodos retornan el producto correcto.
4. Desactivar un producto. → Ya no aparece en listados activos.
5. Agregar una segunda configuración ADR a un producto. → La primera se cierra automáticamente (`valid_to = hoy`).
6. Crear una promoción de cantidad (3 unidades, 10% descuento). → Se guarda y se recupera.

### 8.2 Integración

7. `npm run migrate:plugins` ejecuta las migraciones de `plugins/productos/` sin errores.
8. Los endpoints responden con 422 si falta `tenant_id` en contexto.
9. No se puede crear un producto con `sku` duplicado en el mismo tenant.
10. No se puede crear un producto con `line_id` inexistente.
11. No se puede marcar más de un barcode activo como principal para el mismo producto.
12. La resolución de precio efectivo respeta la precedencia: CRM > promoción > precio base.

### 8.3 Calidad

13. `ruff check plugins/productos/` → 0 errores.
14. `pyright plugins/productos/` → 0 errores.
15. `pytest plugins/productos/` → todas las pruebas pasan.

---

## 9. Dependencias

- Runtime de plugins (existe y funciona).
- Kernel: auth JWT, multi-tenant, RBAC, auditoría, event bus.
- No depende de CRM ni logistics.

---

## 10. Referencias

- ADR 0015: Plugin productos — decisión arquitectónica
- `docs/database/modulo_productos/` — análisis completo del legacy (13 archivos)
- `docs/database/modulo_stock/` — análisis de stock (dependencia de productos)
- ADR 0012: CRM Plugin de Clientes
- ADR 0004: Runtime de Plugins
- ADR 0006: Migración Legacy CSV Manifest
