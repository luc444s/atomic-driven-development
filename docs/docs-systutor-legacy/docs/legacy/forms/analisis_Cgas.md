# Análisis — Cgas.vb (2631 líneas, 96 métodos)

---

## 1. Resumen

`Cgas` es la 5ª clase más grande de CAtencion. Agrupa toda la lógica de **GLP — envases, cilindros, retimbrado, carga peligrosa, flota y servicios asociados**. Se divide en dos grandes bloques:

| Bloque | Líneas | Métodos | Origen |
|---|---|---|---|
| GLP general (envases, garantías, cambios) | 1–1574 | ~60 | Código original multi-empresa |
| SOLYGAS específico | 1575–2631 | ~36 | Adiciones para SOLYGASES |

---

## 2. Dominios funcionales

### 2.1 Envases (core GLP)

Maneja el ciclo de vida completo del envase/cilindro: consulta, disponibilidad, movimiento entre almacenes, traslados, ingreso, salida.

**Métodos representativos:**
- `consultar_envase_venta`, `consultar_envase_ventaBlanco`, `consultar_envase_ventaReal`
- `mostrar_envases_disponibles`, `mostrar_envases_disponiblesTraslado`, `mostrar_envases_VACIO`
- `mostrar_nrodoc`, `mostrar_DETALLEnrodoc[Envase][EnvaseSalida][EnvaseTrasl]`
- `mostrar_ingresos_pendientes`, `Buscarproductos_pendientes`
- `cambiar_envases`, `actualizar_estado`, `actualizar_edetalle_pedido`
- `actualizar_AlmacenTransfEnv`

**SPs asociados (patrón):** `Buscar_mostrardocumento*`, `consultar_envase*`, `detalle_*`

### 2.2 Garantías

Gestión de garantías sobre envases.

- `InsertarGarantia` → `Egarantia_Insertar`
- `actualizar_garantia` → `EGarantia_Modificar`
- `Buscar_garantia` → `buscar_garantia_envase`
- `MOSTRAR_CATEGORIA` → `mostrar_GARANTIAS_DISP`
- `BuscarEnvase_dias_Arriendo` → `Buscar_Envase_diasArriendo`

### 2.3 Cambios de dueño

Registro de cambios de propiedad/custodia del envase entre personas.

- `InsertarEcilDuenio` → `InsertarEcilDuenio`
- `ModificarEcilDuenio` → `ModificarEcilDuenio`
- `MostrarUltimoEcilDuenioPorProducto` → `MostrarUltimoEcilDuenioPorProducto`
- `InsertarCambios` → `Ecambios_Insertar`

### 2.4 Pedidos especiales de envases

Cabecera y detalle de pedidos de préstamo/cambio de envases.

- `InsertarECabeceraPedido` → `ECabeceraPedido_Insertar` (27 parámetros)
- `InsertardetallePedido` → `EDetallePedido_Insertar`
- `mostrar_edetalle` → `buscar_edetallepedido`
- `ModificarDocAfect` → `Modificar_DocAfect_EPrestamos`

### 2.5 Retimbrado

Control técnico de cilindros (revisión periódica obligatoria para GLP): peso, presión, válvulas, marcado, nº ONU, clase de peligro.

- `InsertarRetimbrado` → `Retimbrado_insertar` (18 campos)
- `actualizar_retimbrado` → `Retimbrado_modificar`
- `Retimbrado_BuscarUltimoPorCodProducto` → `Retimbrado_buscarUltimo`
- `modificarfecha_ph` → `modificar_fecha_ph` (próxima prueba hidrostática)

### 2.6 SOLYGAS — Servicios de cilindros

Adición específica SOLYGASES. Cilindros asignados a servicios (mantenimiento, limpieza, etc.).

- `InsertarServicio` → `InsertarECilindrosServicios`
- `ActualizarServicio` → `ActualizarECilindrosServicios`
- `EliminarServicio` → `EliminarECilindrosServicios`
- `MostrarServiciosPendientes` → `ObtenerServiciosPendientes`
- `ObtenerTodosServicios` → `ObtenerTodosECilindrosServicios`
- `mostrar_ObtenerEnvasesPorServicio` → `ObtenerEnvasesPorServicio`
- `Mostrar_ServiciosXproducto` → `Mostrar_Servicios`

### 2.7 SOLYGAS — Reporte de Carga Peligrosa

Documento obligatorio para transporte de GLP (carga peligrosa).

- `InsertarReporteCargaPeligrosa` → `Insertar_Reporte_Carga_Peligrosa`
- `MostrarReporteCargaPeligrosa` → `Mostrar_Reporte_Carga_Peligrosa`
- `ActualizarReporteCargaPeligrosa` → `Modificar_Reporte_Carga_Peligrosa`

### 2.8 SOLYGAS — Choferes y flota

Asignación de choferes y equipos de transporte a movimientos.

**Choferes:**
- `InsertarChoferPorMovimiento`, `ModificarChoferPorMovimiento`, `EliminarChoferPorMovimiento`
- `ConfirmarCargaChofer`

**Equipos (camiones, cisternas):**
- `InsertarEquipoTransporte`, `ActualizarEquipoTransporte`, `EliminarEquipoTransporte`
- `ConsultarEquipoTransporte`, `mostrar_equiposTransp_por_tipo`
- `InsertarEquipoPorMovimiento`, `ActualizarEquipoPorMovimiento`, `EliminarEquipoPorMovimiento`
- `ConsultarEquiposPorMovimiento`

