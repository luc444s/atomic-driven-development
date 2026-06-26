# HITO 3 — Arquitectura Interna: Patrones de Forms, CAtencion y Módulos

---

## 1. Librería CAtencion (Core Compartido)

**Ubicación:** `Libreria_GMS PRO_2.0/CAtencion/` — **55 clases** (54 entidad + ClsConexion)

Es la capa de acceso a datos y lógica de negocio. Cada clase representa una entidad y expone métodos que internamente ejecutan SPs.

**Total métodos extraídos: ~1,300** en 54 archivos `ca_*_methods.txt`

### Clases principales por cantidad de métodos

| Clase | Métodos | Propósito |
|---|---|---|
| `CMovimiento` | 136 | Movimientos de almacén (ventas, compras, guías, traslados) |
| `CComprobante` | 128 | Documentos de venta (facturas, boletas, N/C, N/D) |
| `CProducto` | 109 | Productos (búsqueda por nombre, serie, código) |
| `CPaciente` | 108 | Clientes/personas (visitas, reparto, historial) |
| `Cgas` | 96 | GLP — envases, cilindros, válvulas, retimbrado |
| `CSucursal` | 38 | Sucursales/almacenes + menú dinámico |
| `cHORARIOS` | 35 | Horarios de visitas y reparto |
| `CFiscal` | 32 | Datos fiscales, impuestos |
| `CPersonaPro` | 27 | Personas PRO (avanzado) |
| `CFamilia` | 24 | Familias de productos (jerárquico) |
| `CConfiguracion` | 21 | Configuración del sistema y regional |
| `CTarifario` | 15 | Tarifas y precios |
| `CDetalleMovimiento` | 12 | Detalle de líneas de movimiento |
| `Cdescuento` | 12 | Descuentos y promociones |
| `CMenu` | 10 | Menú dinámico MDI |
| `CZona` | 10 | Zonas geográficas |
| `CUsuario` | 9 | Usuarios y permisos |
| `CAseguradora` | 9 | Aseguradoras |
| `CDistrito` / `CDepartamento` / `CProvincia` | 8-9 | Ubicación geográfica (3 niveles) |
| `CsubLinea` | 9 | Sub-líneas de productos |
| `CAnalisisEmpresa` | 8 | Análisis de empresas |
| `CTipoInsumo` | 8 | Tipos de insumo |
| `CEspecialidad` / `CMedico` / `CCargo` | 7 | Catálogos médicos/admin |
| `CSubcategoria` / `CUbicacion` / `CLinea` | 7 | Catálogos de producto |
| `CTipochequeo` / `CTipoDscto` | 7 | Catálogos de proceso |
| `CEmpresa` | 6 | Empresas |
| `CEstadoProducto` / `Cserie` / `CtIPOdOC` | 6 | Catálogos menores |
| `CContab` | 6 | Contabilidad |
| `CConversion` | 6 | Conversión de unidades |
| `CMarca` / `CGrupo` / `Cunidad` | 6 | Catálogos de producto |
| `CReceta` | 6 | Recetas/moldes |
| `Cbarcode` | 3 | Códigos de barras |
| `CConstante` | 3 | Constantes del sistema |
| Resto (14 clases) | 4-5 c/u | Catálogos menores (Agenda, Copia, Donante, etc.) |

### Patrón interno de cada clase

```vb.net
Public Class CProducto
    Private objcn As SqlConnection

    Public Sub Conectar()
        objcn = New SqlConnection(CAtencion.ClsConexion.ConnectionString)
        objcn.Open()
    End Sub

    Public Sub DesConnectar()
        If objcn IsNot Nothing AndAlso objcn.State = ConnectionState.Open Then
            objcn.Close()
        End If
    End Sub

    Public Function BuscarxNom(ByVal nombre As String) As SqlDataReader
        Conectar()
        Dim cmd As New SqlCommand("sp_Producto_BuscarxNom", objcn)
        cmd.CommandType = CommandType.StoredProcedure
        cmd.Parameters.AddWithValue("@nombre", nombre)
        Return cmd.ExecuteReader()
    End Function
End Class
```

