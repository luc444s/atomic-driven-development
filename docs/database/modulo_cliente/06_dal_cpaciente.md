# Módulo Clientes — CPaciente.vb (DAL)

## 1. Estructura de la Clase

```vb.net
Imports System.Data
Imports System.Data.SqlClient
Imports System
Imports System.Configuration

Public Class CPaciente
    Private objcn As SqlClient.SqlConnection
    Public Event OnError(ByVal sError As String)
```

- **Sin inherits ni interfaces**
- **Variable de clase única**: `Private objcn As SqlClient.SqlConnection`
- **Evento**: `OnError(ByVal sError As String)`
- **Conexión**: `ConfigurationManager.ConnectionStrings("ConexionPrincipal").ConnectionString`

---

## 2. Métodos de Conexión

```vb.net
Private Sub Conectar()
    Dim cs As String = ConfigurationManager.ConnectionStrings("ConexionPrincipal").ConnectionString
    objcn = New SqlConnection(cs)
    objcn.Open()
End Sub

Public Sub DesConnectar()    ' Cierra y libera
Public Sub DesConectar()     ' DUPLICADO exacto de DesConnectar
```

---

## 3. Lista Completa de Métodos (109 activos + 1 comentado)

### CRUD Persona/Paciente

| # | Método | Tipo Retorno | SP que llama |
|---|--------|-------------|-------------|
| 1 | `InsertarPaciente(params)` | Integer | `Paciente_Insertar` |
| 2 | `InsertarClienteProveedor(params)` | Integer | `Insertar_ClienteProveedor` |
| 3 | `Personal_Insertar(params)` | Integer | `Personal_Insertar` |
| 4 | `InsertarPersonal(params)` | (COMENTADO) | — |
| 5 | `Modificarmozo(params)` | Boolean | `mozo_Modificar` |
| 6 | `ModificarPaciente(params)` | Boolean | `Paciente_Modificar` |
| 7 | `ModificarPersonal(params)` | Boolean | `Personal_Modificar` |
| 8 | `ModificarEdad(params)` | Boolean | `Paciente_ModificarEdad` |
| 9 | `Modificar_ClienteProveedor(params)` | Boolean | `Modificar_ClienteProveedor` |
| 10 | `InsertarPersonaNuevo(params)` | Integer | `Insertar_Persona_Nuevo` (OUTPUT @Cod_Persona) |
| 11 | `ModificarPersonaNuevo(params)` | Boolean | `Modificar_Persona_Nuevo` (OUTPUT @Resultado) |

### Búsqueda de Persona

| # | Método | Tipo Retorno | SP que llama |
|---|--------|-------------|-------------|
| 12 | `BuscarMOZO(params)` | SqlDataReader | `mozo_mostrarxAlmacen` |
| 13 | `BuscarPersonaxNombre(params)` | SqlDataReader | `Paciente_BuscarxNom` |
| 14 | `BuscarPersonaxNombregasguia(params)` | SqlDataReader | `Paciente_BuscarxNomgasguia` |
| 15 | `BuscarPersonaxNombregasguia2(params)` | SqlDataReader | `Paciente_BuscarxNomgasguia2` |
| 16 | `BuscarPersonaxNombreCLIPROV(params)` | SqlDataReader | `Paciente_BuscarxNomgasguiadUEÑOCIL` |
| 17 | `BuscarPersonaxNombreCLIPROV2(params)` | SqlDataReader | `Paciente_BuscarxNomgasguiadUEÑOCIL2` |
| 18 | `BuscarPersonaxNombregasguiaContacto(params)` | SqlDataReader | `Paciente_BuscarxContactogasguia` |
| 19 | `MOSTRAR_PERSONA(params)` | SqlDataReader | `MOSTRAR_PERSONA` |
| 20 | `MOSTRAR_PERSONAResponsable(params)` | SqlDataReader | `MOSTRAR_PERSONAresponsable` |
| 21 | `BuscarPersonaxCM(params)` | SqlDataReader | `Paciente_BuscarxMC` |
| 22 | `BuscarPaciente(params)` | SqlDataReader | `Paciente_Buscar` |
| 23 | `BuscarPacientegasxcod(params)` | SqlDataReader | `Paciente_BuscarGas` |
| 24 | `BuscarPacientextelefono(params)` | SqlDataReader | `Paciente_BuscarTelf` |
| 25 | `BuscarPacientexDesc2(params)` | SqlDataReader | `Paciente_mostrarxfiltrosgas` |
| 26 | `BuscarDNI(params)` | SqlDataReader | `PERSONA_Buscarxdni` |
| 27 | `BuscarRUC(params)` | SqlDataReader | `PERSONA_Buscarxruc` |
| 28 | `BuscarRUCxTipo(params)` | SqlDataReader | `PERSONA_BuscarxrucTipo` |
| 29 | `BuscarPacientexDesc(params)` | SqlDataReader | (inline) |
| 30 | `BuscarPermisosAdministrador(params)` | SqlDataReader | `mostrar_permisosAdministrador` |
| 31 | `BuscarPermisosCaja(params)` | SqlDataReader | `mostrar_permisosCaja` |
| 32 | `BuscarPermisosContabilidad(params)` | SqlDataReader | `mostrar_permisosContabilidad` |
| 33 | `BuscarPermisosSistemas(params)` | SqlDataReader | `mostrar_permisosSistemas` |
| 34 | `BuscarPermisosservicios(params)` | SqlDataReader | `mostrar_permisosServicios` |
| 35 | `BuscarPermisosrecepcion(params)` | SqlDataReader | `mostrar_permisosrecepcion` |
| 36 | `BuscarPermisosprogramacion(params)` | SqlDataReader | `mostrar_permisosProgramacion` |
| 37 | `BuscarClientProvxnom(params)` | SqlDataReader | `Buscar_ClientProvxnom` |
| 38 | `BuscarClientexnomFiscal(params)` | SqlDataReader | `Buscar_ClientexnomFiscal` |
| 39 | `BuscarPersonaPorNombre(params)` | SqlDataReader | `Persona_BuscarXnom` |
| 40 | `Mostrar_persona_xcargo(params)` | SqlDataReader | `Persona_BuscarXcargo` |
| 41 | `Mostrar_persona_xfiltro(params)` | SqlDataReader | `Persona_BuscarXfiltro` |

