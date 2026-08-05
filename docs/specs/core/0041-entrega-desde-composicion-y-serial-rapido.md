# SPEC 0041 — Entrega desde composicion y serial rapido

**Estado**: vigente  
**Tipo**: frontend  
**Modulo**: logistics (jornadas)  
**Creado**: 2026-08-04

## Alcance

Solo frontend. Sin cambios en backend, API, modelos ni migraciones.

## Resumen

En el formulario `RouteOperationForm`, cuando la operacion es DELIVERY, el repartidor debe poder seleccionar productos directamente desde su composicion vigente (lo que lleva en el camion) en vez de abrir un `ProductSearchDialog` generico. Ademas, un combobox de serial rapido permite escanear un cilindro y que el sistema detecte automaticamente el producto.

Para PICKUP y EXCHANGE el flujo actual se mantiene sin cambios.

## Motivacion

El repartidor en calle ya sabe que lleva en el camion. Obligarlo a buscar un producto en un catalogo de cientos de items cuando solo tiene 3-5 tipos cargados es friccion innecesaria. El serial rapido evita incluso tener que pensar en el producto: escanea el cilindro y listo.

## Diseno visual

Solo visible cuando `operationType === "DELIVERY"`.

```
┌─ Serial rapido ───────────────────────────────────────────────────┐
│ [Escanear o escribir serial                             ▾] [Agregar] │
└───────────────────────────────────────────────────────────────────┘

OXIGENO B10 ⚡3    CO2 B14 ⚡5    ARGON B5 ⚡2    NITROGENO B14 ⚡1
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│OXIGENO B10   │  │CO2 B14       │  │ARGON B5      │  │NITROGENO B14 │
│╺╺╺╺╺╺╺╺╺╺╺╺╺│  │╺╺╺╺╺╺╺╺╺╺╺╺╺│  │╺╺╺╺╺╺╺╺╺╺╺╺╺│  │╺╺╺╺╺╺╺╺╺╺╺╺╺│
│   ⚡3          │  │   ⚡5          │  │   ⚡2          │  │   ⚡1          │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

## Componentes

### 1. Combobox de serial rapido

- Usa `Combobox` de `shared/ui/combobox`
- Busca contra `GET /vehicle-sessions/{sessionId}/load-serials/search` con contexto `LOAD_PLAN`
- Filtro: solo muestra resultados con `availability_status === "AVAILABLE"`
- Al seleccionar un serial, el sistema resuelve el producto desde el cilindro y agrega un `RouteDraftItem` con:
  - `product_id` = del cilindro
  - `product_name` = del cilindro o producto asociado
  - `quantity` = "1"
  - `direction` = "OUT"
  - `selected_serials_count` = 1 (el serial ya queda vinculado automaticamente)

### 2. Cards de composicion

- Datos desde `controller.composition` (`CurrentComposition.product_lines`)
- Solo se muestran si `operationType === "DELIVERY"`
- Card minima con: nombre abreviado del producto + cantidad disponible (`⚡N`)
- Al hacer clic: agrega un `RouteDraftItem` con:
  - `product_id` = de la linea de composicion
  - `product_name` = de la linea de composicion
  - `quantity` = "1"
  - `direction` = "OUT"
  - `selected_serials_count` = 0
- La cantidad maxima editable esta limitada por la composicion

### 3. Seccion de lineas (existente, sin cambios)

- Muestra los `draftItems` agregados
- Permite editar cantidad, quitar, y escanear seriales por linea
- Funciona igual que ahora

## Comportamiento

| Operacion | Serial rapido | Cards composicion | ProductSearchDialog |
|-----------|:---:|:---:|:---:|
| DELIVERY  | ✅ | ✅ | ❌ |
| PICKUP    | ❌ | ❌ | ✅ |
| EXCHANGE  | ❌ | ❌ | ✅ (OUT + IN) |

## Archivos afectados

| Archivo | Cambio |
|---------|--------|
| `RouteOperationForm.tsx` | Seccion DELIVERY: reemplazar "Agregar producto" por Combobox de serial + Cards de composicion |
| `useSessionRouteTabUiState.ts` | Nuevo handler `addDeliveryProduct` que recibe product_id, product_name, quantity y serial opcional |
| `useSessionRouteTabController.ts` | Exponer `addDeliveryProduct` como metodo del controller |
| `SessionRouteTabDialogs.tsx` | Pasar `composition` al `RouteOperationForm` |

## No objetivos

- Cambios en backend
- Cambios en PICKUP o EXCHANGE
- Validacion de stock en frontend (sigue en backend)
- Auto-seleccion de seriales al crear desde card (se hace en paso separado)

## Edge cases

- **Composicion vacia**: mostrar mensaje "Sin carga en el camion" en vez de cards
- **Serial duplicado**: el backend rechaza con error, mostrar alerta
- **Card de producto con cantidad 0**: no mostrarla
- **Serial que excede cantidad en composicion**: el backend lo rechaza al confirmar, el frontend no lo previene
