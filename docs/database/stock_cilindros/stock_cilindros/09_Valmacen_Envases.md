# Vista Valmacen_Envases — SQL Completo y Análisis

## SQL Completo

```sql
CREATE VIEW dbo.Valmacen_envases
AS
SELECT
    dbo.EDetalle_cpedido.motivo,           -- 'Lleno', 'Vacio', 'Cargado', 'En transito', 'Recepcionado'
    dbo.EDetalle_cpedido.condicion,         -- CILCLI, CILPROV, CILPRO, CILGAR
    dbo.Producto.cod_producto,              -- Cod_Producto del envase
    dbo.Producto.Nro_Producto,              -- Serie del cilindro (CodBarra)
    dbo.Producto.Desc_Producto,             -- Descripcion del tipo de envase
    dbo.EDetalle_cpedido.detalle_asoc,      -- Documento asociado
    dbo.Persona_Nuevo.Cod_Persona,          -- Codigo del cliente/proveedor

    CASE
        WHEN EsubVista_EstadoTraslado.EstadoNuevo IS NOT NULL
        THEN Persona_Nuevo.Nom_Persona + ' / ' + EsubVista_EstadoTraslado.EstadoNuevo
        ELSE Persona_Nuevo.Nom_Persona
    END AS Nom_Persona_Estado,

    Cabecera_Pedido.tipo_movimiento,        -- 'Ingreso', 'Salida'
    Cabecera_Pedido.forma_mov,
    dbo.EDetalle_cpedido.ubicacion,
    dbo.EDetalle_cpedido.total,
    Cabecera_Pedido.fecha_pedido,
    DATEDIFF(DAY, Cabecera_Pedido.fecha_pedido, GETDATE()) AS dias_transcurridos,
    GETDATE() AS fecha_actual,
    Cabecera_Pedido.documento_asoc,
    Cabecera_Pedido.nro,
    Cabecera_Pedido.serie,
    dbo.Linea.Desc_Linea,
    dbo.Unidad.Desc_Unidad,
    dbo.Persona_Nuevo.Telefono_Persona,
    dbo.Persona_Nuevo.Cod_TipoPersona,
    dbo.Producto.tiempoi,
    dbo.Producto.condicion AS Dueno,

    (SELECT TOP (1) id_detalle
     FROM dbo.EDetalle_cpedido AS Detalle_Sub
     WHERE cod_producto = dbo.EDetalle_cpedido.cod_producto
     ORDER BY id_detalle DESC) AS ultimo_id_detalle,

    dbo.EDetalle_cpedido.id_detalle,
    dbo.Almacen.Desc_Almacen,
    dbo.Sublinea.Desc_SubLinea,
    dbo.Almacen.Direccion_Almacen,
    dbo.Vehiculo_cliente_nuevo.Codigo AS Codigo_Vehiculo_Cliente,
    Cabecera_Pedido.persona,
    Cabecera_Pedido.Almacen,
    dbo.Persona_Nuevo.Dni_Persona,

    CASE
        WHEN Cabecera_Pedido.motivo = 'prestamo' THEN 'Arriendo'
        ELSE Cabecera_Pedido.motivo
    END AS motivo_descripcion,

    dbo.EsubVista_EstadoTraslado.EstadoNuevo AS Motivo2,
    dbo.Persona_Nuevo.Nom_Persona,
    dbo.Vehiculo_cliente_nuevo.Direccion AS Direccion_Persona,
    dbo.Vehiculo_cliente_nuevo.Contacto,
    dbo.Vehiculo_cliente_nuevo.Id_ClientePersona AS cliente,
    DATEDIFF(DAY, Cabecera_Pedido.fecha_pedido, GETDATE()) AS DIAS

FROM dbo.ECabecera_pedido AS Cabecera_Pedido
INNER JOIN dbo.EDetalle_cpedido
    ON dbo.EDetalle_cpedido.cod_pedido = Cabecera_Pedido.cod_cpedido
INNER JOIN dbo.Producto
    ON dbo.EDetalle_cpedido.cod_producto = dbo.Producto.cod_producto
INNER JOIN dbo.Valmacen_asoc
    ON dbo.EDetalle_cpedido.id_detalle = dbo.Valmacen_asoc.id
INNER JOIN dbo.Sublinea
    ON dbo.Producto.Cod_Linea = dbo.Sublinea.Cod_Sublinea
INNER JOIN dbo.Linea
    ON dbo.Sublinea.Cod_linea = dbo.Linea.cod_Linea
INNER JOIN dbo.Unidad
    ON dbo.Producto.Cod_Unidad = dbo.Unidad.Cod_Unidad
INNER JOIN dbo.Almacen
    ON Cabecera_Pedido.Almacen = dbo.Almacen.Cod_Almacen
INNER JOIN dbo.Vehiculo_cliente_nuevo
    ON Cabecera_Pedido.persona = dbo.Vehiculo_cliente_nuevo.Codigo
INNER JOIN dbo.Persona_Nuevo
    ON dbo.Vehiculo_cliente_nuevo.Id_ClientePersona = dbo.Persona_Nuevo.Cod_Persona
LEFT OUTER JOIN dbo.EsubVista_EstadoTraslado
    ON dbo.Producto.cod_producto = dbo.EsubVista_EstadoTraslado.CodProducto

WHERE dbo.EDetalle_cpedido.id_detalle = (
    SELECT TOP (1) id_detalle
    FROM dbo.EDetalle_cpedido AS Detalle_Sub
    WHERE cod_producto = dbo.EDetalle_cpedido.cod_producto
    ORDER BY id_detalle DESC
);
```