**Historial de estados de traslado:**
- `InsertarHistorialEstadoTraslado`, `ActualizarEstadoMovimiento`
- `MostrarHistorialEstadosTraslados`, `ListarHistorialEstados`
- `EliminarHistorialEstadoTraslado`, `EliminarHistorialDeMovimiento`

---

## 3. Anomalías encontradas

| # | Problema | Detalle |
|---|---|---|
| 1 | **SQL texto plano** | `BuscarTarifaCliente` (línea 2556) es el único método que NO usa SP; ejecuta `SELECT TOP 1 precio FROM dbo.Tarifa_cliente WHERE ...` directamente. |
| 2 | **Duplicación sospechosa** | `consulta_detalle_envase` llama a `BuscarProd_pendientexOrden` pero `consultar_detalle_envase` llama a `buscar_detalle_envases`. Nombres casi idénticos, SPs diferentes. Posible bug o copia/pega. |
| 3 | **Código comentado** | `Insertarrepdetenv1` (línea 498) y `consultar_envase_ventaBlanco` viejo (línea 600) están comentados pero no eliminados. |
| 4 | **Calidad despareja** | Métodos nuevos (desde línea 1575) usan `Using`, `Dispose()`, `DataTable`, manejo de `DBNull`. Métodos viejos dejan `DataReader` abierto y gestión manual de conexión. |
| 5 | **Método sin transacción** | `ActualizarEquipoTransporte` y `EliminarEquipoTransporte` ejecutan SP sin transacción (`BeginTransaction`), a diferencia del resto de la clase. |

---

## 4. Patrón de código (2 versiones)

### Versión vieja (GLP general)

```vb.net
Public Function mostrar_envases_disponibles(ByVal Almacen) As SqlDataReader
    Dim objCommand As New SqlCommand
    Dim objDr As SqlDataReader
    Try
        Conectar()
        objCommand.Connection = objcn
        objCommand.CommandText = "Buscar_mostrardocumentodisponible"
        objCommand.CommandType = CommandType.StoredProcedure
        objCommand.Parameters.Add("@Almacen", SqlDbType.Int).Value = Trim(Almacen)
        objDr = objCommand.ExecuteReader(CommandBehavior.SingleResult)
        Return objDr  ' ← DataReader abierto, el form debe cerrarlo
    Catch ex As Exception
        RaiseEvent onError(ex.Message)
    Finally
        ' No cierra conexión ni reader
    End Try
End Function
```

### Versión nueva (SOLYGAS)

```vb.net
Public Function ConsultarEquiposPorMovimiento(ByVal Cod_Movimiento As Integer) As DataTable
    Dim objCommand As New SqlCommand
    Dim objAdapter As New SqlDataAdapter
    Dim objTable As New DataTable
    Conectar()
    Try
        objCommand.CommandText = "EEquiposPorMovimiento_Consultar"
        objCommand.CommandType = CommandType.StoredProcedure
        objCommand.Parameters.Add("@Cod_Movimiento", SqlDbType.Int).Value = Cod_Movimiento
        objCommand.Connection = objcn
        objAdapter.SelectCommand = objCommand
        objAdapter.Fill(objTable)  ' ← DataTable, cierra todo automático
        Return objTable
    Catch ex As Exception
        RaiseEvent onError(ex.Message)
        Return Nothing
    Finally
        objcn.Close()
        objCommand = Nothing
    End Try
End Function
```

---

## 5. SPs referenciados (~75 SPs únicos)

Prefijos detectados en los SPs que llama Cgas:

| Prefijo | Función |
|---|---|
| `Buscar_mostrar*` | Consultas de documentos y disponibilidad |
| `consultar_envase*` | Consulta de envases |
| `detalle_*` | Operaciones sobre detalle de envases |
| `E*` | Entidades específicas (ECabeceraPedido, EDetallePedido, EcilDuenio) |
| `Retimbrado_*` | Retimbrado de cilindros |
| `InsertarECilindrosServicios` | Servicios SOLYGAS |
| `*_Reporte_Carga_Peligrosa` | Carga peligrosa |
| `*ChoferPorMovimiento` | Asignación choferes |
| `*Equipo*` | Gestión de flota |
| `*HistorialEstado*` | Trazabilidad de estados |

---

## 6. Conexión con tablas probables

Por los nombres de SPs y parámetros, las tablas que presumiblemente opera son:

- `Envases`, `DetalleEnvase`, `ReporteDetEnvase`
- `EGarantia`, `EcilDuenio`, `Ecambios`
- `ECabeceraPedido`, `EDetallePedido`
- `Retimbrado`
- `ECilindrosServicios`
- `Reporte_Carga_Peligrosa`
- `Equipos`, `EquiposPorMovimiento`, `ChoferesPorMovimiento`
- `HistorialEstadoTraslado`
- `SubCategoria`, `Contenido`
- `Tarifa_cliente`, `Producto`

---

## 7. Riesgos identificados

1. **Bug potencial:** `consulta_detalle_envase` vs `consultar_detalle_envase` — llaman a SPs distintos pero tienen la misma firma. Si un form llama al equivocado, devuelve datos incorrectos.
2. **Fuga de conexiones:** Métodos viejos que devuelven `DataReader` abierto sin cerrar conexión — si el form no llama a `DesConnectar()` consistentemente, hay fugas.
3. **Sin transacción en flota:** `ActualizarEquipoTransporte` y `EliminarEquipoTransporte` no usan transacción — si falla a mitad, datos inconsistentes.
4. **SQL injection potencial:** `BuscarTarifaCliente` usa SQL texto plano (riesgo bajo porque usa parámetros, pero anti-patrón vs el resto del sistema).
