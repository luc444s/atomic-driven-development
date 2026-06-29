# Módulo Clientes — Forms de Mantenimiento

## 1. FrmCatClientes.vb (818KB) — Formulario Principal Multi-País

### 1.1 Estructura General

```vb.net
Public Class FrmCatClientes
    ' Sin Inherits explícito (por defecto System.Windows.Forms.Form)
    ' ~180+ métodos entre Subs, Functions y manejadores de eventos
```

### 1.2 Variables Globales

```vb.net
Private objcn As SqlConnection
Private _bloqueoCascada As Boolean = False
Private bloqueandoEventosDireccion As Boolean = False
Private Shared ReadOnly ReCP5 As New Regex("\b(\d{5})\b", RegexOptions.Compiled)
Private _cpToRemove As String = Nothing
Private _IdRutaSeleccionada As Integer = 0
Private _NombreRutaSeleccionada As String = ""
Private _cargandoBancos As Boolean = False
Private cargandoCombo As Boolean = False
Private cargandoFormulario As Boolean = False
Private modoEdicionDireccion As Boolean = False
Private _huboCambiosDireccion As Boolean = False
Private _IdLocalidadSeleccionada As Integer = 0
Private _IdMunicipioSeleccionado As Integer = 0
Private _IdProvinciaSeleccionada As Integer = 0
Private _IdComunidadSeleccionada As Integer = 0
Private _Latitud As String = ""
Private _Longitud As String = ""
Private WithEvents timerMaps As New Timer
Private bloqueandoFormatoIBAN As Boolean = False
Private _idAgente As Integer = 0
Public AppPath As String = System.IO.Directory.GetCurrentDirectory()
Dim apiKey As String = ConfigurationManager.AppSettings("GoogleApiKey")
Public Cnx As New SqlConnection(ClsConexion.ConnectionString)
Public UsuarioEsAdmin As Boolean

' Objetos DAL
Dim WithEvents obju As New CAtencion.CZona
Dim WithEvents objzona As New CAtencion.CZona
Dim WithEvents objdist As New CAtencion.CDistrito
Dim WithEvents objprov As New CAtencion.CProvincia
Dim WithEvents objdpto As New CAtencion.CDepartamento
Dim WithEvents objP As New CAtencion.CPaciente
Dim WithEvents objcontab As New CAtencion.CContab
Dim WithEvents objg As New CAtencion.CSucursal
Dim myInfo As Persona
Dim WithEvents objComp As New CAtencion.CComprobante
Dim WithEvents obj As New CAtencion.CPaciente
Dim WithEvents objPRO As New CAtencion.CPersonaPro
```

### 1.3 Controles del Formulario

