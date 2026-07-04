# Avance: Módulo Productos

## Propósito

Documentar el estado actual del módulo `productos`, sus decisiones de arquitectura ya cerradas, sus límites con `logistics` y `crm`, y el orden correcto de implementación para reducir ambigüedad durante la construcción del plugin.

Este documento debe leerse antes de implementar o refactorizar cualquier parte de `plugins/productos/`.

---

## 1. Estado actual

### Identidad

| Propiedad | Valor |
|---|---|
| Plugin ID | `productos` |
| Estado | **Cerrado** — listo para integración con otros plugins |
| ADR principal | `docs/adr/0015-productos-plugin.md` |
| Spec principal | `docs/specs/core/0015-productos-plugin/index.md` |
| Implementación real | Backend + Frontend completos |

### Situación del dominio

- **EL PLUGIN ESTÁ CERRADO** — backend + frontend completos, listo para integración con otros plugins;
- `logistics` sigue operando con `lg_gas_products` y `lg_brands` (catálogos transitorios);
- el legacy `Producto` mezclaba identidad, precios, costos, ADR, impuestos, imágenes y stock en una sola tabla;
- ADR 0015 y SPEC 0015 ya cerraron la separación del dominio y su ownership.

### Lectura correcta del estado

- `productos` **SÍ existe como plugin implementado** con todos los modelos, endpoints y frontend;
- `logistics` sigue operando con su modelo actual (convivencia temporal);
- la creación de `productos` no implica todavía una migración profunda de `logistics`;
- la integración completa con `logistics` está definida por fases, no para la primera iteración.

---

## 1.1 Inventario de implementación real

### Backend (`plugins/productos/backend/`)

| Archivo | Estado | Líneas | Contenido |
|---------|--------|--------|-----------|
| `models.py` | ✅ Completo | 424 | Todos los modelos ORM: ProductCondition, ProductStatus, ProductCategory, ProductLine, ProductSubline, ProductBrand, ProductInsumoType, ProductUnit, ProductSubcategory, ProductGroup, Product, ProductBarcode, ProductPrice, ProductCost, ProductTaxConfig, ProductAdr, ProductMedia, ProductPromotion |
| `schemas.py` | ✅ Completo | ~600 | Todos los schemas Pydantic para request/response |
| `router.py` | ✅ Completo | 1549 | Todos los endpoints: catálogos, productos, precios, costos, barcodes, ADR, impuestos, media, promociones |
| `plugin.py` | ✅ Completo | - | Registro del plugin con rutas |
| `common.py` | ✅ Completo | - | Utilidades compartidas |
| `services/products.py` | ✅ Completo | - | CRUD productos, búsqueda |
| `services/catalog.py` | ✅ Completo | - | CRUD catálogos base |
| `services/pricing.py` | ✅ Completo | - | Gestión precios historificados |
| `services/barcode.py` | ✅ Completo | - | Gestión códigos de barras |
| `services/adr.py` | ✅ Completo | - | Gestión ADR con vigencias |
| `services/media.py` | ✅ Completo | - | Upload/gestión imágenes |
| `services/promotions.py` | ✅ Completo | - | Gestión promociones |

### Frontend (`plugins/productos/frontend/`)

| Archivo | Estado | Contenido |
|---------|--------|-----------|
| `register.tsx` | ✅ Completo | Registro de rutas y componentes |
| `api.ts` | ✅ Completo | Funciones API |
| `types.ts` | ✅ Completo | Tipos TypeScript |
| `components/ModalNuevoProducto.tsx` | ✅ Completo | Formulario creación/edición |
| `components/ModalDetalleProducto.tsx` | ✅ Completo | Vista detalle completa |
| `components/ModalCatalogo.tsx` | ✅ Completo | Gestión catálogos |
| `components/ProductSearchDialog.tsx` | ✅ Completo | Búsqueda reutilizable |
| `components/ProductosSection.tsx` | ✅ Completo | Sección contenedora |
| `pages/ProductListPage.tsx` | ✅ Completo | Listado principal |
| `pages/ProductFormPage.tsx` | ✅ Completo | Formulario (legacy, reemplazado por modal) |
| `pages/ProductDetailPage.tsx` | ✅ Completo | Detalle (legacy, reemplazado por modal) |
| `pages/CatalogManagerPage.tsx` | ✅ Completo | Catálogos (legacy, reemplazado por modal) |

### Migraciones

| Archivo | Estado |
|---------|--------|
| `migrations/001_initial_productos.py` | ✅ Completa |

### Permisos y eventos

| Tipo | Estado | Cantidad |
|------|--------|----------|
| Permisos | ✅ Completos | 15 (catalog, product, price, cost, adr, media, promotion) |
| Eventos | ✅ Completos | 14 (product, brand, line, promotion) |

---

## 2. Decisiones ya cerradas

### 2.1 El plugin se llama `productos`

