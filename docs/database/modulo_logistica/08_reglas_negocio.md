# Reglas de Negocio — Módulo Logística

## 1. PLANIFICACIÓN

### Stock disponible
- No se puede planificar más cantidad que el stock físico disponible.
- `CantPlanificada` no puede exceder `CantPendiente` del detalle de movimiento.
- El stock disponible se calcula mediante `fn_StockFisico_Planificador`:
  `StockDisponible = StockActual - StockComprometido - StockPlanificado`

### Estados visuales en planificación
| Estado | Color | Condición |
|---|---|---|
| OK | Verde | Stock disponible >= CantSolicitada |
| PARCIAL | Amarillo | Stock disponible > 0 pero < CantSolicitada |
| SIN STOCK | Rojo | Stock disponible <= 0 |

### Pre-carga
- Solo una pre-carga activa por fecha y almacén.
- Estados de pre-carga: `PENDIENTE`, `ACEPTADA`, `CANCELADA`.
- Al aceptar una pre-carga se genera el traslado automáticamente.

### Modos de planificación
| Modo | Descripción |
|---|---|
| Planificar todo | Planifica la cantidad solicitada completa |
| Planificar completos | Solo planifica pedidos con stock suficiente para el total |
| Planificar parciales | Planifica con la cantidad disponible aunque sea parcial |

### Tipo de tarea en agenda
| Origen | Tipo Tarea |
|---|---|
| Pedido cliente (entrega cilindro) | `ENTREGA_CILINDRO` |
| Servicio CILCLI (cambio/carga in situ) | `SERVICIO_CILCLI` |

### Permitir sin stock
- Si `chkPermitirSinStock` está marcado, se permite planificar cantidades que excedan el stock disponible (modo proyectado / sobreventa).

---

## 2. AGENDA REPARTIDOR

### Ciclo de estados
```
PROGRAMADO ──> ENRUTA ──> REALIZADO
    │                      o ENTREGADO
    ├──> REPROGRAMADO ──> ENRUTA (reingresa)
    ├──> ANULADO
    └──> FALLIDO
```

### Inicio de ruta
- Solo transiciones permitidas: `PROGRAMADO` → `ENRUTA` y `REPROGRAMADO` → `ENRUTA`.
- Al iniciar ruta se asigna número de guía.
- Se registra coordenada GPS de inicio (latitud, longitud).
- Validación: no puede iniciar ruta si hay tareas sin coordenada de inicio del día anterior.

### Fin de ruta por tarea
- Solo tareas en estado `ENRUTA` pueden recibir coordenada de fin.
- Registrar coordenada de fin NO cambia el estado de la tarea.
- El cierre de tarea se realiza desde el **Módulo Recojo** (no desde agenda).

### Fin de ruta del día (masivo)
- Cambia a `ENRUTA` → `REALIZADO` para todas las tareas del día del repartidor.
- Solo aplica a tareas en estado `ENRUTA`.
- Registra hora de fin y coordenada de cierre.

### Reprogramación
- No puede reprogramar tareas en estado `REALIZADO` o `ANULADO`.
- Al reprogramar, la tarea vuelve a estado `PROGRAMADO` con nueva fecha.

### Coordenadas GPS
- El sistema registra coordenadas en `(0,0)` cuando no hay GPS real disponible.
- Valores en `Registro_Coordenadas`: Latitud DECIMAL(18,10), Longitud DECIMAL(18,10).

---

## 3. TRASLADOS

### Validaciones
- Origen y destino no pueden ser el mismo almacén.
- Cilindros **LLENOS** y **VACÍOS** se procesan como 2 pedidos separados (no se mezclan en un mismo detalle).

### Estados de traslado
| Estado | Descripción |
|---|---|
| EN_ALMACEN | Traslado creado, pendiente de carga |
| EN_RUTA | Trasladado, en camino |
| DESCARGADO_POR_RECEPCIONAR | Llegó a destino, pendiente de recepción formal |
| RECEPCIONADO | Recepcionado en destino final |

### Tablas de estado
| Tabla | Propósito |
|---|---|
| `ECilindroEstadoActual` | Estado actual del cilindro (1 registro por serie) |
| `ECilindroEstadoLog` | Historial de cambios de estado |
| `HistorialEstadosTraslados` | Historial por movimiento/traslado |

### Sincronización
- El trigger `trg_Movimiento_LogEstadoTraslado` sincroniza automáticamente `HistorialEstadosTraslados` al actualizar estado en `Movimiento`.

---

## 4. ADR (Acuerdo de Transporte de Mercancías Peligrosas)

### Configuración
- Cada producto gas tiene una configuración ADR vigente visible en `vw_EdetPB_Vigente`.
- La configuración incluye: `ClaseADR`, `PuntosADR`, `Tunel`, `CantidadMaxima`.
- La vigencia se controla por rango de fechas (`FechaInicio`/`FechaFin`).

### Cálculo de puntos
- `fn_ADR_Points(@CodProducto, @Cantidad)` calcula los puntos totales según la configuración vigente y la cantidad.
- `usp_ADR_CalcularPuntosDocumento(@CodMovimiento)` suma los puntos de todos los productos en un movimiento.

### Selección de vehículo
- `usp_ADR_SeleccionarCamion` busca el vehículo con capacidad ADR suficiente para el total de puntos del movimiento.
- Prioriza vehículos con mayor capacidad ADR disponible.

---

## 5. CARGA REPARTIDOR

### Peso máximo
- Peso máximo por repartidor: **5,000 kg** (hardcodeado en lógica de validación).
- Se valida antes de asignar cilindros adicionales.

### Tabla de asignación
- `AGENDA_PREPARACION_CARGA` es la tabla puente entre cilindros y repartidores.
- Columnas principales: `Serie`, `IdAgenda`, `Peso`, `FechaAsignacion`.

### Cilindros disponibles para carga
- Solo cilindros en `ECilindroEstadoActual` con estado:
  - `LLENO_EN_ALMACEN`
  - `LLENADO_OK`

---

## 6. INCIDENCIAS

### Motivos
- Los motivos de incidencia se listan desde `CatalogoMotivoCilindro`.
- Cada motivo tiene: `CodMotivo`, `Descripcion`, `EstadoDestino`.

### Estados destino
| Estado | Descripción |
|---|---|
| OBSERVADO | Cilindro con observación (defecto menor) |
| PARA_REPARACION | Cilindro requiere reparación |

### Origen
- Las incidencias de logística se registran con `Origen = 'REPARTO'` en `ECilindroEstadoLog`.

---

## 7. RECEPCIÓN

### Validación previa
- Solo se puede recepcionar un traslado si su estado actual es `Descargado` (es decir, `DESCARGADO_POR_RECEPCIONAR`).

### Diferencia de inventario
- Si hay diferencia entre lo enviado y lo recepcionado:
  - Se crea automáticamente un registro como `FALTANTE NO TRANSFERIDO`.
  - El faltante queda registrado para seguimiento.

### Trigger de sincronización
- `trg_Movimiento_LogEstadoTraslado` se dispara automáticamente al actualizar el estado del movimiento, registrando en `HistorialEstadosTraslados`.
