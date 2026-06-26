# Diseño de Módulos de Trazabilidad de Cilindros

**Fecha:** 26/06/2026

---

## 1. Módulos a Construir (7 módulos)

| # | Módulo | Form legacy existente | ¿Se reutiliza? |
|---|---|---|---|
| 1 | **Maestro Clientes** (personas + puntos entrega) | `FrmCatClientes`, `FrmRegSUCURSAL` | Tablas `Persona_Nuevo`, `Cliente_Sucursal` |
| 2 | **Planificación de ruta** (asignar cilindros a repartidor) | `FrmMovPlanificacionOperaciones` | Tablas `AGENDA_REPARTIDOR`, `PLAN_PREPARACION_CARGA` |
| 3 | **Preparación de carga** (armar carga del camión) | `FrmMovPreparacionCarga` | Tablas `AGENDA_PREPARACION_CARGA`, `AGENDA_REPARTIDOR` |
| 4 | **Salida de almacén** (despachar a cliente con planif. visible) | `FrmOrdenSalida`, `FrmMovIntercambioCliente` | Tablas `ECabecera_pedido`, `EDetalle_cpedido`, `Movimiento` |
| 5 | **Traslado entre almacenes** | `FrmMovTrasladoAlmacen` | Tablas `Movimiento`, `HistorialEstadosTraslados` |
| 6 | **Ingreso a almacén** (recepción de cilindros) | `FrmOrdenIngresoC` | Tablas `ECabecera_pedido`, `EDetalle_cpedido` |
| 7 | **Trazabilidad del cilindro** (historial completo) | `FrmHistorialCilindro` | Tablas `ECilindroEstadoActual`, `ECilindroEstadoLog` |

---

## 2. Flujo Completo de Trazabilidad (Nuevo)

```
PLANIFICACIÓN
  │
  ├── Repartidor selecciona ruta del día
  │   └── Se crean tareas en AGENDA_REPARTIDOR (Tipo_Tarea = 'ENTREGA_CILCLI_LLENO')
  │
  ▼
PREPARACIÓN DE CARGA
  │
  ├── Muestra cilindros planificados por cliente
  ├── Se cargan físicamente al camión
  ├── Se marca AGENDA_REPARTIDOR.Estado_Tarea = 'CARGADO'
  │
  ▼
SALIDA DE ALMACÉN  ←═══ Acá se resuelve el problema del traslado
  │
  ├── Muestra SOLO lo cargado para ese repartidor (filtrado por agenda)
  ├── Se registra salida en Movimiento + DetalleMovimiento
  ├── Se registra en ECilindroEstadoActual (ubicación = "EN RUTA")
  ├── Se marca AGENDA_REPARTIDOR.Estado_Tarea = 'ENRUTA'
  │
  ▼
ENTREGA AL CLIENTE
  │
  ├── Se registra intercambio (cilindro lleno ↔ vacío)
  ├── Se actualiza ECilindroEstadoActual (ubicación = "CLIENTE")
  ├── Se marca AGENDA_REPARTIDOR.Estado_Tarea = 'REALIZADO'
  │
  ▼
INGRESO (DEVOLUCIÓN)
  │
  ├── Se registra ingreso de cilindros vacíos
  ├── Se actualiza ECilindroEstadoActual (ubicación = "ALMACEN")
  │
  ▼
ECilindroEstadoLog (historial completo)
  ── Cada transición queda registrada con fecha, usuario, movimiento
```

---

## 3. Diseño de Cada Módulo

### 3.1 Maestro Clientes + Puntos de Entrega

**Propósito:** Registrar clientes/empresas y sus puntos de entrega (sucursales).

**Reutiliza:** Tablas `Persona_Nuevo`, `Cliente_Sucursal`, `Direccion`

**Use cases:**
- `RegistrarCliente` — crear/actualizar persona
- `AgregarPuntoEntrega` — crear sucursal + dirección + coordenadas
- `ConsultarRutaCliente` — obtener puntos de entrega por zona/repartidor

**Indicaciones:** Este módulo puede reutilizar los forms existentes `FrmCatClientes` y `FrmRegSUCURSAL` sin cambios, ya que funcionan correctamente. Solo se crean los use cases si se necesita lógica nueva.

---

### 3.2 Planificación de Ruta / Agenda

**Propósito:** Asignar tareas de entrega/recojo a repartidores para una fecha.

**Reutiliza:** Tabla `AGENDA_REPARTIDOR`, vista `v_AgendaRepartidor_PedidosPendientes`