- nombre de negocio y de plugin: `productos`;
- no se usará `products` como ID principal del plugin.

### 2.2 Productos es el catálogo maestro futuro

- el catálogo maestro de productos vive en `plugins/productos/`;
- el ownership de marcas también vive ahí;
- `logistics` no debe consolidar a largo plazo su propio catálogo de gas ni de marcas.

### 2.3 `lg_gas_products` y `lg_brands` son transitorios

- siguen existiendo porque forman parte del estado actual de `logistics`;
- no son el destino final del dominio;
- el destino final es:
  - `prod_products`
  - `prod_brands`

### 2.4 Pricing y costos tienen una sola fuente de verdad

- precios vigentes e históricos viven solo en `prod_prices`;
- costos vigentes e históricos viven solo en `prod_costs`;
- no deben existir listas de precio operativas en `prod_groups`;
- `logistics` no debe convertirse en dueño de pricing.

### 2.5 Precedencia de precio efectiva

Cuando otro módulo necesite resolver el precio efectivo de venta:

1. tarifa especial por cliente en CRM;
2. promoción activa del producto;
3. precio base vigente del producto.

### 2.6 `Tarifa_cliente` vive en CRM

- los precios especiales por cliente no pertenecen a `productos`;
- `productos` es dueño del precio base y promociones;
- CRM es dueño del override por cliente.

### 2.7 ADR de producto vs datos del cilindro

- la configuración ADR del producto transportado pertenece a `productos`;
- retimbrado, PH, propiedad, custodia, servicios y trazabilidad física del cilindro siguen en `logistics`;
- no mezclar el catálogo ADR del producto con la vida operativa del envase.

### 2.8 Stock no entra en esta iteración

- stock actual, stock mínimo y stock por almacén no se implementan en `productos`;
- ese ownership pertenece al módulo `stock` (ya implementado).

### 2.9 Moneda explícita

- `productos` no asume una moneda país por defecto;
- `currency` debe enviarse explícitamente al guardar precios y costos.

### 2.10 Media preparada para R2

- fase inicial: filesystem local;
- diseño preparado para Cloudflare R2;
- la aplicación guarda URL o referencia de storage, no blobs gigantes en tablas base.

---

## 3. Qué incluye el módulo

### Submódulos funcionales de `productos`

| Submódulo | Contenido |
|---|---|
| Catálogos base | línea, sublínea, marca, categoría, tipo de insumo, unidad, condición, subcategoría, grupo, estado |
| Producto | CRUD maestro, SKU, descripción, unidad principal, unidad de caja, relación con marca/línea/grupo |
| Barcodes | múltiples códigos por producto, un único principal |
| Precios | histórico por vigencia |
| Costos | histórico por vigencia |
| ADR | configuración ADR del producto con vigencias |
| Impuestos | IGV, percepción, comisión externa |
| Media | imágenes y archivos relacionados |
| Promociones | promociones simples por producto |

### Tablas esperadas

- `prod_lines`
- `prod_subline`
- `prod_brands`
- `prod_categories`
- `prod_insumo_types`
- `prod_units`
- `prod_conditions`
- `prod_subcategories`
- `prod_groups`
- `prod_status`
- `prod_products`
- `prod_barcodes`
- `prod_prices`
- `prod_costs`
- `prod_tax_config`
- `prod_adr`
- `prod_media`
- `prod_promotions`

---

## 4. Qué NO incluye el módulo

- stock actual;
- stock mínimo/máximo por almacén;
- kardex;
- movimientos de inventario;
- retimbrado de cilindros;
- pruebas hidrostáticas;
- estado/ciclo de vida del cilindro;
- tarifas especiales por cliente;
- descuentos por cliente o por línea;
- facturación;
- contabilidad;
- cobranzas;
- migración legacy en esta primera iteración.

---

## 5. Relación con otros módulos

### Con `logistics`

#### Ahora

- `logistics` sigue usando `lg_gas_products` y `lg_brands`;
- no se hace todavía refactor profundo del plugin;
- se permite convivencia temporal.

#### Después

Fase 2:

- agregar FKs opcionales hacia `prod_products` y `prod_brands`;
- permitir que nuevas relaciones ya capturen `product_id` maestro.

Fase 3:

- migrar `lg_gas_products` hacia `prod_products` con `condition_code = 'GAS'`;
- migrar `lg_brands` hacia `prod_brands`;
- volver obligatorias las nuevas FKs;
- eliminar los catálogos transitorios de `logistics`.

#### Regla importante

- `product_name` puede sobrevivir como snapshot histórico de lectura en tablas transaccionales;
- `product_id` será la referencia maestra futura.

### Con `crm`

- CRM es dueño de la tarifa especial por cliente;
- `productos` no debe duplicar esa lógica;
- cualquier cálculo de precio efectivo debe respetar la precedencia ya definida.