**Características:**
- Cada método abre y deja la conexión abierta (el llamador debe cerrar con `DesConnectar()`)
- Devuelven `SqlDataReader` casi siempre
- No usan `Using` ni transacciones — el form gestiona el ciclo de vida

### Cómo se usa desde un form

```vb.net
Dim WithEvents objc As New CAtencion.CComprobante
Dim Dr As SqlClient.SqlDataReader
Dr = objc.mostrarmonedas(sucursalId, usuarioId)
If Dr.Read Then
    ' procesar
End If
objc.DesConnectar()
```

---

## 2. Módulos Globales

| Módulo | Propósito | Contenido |
|---|---|---|
| `Modulo.vb` | Objetos compartidos + utilidades | Instancias globales de forms (`objUsuario`, `objregcli`, etc.) + funciones `BuscarElemento`, `ValidacionTexto`, `ValidacionNumero` |
| `modReportes.vb` | Helper de reportes | `AplicarConexionReporte()` — conecta Crystal Reports a la BD |
| `modFacturacion_*.vb` (7 módulos) | Lógica de facturación | `modFacturacion_Cilindros`, `_Comprobantes`, `_Despacho`, `_Pedidos`, `_Validaciones`, `_Movimientos` |
| `modQR.vb` | Generación de QR | Códigos QR para facturación electrónica |
| `ModToken.vb` | Tokens de API | Tokens para Nubefact/SUNAT |
| `ModPlanificacionUtils.vb` | Utilidades de planificación | Helper para operaciones logísticas |
| `modArchivos.vb` | Archivos | Manejo de archivos del sistema |
| `modCartaPorteReflection.vb` | Carta Porte | Reflection para documentos de transporte |
| `ModFact_UtilNumeros.vb` | Números | Conversión a letras, formateo |

### Módulos exportados como clase

| Clase | Propósito |
|---|---|
| `ClsContexto` | Contexto global: `PaisActivo` |
| `ClsContextoRegional` | Configuración regional: moneda, impuesto, símbolos, formato |
| `ClsConfiguracion` | Lectura de parámetros desde BD (`ObtenerPaisActivo`, `ObtenerNombreDocumentoPersonal`) |
| `ClsFunciones` | Helper: `fnMostrarDetalleOrden()` |
| `ClsValidaciones` | Validación de documentos: DNI Perú, RUC Perú, DNI España, NIF, RUT Chile, cédulas CR, DIMEX, NITE |
| `ClsFacturacionElectronica` | Dispatcher: `EnviarFactura(codComprobante)` según país (CR o PE) |
| `ClsReportes` | Helper de conexión a Crystal Reports |

---

## 3. Patrón de Forms — 3 representantes

### A) Catálogo simple (FrmCatClientes)

```vb.net
Public Class FrmCatClientes
    Private objcn As SqlConnection
    
    Private Sub Conectar() / Desconectar()  ' siempre igual
    
    ' Carga de combos en Load
    Private Sub FrmCatClientes_Load() Handles MyBase.Load
        ' llena combos desde SPs Buscar_* / Mostrar_*
    End Sub
    
    ' CRUD
    Private Sub BtnNuevo_Click()   ' limpia campos
    Private Sub BtnGuardar_Click() ' valida → INSERT o UPDATE vía SP
    Private Sub BtnEliminar_Click() ' DELETE vía SP
    Private Sub BtnBuscar_Click()  ' abre FBus* o ejecuta SP Buscar_*
    
    ' Navegación
    Private Sub BtnPrimero_Click() / BtnAnterior_Click() / etc.
End Class
```

### B) Transacción compleja (FrmMovFacturacion)

