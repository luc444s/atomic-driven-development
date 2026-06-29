# 01 — DDL de Tablas — Productos/Catálogos

## Producto — Tabla principal (70+ columnas)

```sql
CREATE TABLE [dbo].[Producto](
    [cod_producto]       [int]           NOT NULL,      -- PK, IDENTITY
    [Nro_Producto]       [nvarchar](20)  NULL,           -- Código de barras / SKU
    [Nro_cja]            [nvarchar](4000) NULL,           -- Nro de caja (descripción larga)
    [Desc_Producto]      [nvarchar](3000) NULL,           -- Descripción del producto
    [StockMin_Producto]  [float]         NULL,           -- Stock mínimo
    [Cod_Linea]          [int]           NULL,            -- FK lógica a Linea
    [Cod_TipoInsumo]     [int]           NULL,            -- FK lógica a TipoInsumo
    [Cod_Unidad]         [int]           NULL,            -- FK lógica a Unidad (unidad principal)
    [Cod_UnidadCja]      [int]           NULL,            -- FK lógica a Unidad (unidad de caja)
    [Precio_Producto]    [money]         NULL,            -- Precio unitario
    [PrecioCja_Producto] [money]         NULL,            -- Precio por caja
    [Costo_Producto]     [money]         NULL,            -- Costo del producto
    [peso_producto]      [float]         NULL,            -- Peso / contenido
    [Marca_Producto]     [int]           NULL,            -- FK lógica a Marca
    [Estado_Producto]    [int]           NULL,            -- FK lógica a EstadoProducto
    [cIGV]               [int]           NULL,            -- 0=Exonerado IGV, 1=Gravado
    [Costo_Rep]          [money]         NOT NULL DEFAULT ((0)), -- Costo de reposición
    [UtilidadxUnid]      [float]         NULL,            -- Utilidad por unidad (%)
    [UtilidadxCja]       [float]         NULL,            -- Utilidad por caja (%)
    [crapido]            [int]           NOT NULL DEFAULT ((0)), -- Código rápido (flag)
    [precio_interm]      [money]         NULL,            -- Precio intermedio
    [utilidadxint]       [float]         NULL,            -- Utilidad intermedia (%)
    [cant]               [float]         NULL,            -- Cantidad por caja
    [UtilidadEstxunid]   [float]         NULL,            -- Utilidad estándar por unidad
    [UtilidadEstxInterm] [float]         NULL,            -- Utilidad estándar intermedia
    [UtilidadEstxCja]    [float]         NULL,            -- Utilidad estándar por caja
    [MargAct]            [int]           NULL,            -- Margen actual
    [MargEst]            [int]           NULL,            -- Margen estándar
    [DifPrecios]         [int]           NULL,            -- Diferencia de precios
    [costo_Ant]          [money]         NOT NULL DEFAULT ((0)), -- Costo anterior
    [codcv]              [int]           NULL,            -- Código contable (¿? posiblemente cuentas)
    [percepcion]         [int]           NOT NULL DEFAULT ((0)), -- Percepción (flag)
    [Cont]               [float]         NULL,            -- Contenido
    [barcode]            [image]         NULL,            -- Imagen de código de barras (obsoleto)
    [Letra]              [nvarchar](1)   NULL,            -- Letra de clasificación
    [foto]               [image]         NULL,            -- Foto del producto
    [cod_SubCategoria]   [int]           NULL,            -- FK lógica a SubCategoria
    [porc_ce]            [float]         NULL,            -- Porcentaje comisión externa
    [cod_grupo]          [int]           NOT NULL DEFAULT ((1)), -- FK lógica a Grupo
    [cgi]                [money]         NOT NULL DEFAULT ((0)), -- Costo de gestión integral
    [costo_total]        [money]         NOT NULL DEFAULT ((0)), -- Costo total
    [tiempoi]            [nvarchar](500) NULL,            -- Tiempo de entrega / instalación
    [eliminar]           [int]           NULL,            -- Flag de eliminación lógica
    [servicio]           [int]           NOT NULL DEFAULT ((0)), -- Es servicio (flag)
    [barcode1]           [nvarchar](150) NULL,            -- Código de barras 1 (CABYS/Hacienda)
    [barcode2]           [nvarchar](50)  NULL,            -- Código de barras 2 (matrícula)
    [stock]              [int]           NOT NULL DEFAULT ((0)), -- Stock actual (desnormalizado)
    [pRECIO_INV]         [money]         NULL,            -- Precio de inventario
    [COSTO_INV]          [money]         NULL,            -- Costo de inventario
    [lista2]             [money]         NOT NULL DEFAULT ((0)), -- Lista de precios 2
    [lista3]             [money]         NOT NULL DEFAULT ((0)), -- Lista de precios 3
    [lista4]             [money]         NOT NULL DEFAULT ((0)), -- Lista de precios 4
    [estadopromo]        [int]           NULL,            -- Estado de promoción
    [condicion]          [nvarchar](50)  NULL,            -- Condición: PRODUCTO, GAS, CILPRO, CILCLI, etc.
    [M3]                 [decimal]       NULL,            -- Metros cúbicos
    [ADR_Categoria]      [nvarchar](50)  NULL,            -- ADR: categoría
    [ADR_TipoBulto]      [nvarchar](50)  NULL,            -- ADR: tipo de bulto
    [ADR_PesoKg]         [decimal]       NULL,            -- ADR: peso en kg
    [ADR_M3]             [decimal]       NULL,            -- ADR: metros cúbicos
    [ADR_UN]             [varchar](10)   NULL,            -- ADR: número UN
    [ADR_Mercancia]      [nvarchar](500) NULL,            -- ADR: denominación mercancía
    [ADR_Etiqueta]       [varchar](50)   NULL,            -- ADR: etiqueta
    [ADR_Tunel]          [varchar](10)   NULL,            -- ADR: restricción de túnel
    [ADR_Sublinea]       [int]           NULL,            -- ADR: sublínea
    [ADR_Factor]         [int]           NULL,            -- ADR: factor
    [ADR_Puntos]         [int]           NULL,            -- ADR: puntos
    [ADR_UnidadMedida]   [nvarchar](20)  NULL,            -- ADR: unidad de medida
    [PaisCodigo]         [char](2)       NULL,            -- País (PE, CR, ES)
 CONSTRAINT [PK_Producto_1] PRIMARY KEY CLUSTERED ([cod_producto] ASC)
)
```

