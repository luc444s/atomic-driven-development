# sp_StockCilindros_PorProducto — SQL Completo y Análisis

## SQL Completo

```sql
CREATE PROCEDURE dbo.sp_StockCilindros_PorProducto
(
    @CodProducto INT,
    @CodAlmacen INT
)
AS
BEGIN
    SET NOCOUNT ON;

    /* 
        LOGICA OFICIAL DE STOCK PARA CILINDROS
        ------------------------------------------------
        ? CILPRO  ? cilindros llenos
        ? CILCLI  ? cilindros vacios
        ? CILGAR  ? cilindros dados en garantia
        ? CILPROV ? cilindros de proveedor
        ------------------------------------------------
        Se usa la vista Valmacen_Envases (ultimo estado de cada cilindro).
    */

    SELECT 
        @CodProducto AS CodProducto,
        @CodAlmacen AS CodAlmacen,

        SUM(CASE WHEN motivo = 'Lleno'  THEN 1 ELSE 0 END) AS Stock_Lleno,
        SUM(CASE WHEN motivo = 'Vacio'  THEN 1 ELSE 0 END) AS Stock_Vacio,
        SUM(CASE WHEN motivo = 'Cargado' THEN 1 ELSE 0 END) AS Stock_Cargado,
        SUM(CASE WHEN motivo = 'En transito' THEN 1 ELSE 0 END) AS Stock_EnTransito,
        SUM(CASE WHEN motivo = 'Recepcionado' THEN 1 ELSE 0 END) AS Stock_Recepcionado

    FROM dbo.Valmacen_Envases
    WHERE cod_producto = @CodProducto
      AND Almacen = @CodAlmacen;
END
```

## Análisis

### ¿Qué hace?
Cuenta cilindros físicos por **estado operativo** (motivo) para un producto y almacén específicos. NO cuenta gas — cuenta envases.

### Joins reales
Solo consulta la vista `Valmacen_Envases`. Sin joins directos adicionales. Los joins están dentro de la vista.

### Filtros
- `@CodProducto` — tipo de envase (ej: "Bombona 15KG")
- `@CodAlmacen` — almacén físico

### ¿Reporte o decisión operativa?
**Híbrido.** Se usa para:
- Consultar disponibilidad de cilindros por estado
- Alimentar la UI de carga/descarga (probablemente en FrmMovTrasladoAlmacen y planificador logístico)
- Diferenciar llenos vs vacíos — algo que `fn_StockDisponible` NO hace

### Dependencia: Valmacen_Envases
La vista `Valmacen_Envases` es el único origen de datos. Ver `09_Valmacen_Envases.md`.

### Limitaciones detectadas
1. Cuenta solo cilindros con registro en `EDetalle_cpedido` — si un cilindro existe en `Producto` pero nunca tuvo pedido, no aparece
2. La vista usa subquery `TOP(1) id_detalle DESC` — solo el último detalle de cada producto. Si un cilindro tiene múltiples pedidos, solo el último cuenta
3. No cruza con `Stock_Actual` ni `fn_Stock*` — es un sistema completamente aparte del stock de gas
4. No hay verificación de que el "motivo" (Lleno/Vacio/Cargado) refleje el estado físico real del cilindro
