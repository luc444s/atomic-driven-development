# Refactor: Productos a Modales — IMPLEMENTADO

## Estado: ✅ COMPLETADO

Este refactor ya fue implementado. Los modales (`ModalNuevoProducto`, `ModalDetalleProducto`, `ModalCatalogo`) están funcionando en `plugins/productos/frontend/components/`.

## Objetivo

Reemplazar la navegación plana (páginas independientes) por diálogos modales dentro de `ProductListPage`, manteniendo rutas de fallback para acceso directo por URL.

## Estrategia de rutas

- Ruta principal: `productos` → `ProductListPage` (única página real)
- Rutas de fallback (acceso directo por URL, Instagram-style):
  - `productos/new` → `ModalNuevoProducto` en modo página
  - `productos/:productId` → `ModalNuevoProducto` en modo página (edición)
  - `productos/:productId/detail` → `ModalDetalleProducto` en modo página
  - `productos/catalogs` → `ModalCatalogo` en modo página

Las rutas de fallback renderizan el mismo componente del modal pero sin overlay (`asPage=true`), evitando duplicación de lógica.

## Árbol de componentes

```
ProductListPage
├── state: showNew, showCatalogo, editId, detailId
├── [Nuevo] → setShowNew(true)
├── [Catálogos] → setShowCatalogo(true)
├── Tabla:
│   ├── [Editar] → setEditId(id) → setShowNew(true)
│   └── [Detalle] → setDetailId(id) → setShowDetail(true)
│
├── ModalNuevoProducto (open={showNew})
│   ├── props: productId (opcional = edit), onClose, onSaved(product)
│   ├── onSaved → close, refresh list, invalidate queries
│   └── onOpenDetail(id) → close modal, open ModalDetalle(id)
│
├── ModalDetalleProducto (open={showDetail})
│   ├── props: productId, onClose
│   ├── [Editar ficha] → close detail, open ModalNuevo(productId)
│   └── [Activar/Desactivar] → toggle
│
└── ModalCatalogo (open={showCatalogo})
    ├── props: onClose
    └── Menú de tipos: [Categorías, Líneas, Sublíneas, Marcas, Tipos insumo, Unidades, Subcategorías, Grupos]
        └── click → abre sub-modal con CRUD de ese catálogo
```

## Archivos

### Nuevos

| Archivo | Líneas aprox | Contenido |
|---------|-------------|-----------|
| `components/ModalNuevoProducto.tsx` | ~350 | Formulario ficha maestra dentro de `Dialog`; acepta `productId` opcional para edición |
| `components/ModalDetalleProducto.tsx` | ~550 | Menú raíz simple + submodales por sección operativa (barcodes, precios, costos, impuestos, ADR, media, promos) |
| `components/ModalCatalogo.tsx` | ~200 | Menú de catálogos + sub-modales para cada tipo |

### Modificados

| Archivo | Cambio |
|---------|--------|
| `pages/ProductListPage.tsx` | Agrega estado `showNew`, `showCatalogo`, `editId`, `detailId`; botones abren modales en vez de `<Link>`; importa los 3 modales |
| `register.ts` | Mantiene ruta `productos`; mantiene rutas de fallback que renderizan modales con `asPage`; exporta los 3 modales |

### Sin cambios

- `api.ts` — no toca
- `types.ts` — no toca
- `components/ProductSearchDialog.tsx` — ya es modal
- `components/ProductosNav.tsx` — no toca
- `components/ProductosSection.tsx` — no toca

### Código muerto (páginas reemplazadas)

- `pages/ProductFormPage.tsx` — reemplazado por `ModalNuevoProducto`
- `pages/ProductDetailPage.tsx` — reemplazado por `ModalDetalleProducto`
- `pages/CatalogManagerPage.tsx` — reemplazado por `ModalCatalogo`

Se mantienen como archivos pero dejan de importarse desde `register.ts`. Se pueden eliminar tras verificar que nada más los importa.

## Flujo de estados

```
ProductListPage state machine:

[showNew=false, showCatalogo=false, showDetail=false, editId=null, detailId=null]

Nuevo     → setShowNew(true), editId=null
Editar    → setEditId(id), setShowNew(true)
Detalle   → setDetailId(id), setShowDetail(true)
Catálogos → setShowCatalogo(true)

ModalNuevoProducto:
  onSaved(product):
    → setShowNew(false), setEditId(null)
    → invalidateQueries(productosKeys.products.all)

  onOpenDetail(productId):
    → setShowNew(false), setEditId(null)
    → setDetailId(productId), setShowDetail(true)

ModalDetalleProducto:
  onClose:
    → setShowDetail(false), setDetailId(null)

  onEditProduct(productId):
    → setShowDetail(false), setDetailId(null)
    → setEditId(productId), setShowNew(true)
```

## ModalDetalleProducto — Arquitectura

Modal con scroll (~85vh) que contiene las mismas secciones que el actual `ProductDetailPage`,
pero dentro de un `Dialog` de shadcn.