### Columnas calculadas / derivadas en aplicación
Ninguna columna es calculada en SQL. Todos los cálculos (precio = costo * (1 + margen/100), utilidades, etc.) se hacen en VB.NET.

## Linea

```sql
CREATE TABLE [dbo].[Linea](
    [cod_Linea]  [int]           NOT NULL,  -- PK
    [Desc_Linea] [nvarchar](500) NULL,
    [cod_rubro]  [int]           NULL,       -- FK lógica a Rubro
 CONSTRAINT [PK_Linea] PRIMARY KEY CLUSTERED ([cod_Linea] ASC)
)
```

## SubLinea

```sql
CREATE TABLE [dbo].[Sublinea](
    [Cod_Sublinea]  [int]           NOT NULL,  -- PK
    [Desc_SubLinea] [nvarchar](500) NOT NULL,
    [Cod_linea]     [int]           NOT NULL,   -- FK lógica a Linea
 CONSTRAINT [PK_Sublinea] PRIMARY KEY CLUSTERED ([Cod_Sublinea] ASC)
)
```

## Marca

```sql
CREATE TABLE [dbo].[Marca](
    [Cod_Marca]  [int]          NOT NULL,  -- PK
    [Desc_Marca] [nvarchar](50) NULL,
 CONSTRAINT [PK_Marca] PRIMARY KEY CLUSTERED ([Cod_Marca] ASC)
)
```

## Rubro

```sql
CREATE TABLE [dbo].[Rubro](
    [Cod_Rubro]  [int]           NOT NULL,  -- PK
    [Desc_Rubro] [nvarchar](500) NULL,
 CONSTRAINT [PK_Rubro] PRIMARY KEY CLUSTERED ([Cod_Rubro] ASC)
)
```

## TipoInsumo