| Tipo | Nombres |
|------|---------|
| **TextBox** | `TxtCodPac`, `txtCliente`, `TxtNomPac`, `txtDni`, `TxtTel`, `txtemail`, `txtruc`, `txtdirEmpresa`, `TxtDocumento`, `TxtCalleNro`, `TxtNumero`, `TXTdirecLinea1`, `TXTdirecLinea2`, `TXTcpostal`, `TXTcontactoPE`, `TXTtelefonoPE`, `correoPE`, `txtLatitud`, `txtLongitud`, `txtLinkMaps`, `txtDirLogistica`, `TxtObsDireccion`, `TxtObsCoor`, `TXTNombrePunto`, `TxtActividadCodigo`, `TxtActividadDescripcion`, `TxtNomComercial`, `TXTobsCliente`, `TxtRutaPDF`, `txtIdRuta`, `txtNomRuta`, `txtCapcha`, `txtfoto`, `txtDireccion`, `txtubigeo`, `TxtBuscarMunicipio` |
| **ComboBox** | `cboTipoDocumento`, `CBPais`, `CBcomunidad`, `CBProvincia`, `CBMunicipio`, `CBLocalidad`, `CBDPTOD`, `CBOPROVINCIA`, `CBzona`, `CBAgente`, `CBclaveOP`, `CBclaveOPIC`, `CBFormaPago`, `CBtipoFac`, `CBnomBanco`, `CBcuentasCajaAdmin`, `cbsucursal`, `CBdelegacion`, `cmbNotificaciones`, `cbRuta`, `CBDocumentoPrincipal` |
| **Button** | `cmdnuevo`, `cmdBuscar`, `cmdmodificar`, `cmdgrabar`, `cmdcerrar`, `CmdAgregar`, `CmdModificaResp`, `BTNPuntoEntrega_Nuevo`, `BTNeditarDireccion`, `BTNCERRAR`, `btnPrincipal`, `BTNguardarCord`, `btnAbrirMaps`, `BtnCapturarAqui`, `btnLeerLink`, `BTNCrearDir`, `BTNguardarDir`, `BtnNuevaLocalidad`, `BTNactividadEco`, `BTNguardarActividad`, `BTNModificarDetalledir`, `BTNSistema`, `BTNguardaAgente`, `Button4`, `ActuRespon`, `btnGuardarDatos`, `btnGuardarCredito`, `BtnGuardarFiscales`, `BtnGuardarCuenta`, `BtnReactivarSeleccionada`, `BtnVerHistorico`, `btnNuevoContrato`, `btnModificarContrato`, `btnVerContrato`, `btnAnularContrato`, `btnRenovarContrato`, `btnBuscarPDF`, `BtnSugerirRuta`, `BtnAsignarRuta`, `BtnUpRuta`, `BtnDownRuta`, `btnCompactarRuta`, `btnBuscarSunat` |
| **CheckBox** | `CheckBox1`, `ChekRetencion`, `ChekNORetencion`, `ChekEnviar`, `CheckPrincipal`, `ChkRequiereAutorizacion`, `ChkBancoActivo`, `CHKClienteUE`, `chkFirmado` |
| **RadioButton** | `RBmasculino`, `RBFemenino` |
| **NumericUpDown** | `NumericUpDown1LC`, `NUDcomisión`, `Diascred`, `NudTop` |
| **DateTimePicker** | `DtpFecha`, `dtpFirma`, `dtpInicio`, `dtpVencimiento` |
| **DataGridView** | `dgvContratos`, `DgvSugerencias`, `DgvMunicipios`, `DgvCuentas`, `dgvRuta` |
| **ListView** | `LVpuntosEntregas` |
| **PictureBox** | `PictureBox3`, `pictureCapcha` |
| **TabControl** | `TabFUNCIONES`, `TabObs` |
| **Panel** | `Panel3establecimientos`, `Panel14DetalleDir`, `PanelCalveOperación`, `PanelRUTA`, `Panelcoordenadas`, `PanelContacto`, `PanelUE` |

### 1.4 Form_Load

```vb.net
Private Sub FrmRegClientePROCR_Load(...) Handles MyBase.Load
    TxtCodPac.Enabled = False
    opc = 1
    cmdgrabar.Enabled = True
    llenarSUCURSALES()
    cmdnuevo_Click(sender, e)       ' Limpia formulario
    LlenarFormasPago()              ' CBFormaPago con Buscar_FormasPago(Nothing)
    ' Carga CBcuentasCajaAdmin desde objComp.MOSTRAR_DESTINO()
    TabFUNCIONES.SelectedTab = TabPageContratos
    TabObs.Visible = True
    CBPais.FindStringExact("España")   ' Default: España
    CargarCatalogoBancos()
    PrepararFiltroDiaSemana()
    PrepararGridSugerencias()
    PrepararCombosGeografia()
    lblUsuario.Text = MDIMenu.sbrBarra.Panels(11).Text
    EnsureHiddenFields()
    ConfigurarGridRuta()
    LlenarRutas()
    CargarTiposDocumento()
    ClsContexto.PaisActivo = ClsConfiguracion.ObtenerPaisActivo()
    CargarCatalogoBancos_UsandoConexionExistente()
    ServicePointManager.SecurityProtocol = DirectCast(3072, SecurityProtocolType)
    UIHelper.ConfigurarTabsPorPais(TabObs)
End Sub
```

