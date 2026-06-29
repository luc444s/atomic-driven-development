# Forms — Módulo Logística SYSTUTOR Legacy

---

## FORMULARIOS DE PLANIFICACIÓN

---

### FrmMovPlanificacionOperaciones.vb (20.880 líneas)

**Clase:** `FrmMovPlanificacionOperaciones`

Arquitectura monolítica. Contiene lógica de planificación, asignación de repartidores, cálculo de stock y generación de pedidos en un solo form.

#### Tabla de eventos y SPs

| Evento | Acción | SP / SQL | Tipo |
|--------|--------|----------|------|
| `Load` | Carga combos e inicializa grid | Varios SPs de carga | Inicialización |
| `btnBuscar_Click` | Lista pedidos pendientes | `usp_Plan_ListarPendientes` | SP |
| `btnGenerarAgenda_Click` | Crea/actualiza agenda de repartidor | `sp_AgendaRepartidor_Upsert` | SP |
| `btnGuardarPlan_Click` | Actualiza planificación | `UPDATE` directo a `DetalleMovimiento` | SQL directo |
| `btnPlanificarTodo_Click` | Planifica todos los pendientes | Interno (cálculo en memoria) | Lógica VB |
| `btnPlanificarParciales_Click` | Planifica cargas parciales | Interno | Lógica VB |
| `btnPlanificarCompletos_Click` | Planifica cargas completas | Interno | Lógica VB |

#### Métodos principales

| Método | Descripción |
|--------|-------------|
| `CalcularStockYPlanificado()` | Calcula stock disponible vs planificado por producto |
| `ObtenerPlanificado()` | Suma cantidades planificadas del día |
| `RecalcularPlanData()` | Refresca datos del grid tras cambios |
| `SimularConsumoStock()` | Simula asignación de stock antes de guardar |
| `ObtenerStockPorProducto()` | Stock actual por producto |
| `ObtenerStockDisponiblePorGas()` | Stock disponible por tipo de gas |

#### ComboBox y orígenes de datos

| ComboBox | Origen |
|----------|--------|
| `cboAlmacen` | `Almacen WHERE Mostrar = 1` |
| `CboUserAsignado` | `Mostrar_persona_xcargo` |
| `cbmoneda` | Hardcoded: "Soles", "Dolares" |
| `CBCuentasBancos` | `MOSTRAR_DESTINO` |
| `CBdocBoletas` | Hardcoded: "DNI" |
| `cboMedioPago` | Hardcoded: "Efectivo" |

#### Bugs detectados

1. **`cboAlmacen_SelectedIndexChanged` vacío** — El evento no actualiza `txtAlmacenId`, dejando el almacén inconsistente si el usuario selecciona manualmente.
2. **Código comentado masivo** — Aproximadamente 4.500 líneas comentadas sin documentación de por qué.
3. **UPDATE directo sin SP** — `btnGuardarPlan_Click` ejecuta `UPDATE DetalleMovimiento SET ...` sin pasar por un SP ni transacción explícita.

---

### FrmMovPlanificacionADR.vb (1.720 líneas)

**Clase:** `FrmMovPlanificacionADR`

Variante del planificador anterior enfocada en ADR (Acuerdo de Reparto).

#### Eventos y SPs

| Evento | Acción | SP / SQL |
|--------|--------|----------|
| `Load` | Carga combos | Similar a Operaciones |
| `btnBuscar_Click` | Lista pendientes | `usp_Plan_ListarPendientes` |
| `btnCargarPlan_Click` | Genera precarga + inserta detalle | `usp_Plan_GenerarPreCarga` + `usp_Plan_InsertarDetallePreCarga` |
| `cboAlmacen_SelectedIndexChanged` | Filtra por almacén | Interno |
| `CboUserAsignado_SelectedIndexChanged` | Filtra por usuario | Interno |
| `grdPlan_CellEndEdit` | Valida edición en celda | Interno |

#### Métodos

| Método | Descripción |
|--------|-------------|
| `GetADRInfo()` | Consulta ADR directa (SQL inline) |
| `CalcularStockYPlanificado()` | Mismo cálculo que Operaciones |
| `ExisteAgendaAbierta()` | Verifica si ya hay agenda abierta |

#### Bugs detectados

1. **CRÍTICO — Recursión infinita en `ExisteAgendaAbierta()`**: El método se llama a sí mismo sin caso base. Causa stack overflow en ejecución.
2. **Conexiones no cerradas en `GetADRInfo()`**: Abre conexiones SQL pero no las cierra explícitamente.

