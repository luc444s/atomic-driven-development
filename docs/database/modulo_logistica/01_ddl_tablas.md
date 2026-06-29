# DDL Tablas — Módulo Logística SYSTUTOR Legacy

---

## TABLAS DE AGENDA Y REPARTIDOR

### AGENDA_REPARTIDOR

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdAgenda | INT (PK) | Identificador único |
| IdSucursal | INT (FK → Sucursal) | Sucursal asignada |
| IdPersonaRepartidor | INT (FK → Persona) | Repartidor asignado |
| FechaAgenda | DATE | Fecha de la agenda |
| HoraInicio | DATETIME | Inicio de ruta |
| HoraFin | DATETIME | Fin de ruta |
| Estado | VARCHAR(20) | CHECK (CK_Agenda_Estado): Programado, EnCurso, Realizado, Cancelado |
| Observaciones | VARCHAR(500) | Notas |

**FK:** IdSucursal → Sucursal.IdSucursal, IdPersonaRepartidor → Persona_Nuevo.IdPersona

### AGENDA_REPARTIDOR_HISTORIAL

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdHistorial | INT (PK) | Identificador único |
| IdAgenda | INT (FK → AGENDA_REPARTIDOR) | Agenda referenciada |
| FechaCambio | DATETIME | Momento del cambio |
| EstadoAnterior | VARCHAR(20) | Estado previo |
| EstadoNuevo | VARCHAR(20) | Estado nuevo |
| UsuarioCambio | VARCHAR(100) | Usuario que realizó el cambio |

### AGENDA_REPARTIDOR_LOG

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdLog | INT (PK) | Identificador único |
| IdAgenda | INT (FK → AGENDA_REPARTIDOR) | Agenda referenciada |
| Accion | VARCHAR(50) | INSERT, UPDATE, DELETE |
| FechaLog | DATETIME | Fecha del log |
| Usuario | VARCHAR(100) | Usuario |

### AGENDA_PREPARACION_CARGA

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdPreparacion | INT (PK) | Identificador único |
| IdAgenda | INT (FK → AGENDA_REPARTIDOR) | Agenda |
| IdUsuarioPreparo | INT | Usuario que preparó |
| FechaPreparacion | DATETIME | Fecha de preparación |
| Estado | VARCHAR(20) | Pendiente, Completado, Parcial |

### PLAN_PREPARACION_CARGA

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdPlan | INT (PK) | Identificador único |
| IdAgenda | INT (FK → AGENDA_REPARTIDOR) | Agenda |
| FechaPlan | DATETIME | Fecha planificada |
| Estado | VARCHAR(20) | Estado del plan |

### PLAN_PREPARACION_DETALLE

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdDetalle | INT (PK) | Identificador único |
| IdPlan | INT (FK → PLAN_PREPARACION_CARGA) | Plan |
| IdProducto | INT (FK → Producto) | Producto |
| CantidadPlanificada | DECIMAL(18,2) | Cantidad planificada |
| CantidadReal | DECIMAL(18,2) | Cantidad real cargada |

### AGENDA_TIPO_TAREA

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdTipoTarea | INT (PK) | Identificador |
| NombreTarea | VARCHAR(100) | Descripción |
| Activo | BIT | Si está habilitado |

---

## TABLAS DE RUTA

### Ruta

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdRuta | INT (PK) | Identificador único |
| NombreRuta | VARCHAR(100) | Nombre descriptivo |
| IdSucursal | INT (FK → Sucursal) | Sucursal |
| Activo | BIT | Estado |

### Ruta_DiaSemana

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdRutaDia | INT (PK) | Identificador |
| IdRuta | INT (FK → Ruta) | Ruta |
| DiaSemana | TINYINT | 1=Lunes … 7=Domingo |

### Ruta_PuntoEntrega

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdPuntoEntrega | INT (PK) | Identificador |
| IdRuta | INT (FK → Ruta) | Ruta |
| IdDireccion | INT (FK → Direccion) | Dirección de entrega |
| Orden | INT | Orden en la ruta |
| IdPersonaCliente | INT (FK → Persona) | Cliente |

---

## TABLAS DE VEHÍCULOS

### Camion

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdCamion | INT (PK) | Identificador |
| Placa | VARCHAR(20) | Placa del vehículo |
| Marca | VARCHAR(100) | Marca |
| Modelo | VARCHAR(100) | Modelo |
| CapacidadCarga | DECIMAL(18,2) | Capacidad en kg |
| CapacidadCilindros | INT | Número de cilindros |
| Activo | BIT | Estado |
| Dvisita | BIT | Requiere visita técnica |

**CHECK:** CK_Vehiculo_Dvisita — valida Dvisita según tipo de vehículo

