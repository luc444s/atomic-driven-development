# Forms de Búsqueda — Módulo Logística SYSTUTOR Legacy

---

## FrmBuscarCargas (346 líneas)

Formulario de búsqueda de movimientos de salida tipo 4 (logística).

| Elemento | Detalle |
|----------|---------|
| **Clase** | `FrmBuscarCargas` |
| **Propósito** | Buscar movimientos de salida por mes, año y sucursal |

### Controles

| Control | Origen de datos |
|---------|-----------------|
| `cbsucursal` | `MOSTRAR_ANEXOS` (SP) |
| `Cbmes` | Hardcoded (Enero–Diciembre) |
| `CbAño` | Años disponibles |

### SPs / Vistas utilizados

| Nombre | Tipo | Uso |
|--------|------|-----|
| `MOSTRAR_ANEXOS` | SP | Lista sucursales |
| `BuscarMovimientoxMesAnoSalidas` | SP | Búsqueda de movimientos tipo 4 |

### Mapeo de columnas del grid de resultados

| Columna | Origen |
|---------|--------|
| NroMovimiento | `Movimiento.IdMovimiento` |
| Fecha | `Movimiento.FechaMovimiento` |
| Cliente | `Persona.RazonSocial` |
| Almacén | `Almacen.Descripcion` |
| Estado | `Movimiento.Estado` |

---

## FrmAgendaRepartidor.vb (1.258 líneas)

Ver también documentación completa en `04_forms.md`.

### Filtros de búsqueda

| Control | Tipo | Descripción |
|---------|------|-------------|
| `dtpFechaInicio` | DateTimePicker | Fecha inicial |
| `dtpFechaFin` | DateTimePicker | Fecha final |
| `cbsucursal` | ComboBox (DAL) | Sucursal |
| `cmbRepartidor` | ComboBox (DAL) | Repartidor (filtrado por Chofer) |
| `cmbEstado` | ComboBox (hardcoded) | Estado: Programado, EnCurso, Realizado, Cancelado |

### SQL de búsqueda (inline)

```sql
SELECT IdAgenda, FechaAgenda, Persona.RazonSocial AS Repartidor,
       Sucursal.Nombre AS Sucursal, Estado, HoraInicio, HoraFin
FROM AGENDA_REPARTIDOR
INNER JOIN Persona_Nuevo ON AGENDA_REPARTIDOR.IdPersonaRepartidor = Persona_Nuevo.IdPersona
INNER JOIN Sucursal ON AGENDA_REPARTIDOR.IdSucursal = Sucursal.IdSucursal
WHERE FechaAgenda BETWEEN @fechaInicio AND @fechaFin
  AND (@sucursal IS NULL OR AGENDA_REPARTIDOR.IdSucursal = @sucursal)
  AND (@repartidor IS NULL OR AGENDA_REPARTIDOR.IdPersonaRepartidor = @repartidor)
  AND (@estado IS NULL OR AGENDA_REPARTIDOR.Estado = @estado)
ORDER BY FechaAgenda, HoraInicio
```

### Problemas conocidos

1. `cmbSucursal` no filtra efectivamente los repartidores
2. No paginación — el grid carga todo el rango de resultados
3. SQL inline sin parametrización adecuada

---

## FrmHistorialAgendaCliente.vb (422 líneas)

Formulario de consulta de historial de agendas filtrado por cliente.

| Elemento | Detalle |
|----------|---------|
| **Clase** | `FrmHistorialAgendaCliente` |
| **SP** | `sp_AgendaRepartidor_HistorialPorCliente` |
| **Filtro** | Cliente (texto o ID) |

### Parámetros del SP

```sql
sp_AgendaRepartidor_HistorialPorCliente @IdPersonaCliente INT
```

### Columnas del resultado

| Columna | Origen |
|---------|--------|
| Fecha | `AGENDA_REPARTIDOR.FechaAgenda` |
| Repartidor | `Persona.RazonSocial` |
| Estado | `AGENDA_REPARTIDOR.Estado` |
| HoraInicio | `AGENDA_REPARTIDOR.HoraInicio` |
| HoraFin | `AGENDA_REPARTIDOR.HoraFin` |
| Observaciones | `AGENDA_REPARTIDOR.Observaciones` |