### 1.5 Lógica por País

```vb.net
' ConfigurarUIporPais()
If ClsContextoRegional.EsCR Then
    Panel14DetalleDir.Visible = True
    BTNCERRAR.Visible = False
    PanelCalveOperación.Visible = False
Else
    Panel14DetalleDir.Visible = False
    BTNCERRAR.Visible = True
    PanelCalveOperación.Visible = True
End If

' ConfigurarUI_PorPais()
If ClsContextoRegional.EsCR Then
    PanelRUTA.Visible = False : PanelRUTA.Enabled = False
Else
    PanelRUTA.Visible = True : PanelRUTA.Enabled = True
End If

' Etiquetas geográficas
If ClsContextoRegional.EsCR Then
    lblComunidad.Text = "Provincia"
    lblProvincia.Text = "Cantón"
    lblMunicipio.Text = "Distrito"
ElseIf ClsContextoRegional.EsES Then
    lblComunidad.Text = "Comunidad"
    lblProvincia.Text = "Provincia"
    lblMunicipio.Text = "Municipio"
End If
```

### 1.6 Guardar Datos Básicos (btnGuardarDatos_Click)

```vb.net
Private Sub btnGuardarDatos_Click(...) Handles btnGuardarDatos.Click
    If opc = 1 Then GuardarDatosBasicos_Nuevo()
    ElseIf opc = 2 Then GuardarDatosBasicos_Modificar()
End Sub

Private Sub GuardarDatosBasicos_Nuevo()
    If txtCliente.Text = "" Then MessageBox.Show("Ingrese nombre") : Exit Sub
    If txtDni.Text <> "" AndAlso obj.BuscarDNI(txtDni.Text).Read Then
        MessageBox.Show("El DNI ya existe.") : Exit Sub
    End If
    ' Clasifica documento: DNI/Cédula Física/RUT Persona → dniInsertar
    ' RUC/NIF/Cédula Jurídica → rucInsertar
    Dim id As Integer = obj.InsertarPersonaNuevo(
        0, "", txtCliente.Text, txtDni.Text, TxtDocumento.Text,
        1, "Masculino", Now, txtemail.Text, TxtTel.Text,
        1, "", "", "", "", 0, 0,
        TxtNomComercial.Text, TXTobsCliente.Text, "",
        CBtipoFac.Text, LblIDFormaPago.Text)
    If id > 0 Then TxtCodPac.Text = id : MessageBox.Show("Cliente registrado.")
End Sub

Private Sub GuardarDatosBasicos_Modificar()
    If LBLclaveOP.Text = "" Then LBLclaveOP.Text = 1
    If Diascred.Text > 0 Then LblIDFormaPago.Text = 8 Else LblIDFormaPago.Text = 1
    Dim rpta As Boolean = obj.Modificar_ClienteProveedor(
        TxtCodPac.Text, "", txtCliente.Text, txtDni.Text, TxtDocumento.Text,
        1, "Masculino", Now, txtemail.Text, TxtTel.Text,
        1, "", "", "", "",
        LBLclaveOP.Text, 0,
        TxtNomComercial.Text, TXTobsCliente.Text, "",
        CBtipoFac.Text, txtdirEmpresa.Text, LblIDFormaPago.Text)
End Sub
```

### 1.7 SQL Inline Encontrado

