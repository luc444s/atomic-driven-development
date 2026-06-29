# Módulo Clientes — Clases VB Adicionales

## 1. CContab.vb — UPDATE directo a Persona_Nuevo (RIESGO CONFIRMADO)

**Archivo:** `Libreria_GMS PRO_2.0\CAtencion\CContab.vb` (160 líneas, 6 métodos)

### Método Peligroso

```vb
Public Function Actualizar_FormaPago(ByVal codPersona As String, ByVal idFormaPago As Integer) As Integer
    Dim objCommand As New SqlClient.SqlCommand
    Try
        Conectar()
        objCommand.Connection = objcn
        objCommand.CommandText = "UPDATE Persona_Nuevo SET Id_FormaPago = @IdFormaPago WHERE Cod_Persona = @CodPersona"
        objCommand.Parameters.AddWithValue("@IdFormaPago", idFormaPago)
        objCommand.Parameters.AddWithValue("@CodPersona", codPersona)
        Dim filasAfectadas As Integer = objCommand.ExecuteNonQuery()
        Return filasAfectadas
    Catch ex As Exception
        RaiseEvent onError("Error al actualizar forma de pago: " & ex.Message)
        Return 0
    Finally
        objCommand.Dispose()
        DesConnectar()
    End Try
End Function
```

**Riesgo:** UPDATE directo a Persona_Nuevo sin stored procedure, sin transacción, sin logging.

### Otros métodos (seguros)
| Método | SP usado |
|--------|----------|
| `Buscar_ClavesVentaEspaña` | `Buscar_Claves` |
| `Buscar_ClavesIC` | `Buscar_ClavesIC` |
| `Buscar_FormasPago` | `Buscar_FormasPago` |

---

## 2. CPersonaPro.vb — Contratos y Dirección

**Archivo:** `Libreria_GMS PRO_2.0\CAtencion\CPersonaPro.vb` (412 líneas, 12 métodos)

### Métodos

| Método | SP o SQL | Tipo |
|--------|----------|------|
| `contrato_Insertar` | `CONTRATO_Registrar` | SP ✅ |
| `contrato_historial_insertar` | `CONTRATO_HISTORIAL_Insertar` | SP ✅ |
| `contrato_modificar` | `UPDATE Contratos SET ...` (inline) + `SELECT ...` previo (concatenado) | **SQL INLINE** ⚠️ |
| `contratos_activos_por_cliente` | `SELECT * FROM Contratos WHERE ... & codigo` | **SQL INLINE (concatenación)** 🔴 |
| `contrato_anular` | `UPDATE Contratos SET Estado='ANULADO' ...` | **SQL INLINE** ⚠️ |
| `contrato_cambiar_archivo` | `UPDATE Contrato SET Ruta...` + `INSERT INTO Contrato_Historial` | **SQL INLINE** ⚠️ |
| `ActualizarDireccionFiscal` | `sp_Direccion_Fiscal_Actualizar` | SP ✅ |
| `ActualizarEnvioEstablecimiento` | `sp_Establecimiento_ActualizarEnvio` | SP ✅ |
| `ObtenerPuntoEntregaCompleto` | `dbo.ObtenerPuntoEntregaCompleto` | SP ✅ |
| `ObtenerActividadParaFactura` | `SELECT CodigoActividadPrincipal FROM Persona_Nuevo WHERE ...` | SQL INLINE ⚠️ |

### Riesgos
- `contratos_activos_por_cliente`: usa concatenación directa de `Cod_Cliente` — **vulnerable a SQL injection**
- `contrato_modificar`: misma concatenación en SELECT previo
- 5 de 12 métodos usan SQL inline

---

## 3. CFiscal.vb — Validación con Hacienda CR

**Archivo:** `Libreria_GMS PRO_2.0\CAtencion\CFiscal.vb` (335 líneas)

### APIs externas
```vb
' Hacienda Costa Rica (producción)
Dim url As String = "https://api.hacienda.go.cr/fe/ae?identificacion=" & identificacion
' Usa WebClient con TLS 1.2, UserAgent, Accept: application/json
' Guarda respuesta en C:\temp\hacienda.json
' Parsea JSON para extraer actividad principal (tipo="P")
```

### Lógica por país
- **CR:** Llama a `api.hacienda.go.cr`, guarda JSON, parsea con Regex, guarda con `sp_Persona_ActividadFiscal_Guardar`
- **ES:** Placeholder vacío (no implementado)
- **PE:** No implementado en esta clase

---

## 4. ClsValidaciones.vb — Algoritmos de Validación Fiscal

**Archivo:** `ClsValidaciones.vb` (370 líneas)

### Dispatcher
```vb
Public Shared Function ValidarDocumento(documento, tipoValidacion, nombreDocumento, mascara, ByRef mensajeError) As Boolean
    ' Según tipoValidacion, llama al método específico
```

### Algoritmos por País

