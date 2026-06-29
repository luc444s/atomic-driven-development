# Módulo Clientes — DDL de Tablas

## Tabla: Persona_Nuevo (Entidad universal)

Almacena clientes, proveedores, empleados, repartidores y usuarios del sistema.

```sql
CREATE TABLE [dbo].[Persona_Nuevo] (
    [Cod_Persona]               [int] IDENTITY(1,1) NOT NULL,
    [Nro_Persona]               [nvarchar](50) NULL,
    [Nom_Persona]               [nvarchar](200) NOT NULL,
    [Dni_Persona]               [nvarchar](20) NULL,
    [Ruc_Persona]               [nvarchar](20) NULL,
    [Cod_TipoPersona]           [int] NOT NULL,
    [Sexo_Persona]              [nvarchar](10) NULL,
    [FNac_Personal]             [date] NULL,
    [mail_Persona]              [nvarchar](100) NULL,
    [Telefono_Persona]          [nvarchar](50) NULL,
    [Activo]                    [bit] NOT NULL,
    [Login_Persona]             [nvarchar](50) NULL,
    [Pass_Persona]              [nvarchar](50) NULL,
    [Nick_Persona]              [nvarchar](50) NULL,
    [Fotografia]                [nvarchar](50) NULL,
    [id_clave_Operacion]        [int] NULL,
    [clave_op_intracomunitaria] [bit] NULL,
    [nombre_comercial]          [varchar](100) NULL,
    [observaciones]             [nvarchar](MAX) NULL,
    [Documento_Principal]       [nvarchar](50) NULL,
    [Tipo_facturacion]          [nvarchar](50) NULL,
    [Id_FormaPago]              [int] NULL,
    [Id_Direccion_Fiscal]       [int] NULL,
    [PaisCodigo]                [varchar](5) NULL,
    [TipoIdentificacionFiscal]  [varchar](20) NULL,
    [NumeroIdentificacionFiscal][varchar](30) NULL,
    [CodigoActividadPrincipal]  [varchar](20) NULL,
    [DescripcionActividadPrincipal] [nvarchar](300) NULL,
    [ActividadValidada]         [bit] NOT NULL,
    [FechaValidacionActividad]  [datetime] NULL,
    [FuenteValidacionActividad] [varchar](50) NULL,
    CONSTRAINT [PK__Persona___366BBA5BA35E20C7] PRIMARY KEY CLUSTERED ([Cod_Persona]),
    CONSTRAINT [FK__Persona_N__Id_Fo__2A2DB1D2] FOREIGN KEY ([Id_FormaPago])
        REFERENCES [dbo].[Formas_pago]([Id_FormaPago]),
    CONSTRAINT [FK_Persona_DireccionFiscal] FOREIGN KEY ([Id_Direccion_Fiscal])
        REFERENCES [dbo].[Direccion]([Id_Direccion])
);
```

**Notas:**
- `Cod_TipoPersona`: 1=Cliente, 2=Proveedor, 3=Empleado, 4=Repartidor, 5=Agente
- `ActividadValidada` tiene default `0` (bit NOT NULL sin default explícito en DDL)
- `FuenteValidacionActividad`: "SUNAT", "HACIENDA_CR", "MANUAL"
- No se encontraron CHECK constraints documentados para Cod_TipoPersona
- No se encontraron triggers documentados en Persona_Nuevo
- No se encontraron índices no-clusterizados documentados (existen físicamente en BD)

---

## Tabla: Direccion