```vb.net
' 1) Tipos de documento (varias veces):
"SELECT IdTipoDocumento, NombreDocumento, TipoValidacion, Mascara, Longitud, SoloNumerico,
        UsaDigitoVerificador FROM TiposDocumentoPais WHERE PaisCodigo = @Pais AND Activo = 1"

' 2) Actualizar foto:
"Update persona Set fotografia=@fotografia WHERE cod_persona = '" & TxtCodPac.Text & "'"

' 3) Puntos de ruta:
"SELECT rp.Id_RutaPunto, rp.Id_Ruta, rp.Id_Punto, rp.Secuencia, ...
 FROM dbo.Ruta_PuntoEntrega rp LEFT JOIN dbo.Vehiculo_cliente_nuevo v ON v.Codigo = rp.Id_Punto
 WHERE rp.Id_Ruta = @Id ORDER BY rp.Secuencia"

' 4) Existe dirección similar:
"SELECT TOP 1 Direccion FROM Vehiculo_cliente_nuevo WHERE Id_ClientePersona = @idCliente AND Activo = 1"

' 5) Cliente tiene puntos:
"SELECT TOP 1 1 FROM Vehiculo_cliente_nuevo WHERE Id_ClientePersona = @cod"

' 6) Cliente tiene dirección fiscal:
"SELECT TOP 1 1 FROM Persona_Nuevo WHERE Cod_Persona = @cod AND Id_Direccion_Fiscal IS NOT NULL"

' 7) Contratos:
"SELECT Cod_Contrato, Tipo_Contrato, ... FROM CONTRATOS WHERE Cod_Cliente = @Cod"

' 8) Foto de persona:
"Select fotografia FROM Persona_Nuevo Where cod_persona = " & Foto
```

### 1.8 Geolocalización

```vb.net
' API Key
Dim apiKey As String = ConfigurationManager.AppSettings("GoogleApiKey")

' Abrir en Google Maps
Private Sub AbrirEnGoogleMaps()
    Dim urlGoogleMaps As String = "https://www.google.com/maps?q=" & txtLatitud.Text & "," & txtLongitud.Text
    Process.Start(urlGoogleMaps)
End Sub

' Capturar desde link de Maps
Private Function TryExtractLatLng(text As String, ByRef lat, ByRef lon) As Boolean
    ' Busca @lat,lon en URLs Google Maps
    ' Busca pares lat/lon en texto libre
End Function

' Parsear link completo de Maps
Private Sub ParsearLinkMaps(link As String)
    ' Extrae CP + localidad + provincia desde bloque /place/ de Google Maps
End Sub

' Guardar coordenadas (BTNguardarCord_Click)
Private Sub BTNguardarCord_Click(...) Handles BTNguardarCord.Click
    ' Valida lat/lon
    ' Si cambió vs _Latitud original, actualiza
    ' Si existe punto cercano (BuscarPuntosCercanos), pregunta
    ' Llama SP dbo.Insertar_Establecimiento con @Latitud, @Longitud
End Sub

' Test de API Key
Private Function TestGoogleKey(apiKey As String) As String
    Dim url As String = "https://maps.googleapis.com/maps/api/geocode/json?latlng=-12.046374,-77.042793&key=" & apiKey
End Function
```

### 1.9 Validación Fiscal e IBAN

```vb.net
' Validación de documento
If Not ClsValidaciones.ValidarDocumento(TxtDocumento.Text, tipoValidacion, nombreDocumento, mascara, mensajeError)

' IBAN España (ES): 24 caracteres, inicia "ES", MOD 97-10
' IBAN Costa Rica (CR): 22 caracteres, MOD 97
' CCI Perú (PE): 20 dígitos, algoritmo factores {3,7,1,3,7,1,...}
Private Function ValidarIBAN_Pro(cuentaUI, ByRef mensajeError, cuentaNormalizada, cuentaFormateada) As Boolean
Private Function ValidarCCI_Peru_Real(cci, mensajeError) As Boolean
    ' 20 dígitos, factores {3,7,1} repetidos, (10 - (suma Mod 10)) Mod 10
Private Function ObtenerLongitudIBAN_ISO(pais As String) As Integer
    ' Tabla completa ISO 13616 para 62 países
End Function
```

### 1.10 SPs Usados desde el Form