| Tipo | Método | Algoritmo |
|------|--------|-----------|
| DNI España | `ValidarDniEspaña` | **Módulo 23**: letras "TRWAGMYFPDXBNJZSQVHLCKE", resto = número Mod 23 |
| NIE España | `ValidarDniEspaña` | Mismo módulo 23, prefijos X→0, Y→1, Z→2 |
| Chile RUT | `ValidarRutChile` | **Módulo 11**: factores 2-7 cíclicos. Resto 11→0, resto 10→K |
| Cédula Física CR | `ValidarCedulaFisicaCR` | 9 dígitos, provincia 1-7 |
| Cédula Jurídica CR | `ValidarCedulaJuridicaCR` | 10 dígitos |
| DIMEX CR | `ValidarDimexCR` | 11-12 dígitos |
| NITE CR | `ValidarNiteCR` | 10 dígitos |
| DNI Perú | `ValidarDniPeru` | 8 dígitos exactos |
| RUC Perú | `ValidarRucPeru` | **Módulo 11**: factores {5,4,3,2,7,6,5,4,3,2}. Resto 10→0, resto 11→1 |

### Algoritmo RUC Perú (código exacto)
```vb
Private Shared Function ValidarRucPeru(ruc As String) As Boolean
    ruc = SoloDigitos(ruc)
    If ruc.Length <> 11 Then Return False
    Dim factores() As Integer = {5, 4, 3, 2, 7, 6, 5, 4, 3, 2}
    Dim suma As Integer = 0
    For i As Integer = 0 To 9
        suma += CInt(ruc(i).ToString()) * factores(i)
    Next
    Dim resto As Integer = 11 - (suma Mod 11)
    Dim dvEsperado As Integer
    If resto = 10 Then dvEsperado = 0
    ElseIf resto = 11 Then dvEsperado = 1
    Else dvEsperado = resto
    Return dvEsperado = CInt(ruc(10).ToString())
End Function
```

### Algoritmo DNI/NIE España (código exacto)
```vb
Private Shared Function ValidarDniEspaña(dni As String) As Boolean
    If dni.Length <> 9 Then Return False
    dni = dni.ToUpper()
    Dim letras As String = "TRWAGMYFPDXBNJZSQVHLCKE"
    Dim numero As Integer
    If Char.IsLetter(dni(0)) Then
        ' NIE: X→0, Y→1, Z→2
        Select Case dni(0)
            Case "X"c : numero = CInt("0" & dni.Substring(1, 7))
            Case "Y"c : numero = CInt("1" & dni.Substring(1, 7))
            Case "Z"c : numero = CInt("2" & dni.Substring(1, 7))
        End Select
    Else
        numero = CInt(dni.Substring(0, 8))
    End If
    Return dni(8) = letras(numero Mod 23)
End Function
```

### Helpers
```vb
Private Shared Function SoloDigitos(valor As String) As String
    ' Filtra solo dígitos numéricos
Private Shared Function LimpiarIBAN(valor As String) As String
    ' Quita espacios, guiones, puntos, pasa a mayúsculas
Public Shared Function ObtenerAyudaDocumento(tipoDoc, pais) As String
    ' Retorna texto de ayuda para cada tipo de documento
```

---

## 5. CDireccion.vb — Constructor de Dirección

**Archivo:** `CDireccion.vb` (168 líneas)

### Método principal
```vb
Public Shared Function ConstruirDireccionDesdeFormulario(
    ByVal CBComunidad As ComboBox, ByVal CBProvincia As ComboBox,
    ByVal CBMunicipio As ComboBox, ByVal CBLocalidad As ComboBox,
    ByVal TxtCalleNro As TextBox, ByVal TxtNumero As TextBox,
    ByVal TXTdirecLinea1 As TextBox, ByVal TXTdirecLinea2 As TextBox,
    ByVal TXTcpostal As TextBox, ByVal TxtObsDireccion As TextBox,
    ByVal lblUSUARIO As Label, ByVal idLocalidadSeleccionada As Integer
) As Dictionary(Of String, Object)
```

### Construye Dictionary con:
| Key | Fuente |
|-----|--------|
| `Country_Code` | `ClsContextoRegional.Pais` |
| `Admin_Area_1` | CBComunidad.Text |
| `Admin_Area_2` | CBProvincia.Text |
| `Id_Localidad` | `idLocalidadSeleccionada` o valor del ComboBox según país |
| `Street_Name` | TxtCalleNro |
| `Street_Number` | TxtNumero |
| `Linea1` | TXTdirecLinea1 |
| `Linea2` | TXTdirecLinea2 |
| `Codigo_Postal` | TXTcpostal |
| `Observaciones` | TxtObsDireccion |
| `DireccionLogistica` | `linea1 + " " + linea2` (sin observaciones) |
| `Capturado_Por` | lblUSUARIO.Text |
| `Capturado_En` | Date.Now |

### Helper
```vb
Private Shared Function GetIntValueCombo(ByVal cbo As ComboBox) As Integer
    ' Obtiene SelectedValue como Integer, retorna 0 si es Nothing
```

---

## Resumen de Riesgos en Clases VB

| Clase | Métodos | SQL Inline | SQL Injection | Bypass SP |
|-------|---------|-----------|-------------|-----------|
| CContab.vb | 6 | 1 | No | **SÍ** (`Actualizar_FormaPago`) |
| CPersonaPro.vb | 12 | **5** | **SÍ** (contratos_activos_por_cliente) | No |
| CFiscal.vb | 7 | 0 | No | No |
| ClsValidaciones.vb | 15 | 0 | No | No (solo lógica) |
| CDireccion.vb | 2 | 0 | No | No (solo construcción de datos) |