**Use cases:**
- `PlanificarRutaDiaria` — crear tareas en `AGENDA_REPARTIDOR` para un repartidor
- `ObtenerCargaDelDia` — obtener todas las tareas planificadas para un repartidor + fecha
- `ReprogramarTarea` — cambiar fecha de una tarea pendiente

**Reglas de negocio:**
- Una tarea no puede duplicarse (mismo cliente + misma fecha + mismo tipo)
- Si ya existe una tarea `ENTREGA_CILCLI_LLENO` para ese cliente/fecha, no se crea otra
- El estado inicial es `PROGRAMADO`

---

### 3.3 Preparación de Carga

**Propósito:** Armar la carga física del camión antes de la salida.

**Reutiliza:** Tablas `AGENDA_PREPARACION_CARGA`, `ECilindros_Servicios`

**Use cases:**
- `PrepararCarga` — registrar cilindros cargados en el camión
- `MarcarCargaCompletada` — cambiar estado de agenda a `CARGADO`
- `ConsultarPendientesDeCarga` — ver lo que falta cargar

**Reglas de negocio:**
- Solo se pueden cargar cilindros que estén en `ECilindroEstadoActual` con ubicación = `ALMACEN`
- Al marcar como `CARGADO`, se registra en `AGENDA_PREPARACION_CARGA`

---

### 3.4 Salida de Almacén (con planificación visible)

**Propósito:** Registrar salida de cilindros desde almacén a cliente, mostrando lo planificado.

**Form nuevo:** `FrmSalidaConAgenda.vb`

**Reutiliza:** Tablas `ECabecera_pedido`, `EDetalle_cpedido`, `Movimiento`, `DetalleMovimiento`, `AGENDA_REPARTIDOR`

**Use cases:**
- `IniciarSalida` — crear movimiento de salida, asociar a tarea de agenda
- `RegistrarCilindrosSalida` — registrar cilindros que salen, actualizar `ECilindroEstadoActual`
- `CerrarSalida` — marcar agenda como `ENRUTA`, generar documento

**Flujo de la UI:**
1. Usuario selecciona repartidor y fecha
2. Se ejecuta `ObtenerCargaDelDia` → se muestra grid con tareas planificadas + cilindros
3. Usuario confirma cilindros que realmente salen (cantidad, series)
4. Se ejecuta `RegistrarCilindrosSalida` → INSERT en `Movimiento` + `DetalleMovimiento`
5. Se ejecuta `CerrarSalida` → UPDATE en `ECilindroEstadoActual` + `AGENDA_REPARTIDOR`

---

### 3.5 Traslado entre Almacenes

**Propósito:** Mover cilindros entre almacenes con trazabilidad completa.

**Reutiliza:** Tablas `Movimiento`, `HistorialEstadosTraslados`, `ECilindroEstadoLog`

**Use cases:**
- `IniciarTraslado` — crear movimiento de traslado, registrar estado "EN TRASLADO"
- `RegistrarCilindrosTraslado` — detalle de cilindros trasladados
- `ConfirmarRecepcionTraslado` — registrar ingreso en almacén destino, actualizar estado

**Mejora sobre el estado actual:**
Hoy `FrmMovTrasladoAlmacen.vb` no muestra la planificación del día. El nuevo flujo debe:
1. Cargar las tareas de agenda del repartidor seleccionado para la fecha
2. Mostrar los cilindros planificados para cada tarea
3. Permitir al usuario confirmar qué cilindros se trasladan
4. Actualizar `ECilindroEstadoActual` + `HistorialEstadosTraslados`
5. Marcar `AGENDA_REPARTIDOR.Estado_Tarea = 'ENRUTA'`

---

### 3.6 Ingreso a Almacén

**Propósito:** Registrar recepción de cilindros (devoluciones de clientes, ingresos de proveedores).

**Reutiliza:** Tablas `ECabecera_pedido`, `EDetalle_cpedido`, `Movimiento`

**Use cases:**
- `RegistrarIngresoCliente` — devolución de cilindros vacíos
- `RegistrarIngresoProveedor` — recepción de cilindros de proveedor
- `ActualizarEstadoCilindro` — cambiar a `EN_ALMACEN` en `ECilindroEstadoActual`

**Reglas de negocio:**
- Al ingresar un cilindro, se actualiza su estado en `ECilindroEstadoActual`
- Se registra la transición en `ECilindroEstadoLog` con fecha, usuario, movimiento asociado

---