| SP | Propósito |
|----|-----------|
| `PERSONA_Buscarxruc` | Buscar por RUC |
| `CONTRATOS_Insertar` | Insertar contrato de alquiler |
| `CONTRATOS_ActualizarRutaArchivo` | Actualizar ruta PDF |
| `CONTRATOS_Anular` | Anular contrato |
| `CONTRATOS_Renovar` | Renovar contrato |
| `dbo.Insertar_Establecimiento` | Insertar punto de entrega |
| `dbo.Vehiculo_cliente_nuevo_ActualizarDireccion` | Actualizar dirección de punto |
| `dbo.Vehiculo_cliente_nuevo_SetPrincipal` | Marcar punto principal |
| `dbo.sp_PuntoEntrega_Insertar` | Insertar punto (nuevo) |
| `dbo.sp_PuntoEntrega_EstablecerPrincipal` | Establecer punto principal |
| `dbo.Ruta_PuntoEntrega_Asignar` | Asignar punto a ruta |
| `dbo.sp_RutaPto_Mover` | Reordenar punto en ruta |
| `dbo.sp_RutaPto_Compactar` | Compactar secuencia de ruta |
| `sp_Agenda_Insertar` | Insertar agenda de reparto |
| `dbo.SugerirRuta_MasCercana_PorPuntoEntrega` | Sugerir ruta más cercana |
| `dbo.CP_Localidad_BuscarTokens` | Buscar localidad por tokens |
| `dbo.CP_Localidad_Insertar` | Insertar nueva localidad |
| `dbo.CP_Localidad_ObtenerJerarquia` | Obtener jerarquía geográfica |
| `dbo.CP_Provincia_ListarPorCA` | Provincias por comunidad |
| `dbo.CP_Municipio_ListarPorProvincia` | Municipios por provincia |
| `dbo.CP_Localidad_ListarPorMunicipio` | Localidades por municipio |
| `dbo.AlmacenGeo_GetDefaults` | Defaults geográficos del almacén |
| `CR_Canton_ListarPorProvincia` | Cantones CR por provincia |
| `CR_Distrito_ListarPorCanton` | Distritos CR por cantón |
| `dbo.BuscarPuntosCercanos` | Puntos cercanos por coordenadas |
| `dbo.DatosBancarios_ObtenerPorCliente` | Datos bancarios del cliente |

---

## 2. FrmRegClientePRO.vb (545KB) — Versión PRO

### 2.1 Diferencias con FrmCatClientes

| Aspecto | FrmCatClientes | FrmRegClientePRO |
|---------|---------------|-----------------|
| País principal | Multi-país (CR focus) | España (default) |
| Búsqueda | FBusPacPROcr | FBusPacPLUS (BUG: apunta a PRO vía KeyPress) |
| Guardar | btnGuardarDatos_Click → GuardarDatosBasicos_Nuevo/Modificar | Mismo patrón |
| cmdgrabar | Comentado (inactivo) | Comentado (inactivo) |
| Botones separados | btnGuardarDatos, btnGuardarCredito, BtnGuardarFiscales, BtnGuardarCuenta | Mismos botones |
| Google Maps | Sí | Sí |
| IBAN | Sí (ES, CR, PE) | Sí (ES focus) |
| Rutas | Sí (PanelRUTA) | Sí |
| Puntos de entrega | Sí | Sí |

### 2.2 Form_Load

```vb.net
Private Sub FrmRegClientePRO_Load(...)
    TxtCodPac.Enabled = False
    opc = 1
    cmdgrabar.Enabled = True
    llenarSUCURSALES()
    cmdnuevo_Click(sender, e)
    LlenarFormasPago()
    ' Carga CBcuentasCajaAdmin
    TabFUNCIONES.SelectedTab = TabPageContratos
    TabObs.Visible = True
    CBPais.FindStringExact("España")   ' Default España
    CargarCatalogoBancos()
    PrepararFiltroDiaSemana()
    PrepararGridSugerencias()
    PrepararCombosGeografia()
    lblUsuario.Text = MDIMenu.sbrBarra.Panels(11).Text
    EnsureHiddenFields()
    ConfigurarGridRuta()
    LlenarRutas()
    ServicePointManager.SecurityProtocol = 3072
End Sub
```

