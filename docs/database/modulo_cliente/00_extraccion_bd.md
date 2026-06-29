# Módulo Clientes — Extracción Directa desde SQL Server

Extraído desde: `Sys_GMS_ES` en `ACONCAGUA`
Fecha: 2026-06-27

---

## 1. Triggers

### Persona_Nuevo
**No existen triggers** en `Persona_Nuevo`.

### Vehiculo_cliente_nuevo
```sql
CREATE TRIGGER TR_VehiculoCliente_SyncDireccionFiscal
ON dbo.Vehiculo_cliente_nuevo
AFTER INSERT, UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE P
    SET Id_Direccion_Fiscal = V.Id_Direccion
    FROM dbo.Persona_Nuevo P
    INNER JOIN (
        SELECT DISTINCT Id_ClientePersona
        FROM inserted
    ) I ON P.Cod_Persona = I.Id_ClientePersona
    INNER JOIN dbo.Vehiculo_cliente_nuevo V 
        ON V.Id_ClientePersona = I.Id_ClientePersona
    WHERE V.Principal = 1
      AND V.Id_Direccion IS NOT NULL;
END
```

**Efecto:** Cuando se inserta o actualiza un punto de entrega con `Principal=1` y `Id_Direccion` no nulo, el trigger automáticamente sincroniza `Persona_Nuevo.Id_Direccion_Fiscal` con `Vehiculo_cliente_nuevo.Id_Direccion`.

### Direccion y Cliente_Sucursal
**No existen triggers.**

---

## 2. Índices No-Clusterizados

### Persona_Nuevo
**Solo el PK clusterizado.** No hay índices no-clusterizados en DNI, RUC, Nom_Persona ni Login_Persona.

### Direccion
| Index | Type | Columns |
|-------|------|---------|
| `IX_Direccion_CP` | NONCLUSTERED | `Codigo_Postal` |
| `IX_Direccion_IdLocalidad` | NONCLUSTERED | `Id_Localidad` |
| `IX_Direccion_Ubigeo` | NONCLUSTERED | `Ubigeo` |
| `IX_Direccion_Zona` | NONCLUSTERED | `Id_Zona` |

### Vehiculo_cliente_nuevo
| Index | Type | Columns |
|-------|------|---------|
| `IX_Vehiculo_cliente_nuevo_Codigo` | NONCLUSTERED | `Codigo` |
| `IX_Vehiculo_cliente_nuevo_Codigo_Alt` | NONCLUSTERED | `Codigo` |
| `IX_VehiculoCliente_Cliente` | NONCLUSTERED | `Id_ClientePersona, Principal, Codigo` |
| `IX_VehiculoCliente_IdDireccion` | NONCLUSTERED | `Id_Direccion` |
| `IX_VehiculoCliente_IdZona` | NONCLUSTERED | `Id_Zona` |
| `IXU_Vehiculo_Principal_1` | NONCLUSTERED | `Id_ClientePersona` |
| `UX_VehiculoCliente_Principal` | NONCLUSTERED | `Id_ClientePersona` |

---

## 3. CHECK Constraints

### Vehiculo_cliente_nuevo
```sql
CK__Vehiculo___Dvisi__165BC34F: ([Dvisita]='' OR [Dvisita]='Domingo' OR [Dvisita]='Sábado'
    OR [Dvisita]='Viernes' OR [Dvisita]='Jueves' OR [Dvisita]='Miércoles'
    OR [Dvisita]='Martes' OR [Dvisita]='Lunes')
```

**Nota:** Soporta días con acento (Miércoles, Sábado) y vacío.

### Persona_Nuevo
**No tiene CHECK constraints** para `Cod_TipoPersona`, `PaisCodigo` ni `FuenteValidacionActividad`.

---

## 4. SQL Jobs Relacionados

**No existen jobs personalizados.** Solo el job por defecto `syspolicy_purge_history` (políticas de gestión).

---

## 5. Tablas que Referencian Persona_Nuevo (FK)