```vb
' Fragmento ilustrativo del bug de recursión
Public Function ExisteAgendaAbierta() As Boolean
    ' ... lógica ...
    Return ExisteAgendaAbierta()  ' Se llama a sí misma infinitamente
End Function
```

---

### FrmMovPlanificacionOperacionesAntiguo.vb (1.593 líneas)

**Clase:** `FrmMovPlanificacionOperacionesAntiguo`

Versión previa del planificador de operaciones. Casi idéntico al ADR.

#### Eventos y SPs

| Evento | SP / SQL |
|--------|----------|
| `btnBuscar_Click` | `usp_Plan_ListarPendientes` |
| `btnCargarPlan_Click` | `usp_Plan_GenerarPreCarga` + `usp_Plan_InsertarDetallePreCarga` |

#### Bug

Misma **recursión infinita** en `ExisteAgendaAbierta()` que en ADR.

---

### FrmRegPlanificacion.vb (430 líneas)

**Clase:** `FrmRegPlanificacion`

Formulario más simple y limpio.

#### Eventos y SPs

| Evento | SP / SQL |
|--------|----------|
| `btnBuscar` | `usp_Plan_ListarPendientes` |
| `btnCargarPlan` | `usp_Plan_AceptarGenerarTraslado` |
| `btnGenerarAgenda` | `sp_AgendaRepartidor_Insertar` |
| `btnGuardarPlan` | `usp_Plan_GuardarLinea` |

#### ComboBox

| ComboBox | Origen |
|----------|--------|
| `cboAlmacen` | `Almacen WHERE Mostrar = 1` |

---

### ZZZFrmRegPlanificacionPro.vb (589 líneas)

**Clase:** `ZZZFrmRegPlanificacionPro`

Variante con prefijo `ZZZ` (posiblemente experimental o en desuso).

#### Eventos y SPs

| Evento | SP / SQL |
|--------|----------|
| `btnBuscar` | `usp_Plan_ListarPendientes` |
| `btnCargarPlan` | `usp_Plan_GenerarPreCarga` + `usp_Plan_InsertarDetallePreCarga` |
| `btnGenerarAgenda` | `sp_AgendaRepartidor_Insertar` |
| `btnGuardarPlan` | `UPDATE` directo a `DetalleMovimiento` |
| `txtBuscarCliente_TextChanged` | `DataView.RowFilter` en grid |
| `grdPlan_CellValidating` | Validación inline de datos de celda |

#### Bugs

1. **`btnGenerarAgenda` sin transacción** — Si el SP falla a mitad de ejecución, los datos quedan inconsistentes.
2. **UPDATE directo sin SP** — Mismo bug que `FrmMovPlanificacionOperaciones`.

---

## FORMULARIOS DE AGENDA Y REPARTIDOR

---

### FrmAgendaRepartidor.vb (1.258 líneas)

**Clase:** `FrmAgendaRepartidor`

Form principal de gestión de agenda diaria del repartidor. Contiene 11 consultas SQL inline (no usa SPs).

#### Eventos

| Evento | SQL / Acción |
|--------|--------------|
| `btnBuscarAgenda` | `SELECT ... FROM AGENDA_REPARTIDOR` (SQL inline) |
| `btnMarcarRealizada` | `UPDATE AGENDA_REPARTIDOR SET Estado = 'Realizado'` (SQL inline) |
| `btnIniciarRuta` | Transacción: `INSERT Registro_Coordenadas` + `UPDATE AGENDA_REPARTIDOR` (SQL inline) |
| `btnReprogramar` | `UPDATE AGENDA_REPARTIDOR SET Fecha = ...` (SQL inline) |
| `btnFinDeRutaTarea` | `UPDATE` tarea como completada (SQL inline) |
| `btnFinRutaDia` | `UPDATE` masivo de todas las tareas del día (SQL inline) |
| `btnImprimirRuta` | Crystal Report `RPT_RutaRepartidor` |

#### ComboBox

| ComboBox | Origen |
|----------|--------|
| `cbsucursal` | `DAL BuscarSucursalxcb` |
| `cmbRepartidor` | `DAL Mostrar_persona_xcargo` (filtrado a Chofer) |

#### Bugs críticos

