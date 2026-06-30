# SPEC 0018 — Pedido de logistica con buscador de productos

## Estado

Propuesta

## Contexto

El frontend de pedidos de logistica hoy permite agregar una linea con `product_name` libre.

Eso es funcional, pero no obliga a escoger un producto real del catalogo `prod_products`.

Para el flujo objetivo de pedidos, eso no es aceptable. Una linea de pedido debe construirse a partir de un producto real seleccionado y no de un nombre escrito manualmente.

La base generica necesaria ya existe:

- `SearchDialog<T>` en `apps/web/src/shared/ui/search-dialog.tsx`;
- `ProductSearchDialog` como wrapper;
- `DataTable` con `onRowClick`.

Esta spec define el refactor minimo para que la linea de pedido use busqueda de productos sin introducir una abstraccion nueva.

## Objetivo

Cambiar el modal de "Agregar línea" del pedido para seleccionar obligatoriamente un producto real desde un buscador modal y guardar esa seleccion como snapshot transaccional.

## No objetivos

- crear una nueva libreria de UI;
- rehacer la pagina de pedidos completa;
- agregar paginacion o filtros avanzados al buscador;
- cambiar la semantica de `lg_order_items`.

## Alcance

### Incluye

1. reemplazar el textbox libre de `product_name` en el modal de linea por un trigger de busqueda de productos;
2. reutilizar `ProductSearchDialog` o `SearchDialog<T>`;
3. seleccionar un producto real y completar `product_id` + `product_name`;
4. enviar siempre `product_id` + `product_name` al backend al guardar la linea;
5. mostrar el producto seleccionado como primera etapa visible del modal de linea;
6. conservar `quantity_requested`, `quantity_planned`, `location` y cualquier otro campo ya existente del formulario minimo.

### No incluye

1. permitir crear una linea sin producto seleccionado;
2. mantener fallback manual por texto libre para productos;
3. agregar otro modal extra ademas del buscador generico;
4. introducir validaciones nuevas de negocio fuera del flujo actual.

## Flujo esperado

1. el usuario selecciona un pedido;
2. pulsa `Agregar línea`;
3. abre el modal de linea;
4. la primera etapa visible del modal muestra el estado de producto seleccionado o pendiente de seleccionar;
5. pulsa `Buscar producto`;
6. abre el buscador modal;
7. selecciona un producto real;
8. el formulario de linea se completa con `product_id` y `product_name`;
9. al guardar, se crea la linea del pedido.

## Contrato minimo

El formulario de linea debe manejar al menos:

```typescript
type OrderItemFormState = {
  product_id: string;
  product_name: string;
  quantity_requested: string;
  quantity_planned: string;
  location: string;
};
```

Reglas del contrato:

1. `product_id` es obligatorio para enviar el formulario;
2. `product_name` no se captura manualmente; se rellena desde el producto seleccionado;
3. si no hay producto seleccionado, la accion de guardar debe bloquearse.

## Decisiones de implementacion

### 1. Producto obligatorio

El flujo no admite texto libre ni modo alterno. Toda linea nueva del pedido debe originarse en una seleccion real del catalogo.

### 2. Primera etapa visible del modal

El modal de linea debe exponer primero el estado del producto:

- producto pendiente de seleccionar; o
- producto ya seleccionado.

No debe empezar con un textbox editable de nombre.

### 3. Reutilizacion minima

No se crea un buscador nuevo. Se reutiliza `ProductSearchDialog` o, si hace falta, un wrapper delgado sobre `SearchDialog<T>`.

## Criterios de aceptacion

### Funcionales

1. el modal de linea ya no depende solo de texto libre para el producto;
2. el usuario puede buscar y seleccionar un producto real;
3. el item creado conserva `product_name` como snapshot;
4. `product_id` se envía siempre al backend;
5. no se puede guardar una linea sin producto seleccionado;
6. el flujo no rompe la experiencia actual de crear pedidos.

### De reutilizacion

1. no se crea un buscador nuevo ad-hoc;
2. se reutiliza la base generica ya existente en `shared/ui`;
3. el cambio permanece acotado a la pagina de pedidos y, si hace falta, a un wrapper delgado.

### De calidad

1. la implementacion mantiene mensajes de UI en español;
2. no introduce colores hardcodeados;
3. se agregan pruebas del flujo de formulario o del adaptador de payload afectado.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| El buscador de productos no devuelve el campo necesario para mostrar la seleccion | medio | extender solo el wrapper delgado |
| El formulario sigue aceptando estados inconsistentes entre `product_id` y `product_name` | medio | rellenar ambos campos al seleccionar y bloquear guardado sin producto |
| El backend aun permite `product_id` opcional aunque la UI no | bajo | endurecer el payload del frontend en este flujo |

## Dependencias

- ADR 0017 — SearchDialog generico en shared/ui;
- SPEC 0015 — Productos plugin;
- SPEC 0011 — Logistics pilot module.