### Con `stock`

- `productos` define el catálogo;
- `stock` define existencias, mínimos, máximos, ledger y disponibilidad (ya implementado).

---

## 6. Reglas de implementación que no deben romperse

### 6.1 No duplicar pricing

No agregar:

- precios operativos en `prod_groups`;
- precios operativos en tablas de `logistics` como fuente maestra;
- defaults escondidos que repliquen listas de precio.

### 6.2 No editar histórico in-place

- precios, costos y ADR se versionan;
- un cambio crea nueva fila y cierra la vigencia anterior;
- no reescribir el histórico vigente como si fuera un registro mutable cualquiera.

### 6.3 Un solo barcode principal

- un producto puede tener muchos códigos;
- solo uno puede ser principal al mismo tiempo;
- `barcode_type` no reemplaza la semántica de `is_primary`.

### 6.4 No reintroducir país duro

- no poner `PEN` como default silencioso;
- no meter lógica fiscal por país dentro del núcleo del catálogo de producto;
- `country_code` es informativo salvo que se defina otra decisión futura.

### 6.5 No volver a meter catálogo maestro en `logistics`

- si una necesidad de `logistics` parece pedir una tabla nueva de producto, primero debe evaluarse si en realidad pertenece a `productos`;
- `logistics` solo debe conservar lo estrictamente operativo del envase y del movimiento.

---

## 7. Características esperadas del backend

### Servicios esperados

```
plugins/productos/backend/services/
├── products.py
├── catalog.py
├── pricing.py
├── barcode.py
├── adr.py
├── media.py
└── promotions.py
```

### Endpoints esperados

- catálogos base;
- CRUD de productos;
- búsqueda de productos;
- gestión de códigos de barras;
- gestión de precios;
- gestión de costos;
- gestión ADR;
- gestión de impuestos;
- gestión de media;
- gestión de promociones.

### Permisos esperados

- `productos.catalog.read`
- `productos.catalog.manage`
- `productos.product.read`
- `productos.product.create`
- `productos.product.update`
- `productos.product.delete`
- `productos.price.read`
- `productos.price.manage`
- `productos.cost.read`
- `productos.cost.manage`
- `productos.adr.read`
- `productos.adr.manage`
- `productos.media.manage`
- `productos.promotion.read`
- `productos.promotion.manage`

Regla importante:

- aunque conceptualmente estos permisos pertenecen al dominio producto, el core exige formato de 3 segmentos (`<module>.<resource>.<action>`);
- por eso la implementación real usa `productos.price.read` y no `productos.product.price.read`.

---

## 8. Características esperadas del frontend

### Páginas

- listado de productos;
- formulario de producto;
- detalle de producto;
- gestor de catálogos base.

### Componente compartido esperado

- `ProductSearchDialog`

Este componente debe quedar reusable para otros módulos como:

- `logistics`
- `ventas`
- `compras`

---

## 9. Orden recomendado de implementación

### Fase 1 — Plugin limpio

1. scaffold de `plugins/productos/`
2. `plugin.json`
3. modelos ORM
4. migración inicial
5. schemas Pydantic
6. servicios backend
7. router
8. permisos y eventos
9. pruebas backend

### Fase 2 — Frontend

1. `register.ts`
2. `api.ts`
3. páginas principales
4. `ProductSearchDialog`
5. pruebas del flujo UI básico

### Fase 3 — Integración posterior

1. integración gradual con `logistics`
2. FKs opcionales
3. coexistencia
4. migración final de catálogos transitorios

---

## 10. Riesgos a vigilar

| Riesgo | Descripción |
|---|---|
| Duplicación de precios | volver a guardar precios en grupos, cilindros o tablas operativas |
| Desalineación con logistics | olvidar que `lg_gas_products` y `lg_brands` son transitorios |
| ADR mezclado | confundir ADR del producto con retimbrado o datos físicos del cilindro |
| Pricing distribuido | resolver precios en cada módulo consumidor sin respetar precedencia |
| Implementación prematura de stock | meter disponibilidad o mínimos dentro de `productos` |

---

## 11. Checklist antes de programar

- leer `AGENTS.md`
- leer este documento
- leer `docs/adr/0015-productos-plugin.md`
- leer `docs/specs/core/0015-productos-plugin/index.md`
- recordar que `logistics` no se migra en profundidad en esta primera iteración
- recordar que `SPEC 0014` de logistics sigue en borrador y no debe usarse como verdad implementada

---

## 12. Resumen operativo

Si un agente necesita una regla rápida:

- catálogo maestro de productos: `productos`
- pricing base y promociones: `productos`
- tarifa por cliente: `crm`
- stock: módulo `stock` (ya implementado)
- retimbrado y ciclo de vida del cilindro: `logistics`
- `lg_gas_products` y `lg_brands`: compatibilidad transitoria, no destino final