### Estructura interna

```
┌─────────────────────────────────────────────────────┐
│ ModalDetalleProducto               [Cerrar]         │
│ SKU · CONDICION                                      │
├─────────────────────────────────────────────────────┤
│ [Editar ficha]  [Activar/Desactivar]                 │
├─────────────────────────────────────────────────────┤
│ Resumen: Estado · Activo · Unidad · Marca ...       │
├──────────────────┬──────────────────────────────────┤
│ Barcodes         │ Precios                          │
│ [tipo][valor][+] │ [lista][monto][mon][+]           │
│ ┌──────────────┐ │ ┌──────────────────────────────┐ │
│ │ tabla        │ │ │ tabla                        │ │
│ └──────────────┘ │ └──────────────────────────────┘ │
├──────────────────┼──────────────────────────────────┤
│ Costos           │ Impuestos                        │
│ [tipo][monto][+] │ [IGV][Percepción][Comisión]      │
│ ┌──────────────┐ │ [Guardar]                        │
│ │ tabla        │ │                                  │
│ └──────────────┘ │                                  │
├──────────────────┴──────────────────────────────────┤
│ ADR (ancho completo)                                 │
│ [cat][bulto][UN][etiqueta][peso][vol][factor]       │
│ [túnel][unidad][sublínea][descripción]               │
│ [Expirar ADR] [Registrar ADR]                        │
│ ┌──────────────────────────────────────────────────┐ │
│ │ tabla ADR                                        │ │
│ └──────────────────────────────────────────────────┘ │
├──────────────────┬──────────────────────────────────┤
│ Media            │ Promociones                       │
│ [tipo][file][+] │ [nombre][tipo][cant][%][prec]    │
│ ┌──────────────┐ │ [Crear]                           │
│ │ tabla        │ │ ┌──────────────────────────────┐ │
│ └──────────────┘ │ │ tabla                        │ │
│                   │ └──────────────────────────────┘ │
└──────────────────┴──────────────────────────────────┘
```

### Diferencias con ProductDetailPage

| Aspecto | Hoy (página) | Mañana (modal) |
|---------|-------------|----------------|
| Contenedor | `<ProductosSection>` + layout | `<Dialog maxWidthClassName="max-w-5xl">` con scroll |
| Scroll | Scroll de página natural | `overflow-y-auto max-h-[85vh]` dentro del Dialog |
| Editar ficha | `<Link>` a otra ruta | `onEditProduct(productId)` → cierra este modal, abre ModalNuevoProducto |
| Navegación | Cambia URL | No cambia URL (estado en ProductListPage) |
| AsPage mode | N/A | Renderiza contenido sin overlay Dialog |
| Hooks de ruta | `useParams`, `useNavigate` | Props `productId`, `onClose` |

### Tratamiento de asPage

```tsx
// asPage=false → render dentro de Dialog overlay (uso desde ProductListPage)
// asPage=true  → render sin Dialog (ruta de fallback directa)

const content = (
  <div className="space-y-6">...cards and grids...</div>
);

if (asPage) {
  return <div className="p-6">{content}</div>;
}

return (
  <Dialog open={open} title={...} onClose={onClose} maxWidthClassName="max-w-5xl">
    <div className="max-h-[85vh] overflow-y-auto space-y-6">{content}</div>
  </Dialog>
);
```

## Contrato de modales (props)

### ModalNuevoProducto

```ts
type ModalNuevoProductoProps = {
  open: boolean;
  productId?: string;          // undefined → create, string → edit
  onClose: () => void;
  onSaved?: (product: ProductResponse) => void;
  onOpenDetail?: (productId: string) => void;
  asPage?: boolean;            // true → render sin overlay Dialog
};
```

### ModalDetalleProducto

```ts
type ModalDetalleProductoProps = {
  open: boolean;
  productId: string;
  onClose: () => void;
  onEditProduct?: (productId: string) => void;
  asPage?: boolean;
};
```

### ModalCatalogo

```ts
type ModalCatalogoProps = {
  open: boolean;
  onClose: () => void;
  asPage?: boolean;
};
```

## Dependencias

- `apps/web/src/shared/ui/dialog.tsx` — componente `Dialog` existente de shadcn/ui
- `apps/web/src/lib/react-query` — hooks `useQuery`, `useMutation`, `useQueryClient`
- `apps/web/src/shared/ui/*` — `Button`, `Card`, `Input`, `DataTable`, `Alert`

## Orden de implementación

1. `ModalNuevoProducto.tsx` — extraer lógica de `ProductFormPage`, envolver en `Dialog`
2. `ModalDetalleProducto.tsx` — extraer lógica de `ProductDetailPage`, envolver en `Dialog`
3. `ModalCatalogo.tsx` — menú + sub-modales para cada catálogo
4. `ProductListPage.tsx` — agregar estado y wiring de modales
5. `register.ts` — actualizar rutas, exportar modales
6. Verificar `npm run build` en `apps/web`
7. Limpiar páginas muertas (opcional)
