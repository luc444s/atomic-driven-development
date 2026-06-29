# 11 — Vistas SQL Completas — Módulo Productos/Catálogos

## vw_EdetPB_Vigente

```sql
-- Propósito: Obtener la fila ADR vigente de cada bombona
CREATE VIEW dbo.vw_EdetPB_Vigente AS
SELECT *
FROM dbo.Edetalle_Producto_Bombona
WHERE VigenteHasta IS NULL;
```

## ECilindroEstadoActual (vista)

```sql
-- Propósito: Obtener el último estado de cada cilindro
CREATE VIEW dbo.ECilindroEstadoActual AS
WITH UltimoEstado AS (
    SELECT
        Serie,
        Estado,
        Fecha,
        Usuario,
        Observacion,
        Origen,
        MotivoCodigo,
        AlmacenId,
        ROW_NUMBER() OVER (PARTITION BY Serie ORDER BY Fecha DESC, IdEstado DESC) AS rn
    FROM dbo.ECilindroEstadoLog
)
SELECT
    Serie,
    ProductoId,
    Estado,
    Fecha,
    UsuarioId,
    Origen,
    AlmacenId
FROM UltimoEstado ue
LEFT JOIN dbo.Producto p ON p.Nro_Producto = ue.Serie
WHERE ue.rn = 1;
```

## vCilindroEstadoLogDet

```sql
-- Propósito: Log de estados de cilindros con datos de persona
CREATE VIEW dbo.vCilindroEstadoLogDet AS
SELECT
    l.IdEstado,
    l.Serie,
    p.cod_producto AS ProductoId,
    p.Nro_Producto,
    p.Desc_Producto,
    p.cod_grupo,
    l.Estado,
    l.Fecha,
    l.Usuario AS UsuarioId,
    pn.Nom_Persona AS UsuarioNombre,
    l.Observacion,
    l.Origen,
    l.MotivoCodigo,
    l.AlmacenId
FROM dbo.ECilindroEstadoLog l
LEFT JOIN dbo.Producto p ON p.Nro_Producto = l.Serie
LEFT JOIN dbo.Persona_Nuevo pn ON pn.Cod_Persona = l.Usuario;
```

## vPlan_PedidosCILPRO

```sql
-- Propósito: Pedidos CILPRO con datos de planificación
CREATE VIEW dbo.vPlan_PedidosCILPRO AS
SELECT
    m.Cod_Movimiento,
    dm.Ids AS Id_DetalleMovimiento,
    m.Id_Cpedido,
    m.NroDocumento,
    m.Cod_Persona AS ClienteId,
    p.Nom_Persona,
    p.Ruc_Persona,
    p.Dni_Persona,
    dm.CodProducto AS Cod_ProductoCilindro,
    dm.glosa AS Serie_Cilindro,
    pr.Desc_Producto AS Desc_Cilindro,
    pr.cod_grupo,
    pr2.cod_producto AS Cod_Gas,
    pr2.Desc_Producto AS Nom_Gas,
    dm.CANT AS CantPedida,
    dm.CantPlanificada,
    (dm.CANT - ISNULL(dm.CantPlanificada, 0)) AS CantPendientePlan,
    m.Cod_Almacen
FROM dbo.Movimiento m
JOIN dbo.DetalleMovimiento dm ON dm.CodMovimiento = m.Cod_Movimiento
JOIN dbo.Producto pr ON pr.cod_producto = dm.CodProducto
LEFT JOIN dbo.Producto pr2 ON pr2.cod_grupo = pr.cod_producto
JOIN dbo.Persona p ON p.Cod_Persona = m.Cod_Persona
WHERE pr.condicion = 'CILPRO';
```
