# 05 — Forms de Búsqueda — Productos/Catálogos

## FrmBuscarProducto.vb

### Descripción
Formulario de búsqueda de productos. Se abre desde `FrmCatProductos.cmdBuscar_Click`.

### Filtros de búsqueda (según código de CProducto.vb)
- Por código: `Producto_Buscar`
- Por nombre: `Producto_BuscarxNom`
- Por código de barras: `Producto_BuscarxNomxCODEBARR`
- Por tipo de insumo: `Producto_BuscarxTipo`
- Por línea: `BuscarProdxlinea`
- Por sublínea: `BuscarProdxsublinea`
- Por marca: `Producto_BuscarxMARCA`

### Cómo pasa resultado al llamante
```vb
' En FrmCatProductos.cmdBuscar_Click:
Dim objbm As New FrmBuscarProducto
objbm.ShowDialog(Owner)
' Al cerrarse, las variables públicas de FrmBuscarProducto
' contienen los valores seleccionados que son leídos por el llamante
```

Los campos se leen directamente de las variables públicas del formulario de búsqueda, luego se asignan a los controles de FrmCatProductos.

## FrmBuscarProductoBomb.vb

Búsqueda específica de bombonas. Filtros por:
- Número de serie: `Producto_BuscarxNroSerie`
- Matrícula: `Buscar_MatriculaBombona`
- Nombre: `Producto_BuscarxNom`

## FrmBuscarPromProducto.vb

Búsqueda de promociones de producto. SPs:
- `Mil_BuscarPromProducto` — búsqueda de promociones por producto
- `Promocion_mostrar` — listar promociones
- `Promocion_mostrarActiva` — solo promociones activas