```vb.net
Public Class FrmMovFacturacion
    ' Multiples objetos CAtencion (WithEvents)
    Dim WithEvents objc As New CAtencion.CComprobante
    Dim WithEvents objM As New CAtencion.CMovimiento
    Dim WithEvents objI As New CAtencion.CProducto
    ' ... hasta 20 objetos de CAtencion
    
    ' Variables de estado
    Private codMovimiento As String
    Private codMovimientoGUIA As String
    Private codMovimientoFACTURA As String
    Private Structure TotalesDocumento
        Public SubTotal, DescuentoTotal, Impuesto, TotalFinal As Double
    End Structure
    
    ' Conexión manual
    Private Sub Conectar() / Desconectar()
    
    ' Flujo principal:
    ' 1. Seleccionar cliente → objP.Buscar()
    ' 2. Agregar items → objI.BuscarxNom() + objM.InsertarDetalle()
    ' 3. Calcular totales → TotalesDocumento
    ' 4. Generar comprobante → INSERT en tabla comprobantes
    ' 5. Enviar a SUNAT/CR → ClsFacturacionElectronica.EnviarFactura()
    ' 6. Imprimir → Crystal Reports con AplicarConexionReporte()
End Class
```

### C) Visor de reportes (FrmReportes)

```vb.net
Public Class FrmReportes
    Public FormulaSeleccion As String = ""
    
    Public Sub MostrarReporte(ByVal reporte As ReportDocument)
        CrystalReportViewer1.ReportSource = Nothing
        reporte.Refresh()
        If Trim(FormulaSeleccion) <> "" Then
            reporte.RecordSelectionFormula = FormulaSeleccion
            CrystalReportViewer1.SelectionFormula = FormulaSeleccion
        End If
        CrystalReportViewer1.ReportSource = reporte
        CrystalReportViewer1.Zoom(100)
        CrystalReportViewer1.RefreshReport()
    End Sub
End Class
```

---

## 4. Infraestructura de Reportes Crystal

Hay **~50 reportes Crystal** (`.rpt`) en la carpeta `Reportes/`.

### Patrón de conexión

```vb.net
' Desde MDIMenu (antiguo):
Dim settings As ConnectionStringSettingsCollection = ConfigurationManager.ConnectionStrings
For Each tbCurrent In objM.Database.Tables
    Dim tliCurrent = tbCurrent.LogOnInfo
    With tliCurrent.ConnectionInfo
        .ServerName = ConfigurationManager.AppSettings.Get("servername")
        .UserID = "sa"
        .Password = ConfigurationManager.AppSettings.Get("password")
        .DatabaseName = ConfigurationManager.AppSettings.Get("database")
    End With
    tbCurrent.ApplyLogOnInfo(tliCurrent)
Next

' Desde modReportes (nuevo):
Public Sub AplicarConexionReporte(ByVal reporte As ReportDocument)
    Dim builder As New SqlConnectionStringBuilder(CAtencion.ClsConexion.ConnectionString)
    For Each tb In reporte.Database.Tables
        Dim tliCurrent = tb.LogOnInfo
        With tliCurrent.ConnectionInfo
            .ServerName = builder.DataSource
            .DatabaseName = builder.InitialCatalog
            .UserID = builder.UserID
            .Password = builder.Password
        End With
        tb.ApplyLogOnInfo(tliCurrent)
    Next
End Sub
```

---

## 5. Resumen de patrones para modificar forms

| Concepto | Cómo se hace hoy |
|---|---|
| **Conexión a BD** | `New SqlConnection(ClsConexion.ConnectionString)` manual en cada form |
| **Leer datos** | `CAtencion.CX.Entidad_Metodo()` → `SqlDataReader` |
| **Escribir datos** | SP directo desde el form (no hay capa de servicio) |
| **Validación** | `ClsValidaciones.ValidarDocumento()` + validación inline en cada form |
| **Reportes** | Crear instancia del `.rpt` → `AplicarConexionReporte()` → `FrmReportes.MostrarReporte()` |
| **Fact. Electrónica** | `ClsFacturacionElectronica.EnviarFactura(codComprobante)` |
| **Contexto regional** | `ClsContextoRegional.Pais`, `.Moneda`, `.TasaImpuesto` — variables Shared |
| **Menú** | Dinámico desde BD (`CMenu.ListarMenuPrincipal` + TreeView) |

### Archivos generados (54 archivos de métodos + 1 de módulos)