---

## 3. FrmRegClientePLUS.vb (199KB) — Versión Simplificada

### 3.1 Qué OMITE vs PRO

| Característica | PRO | PLUS |
|----------------|-----|------|
| Google Maps / apiKey | ✅ | ❌ |
| IBAN / validación bancaria | ✅ | ❌ |
| Cuentas bancarias (CBnomBanco, DgvCuentas) | ✅ | ❌ |
| CBPais (selector de país) | ✅ | ✅ (solo selector, sin catálogo bancario) |
| CBclaveOP / CBclaveOPIC | ✅ | ❌ |
| PanelUE / CHKClienteUE | ✅ | ❌ |
| Puntos de entrega con coordenadas | ✅ | ❌ |
| txtLatitud, txtLongitud | ✅ | ❌ |
| LVpuntosEntregas | ✅ | ❌ |
| Rutas / DgvSugerencias | ✅ | ❌ |
| CBLocalidad, CBMunicipio (geografía detallada) | ✅ | ❌ |
| Botones separados (GuardarDatos, GuardarCredito, etc.) | ✅ | ❌ |
| cmdgrabar_Click | Comentado (inactivo) | ✅ Activo con lógica completa |

### 3.2 cmdgrabar_Click en PLUS (Activo)

```vb.net
Private Sub cmdgrabar_Click(...) Handles cmdgrabar.Click
    ' Validaciones: TxtRetencion <> ""
    ' Case opc = 1: confirma, busca DNI duplicado, llama
    '   obj.InsertarPersonaNuevo(...)
    '   obj.InsertarLineaCredito(...)
    ' Case opc = 2: confirma, llama
    '   obj.Modificar_ClienteProveedor(...)
    '   obj.ModificarLineaCred(...)
    '   obj.Cliente_Retencion_modificar(...)
End Sub
```

---

## 4. FrmRegCliente.vb (65KB) — Versión Antigua

### 4.1 Diferencias Clave

| Característica | PLUS | Antiguo |
|----------------|------|---------|
| TabControl / TabPageContratos | ✅ | ❌ |
| Contratos | ✅ | ❌ |
| Formas de pago | ✅ | ❌ |
| CBPais | ✅ | ❌ |
| InsertPersonaNuevo | ✅ (InsertarPersonaNuevo) | ❌ (usa InsertarClienteProveedor) |
| Coordenadas obligatorias | ❌ | ✅ (txtLatitud, txtLongitud required) |
| Agente obligatorio | ❌ | ✅ (CBAgente required) |
| BusquedaReniec | ❌ | ✅ |
| mostrar_sunat / captcha | ❌ | ✅ |
| ModificarLineaCred | ✅ | ✅ |
| Cliente_Retencion_modificar | ✅ | ✅ |

### 4.2 Guardar en versión antigua

```vb.net
Private Sub cmdgrabar_Click(...) Handles cmdgrabar.Click
    ' Case 1:
    '   obj.InsertarClienteProveedor(0, "", nombre, dni, ruc, 1, Now, "Masculino", email, tel, 1, ...)
    '   obj.InsertarLineaCredito(id, monto, dias, Now, True)
    ' Case 2:
    '   obj.Modificar_ClienteProveedor(cod, "", nombre, dni, ruc, 1, "Masculino", email, tel, 1, ...)
    '   obj.ModificarLineaCred(...)
    '   obj.Cliente_Retencion_modificar(...)
End Sub
```

---

## 5. BUG Conocido

**FBusPacPLUS.KeyPress (línea 153):** Apunta a `FrmRegClientePRO` en lugar de `FrmRegClientePLUS`:

```vb.net
' En FBusPacPLUS.KeyPress:
With FrmRegClientePRO  ' <-- BUG: debería ser FrmRegClientePLUS
    .TxtCodPac.Enabled = False
    ...
End With
```