1. **Credenciales "sa" hardcodeadas en Crystal Reports** — El form pasa usuario `sa` y contraseña en texto plano al report viewer.
2. **Coordenadas GPS fijas en 0,0** — `btnIniciarRuta` inserta `Latitud=0, Longitud=0` (no se implementó geolocalización real).
3. **UPDATE directos sin auditoría** — Ninguna modificación a `AGENDA_REPARTIDOR` pasa por un SP ni deja traza en tabla de log.
4. **`LlenarRepartidores_Bind` vs `LlenarRepartidores`** — Dos métodos con criterios de filtrado distintos causan resultados inconsistentes.
5. **`cmbSucursal` ignora sucursal al cargar repartidores** — No filtra repartidores por sucursal seleccionada.

---

### FrmCargaRepartidor.vb (421 líneas)

**Clase:** `FrmCargaRepartidor`

Gestión de carga de cilindros en el vehículo del repartidor.

#### Eventos

| Evento | SQL / SP |
|--------|----------|
| `BTNConsultarAgenda` | SQL inline: `v_ResumenCarga_Repartidor`, `ECilindroEstadoActual`, `AGENDA_PREPARACION_CARGA` |
| `BTNAgregarSerie` | `sp_CargaRepartidor_Insertar` |
| `BTNQuitarSerie` | `sp_CargaRepartidor_Eliminar` |
| `BTNValidarPesoCamion` | `sp_CargaRepartidor_ResumenPeso` |

#### ComboBox

| ComboBox | Origen |
|----------|--------|
| `CboRepartidor` | SQL inline: `Persona_Nuevo WHERE Cod_TipoPersona = 2` |
| `CboAlmacen` | SQL inline: `Almacen` |

#### Bugs

1. **`sp_CargaRepartidor_Eliminar` no encontrado** — El SP referenciado no existe en el repositorio de BD.
2. **Filtro `Cod_TipoPersona = 2` inconsistente** — Otros forms usan distintos criterios para identificar repartidores.

---

### FrmIncidenciasRepartidor.vb (108 líneas)

**Clase:** `FrmIncidenciasRepartidor`

Registro de incidencias durante la ruta del repartidor.

#### Eventos

| Evento | SP / Acción |
|--------|-------------|
| `btnRegistrar` | `usp_Cilindro_Estado_LogBulk` con TVP `CilindroEstadoTVP` |

#### ComboBox

| ComboBox | Origen |
|----------|--------|
| `cboMotivoCodigo` | SQL inline: `CatalogoMotivoCilindro` |

---

### FrmParametrosRepartidor.vb (151 líneas)

**Clase:** `FrmParametrosRepartidor`

Configuración de parámetros por repartidor.

#### Eventos

| Evento | SP |
|--------|----|
| `btnGuardar` | `sp_Repartidor_GuardarParametro` |

---

### FrmHistorialAgendaCliente.vb (422 líneas)

**Clase:** `FrmHistorialAgendaCliente`

Consulta de historial de agendas por cliente.

#### Eventos

| Evento | SP |
|--------|----|
| `btnBuscarHistorial` | `sp_AgendaRepartidor_HistorialPorCliente` |

---

### FrmRepartoSuc.vb (107 líneas)

**Clase:** `FrmRepartoSuc`

Formulario mínimo que accede directamente a controles de `FrmRegTransf` (alto acoplamiento).

#### Problema

Acceso directo a controles de otro form:

```vb
FrmRegTransf.txtAlmacen.Text = ...
FrmRegTransf.cboTipoMov.SelectedValue = ...
```

Esto genera alto acoplamiento y dificulta el mantenimiento.

---

## FORMULARIOS DE TRASLADOS, DESPACHO Y RECEPCIÓN

---

### FrmMovTrasladoAlmacen.vb (4.300 líneas)

**Clase:** `FrmMovTrasladoAlmacen`

Gestión de traslados entre almacenes. Crea dos pedidos separados (LLENO/VACÍO) por cada traslado.

#### Eventos

| Evento | SP / SQL |
|--------|----------|
| `cmdgrabar` | `InsertarECabeceraPedido` + `InsertardetallePedido` + `Insertarrepdetenv` + `actualizar_REPORTEDETENVASE` |
| `BTNgrabarSalida` | `Insertarmovimiento` |

#### Bugs

1. **`cmdgrabar` llama a `BTNgrabarSalida_Click`** — Flujo no lineal, el evento de grabación de pedido termina invocando el evento de salida, dificultando el seguimiento.
2. **~400 líneas comentadas** — Sin documentación de por qué se desactivaron.

