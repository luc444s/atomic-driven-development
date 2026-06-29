# Forms de Búsqueda Relacionados con Stock

---

## Búsqueda de stock por forms "FBus*"

**No se encontraron forms FBus* específicos de stock** en el proyecto. Los forms FrmMostrarSotck* tienen su propia lógica de búsqueda embebida (no usan forms separados de búsqueda).

---

## Búsquedas de producto usadas en stock

Los forms de stock usan los siguientes métodos de búsqueda de productos:

| Form | Método de búsqueda | SP | Criterio |
|------|-------------------|-----|----------|
| FrmInventario | `BuscarProductoxCODEBARR()` | `Producto_BuscarxNomxCODEBARR` | Código de barra |
| FrmInventario | `BuscarProdxTipo()` | `Producto_BuscarxTipo` | Nombre de producto |
| FrmInventario | `BuscarProducto()` | `Producto_Buscar` | Código de producto |
| FrmMostrarSotck | `BuscarProdxsublinea()` | `Producto_BuscarxTipo1` | Sublínea |
| FrmMostrarSotck | `BuscarProdxTipo()` | `Producto_BuscarxTipo` | Tipo insumo |
| FrmMostrarSotckGeneral | `BuscarProdxlinea()` | `Producto_BuscarxTipo2` | Línea |
| FrmMostrarSotckxMarca | `BuscarProdxMARCA()` | `Producto_BuscarxMARCA` | Marca |
| FrmMostrarSotckxpROV | `BuscarProdxPROV()` | `Producto_BuscarxPROVEEDOR` | Proveedor |

No existe un form de búsqueda genérico de stock reutilizable. Cada form implementa su propia lógica.