### 3.7 Trazabilidad del Cilindro (Historial)

**Propósito:** Consultar el historial completo de un cilindro.

**Reutiliza:** Tablas `ECilindroEstadoActual`, `ECilindroEstadoLog`, `ECilindroEstadoCatalogo`, `ECilindroEstadoTransicion`

**Use cases:**
- `ConsultarHistorialCompleto` — toda la vida del cilindro (ordenado por fecha descendente)
- `ConsultarEstadoActual` — ubicación y estado presente
- `ConsultaPorLote` — todos los cilindros de una misma carga/fecha

**DTO de salida:**
```vb.net
Public Class HistorialCilindroDto
    Public Property NroSerie As String
    Public Property Fecha As DateTime
    Public Property EstadoAnterior As String
    Public Property EstadoNuevo As String
    Public Property Ubicacion As String
    Public Property DocumentoAsociado As String
    Public Property Usuario As String
    Public Property IdMovimiento As Integer
End Class
```

---

## 4. Activación de Agenda (Pendientes del Legacy)

### Puntos donde la agenda está comentada o ausente

| Archivo | Línea | Acción requerida |
|---|---|---|
| `FrmMovIntercambioCliente.vb` | 3851-3856 | Activar `ActualizarAgendaPorIngreso` y `InsertarAgendaDesdePlus` |
| `FrmMovIntercambioCliente.vb` | 7082 | Activar `CerrarAgendaDesdePlus` |
| `FrmOrdenSalida.vb` | (todo el archivo) | Agregar integración con agenda vía `AgendaService.InsertarTarea` |
| `FrmOrdenIngresoC.vb` | (todo el archivo) | Agregar integración con agenda vía `AgendaService.InsertarTarea` |

### Nueva estrategia (centralizada)

Todo el código de inserción en agenda se mueve a `AgendaService.vb`:

```vb.net
Public Class AgendaService
    Public Function InsertarTarea(request As NuevaTareaDto) As Integer
        ' Siempre inserta, nunca queda comentado
        ' Si es ENTREGA_CILCLI_LLENO, verificar duplicado
        ' Si es SERVICIO, calcular fecha según tipo
        ' Retorna Id_Agenda
    End Function

    Public Sub MarcarRealizado(idAgenda As Integer, documento As String)
        ' Cambia estado a REALIZADO y asocia documento
    End Sub

    Public Sub MarcarEnRuta(idAgenda As Integer)
        ' Cambia estado a ENRUTA
    End Sub

    Public Function ObtenerPlanificacionDelDia(
        idRepartidor As Integer, fecha As Date) As List(Of TareaDto)
        ' Retorna todas las tareas del día para un repartidor
    End Function
End Class
```

Los 7 puntos del legacy donde hoy hay `'InsertarAgenda...` comentado se reemplazan por:
```vb.net
Dim idAgenda = _agendaService.InsertarTarea(nuevaTarea)
```

---

## 5. Ejemplo de Use Case (Código)

```vb.net
' Application/UseCases/PlanificacionDiaria.vb

Public Class PlanificacionDiaria
    Private ReadOnly _agendaRepo As IAgendaRepository

    Public Sub New(agendaRepo As IAgendaRepository)
        _agendaRepo = agendaRepo
    End Sub

    Public Function ObtenerCargaDelDia(
        idRepartidor As Integer,
        fecha As Date
    ) As List(Of CargaPlanificadaDto)

        Dim tareas = _agendaRepo.ObtenerTareasDelDia(idRepartidor, fecha)

        Dim result = New List(Of CargaPlanificadaDto)
        For Each t In tareas
            result.Add(New CargaPlanificadaDto With {
                .IdAgenda = t.IdAgenda,
                .Cliente = t.NombreCliente,
                .Direccion = t.DireccionEntrega,
                .TipoTarea = t.TipoTarea,
                .Estado = t.EstadoTarea,
                .DocumentoAsociado = t.DocumentoAsociado
            })
        Next

        Return result
    End Function
End Class
```

Uso desde el form:

```vb.net
' Forms/Trazabilidad/FrmSalidaConAgenda.vb

Private Sub FrmSalidaConAgenda_Load()
    Dim agendaRepo = New AgendaRepository(ClsConexion.ConnectionString)
    Dim planDiaria = New PlanificacionDiaria(agendaRepo)

    dgvCarga.DataSource = planDiaria.ObtenerCargaDelDia(
        cboRepartidor.SelectedValue,
        dtpFecha.Value
    )
End Sub
```