### Camion_Ruta_Restriccion

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdRestriccion | INT (PK) | Identificador |
| IdCamion | INT (FK → Camion) | Vehículo |
| IdRuta | INT (FK → Ruta) | Ruta restringida |

---

## TABLAS DE EQUIPOS Y CHOFERES

### EEquipos

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdEquipo | INT (PK) | Identificador |
| NombreEquipo | VARCHAR(100) | Descripción |
| TipoEquipo | VARCHAR(50) | Tipo (ej: Bomba, Manguera) |

### EChoferesPorMovimiento

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdRegistro | INT (PK) | Identificador |
| IdMovimiento | INT (FK → Movimiento) | Movimiento asociado |
| IdPersonaChofer | INT (FK → Persona) | Chofer |
| EsPrincipal | BIT | Chofer principal |

### EEquiposPorMovimiento

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdRegistro | INT (PK) | Identificador |
| IdMovimiento | INT (FK → Movimiento) | Movimiento |
| IdEquipo | INT (FK → EEquipos) | Equipo |

---

## TABLAS DE COORDENADAS Y PARÁMETROS

### Registro_Coordenadas

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdCoordenada | INT (PK) | Identificador |
| IdAgenda | INT (FK → AGENDA_REPARTIDOR) | Agenda |
| Latitud | DECIMAL(10,7) | Latitud GPS |
| Longitud | DECIMAL(10,7) | Longitud GPS |
| FechaRegistro | DATETIME | Momento del registro |
| Direccion | VARCHAR(500) | Dirección (populada por trigger) |

**Trigger asociado:** `tr_RegistroCoordenadas_ToDireccion`

### Parametros_Repartidor

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdParametro | INT (PK) | Identificador |
| IdPersonaRepartidor | INT (FK → Persona) | Repartidor |
| ParametroClave | VARCHAR(100) | Clave del parámetro |
| ParametroValor | VARCHAR(500) | Valor |

---

## TABLAS DE ADR (ACUERDO DE REPARTO)

### ADR_Incompatibilidades

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdIncompatibilidad | INT (PK) | Identificador |
| IdProductoOrigen | INT (FK → Producto) | Producto origen |
| IdProductoDestino | INT (FK → Producto) | Producto incompatible |

### ADR_Referencia

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdReferencia | INT (PK) | Identificador |
| IdAgenda | INT (FK → AGENDA_REPARTIDOR) | Agenda |
| IdMovimiento | INT (FK → Movimiento) | Movimiento referenciado |
| TipoReferencia | VARCHAR(50) | Tipo de ADR |

---

## TABLAS DE HISTORIAL DE ESTADOS

### HistorialEstadosTraslados

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdHistorial | INT (PK) | Identificador |
| IdMovimiento | INT (FK → Movimiento) | Movimiento |
| EstadoAnterior | VARCHAR(50) | Estado previo |
| EstadoNuevo | VARCHAR(50) | Estado nuevo |
| FechaCambio | DATETIME | Fecha del cambio |
| Usuario | VARCHAR(100) | Usuario |

**Trigger asociado:** `trg_Movimiento_LogEstadoTraslado`

### HistorialMovimientoEstado

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdHistorial | INT (PK) | Identificador |
| IdMovimiento | INT (FK → Movimiento) | Movimiento |
| Estado | VARCHAR(50) | Estado |
| FechaRegistro | DATETIME | Fecha |
| Observacion | VARCHAR(500) | Nota |

---

## TABLAS DE ESTADO DE CILINDROS

### ECilindroEstadoLog

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdLog | BIGINT (PK) | Identificador |
| IdCilindro | INT (FK → Cilindro) | Cilindro |
| IdMovimiento | INT (FK → Movimiento) | Movimiento |
| EstadoLogístico | VARCHAR(50) | Estado en logística |
| FechaRegistro | DATETIME | Fecha |
| IdUsuarioRegistro | INT | Usuario |

**Trigger asociado:** `trg_CilLog_AfterInsert`

### ECilindroEstadoActual

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdCilindro | INT (PK) | Cilindro |
| EstadoActual | VARCHAR(50) | Estado logístico actual |
| IdUbicacion | INT | Ubicación actual |
| FechaUltimoMov | DATETIME | Último movimiento |

---

## TABLA DE PUNTOS DE ENTREGA

### Vehiculo_cliente_nuevo

| Columna | Tipo | Descripción |
|---------|------|-------------|
| IdRegistro | INT (PK) | Identificador |
| IdPersonaCliente | INT (FK → Persona) | Cliente |
| IdDireccion | INT (FK → Direccion) | Dirección de entrega |
| IdVehiculo | INT (FK → Camion) | Vehículo asignado |
| FechaAsignacion | DATETIME | Fecha de asignación |
| Activo | BIT | Estado |

**Trigger asociado:** `TR_VehiculoCliente_SyncDireccionFiscal`
