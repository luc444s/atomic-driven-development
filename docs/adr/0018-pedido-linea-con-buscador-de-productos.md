# ADR 0018 — Pedido de logística con buscador de productos

## Estado

Propuesto

## Contexto

En `plugins/logistics/frontend/pages/OrdersPage.tsx`, el modal de "Agregar línea" usa hoy un `Input` libre para capturar `product_name`.

Eso permite registrar líneas transaccionales, pero no fuerza la selección de un producto real del catálogo de `productos`.

Ese comportamiento no es aceptable para el flujo objetivo. En pedidos de logística, el producto debe provenir siempre del catálogo real y no debe existir ingreso manual alterno.

La base compartida ya existe:

- `SearchDialog<T>` generico en `apps/web/src/shared/ui/search-dialog.tsx`;
- `ProductSearchDialog` como wrapper reutilizable;
- `DataTable` con seleccion por fila.

La spec de logística ya define que `lg_order_items` representa lineas de pedido y que el detalle debe operar sobre productos reales cuando aplique.

## Decision

El modal de "Agregar línea" del pedido de logística debe cambiar de entrada libre a seleccion obligatoria de producto real mediante buscador modal.

Flujo objetivo:

1. abrir modal de "Agregar línea";
2. abrir buscador de productos;
3. seleccionar un item de `prod_products`;
4. llenar `product_id` y `product_name` snapshot en la línea;
5. guardar la línea en `lg_order_items`.

La selección de producto es obligatoria. No existe fallback a texto libre ni modo manual para productos no catalogados dentro de este flujo.

## Alcance

### Incluye

- reemplazar el textbox libre de producto por un boton o trigger que abra el buscador;
- reutilizar `ProductSearchDialog` o `SearchDialog<T>`;
- mantener `product_name` como snapshot transaccional;
- enviar siempre `product_id` junto con `product_name` cuando el usuario seleccione el producto.
- mostrar el producto seleccionado como primera etapa visible dentro del modal de línea.

### No incluye

- redisenar el listado de pedidos;
- agregar filtros avanzados al buscador;
- cambiar el modelo de `lg_order_items`;
- tocar otros modales de logistics que no sean el de linea de pedido.

## Consecuencias

**Positivas:**
- evita capturar nombres libres cuando existe catalogo real;
- reutiliza el buscador generico ya construido;
- alinea pedidos con el modelo de productos.

**Negativas:**
- el modal de linea cambia de una entrada simple a un flujo de seleccion;
- requiere ajustar la UI para exponer producto seleccionado.

## Riesgos

- Si el buscador de productos aun no cubre el filtro necesario para logistica, puede requerir un wrapper delgado adicional.
- El backend actual permite `product_id` opcional; la UI de este flujo debe endurecer esa restriccion y operar como producto obligatorio.

## Referencias

- `docs/specs/core/0015-productos-plugin/index.md`
- `docs/specs/core/0011-logistics-pilot-module.md`
- `docs/adr/0017-search-dialog-generico.md`
- `apps/web/src/shared/ui/search-dialog.tsx`
- `plugins/logistics/frontend/pages/OrdersPage.tsx`