| Archivo | Clase | Métodos |
|---|---|---|
| `ca_CMovimiento_methods.txt` | CMovimiento | 136 |
| `ca_CComprobante_methods.txt` | CComprobante | 128 |
| `ca_CProducto_methods.txt` | CProducto | 109 |
| `ca_CPaciente_methods.txt` | CPaciente | 108 |
| `ca_Cgas_methods.txt` | Cgas | 96 |
| `ca_CSucursal_methods.txt` | CSucursal | 38 |
| `ca_cHORARIOS_methods.txt` | cHORARIOS | 35 |
| `ca_CFiscal_methods.txt` | CFiscal | 32 |
| `ca_CPersonaPro_methods.txt` | CPersonaPro | 27 |
| `ca_CFamilia_methods.txt` | CFamilia | 24 |
| `ca_CConfiguracion_methods.txt` | CConfiguracion | 21 |
| `ca_CTarifario_methods.txt` | CTarifario | 15 |
| `ca_CDetalleMovimiento_methods.txt` | CDetalleMovimiento | 12 |
| `ca_Cdescuento_methods.txt` | Cdescuento | 12 |
| `ca_CMenu_methods.txt` | CMenu | 10 |
| `ca_CZona_methods.txt` | CZona | 10 |
| `ca_CUsuario_methods.txt` | CUsuario | 9 |
| `ca_CAseguradora_methods.txt` | CAseguradora | 9 |
| `ca_CsubLinea_methods.txt` | CsubLinea | 9 |
| `ca_CDistrito_methods.txt` | CDistrito | 9 |
| `ca_CDepartamento_methods.txt` | CDepartamento | 8 |
| `ca_CProvincia_methods.txt` | CProvincia | 8 |
| `ca_CAnalisisEmpresa_methods.txt` | CAnalisisEmpresa | 8 |
| `ca_CTipoInsumo_methods.txt` | CTipoInsumo | 8 |
| `ca_CSubcategoria_methods.txt` | CSubcategoria | 7 |
| `ca_CUbicacion_methods.txt` | CUbicacion | 7 |
| `ca_CLinea_methods.txt` | CLinea | 7 |
| `ca_CEspecialidad_methods.txt` | CEspecialidad | 7 |
| `ca_CCargo_methods.txt` | CCargo | 7 |
| `ca_CMedico_methods.txt` | CMedico | 7 |
| `ca_CTipochequeo_methods.txt` | CTipochequeo | 7 |
| `ca_CTipoDscto_methods.txt` | CTipoDscto | 7 |
| `ca_CEmpresa_methods.txt` | CEmpresa | 6 |
| `ca_CEstadoProducto_methods.txt` | CEstadoProducto | 6 |
| `ca_Cserie_methods.txt` | Cserie | 6 |
| `ca_CtIPOdOC_methods.txt` | CtIPOdOC | 6 |
| `ca_CContab_methods.txt` | CContab | 6 |
| `ca_CConversion_methods.txt` | CConversion | 6 |
| `ca_CMarca_methods.txt` | CMarca | 6 |
| `ca_CGrupo_methods.txt` | CGrupo | 6 |
| `ca_Cunidad_methods.txt` | Cunidad | 6 |
| `ca_CReceta_methods.txt` | CReceta | 6 |
| `ca_CtipoCambio_methods.txt` | CtipoCambio | 5 |
| `ca_CAgenda_methods.txt` | CAgenda | 5 |
| `ca_CTipoA_methods.txt` | CTipoA | 5 |
| `ca_CDonante_methods.txt` | CDonante | 5 |
| `ca_CDetLibro_methods.txt` | CDetLibro | 5 |
| `ca_CLibroReg_methods.txt` | CLibroReg | 5 |
| `ca_CTcontado_methods.txt` | CTcontado | 5 |
| `ca_CPaquete_methods.txt` | CPaquete | 5 |
| `ca_CCopia_methods.txt` | CCopia | 4 |
| `ca_CDEdad_methods.txt` | CDEdad | 4 |
| `ca_Cbarcode_methods.txt` | Cbarcode | 3 |
| `ca_CConstante_methods.txt` | CConstante | 3 |
| `modulos_globales_lista.txt` | Módulos globales .vb | — |
