# 07 — Reportes Crystal — Módulo Productos/Catálogos

## Búsqueda de archivos .rpt relacionados

Los siguientes reportes Crystal están referenciados en el código del módulo productos:

| Reporte | Propósito | Referencia |
|---------|-----------|------------|
| Etiqueta de producto | Etiqueta con código de barras | FrmCatProductos |
| Etiqueta de cilindro | Etiqueta ADR para bombonas | FrmCatBombonas (btnVistaPreviaEtiqueta) |
| Lista de precios | Listado de precios de productos | FrmRegPrecios |
| Kardex de producto | Movimientos de kardex | FrmCatProductos |
| Productos por línea | Listado de productos agrupados | Menú de reportes |

## Archivos .rpt específicos (por confirmar)
Se recomienda buscar archivos `.rpt` con: `Get-ChildItem -Recurse *.rpt | Where-Object { $_ -match "Producto|Precio|Etiq|Bombona|Cilindro" }`

## Riesgos
- Los reportes Crystal utilizan conexión directa a BD (riesgo de SQL injection si toman parámetros del usuario)
- Las etiquetas de bombonas leen de `usp_EtiquetaCilindro_Datos` que incluye datos ADR del último retimbrado
- No se identificaron reportes Crystal de promociones
