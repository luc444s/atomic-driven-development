# ADR 0015 — Plugin productos: Catálogo Maestro

## Estado

Aceptado

## Contexto

SYSTUTOR OSS maneja productos de forma fragmentada: `plugins/logistics/` tiene `lg_gas_products` y `lg_brands` como catálogos propios, pero no existe un catálogo maestro de productos. El análisis del legacy (`docs/database/modulo_productos/`) revela que `Producto` (~70 columnas, tabla única, 0 FKs) es la tabla más referenciada del sistema (~100+ SPs, ~30 formularios, dependencias de stock, logística, ventas, compras, contabilidad y escaneo).

Los problemas del legacy que este ADR resuelve:

| Problema | Impacto |
|----------|---------|
| `Producto` anti-normalizada: 70 columnas mezclan identidad, precios (4 niveles), costos (5 campos), ADR (10 campos), impuestos, imágenes, stock | Mantenibilidad 0, bugs de inconsistencia |
| 0 FKs en tabla Producto | Datos huérfanos, migración requiere limpieza masiva |
| Lógica de precios en 3 capas (VB, DAL, SPs) | Inconsistencia: modificar precio en una capa no actualiza las otras |
| 38 parámetros posicionales en InsertarProducto/ModificarProducto | Bugs de mapeo: la llamada real en cmdgrabar no coincide con la firma formal |
| 10 campos ADR no se guardan (bug confirmado desde 2022 en FrmCatBombonas) | Datos ADR perdidos, riesgo normativo |
| ~40 SPs de búsqueda duplicados (Producto_BuscarxTipo, xTipo1, xTipo2…) | Código redundante, dificulta migración a ORM |
| CFamilia maneja promociones (error de naming) | Confusión arquitectónica |

## Decisión

Se crea el plugin `productos` como catálogo maestro de productos de SYSTUTOR OSS.

### Reglas de diseño

**Alcance — submódulos incluidos:**

| Submódulo | Contenido |
|-----------|-----------|
| **Catálogos base** | Línea, Sublínea, Marca, Categoría/Rubro, TipoInsumo, Unidad, Condición, Subcategoría, Grupo, EstadoProducto |
| **Producto** | CRUD maestro con multi-código de barras, multi-unidad, imágenes |
| **Precios** | 4+ niveles de precio con historial por vigencia |
| **Costos** | Histórico de costos (actual, reposición, anterior, CGI, total) |
| **ADR** | Configuración ADR con vigencias (reemplaza `Edetalle_Producto_Bombona`) |
| **Impuestos** | IGV, percepción, comisión externa por producto |
| **Media** | Imágenes de producto y códigos de barras (filesystem local → Cloudflare R2) |
| **Promociones** | Promociones por producto (minimal, extraíble a plugin propio si crece) |

**Alcance — NO incluidos:**

| Funcionalidad | Destino | Justificación |
|---------------|---------|---------------|
| Stock actual (`stock` cache, `Stock_Actual`) | Módulo Stock (futuro) | Stock se computa del ledger |
| Stock mínimo/máximo por almacén | Módulo Stock (futuro) | Es configuración de inventario, no de catálogo |
| Retimbrado de bombonas | Logistics | Evento de ciclo de vida del envase |
| Estado de cilindros (`ECilindroEstado*`) | Logistics | Trazabilidad física del envase |
| Precios especiales por cliente (`Tarifa_cliente`) | CRM | Precio depende del cliente, no del producto |
| Descuentos por cliente/línea | CRM (futuro pricing) | Reglas de descuento cruzan cliente y producto |

**Normalización del producto legacy:**

La tabla única `Producto` (70 columnas) se descompone en:

```
Producto (legacy, 70 cols)
├── prod_products        (20 columnas núcleo)
├── prod_prices          (precios historificados)
├── prod_costs           (costos historificados)
├── prod_barcodes        (múltiples códigos)
├── prod_tax_config      (impuestos)
├── prod_adr             (ADR con vigencias)
├── prod_stock_config    → módulo stock (futuro)
├── prod_media           (imágenes)
├── prod_promotions      (promociones)
└── prod_discounts       → CRM (futuro pricing)
```

**Multi-universal (no multi-país):**

No se implementa lógica de país diferencial. `country_code` es un campo informativo. El diccionario CABYS hardcodeado del legacy (13 gases de Costa Rica) se modela como `prod_barcodes` con tipo `CABYS`.

**Pricing con una sola fuente de verdad:**

- los precios vigentes e históricos viven solo en `prod_prices`;
- los costos vigentes e históricos viven solo en `prod_costs`;
- `prod_groups` no almacena precios operativos ni listas de precio;
- cualquier precio mostrado por ventas, logistics o compras debe resolverse desde estas tablas,
  no desde catálogos auxiliares.

**Precedencia de precio:**

- cuando un módulo necesite resolver el precio efectivo de venta, la precedencia es:
  1. tarifa especial por cliente en CRM;
  2. promoción activa del producto en `productos`;
  3. precio vigente base del producto en `prod_prices`.