```sql
CREATE TABLE [dbo].[TipoInsumo](
    [Cod_TipoInsumo]  [int]          NOT NULL,  -- PK
    [Desc_TipoInsumo] [nvarchar](50) NULL,
 CONSTRAINT [PK_TipoInsumo] PRIMARY KEY CLUSTERED ([Cod_TipoInsumo] ASC)
)
```

## Unidad

```sql
CREATE TABLE [dbo].[Unidad](
    [Cod_Unidad]  [int]          NOT NULL,  -- PK
    [Desc_Unidad] [nvarchar](50) NULL,
    [Equivalencia] [int]         NULL,       -- 1=unidad base, otro=conversión
    [m3]           [float]       NULL,       -- Factor m3
    [Litros]       [float]       NULL,       -- Factor litros
    [Kilogramos]   [float]       NULL,       -- Factor kilogramos
 CONSTRAINT [PK_Unidad] PRIMARY KEY CLUSTERED ([Cod_Unidad] ASC)
)
```

## SubCategoria

```sql
CREATE TABLE [dbo].[SubCategoria](
    [codigo]       [int]          NOT NULL,  -- PK
    [Descripcion]  [nvarchar](50) NULL,       -- GAS, BOMBONAS, PRODUCTOS, SERVICIOS, etc.
 CONSTRAINT [PK_SubCategoria_1] PRIMARY KEY CLUSTERED ([codigo] ASC)
)
```

## Grupo

```sql
CREATE TABLE [dbo].[Grupo](
    [Cod_Grupo]             [int]          NOT NULL,  -- PK
    [ID_ProductoGas]        [int]          NULL,       -- ID del producto gas asociado
    [CodBar_ProductoGas]    [nvarchar](50) NULL,       -- Código de barras del gas
    [Desc_Grupo]            [nvarchar](50) NULL,       -- Descripción del grupo
    [id_Categoria]          [int]          NULL,       -- Categoría
    [Categoria]             [nvarchar](50) NULL,
    [id_Linea]              [int]          NULL,       -- Línea asociada
    [Desc_Linea]            [nvarchar](50) NULL,
    [id_SubLinea]           [int]          NULL,       -- Sublínea asociada
    [Desc_SubLinea]         [nvarchar](50) NULL,
    [id_unidad]             [int]          NULL,       -- Unidad asociada
    [Desc_unidad]           [nvarchar](50) NULL,
    [Precio1]               [money]        NULL,       -- Precio nivel 1
    [Precio2]               [money]        NULL,       -- Precio nivel 2
    [Precio3]               [money]        NULL,       -- Precio nivel 3
    [Precio4]               [money]        NULL,       -- Precio nivel 4
 CONSTRAINT [PK_Grupo] PRIMARY KEY CLUSTERED ([Cod_Grupo] ASC)
)
```

## EstadoProducto

```sql
CREATE TABLE [dbo].[EstadoProducto](
    [Cod_EstadoProd]  [int]          NOT NULL,  -- PK
    [Desc_EstadoProd] [nvarchar](50) NULL,       -- Activo, Inactivo, etc.
 CONSTRAINT [PK_EstadoProducto] PRIMARY KEY CLUSTERED ([Cod_EstadoProd] ASC)
)
```

## Promocion

```sql
CREATE TABLE [dbo].[Promocion](
    [Cod_Id]      [int]      NOT NULL,  -- PK
    [Cantidad]    [int]      NULL,       -- Cantidad requerida
    [PrecioUni]   [money]    NULL,       -- Precio unitario en promoción
    [FechaVenc]   [datetime] NULL,       -- Fecha de vencimiento
    [Porcentaje]  [money]    NULL,       -- Porcentaje de descuento
    [Oferta]      [nvarchar](10) NULL,   -- Tipo de oferta
    [cod_prod]    [int]      NOT NULL,   -- FK lógica a Producto
    [FechaIni]    [datetime] NULL,       -- Fecha de inicio
    [estadoPromo] [int]      NULL,       -- 0=inactiva, 1=activa
    [PrecioCaja]  [money]    NULL,       -- Precio por caja en promoción
 CONSTRAINT [PK_Promocion] PRIMARY KEY CLUSTERED ([Cod_Id] ASC)
)
```