```sql
CREATE TABLE [dbo].[Direccion] (
    [Id_Direccion]     [int] IDENTITY(1,1) NOT NULL,
    [Linea1]           [nvarchar](200) NOT NULL,
    [Linea2]           [nvarchar](200) NULL,
    [Codigo_Postal]    [nvarchar](12) NULL,
    [Id_Zona]          [int] NULL,
    [Ubigeo]           [nvarchar](6) NULL,
    [Latitud]          [float] NULL,
    [Longitud]         [float] NULL,
    [Observaciones]    [nvarchar](250) NULL,
    [Activo]           [bit] NOT NULL,
    [Fecha_Alta]       [date] NOT NULL,
    [Id_Localidad]     [int] NULL,
    [Formatted_Address][nvarchar](255) NULL,
    [Place_Id]         [nvarchar](64) NULL,
    [Country_Code]     [char](2) NULL,
    [Admin_Area_1]     [nvarchar](120) NULL,
    [Admin_Area_2]     [nvarchar](120) NULL,
    [Localidad]        [nvarchar](120) NULL,
    [Street_Name]      [nvarchar](160) NULL,
    [Street_Number]    [nvarchar](20) NULL,
    [Fuente_Geocod]    [nvarchar](20) NULL,
    [Precision_Metros] [int] NULL,
    [Capturado_Por]    [nvarchar](50) NULL,
    [Capturado_En]     [datetime2] NULL,
    CONSTRAINT [PK__Direccio__535FD61188D64EC3] PRIMARY KEY CLUSTERED ([Id_Direccion])
);
```

**Notas:**
- FKs a ZONA (Id_Zona) y Localidad (Id_Localidad) existen físicamente pero no están en constraints documentados
- `Fuente_Geocod`: "GOOGLE", "MANUAL", "OSM"
- `Country_Code`: ISO 3166-1 alpha-2 (PE, ES, CR)
- No se encontraron triggers documentados

---

## Tabla: Vehiculo_cliente_nuevo (Puntos de Entrega)

```sql
CREATE TABLE [dbo].[Vehiculo_cliente_nuevo] (
    [Codigo]              [int] IDENTITY(1,1) NOT NULL,
    [Id_ClientePersona]   [int] NOT NULL,
    [Direccion]           [nvarchar](200) NOT NULL,
    [Contacto]            [nvarchar](100) NULL,
    [Telefono]            [nvarchar](50) NULL,
    [Correoresp]          [nvarchar](100) NULL,
    [Enlace_GPS]          [nvarchar](200) NULL,
    [Id_Zona]             [int] NOT NULL,
    [Dreparto]            [nvarchar](50) NULL,
    [Id_Agente_Asignado]  [int] NULL,
    [Id_DatoBancario]     [int] NULL,
    [Observ_Responsable]  [nvarchar](200) NULL,
    [Principal]           [bit] NOT NULL,
    [Activo]              [bit] NOT NULL,
    [Fecha_Registro]      [date] NOT NULL,
    [ubigeo]              [nvarchar](6) NULL,
    [Dvisita]             [nvarchar](50) NULL,
    [garantia]            [nvarchar](50) NULL,
    [Envio]               [int] NULL,
    [Id_Sucursal]         [int] NOT NULL,
    [Id_Direccion]        [int] NULL,
    [NombrePunto]         [nvarchar](100) NULL,
    [VentanaHorario]      [nvarchar](50) NULL,
    [Indicaciones]        [nvarchar](200) NULL,
    [Id_RutaAsignada]     [int] NULL,
    [UsuarioCrea]         [nvarchar](50) NULL,
    [FechaCrea]           [datetime2] NULL,
    [UsuarioMod]          [nvarchar](50) NULL,
    [FechaMod]            [datetime2] NULL,
    [RowVersion]          [timestamp] NOT NULL,
    [TiempoServicioMin]   [int] NULL,
    [DemandaUnidades]     [int] NULL,
    [DemandaPesoKg]       [decimal] NULL,
    [PaisCodigo]          [varchar](5) NULL,
    [Documento_Fiscal_Operacion] [nvarchar](50) NULL,
    [TipoOperacionFiscal] [varchar](30) NULL,
    CONSTRAINT [PK__Vehiculo__06370DADE8241667] PRIMARY KEY CLUSTERED ([Codigo]),
    CONSTRAINT [CK__Vehiculo___Dvisi__165BC34F]
        CHECK ([Dvisita] IS NULL OR [Dvisita] IN (N'LUNES',N'MARTES',N'MIÉRCOLES',N'JUEVES',N'VIERNES',N'SÁBADO',N'DOMINGO')),
    CONSTRAINT [FK_VehCliente_Direccion]
        FOREIGN KEY ([Id_Direccion]) REFERENCES [dbo].[Direccion]([Id_Direccion]),
    CONSTRAINT [FK__Vehiculo___Id_Cl__6C658983]
        FOREIGN KEY ([Id_ClientePersona]) REFERENCES [dbo].[Persona_Nuevo]([Cod_Persona]),
    CONSTRAINT [FK__Vehiculo___Id_Zo__576A6C9D]
        FOREIGN KEY ([Id_Zona]) REFERENCES [dbo].[ZONA]([Cod_Zona]),
    CONSTRAINT [FK_Vehiculo_Almacen]
        FOREIGN KEY ([Id_Sucursal]) REFERENCES [dbo].[Almacen]([Cod_Almacen]),
    CONSTRAINT [FK_VehiculoCliente_EcargoFuncion]
        FOREIGN KEY ([Id_Agente_Asignado]) REFERENCES [dbo].[Ecargos_funciones]([Id_CargoFuncion])
);
```