- `productos` es dueño del catálogo y del precio base/promoción;
- CRM es dueño de `Tarifa_cliente` y de cualquier override específico por cliente.

**Migración desde logistics:**

- `lg_gas_products` y `lg_brands` coexisten en Fase 1.
- El plugin `productos` se crea limpio.
- Logistics agrega FKs opcionales hacia `prod_products` y `prod_brands`.
- En Fase 2 se migran los datos y logistics apunta a las nuevas tablas.
- En Fase 3 se eliminan `lg_gas_products` y `lg_brands`.

**Media storage:**

- Fase 1: filesystem local con URL (`/media/products/{id}/{file}`).
- Arquitectura preparada para Cloudflare R2: la URL de media se almacena como texto, el storage backend es intercambiable.

**Promociones minimales:**

- Se implementan dentro de `productos` como un submódulo simple (tabla `prod_promotions` con CRUD básico).
- Si el módulo crece (reglas complejas, descuentos por cliente, bundles), se extrae a plugin propio `pricing` o `marketing`.

**Barcodes sin ambigüedad:**

- `prod_barcodes` usa `barcode_type` para clasificar el código (`CABYS`, `MATRICULA`, `GS1`, `INTERNAL`);
- la primariedad se expresa solo con `is_primary`, no con un tipo `PRINCIPAL`;
- un producto tiene exactamente un barcode primario activo.

**Actualización historificada, no in-place:**

- precios, costos y ADR no se editan in-place una vez vigentes;
- un cambio funcional crea una nueva fila y cierra la vigencia anterior;
- solo se permiten correcciones administrativas en registros futuros o no vigentes.

**Snapshots transaccionales en logistics:**

- las tablas transaccionales de logistics pueden conservar `product_name` como snapshot histórico de lectura;
- la referencia maestra pasa a ser `product_id` con FK a `prod_products`;
- durante la coexistencia, logistics puede leer desde catálogo legacy y nuevo, pero toda nueva relación debe capturar `product_id` cuando exista.

### Arquitectura del plugin

```
plugins/productos/
├── plugin.json
├── backend/
│   ├── __init__.py
│   ├── plugin.py              # register()
│   ├── router.py              # FastAPI router con todos los endpoints
│   ├── schemas.py             # Pydantic request/response
│   ├── models.py              # SQLAlchemy ORM
│   └── services/
│       ├── __init__.py
│       ├── products.py        # CRUD de producto
│       ├── catalog.py         # CRUD de catálogos (línea, marca, unidad...)
│       ├── pricing.py         # Gestión de precios y costos
│       ├── barcode.py         # Gestión de códigos de barras
│       ├── adr.py             # Configuración ADR por producto
│       ├── media.py           # Imágenes y archivos
│       └── promotions.py      # Promociones
├── frontend/
│   ├── register.ts
│   ├── api.ts
│   ├── pages/
│   ├── components/
│   └── types.ts
├── migrations/
├── permissions/
├── events/
└── README.md
```

### Migración de datos legacy

No hay migración de datos legacy del SQL Server en esta etapa. El plugin opera con datos nuevos.

El migrador legacy (`tools/migrator/`) se actualizará separadamente con manifiestos CSV para productos cuando se defina la migración del dominio.

## Consecuencias

**Positivas:**
- Catálogo maestro normalizado con FKs reales.
- Precios y costos historificados (nunca se pierde el valor anterior).
- Una sola fuente de verdad para precios y costos.
- ADR corregido (el bug legacy de FrmCatBombonas no se replica).
- Un solo lugar para definir impuestos por producto.
- Logistics se desacopla de su propio catálogo de gases.
- Tarifa_cliente migra a CRM, manteniendo la coherencia del legacy.

**Negativas:**
- Las tablas `lg_gas_products` y `lg_brands` en logistics deben migrarse en fases.
- La migración de datos legacy (cuando llegue) requerirá mapear 70 columnas → 8 tablas.
- El frontend de logistics deberá actualizarse para usar `ProductSearchDialog` en lugar de sus propios catálogos.

**Riesgos:**
- Si la migración de logistics no se coordina, pueden quedar FKs huerfanas.
- La extracción futura de promociones a plugin propio requerirá migración de datos.
- La media storage en filesystem local no escala a múltiples servidores (mitigación: R2 en Fase 2).
- La resolución de precio requiere coordinación entre `productos` y CRM para respetar la precedencia definida.

## Dependencias

- Runtime de plugins (existe y funciona).
- Kernel: auth JWT, multi-tenant, RBAC, auditoría, event bus.
- CRM plugin: opcional (solo si se usan precios por cliente desde CRM).
- Logistics plugin: declara `"requires": ["productos"]` cuando se complete la migración de FKs.

## Referencias

- SPEC 0015: `docs/specs/core/0015-productos-plugin/index.md`
- `docs/database/modulo_productos/` — análisis completo del legacy
- `docs/database/modulo_stock/` — análisis de stock (dependencia de productos)
- ADR 0012: CRM Plugin de Clientes
- ADR 0010: Logistics como Plugin Piloto
- ADR 0004: Runtime de Plugins
- ADR 0006: Migración Legacy CSV Manifest