## Análisis

### Propósito
Mostrar el **último estado** de cada cilindro/envase, cruzando:
- Datos del producto (envase)
- Datos del último pedido/detalle
- Datos del cliente/vehículo asociado
- Estado de traslado

### Joins (8 tablas + 1 left join + 1 subquery)
1. `ECabecera_pedido` (Cabecera_Pedido)
2. `EDetalle_cpedido` (detalle del pedido)
3. `Producto` (el envase)
4. `Valmacen_asoc` (asociacion almacen)
5. `Sublinea` + `Linea` (categorización)
6. `Unidad` (unidad de medida)
7. `Almacen` (almacén actual)
8. `Vehiculo_cliente_nuevo` (vehículo del cliente)
9. `Persona_Nuevo` (cliente/proveedor)
10. `EsubVista_EstadoTraslado` (LEFT JOIN — estado de traslado)

### Filtro clave
```sql
WHERE dbo.EDetalle_cpedido.id_detalle = (
    SELECT TOP (1) id_detalle
    FROM dbo.EDetalle_cpedido AS Detalle_Sub
    WHERE cod_producto = dbo.EDetalle_cpedido.cod_producto
    ORDER BY id_detalle DESC
);
```
Solo el **último detalle** de cada producto. Si un cilindro tiene 10 pedidos, solo el último cuenta.

### Columnas críticas para stock
- `motivo` = 'Lleno' / 'Vacio' / 'Cargado' / 'En transito' / 'Recepcionado' → **estado operativo**
- `condicion` = CILCLI / CILPROV / CILPRO / CILGAR → **propietario del cilindro**
- `cod_producto` → tipo de envase
- `Nro_Producto` → serie individual
- `ultimo_id_detalle` → último movimiento registrado

### Limitaciones
1. No incluye cilindros que están en `Producto` pero nunca tuvieron pedido
2. No incluye cilindros cuyo último pedido fue eliminado
3. La subquery `TOP(1)` puede tener problemas de performance con muchos cilindros
4. No muestra el estado de `ECilindroEstadoActual` — solo el motivo del último `EDetalle_cpedido`
5. Depende de `Vehiculo_cliente_nuevo` — si un cilindro no está asignado a un vehículo-cliente, el INNER JOIN lo excluye