### Vehículo / Puntos de Entrega

| # | Método | Tipo Retorno | SP que llama |
|---|--------|-------------|-------------|
| 42 | `vehiculo_Insertar(params)` | Integer | `crear_vehiculo_cliente` |
| 43 | `Modificarvehiculo_Insertar(params)` | Integer | `Modificar_vehiculo_cliente` |
| 44 | `Mostrar_cliente_vehiculo(params)` | SqlDataReader | `vehiculo_cliente_Buscarxcliente` |
| 45 | `Mostrar_cliente_vehiculoxcodigo(params)` | SqlDataReader | `vehiculo_cliente_Buscarxcodigo` |
| 46 | `Mostrar_PLACA(params)` | SqlDataReader | `mostrar_placas` |
| 47 | `Mostrar_cliente_PLACA(params)` | SqlDataReader | `vehiculo_cliente_Buscarxplaca` |
| 48 | `Eliminar_persona_vehiculo(params)` | Boolean | `vehiculo_cliente_Eliminar` |
| 49 | `InsertarEstablecimiento(params)` | Integer | `Insertar_Establecimiento` |
| 50 | `ModificarEstablecimiento(params)` | Boolean | `Actualizar_Establecimiento` |

### Dirección

| # | Método | Tipo Retorno | SP que llama |
|---|--------|-------------|-------------|
| 51 | `InsertarDireccion(params)` | Boolean | `Insertar_Direccion_Persona` |
| 52 | `ModificarDireccion(params)` | Boolean | `Modificar_Direccion_Persona` |

### Cliente_Sucursal / Agente

| # | Método | Tipo Retorno | SP que llama |
|---|--------|-------------|-------------|
| 53 | `InsertarClienteSucursal(params)` | Integer | `InsertarClienteSucursal` |
| 54 | `InsertarEcargoFuncion(params)` | Integer | `Insertar_Ecargo_Funcion` |
| 55 | `ModificarEcargoFuncion(params)` | Boolean | `Modificar_Ecargo_Funcion` |
| 56 | `Agentes_Sucursal_Insertar(params)` | Integer | `dbo.Insertar_AgenteSucursal` |

### Crédito

| # | Método | Tipo Retorno | SP que llama |
|---|--------|-------------|-------------|
| 57 | `InsertarLineaCredito(params)` | Boolean | `Resp_insertarLineaCredito` |
| 58 | `ModificarLineaCred(params)` | Boolean | `Personal_LineaCredito` |

### Retención

| # | Método | Tipo Retorno | SP que llama |
|---|--------|-------------|-------------|
| 59 | `Cliente_Retencion_modificar(params)` | Boolean | `clienteRetencion_modificar` |

### Coordenadas

| # | Método | Tipo Retorno | SP que llama |
|---|--------|-------------|-------------|
| 60 | `Registro_Coordenadas_Insertar(params)` | Integer | `InsertarRegistroCoordenadas` |
| 61 | `Registro_Coordenadas_Buscar(params)` | DataTable | `BuscarCoordenadas` |
| 62 | `Registro_Coordenadas_Modificar(params)` | Boolean | `ModificarCoordenadas` |