## Descuento

La tabla `Descuento` se referencia en SPs como `sp_Descuento_Buscarxproducto` pero no se encontró su DDL en INFORMATION_SCHEMA. Se usan SPs como `descuento_Buscar`, `descuento_Insertar`, `descuento_Modificar`.

## Tablas de Bombonas/Envases

### Edetalle_retimbrado
```sql
-- Histórico de retimbrado de bombonas
CREATE TABLE [dbo].[Edetalle_retimbrado](
    [Id]                 [int] IDENTITY(1,1) NOT NULL,
    [Cod_producto]       [int] NULL,
    [Codigo_fabricacion] [nvarchar](50) NULL,
    [Anio_fabricacion]   [int] NULL,
    [Nro_Bombona]        [nvarchar](50) NULL,
    [Peso_origen]        [decimal](18,2) NULL,
    [Peso_actual]        [decimal](18,2) NULL,
    [Presion_servicio]   [decimal](18,2) NULL,
    [Presion_prueba]     [decimal](18,2) NULL,
    [Nro_aprobacion]     [nvarchar](50) NULL,
    [Clase_peligro]      [nvarchar](50) NULL,
    [Marcado1]           [nvarchar](50) NULL,
    [Marcado2]           [nvarchar](50) NULL,
    [Formato_Bulto]      [nvarchar](50) NULL,
    [Transporte]         [nvarchar](50) NULL,
    [Etiqueta]           [nvarchar](50) NULL,
    [Tuneles]            [nvarchar](50) NULL,
    [Nro_ONU]            [nvarchar](50) NULL,
    [Regist_Alimentario] [nvarchar](50) NULL,
    [Estado]             [int] NULL
)
```

### Edetalle_Producto_Bombona
```sql
-- Datos ADR con vigencias por bombona
CREATE TABLE [dbo].[Edetalle_Producto_Bombona](
    [Id_PROD_Bombonas]       [int] NOT NULL,
    [CATEG_transp]           [nvarchar](100) NULL,
    [TIPO_DE_BULTO]          [varchar](50) NULL,
    [CANTIDAD_NETA]          [decimal](18,6) NULL,
    [UNIDAD]                 [int] NULL,
    [M3_gas]                 [decimal](10,2) NULL,
    [PESO_NETO_KG]           [decimal](10,2) NULL,
    [DENOMINACION_MERCANCIA] [nvarchar](1000) NULL,
    [NRO_ONU]                [varchar](10) NULL,
    [PRODUCTO_TRANSPORTADO]  [nvarchar](1000) NULL,
    [ETIQUETA]               [varchar](50) NULL,
    [TUNEL]                  [varchar](10) NULL,
    [SUBLINEA_PROD]          [int] NULL,
    [VigenteDesde]           [date] NULL,
    [VigenteHasta]           [date] NULL
)
```

### Eph (Pruebas Hidráulicas)
```sql
CREATE TABLE [dbo].[Eph](
    [Id_Cilindro]   [int] NULL,
    [Fecha_PH]      [datetime] NULL,
    [Estado]        [nvarchar](50) NULL,
    [Modificado_por][nvarchar](50) NULL
)
```

### ECilindroEstadoLog / ECilindroEstadoActual
```sql
-- Log de cambios de estado de cilindros
CREATE TABLE [dbo].[ECilindroEstadoLog](
    [IdEstado]     [int] IDENTITY(1,1) NOT NULL,
    [Serie]        [varchar](50) NULL,
    [Estado]       [varchar](20) NULL,
    [Fecha]        [datetime] NULL,
    [Usuario]      [int] NULL,
    [Observacion]  [varchar](400) NULL,
    [Origen]       [varchar](50) NULL,
    [MotivoCodigo] [varchar](30) NULL,
    [AlmacenId]    [int] NULL
)

-- Vista materializada del último estado
CREATE VIEW [dbo].[ECilindroEstadoActual] AS
SELECT ... FROM ECilindroEstadoLog con ROW_NUMBER() ...
```
