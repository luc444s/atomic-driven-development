# Reconciliación Stock vs Estado de Cilindros

## Situación Actual en Legacy

**No hay proceso automático de conciliación.** No existe un SP que compare:

- `Producto.stock` (o `fn_StockReal`) = 50 unds
- `COUNT(*) FROM ECilindroEstadoActual WHERE ProductoId = X AND AlmacenId = Y` = 48 o 52

## Gaps Identificados

| Sistema | Dato | Fuente | Posible valor |
|---|---|---|---|
| Stock (cantidad) | "50 bombonas 15KG" | `fn_StockReal(prod, almacen)` | 50 |
| Estado (individual) | "48 cilindros registrados" | `SELECT COUNT(*) FROM ECilindroEstadoActual WHERE ProductoId=X AND AlmacenId=Y` | 48 |
| **Diferencia** | "2 cilindros faltan en control de estados" | **Nunca se detecta** | **SABER CUANDO FALLAN** |

## Causas de Diferencia

1. **Creación de cilindro**: `InsertarProducto` crea el producto (stock=0), pero `ECilindroEstadoActual` puede no crearse si `LogEstadoCilindro` no se llama o falla
2. **Pérdida/robo**: Se da de baja en stock pero no en estado, o viceversa
3. **Movimiento manual**: Ajuste de stock que no actualiza estado individual
4. **Bug en traslados**: `FrmMovTrasladoAlmacen` actualiza `REPORTEDETENVASE` pero no necesariamente `ECilindroEstadoActual`
5. **Cilindros sin seguimiento**: Cilindros antiguos que nunca migraron a `ECilindroEstadoActual`

## Recomendación para OSS

Implementar un **reporte de conciliación** periódico:

```sql
SELECT
    p.Cod_Producto,
    p.Desc_Producto,
    fn_StockReal(p.Cod_Producto, @Almacen) AS Stock_Sistema,
    COUNT(e.Serie) AS Cilindros_Registrados,
    fn_StockReal(p.Cod_Producto, @Almacen) - COUNT(e.Serie) AS Diferencia
FROM Producto p
LEFT JOIN ECilindroEstadoActual e 
    ON e.ProductoId = p.Cod_Producto 
    AND e.AlmacenId = @Almacen
WHERE p.Condicion IN ('CILPRO', 'CILCLI', 'CILPROV', 'CILGAR')
GROUP BY p.Cod_Producto, p.Desc_Producto
HAVING ABS(fn_StockReal(p.Cod_Producto, @Almacen) - COUNT(e.Serie)) > 0
```

## ¿Había proceso manual?

Probablemente sí — inventarios físicos periódicos donde el usuario:
1. Contaba cilindros físicos en almacén
2. Comparaba con el stock del sistema
3. Ajustaba diferencias manualmente via `FrmInventario` o actualización directa

Pero **no había** conciliación automática entre stock y estado individual.