### Otros métodos

| # | Método | Tipo Retorno |
|---|--------|-------------|
| 63-72 | ModificarPermiso* (8 métodos) | Boolean |
| 73 | `Buscarlogin()` | SqlDataReader |
| 74 | `Mostrar_dia_visita(params)` | SqlDataReader |
| 75 | `Mostrar_dia_reparto(params)` | SqlDataReader |
| 76-80 | OrdenPago (5 métodos) | Integer / Boolean / SqlDataReader |
| 81 | `Mostrarhuellas(params)` | SqlDataReader |
| 82 | `Insertar_persona_alm(params)` | Boolean |
| 83 | `Eliminar_persona_almXCargo(params)` | Boolean |
| 84-86 | Mostrar personal disponible (3 métodos) | SqlDataReader |
| 87-88 | Comisión (2 métodos) | Integer / SqlDataReader |
| 89-90 | Historial / Total movimiento | SqlDataReader |
| 91 | `BuscarPacientemozo(params)` | SqlDataReader |
| 92 | `Mostrar_mozo(params)` | SqlDataReader |
| 93 | `Actualizar_estado_envnuevo(params)` | Boolean |
| 94-96 | Responsables (3 métodos) | SqlDataReader / Boolean |
| 97 | `Actualizar_ubigeo(params)` | Boolean |
| 98 | `MOSTRAR_Nrousuario(params)` | SqlDataReader |
| 99 | `Persona_ProcesoAlmacen(params)` | SqlDataReader |
| 100 | `Obtener_personas_por_cargo(params)` | SqlDataReader |
| 101 | `Listardemo()` | SqlDataReader |
| 102 | `ObtenerProcesoActivo(params)` | String (**SQL inline**) |
| 103 | `ObtenerProcesosSucursal(params)` | List(Of String) (**SQL inline**) |

---

## 4. SQL Inline (Riesgo)

Solo **2 métodos** usan SQL directo en lugar de SP:

```vb.net
' ObtenerProcesoActivo (línea ~2897)
objCommand.CommandText = "SELECT TOP 1 PROCESO FROM Persona_Proceso_Almacen WHERE Cod_Almacen = @Cod_Almacen"

' ObtenerProcesosSucursal (línea ~2924)
objCommand.CommandText = "
    SELECT PROCESO
    FROM Persona_Proceso_Almacen
    WHERE Cod_Almacen = @Cod_Almacen
    AND LTRIM(RTRIM(Grupo)) = LTRIM(RTRIM(@Grupo))"
```

Ambos usan `CommandType.Text` con parámetros (bajo riesgo de inyección). Los 107 métodos restantes usan `CommandType.StoredProcedure`.

---

## 5. Transacciones

- **~16 métodos** usan `BeginTransaction(IsolationLevel.Serializable)`: InsertarPaciente, InsertarClienteProveedor, Personal_Insertar, InsertarPersonaNuevo, ModificarPersonaNuevo, InsertarDireccion, ModificarDireccion, InsertarClienteSucursal, InsertarEcargoFuncion, ModificarEcargoFuncion, Agentes_Sucursal_Insertar, InsertarEstablecimiento, ModificarEstablecimiento, Modificar_ClienteProveedor, Registro_Coordenadas_Insertar, Registro_Coordenadas_Modificar
- **~25 métodos** usan `BeginTransaction()` simple (sin Serializable)
- **~10 métodos** tienen `Rollback` comentado (riesgo de transacciones huérfanas)

---

## 6. Riesgos Identificados

| Riesgo | Descripción |
|--------|-------------|
| **R1** | Rollback comentado en ~10 métodos: si fallan, la transacción queda abierta |
| **R2** | Métodos duplicados: `DesConnectar`/`DesConectar`, `Mostrardispemp`/`Mostrar_personal_disp` |
| **R3** | `InsertarEstablecimiento` trata `Envio` como `NVarChar(50)` en lugar de `Int` |
| **R4** | Los métodos SELECT nunca cierran conexión (dependencia del DataReader) |
| **R5** | `BuscarPacientextelefono` usa `SqlDbType.NVarChar` sin especificar tamaño |
| **R6** | 2 métodos con SQL inline (`ObtenerProcesoActivo`, `ObtenerProcesosSucursal`) |
| **R7** | `InsertarPaciente` no tiene `Finally` con `objcn.Close()` |

**No se encontró bypass a Persona_Nuevo.** Todos los INSERT/UPDATE usan SPs. El riesgo documentado previamente sobre `CContab.vb` haciendo UPDATE directo no está en esta clase.