**Notas:**
- `Principal`: 1 = punto de entrega principal
- `Id_Agente_Asignado` FK a Ecargos_funciones (no a Persona_Nuevo directamente)
- `RowVersion`: timestamp automático para concurrencia
- No se encontró CHECK constraint para VentanaHorario (formato HH:MM-HH:MM)
- Falta FK a Ruta (Id_RutaAsignada) y DatosBancarios (Id_DatoBancario) en constraints documentados

---

## Tabla: Cliente_Sucursal

```sql
CREATE TABLE [dbo].[Cliente_Sucursal] (
    [Id_Cliente]         [int] NOT NULL,
    [Id_Sucursal]        [int] NOT NULL,
    [Fecha_Creacion]     [datetime] NOT NULL,
    [Creado_Por]         [nvarchar](50) NULL,
    [Fecha_Modificacion] [datetime] NULL,
    [Modificado_Por]     [nvarchar](50) NULL,
    CONSTRAINT [PK_Cliente_Sucursal] PRIMARY KEY CLUSTERED ([Id_Cliente], [Id_Sucursal]),
    CONSTRAINT [FK_Cliente_Sucursal_Vehiculo]
        FOREIGN KEY ([Id_Cliente]) REFERENCES [dbo].[Vehiculo_cliente_nuevo]([Codigo]),
    CONSTRAINT [FK_Cliente_Sucursal_Almacen]
        FOREIGN KEY ([Id_Sucursal]) REFERENCES [dbo].[Almacen]([Cod_Almacen])
);
```

**Nota:** La FK `Id_Cliente` apunta a `Vehiculo_cliente_nuevo` (no a Persona_Nuevo). Esto significa que la relación cliente-sucursal se resuelve a través del punto de entrega.

---

## Tabla: Cliente_Sucursal_Auditoria

```sql
CREATE TABLE [dbo].[Cliente_Sucursal_Auditoria] (
    [Id_Cliente]  [int] NOT NULL,
    [Id_Sucursal] [int] NOT NULL,
    [Accion]      [nvarchar](50) NOT NULL,
    [Fecha]       [datetime] NOT NULL,
    [Usuario]     [nvarchar](50) NOT NULL
);
```

**Nota:** No aparece en `01_tablas.txt`. Reconstruida desde SPs que insertan en ella. La auditoría se maneja vía SPs (`EliminarClienteSucursal`, `InsertarClienteSucursal`, `ActualizarClienteSucursal`), NO vía triggers.

---

## Tabla: Formas_pago (Catálogo)

