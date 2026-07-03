# Stock ↔ Cilindros — Extracción Completa

## Archivos

| # | Archivo | Contenido |
|---|---|---|
| 01 | `01_sp_StockCilindros_PorProducto.md` | SQL completo, joins, filtros, análisis |
| 02 | `02_ECilindroEstadoActual.md` | DDL real, cardinalidad, uso del ProductoId, tabla log, validación de transiciones |
| 03 | `03_traslados.md` | Flujo FrmMovTrasladoAlmacen (4,300 líneas), diferencia llenos/vacíos |
| 04 | `04_Producto_stock.md` | Significado de Producto.stock, cache vs realidad, fn_Stock* vs estado |
| 05 | `05_disponibilidad_logistica.md` | Qué consulta logística (stock genérico + estado individual + vistas) |
| 06 | `06_reconciliacion.md` | Gaps entre stock y estados, causas, reporte OSS propuesto |
| 07 | `07_casos_ingreso_egreso.md` | Matriz de 10 casos: qué afecta cantidad, estado o ambos |
| 08 | `08_que_es_un_cilindro.md` | Producto envase vs producto gas, Cod_Grupo, cuándo se mueve cada uno |
| 09 | `09_Valmacen_Envases.md` | SQL completo de la vista clave, 8+1 joins, limitaciones |
| 10 | `10_pregunta_final.md` | "50 bombonas 15KG" = ¿qué? Las 4 interpretaciones posibles |

## Hallazgos Clave

1. **Stock y estado de cilindros son dos sistemas paralelos sin sincronización**
2. `sp_StockCilindros_PorProducto` es el único puente que cruza cantidad + estado
3. `Valmacen_Envases` es la vista central pero tiene limitaciones (solo último pedido, excluye cilindros sin pedido)
4. `FrmMovTrasladoAlmacen` maneja llenos/vacios separados pero NO actualiza `ECilindroEstadoActual`
5. Venta NO actualiza estado del cilindro automáticamente
6. Existen 37 vistas relacionadas con cilindros — síntoma de diseño no resuelto
7. Producto.stock es cache de DetalleMovimiento; la verdad real son las fn_Stock*

## Contrato OSS

- Stock y estado deben ser un solo sistema sincronizado
- Cada movimiento de stock debe reflejarse en estado individual
- La pregunta "50 bombonas" debe responder cantidad + distribución de estados
- Reporte de conciliación debe detectar diferencias automáticamente
