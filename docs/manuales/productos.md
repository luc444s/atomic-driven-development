# Guía de uso — Módulo de Productos

**Público:** personal operativo (producto, compras, almacén).
No requiere conocimientos técnicos ni de programación.

**Fuente:** este manual se escribió desde el comportamiento real de la aplicación, no desde diseños teóricos.

---

## ¿Qué es Productos?

Es el catálogo maestro de los productos que comercializa el negocio: SKU, nombre, clasificación (categoría/línea/marca), unidad, condición y datos de ADR.

Se organiza en dos cosas:
1. **Catálogos base** — la estructura sobre la que se apoyan los productos (categorías, líneas, marcas, unidades, etc.), creada **antes** de los productos.
2. **Productos** — cada artículo concreto con SKU y clasificación.

En el menú lateral, la sección **Productos** te lleva a la pantalla principal.

---

## La pantalla principal

- **Buscar:** por **SKU** o **nombre**.
- **Nuevo producto:** botón naranja para dar de alta un artículo.
- **Catálogos:** botón secundario para administrar la estructura maestra (ver más abajo).
- Cada fila muestra **SKU, Producto, Línea, Marca, Condición, Activo** y columnas de acción:
  - **Editar:** modifica la ficha del producto.
  - **Detalle:** abre la ficha operativa completa.

La lista se pagina (10 por página).

---

## Crear un producto

Al pulsar **Nuevo producto** se abre el formulario con dos bloques: **Ficha maestra** y **Detalle operativo**.

### Bloque 1 — Ficha maestra

Datos de identificación del producto:

- **SKU:** código único de producto (cómo se busca en stock y en todo el sistema).
- **Nombre:** nombre del producto.
- **Clasificación:**
  - **Línea** (obligatoria): clasificación principal (creada antes en Catálogos).
  - **Sublínea:** detalle de línea (opcional, filtrada según la línea elegida).
  - **Categoría / Subcategoría:** para agrupar (ej. GAS, BOMBONAS, PRODUCTOS, SERVICIOS).
  - **Marca:** marca comercial.
- **Tipo de insumo:** segmentación del insumo según la operación.
- **Unidad y Unidad de caja:**
  - **Unidad base:** cómo se cuenta el producto (unidad, m³, litros, kg).
  - **Unidad de caja:** unidad de empaque/embalaje (opcional).
- **Condición:** estado comercial del producto (ej. `PRODUCTO`). Se selecciona de catálogo.
- **Datos ADR y accesorios:** marca ADR, junto con otros datos operativos según el producto.

### Bloque 2 — Detalle operativo

Configuración propia para la operación y costeo del producto (precios, costos, promociones) que se completa según el tipo de artículo. Compártela con Compras/Contabilidad para que queden coherentes.

Al pulsar **Guardar** el producto queda disponible para usarse en Stock y Logística.

---

## Catálogos base

El botón **Catálogos** abre un menú para construir la estructura maestra. Cada entrada permite **crear** elementos con un código, nombre y descripción, y ver los ya existentes en una tabla.

| Catálogo | Para qué sirve |
|---|---|
| **Categorías** | Rubros superiores del negocio. |
| **Líneas** | Clasificación principal de los productos. |
| **Sublíneas** | Detalle de línea para segmentar más fino. |
| **Marcas** | Marcas comerciales y técnicas. |
| **Tipos de insumo** | Segmentación del insumo según operación. |
| **Unidades** | Unidad base, m³, litros y kg con sus factores de equivalencia. |
| **Subcategorías** | GAS, BOMBONAS, PRODUCTOS, SERVICIOS u otras variantes. |
| **Grupos** | Agrupación logística/comercial sin pricing operativo. |

Detalles por catálogo:

- **Líneas:** se vinculan opcionalmente a una **categoría**.
- **Sublíneas:** se vinculan a una **línea**.
- **Unidades:** además de código y nombre, llevan **equivalencia** y **factores** de conversión a m³, litros y kg.
- **Grupos:** admiten línea, sublínea, unidad y opcionalmente producto de gas, para agrupación logística.

> Orden recomendado: crea primero **categorías → líneas → sublíneas**, y **unidades**, antes de los productos. Cada producto se apoya en esa estructura.

---

## Casos comunes (paso a paso)

### A. Crear un producto nuevo
1. Crea antes la **línea** (y/o categoría, marca, unidad) en **Catálogos** si no existen.
2. **Productos** → **Nuevo producto**.
3. Escribe **SKU** y **nombre**.
4. Asigna **línea** (obligatoria), sublínea y **unidad**.
5. **Guardar**.

### B. Buscar un producto por código
- En **Productos**, escribe el **SKU** en el buscador. La lista filtra al instante.

### C. Añadir una línea de producto
1. **Catálogos** → **Líneas**.
2. Escribe código, nombre y categoría (opcional).
3. **Crear**.

---

## Qué contempla el módulo (v1)

- Catálogo maestro con SKU, nombre, línea, sublínea, categoría, marca e insumo.
- Unidades con factores de equivalencia (m³, litros, kg).
- Condición del producto y datos ADR.
- Administración de catálogos base (categorías, líneas, sublíneas, marcas, tipos de insumo, unidades, subcategorías, grupos).
- Base para costos y pricing del producto.

## Qué NO contempla el módulo (v1)

- **No controla existencias:** el stock físico se administra en el módulo Stock.
- **No maneja reparto de envases:** eso es Logística.
- **No factura:** emisión de venta es otro módulo.

## Límites y advertencias operativas

- La **línea** es obligatoria para crear un producto: configúrala antes en **Catálogos**.
- Las **sublíneas** se filtran según la línea elegida.
- Los **catálogos base** deben crearse primero; sin ellos no hay dónde clasificar los productos.

---

## Vocabulario básico

| Término | Significado |
|---|---|
| SKU | Código único del producto. |
| Línea | Clasificación principal del producto. |
| Sublínea | Segmentación más fina de la línea. |
| Insumo | Material/mercancía que se opera. |
| Condición | Estado comercial del producto. |
| ADR | Normativa de mercancías peligrosas. |
| Factor | Conversión de unidad a m³, litros o kg. |