| Tabla | Columna | FK Name |
|-------|---------|---------|
| `Correos` | `Cod_Persona` | `FK_Correos_PersonaNuevo` |
| `Creditos` | `Cod_VehiculoCliente` | `FK_CREDITOS_Persona` |
| `Datos_Bancarios` | `Cod_Responsable` | `FK_DatosBancariossi_Responsable` |
| `Datos_Bancarios` | `Id_ClientePersona` | `FK_DatosBancariossi_Cliente` |
| `Direcciones_NoClientes` | `Cod_Persona` | `FK__Direccion__Cod_P__60F3D6D7` |
| `Ecargos_funciones` | `Cod_Persona` | `FK_ECargosFunciones_PersonaNuevo` |
| `EChoferesPorMovimiento` | `Cod_Persona` | `FK_EChoferesPorMovimiento_PersonaNuevo` |
| `Persona_Proceso_Almacen` | `Cod_Persona` | `FK_Epersona_Cliente_proveedor_Persona_Nuevo` |
| `Registro_Coordenadas` | `Id_Repartidor` | `FK_Repartidor_Persona` |
| `Tarifa_cliente` | `codcliente` | `FK_TarifaCliente_Persona` |
| `Telefonos` | `Cod_Persona` | `FK_Telefonos_PersonaNuevo` |
| `Vehiculo_cliente_nuevo` | `Id_ClientePersona` | `FK__Vehiculo___Id_Cl__6C658983` |
| `Vehiculo_cliente_nuevo` | `Id_ClientePersona` | `FK__Vehiculo___Cod_P__69891CD8` |

**Total: 13 FK referencias desde 10 tablas distintas.**

---

## 6. v_ClientesEnRiesgo

**NO EXISTE** físicamente en la BD. Fue listada en `01_tablas.txt` como parte del inventario de vistas pero nunca fue creada. Pendiente de creación o documentación incorrecta.

---

## 7. DDL de Tablas Referenciadas (Extraído desde BD)

### CONTRATOS
```sql
CREATE TABLE [dbo].[CONTRATOS] (
    [Cod_Contrato]          [int] IDENTITY(1,1) NOT NULL,
    [Cod_Cliente]           [int] NOT NULL,
    [Cod_Sucursal]          [int] NULL,
    [Tipo_Contrato]         [nvarchar](50) NOT NULL,
    [Fecha_Firma]           [date] NOT NULL,
    [Fecha_Inicio]          [date] NOT NULL,
    [Fecha_Vencimiento]     [date] NULL,
    [Ruta_Archivo_Contrato] [nvarchar](500) NULL,
    [Firmado_Digital]       [bit] NOT NULL DEFAULT ((1)),
    [Estado]                [nvarchar](50) NOT NULL DEFAULT ('VIGENTE'),
    [Observaciones]         [nvarchar](1000) NULL,
    [Fecha_Registro]        [datetime] NOT NULL DEFAULT (getdate()),
    [Usuario_Registro]      [nvarchar](100) NOT NULL,
    CONSTRAINT [PK__CONTRATOS__Cod_Contrato] PRIMARY KEY CLUSTERED ([Cod_Contrato])
);
```

### Datos_Bancarios
```sql
CREATE TABLE [dbo].[Datos_Bancarios] (
    [Id_DatoBancario]   [int] IDENTITY(1,1) NOT NULL,
    [Cod_Responsable]   [int] NULL,
    [Id_ClientePersona] [int] NULL,
    [Numero_Cuenta]     [nvarchar](34) NOT NULL,
    [Forma_Pago]        [nvarchar](50) NOT NULL,
    [Activo]            [bit] NOT NULL DEFAULT ((1)),
    [Fecha_Alta]        [date] NOT NULL DEFAULT (getdate()),
    [Fecha_Baja]        [date] NULL,
    [Motivo_Baja]       [nvarchar](200) NULL,
    [Usuario_Baja]      [nvarchar](50) NULL,
    [IdBanco]           [int] NOT NULL,
    CONSTRAINT [PK__Datos_Bancarios] PRIMARY KEY CLUSTERED ([Id_DatoBancario])
);
```

### Ruta
```sql
CREATE TABLE [dbo].[Ruta] (
    [Id_Ruta]     [int] IDENTITY(1,1) NOT NULL,
    [Nombre]      [nvarchar](80) NOT NULL,
    [Descripcion] [nvarchar](200) NULL,
    [Activo]      [bit] NOT NULL DEFAULT ((1)),
    [ColorHex]    [char](7) NULL,
    CONSTRAINT [PK__Ruta] PRIMARY KEY CLUSTERED ([Id_Ruta])
);
```

### Ecargos_funciones
```sql
CREATE TABLE [dbo].[Ecargos_funciones] (
    [Id_CargoFuncion]  [int] IDENTITY(1,1) NOT NULL,
    [Cod_Persona]      [int] NOT NULL,
    [Cod_Sucursal]     [int] NOT NULL,
    [CargoFuncion]     [nvarchar](50) NOT NULL,
    [Activo]           [bit] NOT NULL DEFAULT ((1)),
    [Fecha_Asignacion] [date] NOT NULL DEFAULT (getdate()),
    [Fecha_Inactivo]   [date] NULL,
    CONSTRAINT [PK__Ecargos_funciones] PRIMARY KEY CLUSTERED ([Id_CargoFuncion]),
    CONSTRAINT [FK_ECargosFunciones_PersonaNuevo]
        FOREIGN KEY ([Cod_Persona]) REFERENCES [dbo].[Persona_Nuevo]([Cod_Persona])
);
```