```sql
CREATE TABLE [dbo].[Formas_pago] (
    [Id_FormaPago]          [int] IDENTITY(1,1) NOT NULL,
    [Descripcion]           [nvarchar](50) NOT NULL,
    [TipoOperacion]         [nvarchar](20) NOT NULL,
    [RequiereAutorizacion]  [bit] NOT NULL,
    [PlazoPago]             [int] NOT NULL,
    [Activo]                [bit] NOT NULL,
    CONSTRAINT [PK__Formas_p__4FF4E53B339188D9] PRIMARY KEY CLUSTERED ([Id_FormaPago]),
    CONSTRAINT [CK__Formas_pa__TipoO__265D20EE]
        CHECK ([TipoOperacion] IN (N'CONTADO', N'CREDITO', N'TARJETA', N'TRANSFERENCIA'))
);

-- Registros del catálogo
INSERT INTO [dbo].[Formas_pago] ([Id_FormaPago], [Descripcion], [TipoOperacion], [RequiereAutorizacion], [PlazoPago], [Activo])
VALUES
    (1, N'Contado',             N'CONTADO',       0, 0,  1),
    (2, N'Crédito 15 días',     N'CREDITO',       0, 15, 1),
    (3, N'Crédito 30 días',     N'CREDITO',       0, 30, 1),
    (4, N'Crédito 60 días',     N'CREDITO',       0, 60, 1),
    (5, N'Tarjeta',             N'TARJETA',       1, 0,  1),
    (6, N'Transferencia',       N'TRANSFERENCIA', 0, 0,  1);
```

---

## Tabla: EClaves_operacion (Solo España/EU)

```sql
CREATE TABLE [dbo].[Eclaves_operacion] (
    [id_clave]                  [int] IDENTITY(1,1) NOT NULL,
    [codigo_clave]              [varchar](10) NOT NULL,
    [descripcion]               [text] NOT NULL,
    [aplicable_a]               [varchar](50) NULL,
    [activo]                    [bit] NULL,
    [tipo_iva]                  [decimal] NULL,
    [tipo_operacion]            [nvarchar](50) NOT NULL,
    [regimen_iva]               [nvarchar](50) NOT NULL,
    [requiere_nif_iva]          [bit] NOT NULL,
    [afecta_intracomunitario]   [bit] NOT NULL,
    [afecta_exportacion]        [bit] NOT NULL,
    CONSTRAINT [PK_Eclaves_operacion] PRIMARY KEY CLUSTERED ([id_clave]),
    CONSTRAINT [chk_regimen_iva]
        CHECK ([regimen_iva] IN (N'GENERAL', N'EXENTO', N'INTRACOMUNITARIO', N'EXPORTACION'))
);
```

---

## Tabla: Telefonos

```sql
CREATE TABLE [dbo].[Telefonos] (
    [Id_Telefono]     [int] IDENTITY(1,1) NOT NULL,
    [Cod_Persona]     [int] NOT NULL,
    [Cod_CargoFuncion][int] NULL,
    [Telefono]        [nvarchar](50) NOT NULL,
    [Tipo]            [nvarchar](20) NULL,
    [Activo]          [bit] NOT NULL,
    CONSTRAINT [PK__Telefono__3F7477302860DBA1] PRIMARY KEY CLUSTERED ([Id_Telefono]),
    CONSTRAINT [FK_Telefonos_PersonaNuevo]
        FOREIGN KEY ([Cod_Persona]) REFERENCES [dbo].[Persona_Nuevo]([Cod_Persona])
);
```

---

## Tabla: Correos

```sql
CREATE TABLE [dbo].[Correos] (
    [Id_Correo]        [int] IDENTITY(1,1) NOT NULL,
    [Cod_Persona]      [int] NOT NULL,
    [Cod_CargoFuncion] [int] NULL,
    [Correo]           [nvarchar](100) NOT NULL,
    [Tipo]             [nvarchar](50) NULL,
    [Activo]           [bit] NOT NULL,
    [Fecha_Asignacion] [date] NOT NULL,
    [Fecha_Inactivo]   [date] NULL,
    CONSTRAINT [PK__Correos__585FE9D262443DB2] PRIMARY KEY CLUSTERED ([Id_Correo]),
    CONSTRAINT [FK_Correos_PersonaNuevo]
        FOREIGN KEY ([Cod_Persona]) REFERENCES [dbo].[Persona_Nuevo]([Cod_Persona])
);
```

---

## Tabla: Creditos

