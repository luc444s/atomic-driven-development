# Estado Actual del Proyecto — ERP-SYSTUTOR

**Fecha:** 26/06/2026
**Propósito:** Documentar el estado actual del legacy antes de iniciar la migración a arquitectura limpia en los módulos de trazabilidad.

---

## 1. Stack Tecnológico

| Componente | Versión |
|---|---|
| Lenguaje | VB.NET WinForms |
| Framework (ERP-SYSTUTOR) | .NET Framework 4.7.2 |
| Framework (CAtencion) | .NET Framework 4.0 |
| Motor BD | SQL Server 2014 Enterprise (64-bit) |
| Base de datos | `Sys_GMS_ESCR` |
| Reportes | Crystal Reports (~50 reportes .rpt) |
| IDE | Visual Studio 2019 (v16.0) |
| Solución | `ERP-SYSTUTOR.sln` (2 proyectos) |

## 2. Dimensiones del Sistema

| Elemento | Cantidad |
|---|---|
| Forms activos | ~110 (de 218 archivos .Designer.vb) |
| Clases CAtencion | 55 clases (~1.300 métodos) |
| Tablas | 184 |
| Vistas | 144 |
| Stored Procedures | 944 |
| Funciones | 22 |
| Constraints | 265 |

## 3. Estructura del Proyecto

```
ERP-SYSTUTOR.sln
├── ERP-SYSTUTOR.vbproj     → WinForms ( .NET 4.7.2 )
└── CAtencion.vbproj         → Librería de acceso a datos ( .NET 4.0 )
     └── CAtencion/          → 55 clases entity + ClsConexion
```

La solución tiene 2 proyectos con **diferentes versiones de .NET Framework**, lo que limita lo que puede usar CAtencion.

## 4. Arquitectura Actual

```
MDIMenu.vb (MDI Principal)
├── TreeView dinámico desde BD (CMenu.ListarMenuPrincipal)
│   └── trv_DoubleClick → apertura de forms por texto del nodo
│
├── Forms → CAtencion (clases) → Stored Procedures → SQL Server
│
├── Crystal Reports → SPs directos
│
└── Módulos globales (Modulo.vb, modReportes.vb, modFacturacion_*.vb, etc.)
```

### Patrón típico de un form:

```vb.net
' 1. Conectar
Dim WithEvents objc As New CAtencion.CComprobante
Dim Dr As SqlClient.SqlDataReader

' 2. Leer
Dr = objc.mostrarmonedas(sucursalId, usuarioId)
If Dr.Read Then
    ' procesar
End If

' 3. Cerrar
objc.DesConnectar()
```

### Patrón de cada clase CAtencion:

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
        Return cmd.ExecuteReader()  ' ← DataReader abierto
    End Function
End Class
```

**Problemas conocidos:**
- Cada método abre la conexión y la deja abierta (el llamador debe cerrar)
- Devuelven `SqlDataReader` casi siempre
- No usan `Using` ni transacciones
- El form gestiona el ciclo de vida manualmente

## 5. Módulos Globales

| Módulo | Propósito |
|---|---|
| `Modulo.vb` | Objetos compartidos + utilidades |
| `modReportes.vb` | Helper de conexión Crystal Reports |
| `modFacturacion_*.vb` (7) | Lógica de facturación por áreas |
| `modQR.vb` | Generación de QR |
| `ModToken.vb` | Tokens para Nubefact/SUNAT |
| `ModPlanificacionUtils.vb` | Utilidades de planificación |
| `ClsValidaciones.vb` | Validación de documentos (DNI, RUC, NIF, RUT, etc.) |
| `ClsFacturacionElectronica.vb` | Dispatcher de envío SUNAT/CR |

## 6. Clases CAtencion — Las 5 más grandes

| Clase | Métodos | Propósito |
|---|---|---|
| `CMovimiento` | 136 | Movimientos de almacén |
| `CComprobante` | 128 | Documentos de venta |
| `CProducto` | 109 | Productos |
| `CPaciente` | 108 | Clientes/personas |
| `Cgas` | 96 | GLP — envases, cilindros, retimbrado |

## 7. Categorías de Forms

| Categoría | Forms |
|---|---|
| Catálogos Maestros | 18 |
| Facturación / Ventas | 16 |
| Compras / Proveedores | 8 |
| Cilindros / Bombonas / Envases | 14 |
| Planificación / Logística / Reparto | 11 |
| Caja / Finanzas | 12 |
| Reportes | 22 |
| Administración / Configuración | 12 |
| Forms de Búsqueda (FBus*) | ~20 |
| Forms Auxiliares | 10 |
| Módulos Específicos | ~15 |