### Ecil_duenio
```sql
CREATE TABLE [dbo].[Ecil_duenio] (
    [Id_cambio]        [int] IDENTITY(1,1) NOT NULL,
    [Id_persona]       [int] NOT NULL,
    [Id_producto]      [int] NOT NULL,
    [Edet_movimiento]  [int] NOT NULL,
    [Fecha_cambio]     [datetime] NULL DEFAULT (getdate()),
    [Estado_condicion] [nvarchar](50) NULL,
    CONSTRAINT [PK__Ecil_duenio] PRIMARY KEY CLUSTERED ([Id_cambio])
);
```

### Persona_Proceso_Almacen
```sql
CREATE TABLE [dbo].[Persona_Proceso_Almacen] (
    [IdRelacion]  [int] IDENTITY(1,1) NOT NULL,
    [Cod_Persona] [int] NULL,
    [Cod_Almacen] [int] NULL,
    [PROCESO]     [nvarchar](50) NULL,
    [Planta]      [varchar](50) NULL,
    [Grupo]       [nvarchar](50) NULL,
    CONSTRAINT [PK__Persona_Proceso_Almacen] PRIMARY KEY CLUSTERED ([IdRelacion])
);
```

### Geografía

#### CP_Pais
```sql
CREATE TABLE [dbo].[CP_Pais] (
    [Id_Pais] [int] IDENTITY(1,1) NOT NULL,
    [Nombre]  [nvarchar](100) NOT NULL,
    [ISO2]    [char](2) NOT NULL,
    CONSTRAINT [PK__CP_Pais] PRIMARY KEY CLUSTERED ([Id_Pais])
);
```

#### CP_Provincia
```sql
CREATE TABLE [dbo].[CP_Provincia] (
    [Id_Provincia]         [int] IDENTITY(1,1) NOT NULL,
    [Id_ComunidadAutonoma] [int] NOT NULL,
    [Nombre]               [nvarchar](120) NOT NULL,
    [INE_Provincia]        [char](2) NOT NULL,
    [PaisCodigo]           [char](2) NULL,
    [CodigoOficial]        [nvarchar](20) NULL,
    CONSTRAINT [PK__CP_Provincia] PRIMARY KEY CLUSTERED ([Id_Provincia])
);
```

#### CP_Municipio
```sql
CREATE TABLE [dbo].[CP_Municipio] (
    [Id_Municipio]  [int] IDENTITY(1,1) NOT NULL,
    [Id_Provincia]  [int] NOT NULL,
    [Nombre]        [nvarchar](150) NOT NULL,
    [INE_Municipio] [char](5) NOT NULL,
    [PaisCodigo]    [char](2) NULL,
    [CodigoOficial] [nvarchar](20) NULL,
    CONSTRAINT [PK__CP_Municipio] PRIMARY KEY CLUSTERED ([Id_Municipio])
);
```

#### CP_Localidad
```sql
CREATE TABLE [dbo].[CP_Localidad] (
    [Id_Localidad]         [int] IDENTITY(1,1) NOT NULL,
    [Id_Municipio]         [int] NOT NULL,
    [Nombre]               [nvarchar](255) NOT NULL,
    [Codigo_Postal]        [char](5) NULL,
    [EsPrincipalMunicipio] [bit] NULL DEFAULT ((0)),
    [EsPlaceholder]        [bit] NULL DEFAULT ((1)),
    [Activo]               [bit] NULL DEFAULT ((1)),
    [PaisCodigo]           [char](2) NULL,
    [CodigoOficial]        [nvarchar](20) NULL,
    CONSTRAINT [PK__CP_Localidad] PRIMARY KEY CLUSTERED ([Id_Localidad])
);
```

---

## 8. Resumen de Hallazgos Críticos

| Hallazgo | Estado Anterior | Estado Real |
|----------|----------------|-------------|
| Triggers en Persona_Nuevo | Desconocido | **No existen** |
| Trigger en Vehiculo_cliente_nuevo | Desconocido | **Sí: `TR_VehiculoCliente_SyncDireccionFiscal`** |
| Índices en Persona_Nuevo | Asumidos (DNI, RUC, Nombre) | **Solo PK clusterizado** |
| CHECK Cod_TipoPersona IN (1,2,3,4,5) | Asumido | **No existe** |
| v_ClientesEnRiesgo | Vista documentada | **No existe físicamente** |
| Jobs personalizados | Desconocido | **No existen** |
| FK de Persona_Nuevo | ~10 tablas | **13 FK desde 10 tablas** |
| CContab.vb UPDATE directo | Sospecha | **Confirmado** (`Actualizar_FormaPago`) |