```sql
CREATE TABLE [dbo].[Creditos] (
    [Id_Credito]       [int] IDENTITY(1,1) NOT NULL,
    [Cod_VehiculoCliente] [int] NOT NULL,  -- En realidad almacena Cod_Persona
    [Linea_Credito]    [decimal] NOT NULL,
    [Dias_Credito]     [int] NOT NULL,
    [Fecha_Registro]   [date] NOT NULL,
    [Activo]           [bit] NOT NULL,
    CONSTRAINT [PK__Creditos__9AA34D3F9777B486] PRIMARY KEY CLUSTERED ([Id_Credito]),
    CONSTRAINT [FK_CREDITOS_Persona]
        FOREIGN KEY ([Cod_VehiculoCliente]) REFERENCES [dbo].[Persona_Nuevo]([Cod_Persona])
);
```

**Nota:** `Cod_VehiculoCliente` es un nombre legacy engañoso. La FK apunta a `Persona_Nuevo`, no a `Vehiculo_cliente_nuevo`. Almacena el `Cod_Persona` del cliente.

---

## Tabla: Direcciones_NoClientes

```sql
CREATE TABLE [dbo].[Direcciones_NoClientes] (
    [Id_Direccion]      [int] IDENTITY(1,1) NOT NULL,
    [Cod_Persona]       [int] NOT NULL,
    [Direccion_Linea_1] [nvarchar](200) NOT NULL,
    [Direccion_Linea_2] [nvarchar](200) NULL,
    [Id_Zona]           [int] NULL,
    [Codigo_Postal]     [nvarchar](10) NULL,
    [Enlace_GPS]        [nvarchar](200) NULL,
    [Tipo_Direccion]    [nvarchar](50) NOT NULL,
    [Activo]            [bit] NOT NULL,
    [Fecha_Registro]    [date] NOT NULL,
    CONSTRAINT [PK__Direccio__535FD61152ABA889] PRIMARY KEY CLUSTERED ([Id_Direccion]),
    CONSTRAINT [FK__Direccion__Cod_P__60F3D6D7]
        FOREIGN KEY ([Cod_Persona]) REFERENCES [dbo].[Persona_Nuevo]([Cod_Persona]),
    CONSTRAINT [FK__Direccion__Id_Zo__61E7FB10]
        FOREIGN KEY ([Id_Zona]) REFERENCES [dbo].[ZONA]([Cod_Zona])
);
```

---

## Tabla: Tarifa_cliente

```sql
CREATE TABLE [dbo].[Tarifa_cliente] (
    [ID]                  [int] IDENTITY(1,1) NOT NULL,
    [codcliente]          [int] NULL,
    [codproducto]         [int] NULL,
    [precio]              [money] NULL,
    [PrecioBase]          [money] NULL,
    [PorcentajeDescuento] [money] NULL,
    [PrecioFinal]         [money] NULL,
    [FechaCotizacion]     [datetime] NULL,
    [CodDetalleMov]       [int] NULL,
    [FechaInicio]         [datetime] NULL,
    CONSTRAINT [PK_Tarifa_Cliente] PRIMARY KEY CLUSTERED ([ID]),
    CONSTRAINT [FK_TarifaCliente_Persona]
        FOREIGN KEY ([codcliente]) REFERENCES [dbo].[Persona_Nuevo]([Cod_Persona]),
    CONSTRAINT [FK_Producto]
        FOREIGN KEY ([codproducto]) REFERENCES [dbo].[Producto]([cod_producto])
);
```

---

## Resumen de documentación faltante en BD

| Elemento | Estado |
|----------|--------|
| Triggers en Persona_Nuevo | **NO documentados** (no existen en archivos) |
| Triggers en Cliente_Sucursal | **NO existen** (auditoría vía SPs) |
| Índices no-clusterizados (DNI, RUC, Nom_Persona, Login_Persona) | **NO documentados** |
| CHECK constraint Cod_TipoPersona IN (1,2,3,4,5) | **NO documentado** |
| CHECK VentanaHorario formato HH:MM-HH:MM | **NO documentado** |
| FK Id_RutaAsignada → Ruta | **NO documentada** |
| FK Id_DatoBancario → DatosBancarios | **NO documentada** |
| Cliente_Sucursal_Auditoria | **NO listada** en inventario de tablas |
