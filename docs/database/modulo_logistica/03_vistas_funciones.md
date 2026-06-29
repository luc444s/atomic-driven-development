# Vistas, Funciones y TVPs del Módulo Logística

## VISTAS

### vPreparacionCarga
Vista principal para preparación de carga. Utilizada por `sp_PreparacionCarga_ListarPendientes`.
```sql
-- SELECT desde DetalleMovimiento con joins a:
--   Movimiento, Producto, Almacen, Cliente, EDetalle_cpedido
-- Filtros: movimientos tipo despacho/traslado pendientes
```

### vw_EdetPB_Vigente
Configuración ADR vigente por producto gas.
```sql
-- SELECT desde EDetalle_PB con vigencia por fecha
-- Muestra: CodProducto, ClaseADR, PuntosADR, Tunel, CantidadMaxima
-- WHERE GETDATE() BETWEEN FechaInicio AND FechaFin
```

### v_CilindrosDisponibles
Cilindros disponibles para asignación en logística.
```sql
-- SELECT desde ECilindroEstadoActual
-- WHERE Estado IN ('LLENO_EN_ALMACEN', 'LLENADO_OK')
-- AND NoAsignado = 1
```

### v_Cilindros_VaciosEnAlmacen
Cilindros vacíos en almacén.
```sql
-- SELECT desde ECilindroEstadoActual
-- WHERE Estado = 'VACIO_EN_ALMACEN'
```

### v_UltimoPH_porCilindro
Última prueba hidráulica (PH) por cilindro.
```sql
-- SELECT Serie, MAX(FechaPH) as UltimaPH, ProximaPH
-- FROM CilindroPH GROUP BY Serie, ProximaPH
```

### vCilindroEstadoActualDet
Estado actual detallado de cilindros (con datos del producto y ubicación).
```sql
-- SELECT desde ECilindroEstadoActual con joins a:
--   Cilindro (serie, capacidad, tara)
--   Producto (nombre, grupo)
--   Almacen (ubicación)
```

### v_ResumenCarga_Repartidor
Resumen de carga por repartidor para un día.
```sql
-- SELECT IdRepartidor, SUM(Peso) as PesoTotal, COUNT(Serie) as TotalCilindros
-- FROM AGENDA_PREPARACION_CARGA
-- GROUP BY IdRepartidor
```

### v_PesoCilindroSerie
Peso por serie de cilindro (incluye contenido estimado).
```sql
-- SELECT Serie, Tara, Capacidad, ContenidoKG
-- FROM Cilindro c
-- JOIN Producto p ON c.CodProducto = p.CodProducto
-- CROSS APPLY fn_ContenidoCilindro(p.CodProducto)
```

### vCartaPorte
Datos completos de carta porte (cabecera + detalle).
```sql
-- SELECT desde Movimiento, Cliente, Transportista, Vehiculo
-- con detalle de productos y bultos
```

### vw_Ruta_Centroides
Centroides de rutas para georreferenciación.
```sql
-- SELECT IdRuta, AVG(Latitud) as CentroLat, AVG(Longitud) as CentroLon
-- FROM RutaPto GROUP BY IdRuta
```

### v_Cilindros_Vacios_ALM_conPH
Cilindros vacíos en almacén con información de prueba hidráulica.
```sql
-- Combinación de v_Cilindros_VaciosEnAlmacen con v_UltimoPH_porCilindro
```

---

## FUNCIONES

### fn_ADR_Points
Calcula puntos ADR según producto y cantidad.
```sql
CREATE FUNCTION fn_ADR_Points
    (@CodProducto NVARCHAR(20), @Cantidad DECIMAL(18,2))
RETURNS DECIMAL(18,2)
AS
BEGIN
    -- Calcula: PuntosADR * @Cantidad según configuración vigente
    -- desde vw_EdetPB_Vigente
END;
```

### fn_ContenidoCilindro
Obtiene contenido en kg de un producto para cilindros.
```sql
CREATE FUNCTION fn_ContenidoCilindro
    (@CodProducto NVARCHAR(20))
RETURNS DECIMAL(18,2)
AS
BEGIN
    -- Retorna ContenidoKG según configuración de producto
END;
```

### ufn_Valida_ADR
Valida si la configuración ADR de un producto está vigente.
```sql
CREATE FUNCTION ufn_Valida_ADR
    (@ProductoGasId INT)
RETURNS BIT
AS
BEGIN
    -- Retorna 1 si existe registro vigente en EDetalle_PB
END;
```

### ufn_Valida_PH
Valida si la prueba hidráulica de un cilindro está vigente.
```sql
CREATE FUNCTION ufn_Valida_PH
    (@CilindroId INT)
RETURNS BIT
AS
BEGIN
    -- Retorna 1 si ProximaPH >= GETDATE()
END;
```

### fn_StockFisico_Planificador
Stock físico disponible para planificador por almacén y producto.
```sql
CREATE FUNCTION fn_StockFisico_Planificador
    (@IdAlmacen INT, @CodProducto NVARCHAR(20))
RETURNS DECIMAL(18,2)
AS
BEGIN
    -- Calcula: StockActual - StockComprometido - StockPlanificado
END;
```

### fn_StockFisico_Planificador_Grupo
Stock físico disponible por almacén y grupo de producto.
```sql
CREATE FUNCTION fn_StockFisico_Planificador_Grupo
    (@IdAlmacen INT, @CodGrupo NVARCHAR(20))
RETURNS DECIMAL(18,2)
AS
BEGIN
    -- Calcula stock sumando todos los productos del grupo
END;
```

---

## TABLE-VALUED PARAMETERS (TVPs)

### CilindroEstadoTVP
Para cambios de estado bulk en cilindros (usado por `usp_Cilindro_Estado_LogBulk`).
```sql
CREATE TYPE dbo.CilindroEstadoTVP AS TABLE
(
    Serie NVARCHAR(50),
    Estado NVARCHAR(50),
    Usuario NVARCHAR(50)
);
```

### Ruta_Reorden_TVP
Para reordenamiento masivo de puntos de ruta.
```sql
CREATE TYPE dbo.Ruta_Reorden_TVP AS TABLE
(
    IdPunto INT,
    NuevoOrden INT
);
```

### TipoListaSeries
Lista de series de cilindros para consultas masivas.
```sql
CREATE TYPE dbo.TipoListaSeries AS TABLE
(
    Serie NVARCHAR(50)
);
```

### TVP_CargaBombonas
Carga de bombonas en escaneo/logística.
```sql
CREATE TYPE dbo.TVP_CargaBombonas AS TABLE
(
    Serie NVARCHAR(50),
    CodProducto NVARCHAR(20),
    Peso DECIMAL(18,2)
);
```

### TVP_Series
Series con observaciones.
```sql
CREATE TYPE dbo.TVP_Series AS TABLE
(
    Serie NVARCHAR(50),
    Observacion NVARCHAR(500)
);
```

### TipoListaProductos
Lista de productos para consultas masivas.
```sql
CREATE TYPE dbo.TipoListaProductos AS TABLE
(
    CodProducto NVARCHAR(20)
);
```