---

### FrmDespacho.vb (343 líneas)

**Clase:** `FrmDespacho`

Registro de despacho de mercadería.

#### Eventos

| Evento | SP / SQL |
|--------|----------|
| `Load` | `mostrar_atenciones` |
| `cmdnuevo` | `cerrar_despacho` |
| `cmdgrabar` | `Movimiento_nroguia` |
| `ToolStripMenuItem2` | Crystal Report `vTICKETGUIA1` |

---

### FrmDespachoRecep.vb (341 líneas)

**Clase:** `FrmDespachoRecep`

Solo vista: muestra atenciones de descarga y detalle.

#### Vistas utilizadas

| Vista | Propósito |
|-------|-----------|
| `MOSTRAR_ATENCIONES_descargas` | Lista de descargas pendientes |
| `MOSTRAR_detalle_ATENCIONESdescargas` | Detalle de cada descarga |

---

### FrmMovRetornoVehiculo.vb (894 líneas)

**Clase:** `FrmMovRetornoVehiculo`

**Formulario más moderno del módulo.** Usa TVP para bulk insert y soporta escaneo láser de cilindros.

#### Eventos

| Evento | SP / SQL |
|--------|----------|
| `cmdgrabar` | `actualizar_despacho` + `InsertarHistorialEstadoTraslado` + `Movimiento_nroguia` |
| `cmdnuevo` | `cerrar_despacho` + `usp_Cilindro_Estado_LogBulk` |
| `txtnroserie_KeyDown` | Escaneo láser con `HashSet` para evitar duplicados |

#### Características

- Usa **TVP `dbo.TVP_Series`** para inserción masiva de series de cilindros
- **Escaneo láser** en tiempo real detectando duplicados vía HashSet
- Bitácora de estados: `"DESCARGADO_POR_RECEPCIONAR"`

---

### FrmRecepcion.vb (551 líneas)

**Clase:** `FrmRecepcion`

Recepción de mercadería en almacén.

#### Eventos

| Evento | SP / SQL |
|--------|----------|
| `cmdgrabar` | `sp_movimiento_aCTUALIZAR` + `InsertarHistorialEstadoTraslado` + SQL directo a `ECilindroEstadoLog` y `ECilindroEstadoActual` |

#### Bug crítico

**INSERT y UPDATE directos a `ECilindroEstadoLog` y `ECilindroEstadoActual`** — Bypass de SPs y DAL. El código ejecuta SQL inline para modificar el estado de cilindros, evadiendo cualquier validación contenida en los SPs oficiales.

#### Lógica de faltantes

```sql
-- Lógica inline que crea detalle "FALTANTE NO TRANSFERIDO"
IF (@cantidadRecibida < @cantidadEsperada)
    INSERT INTO DetalleMovimiento (...) VALUES ('FALTANTE NO TRANSFERIDO', ...)
```

---

### FrmMovPreparacionCarga.vb (1.109 líneas)

**Clase:** `FrmMovPreparacionCarga`

Preparación de carga para reparto.

#### Eventos

| Evento | SP / SQL |
|--------|----------|
| `BTNgenerarCarga` | `sp_PreparacionCarga_MarcarCargado` |

#### Problema

**100% SQL directo** en métodos de carga de repartidores y almacenes. No usa SPs ni DAL para estas operaciones.

---

### FrmMovLlenadoBombonas.vb (2.601 líneas) y FrmMovSalidaProveedor.vb (2.308 líneas)

**Clase:** `FrmMovLlenadoBombonas` / `FrmMovSalidaProveedor`

Mismo patrón que `FrmMovTrasladoAlmacen`: crean pedidos separados para LLENO/VACÍO y múltiples SPs de inserción encadenados.

---

### FrmBuscarCargas.vb (346 líneas)

**Clase:** `FrmBuscarCargas`

Búsqueda simple de movimientos de salida.

| Evento | SP / SQL |
|--------|----------|
| Acción de búsqueda | `MOSTRAR_ANEXOS`, `BuscarMovimientoxMesAnoSalidas` |

#### ComboBox

| ComboBox | Origen |
|----------|--------|
| `cbsucursal` | `MOSTRAR_ANEXOS` |
| `Cbmes` | Hardcoded: lista de meses |
| `CbAño` | Años disponibles |
