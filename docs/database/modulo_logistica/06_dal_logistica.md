# DAL (Data Access Layer) — Módulo Logística SYSTUTOR Legacy

---

## CMovimiento.vb (3.628 líneas)

Clase principal del módulo logístico. Contiene la mayoría de las operaciones CRUD sobre movimientos.

### Métodos

| Método | SP / SQL | Propósito |
|--------|----------|-----------|
| `mostrar_atenciones` | SP | Lista atenciones pendientes |
| `MOSTRAR_ATENCIONES_descargas` | SP | Lista descargas pendientes |
| `cerrar_despacho` | SP | Cierra un despacho |
| `actualizar_despacho` | SP | Actualiza datos de despacho |
| `actualizar_nroguia` | SP | Asigna número de guía |
| `Insertarmovimiento` | SP | Inserta un movimiento nuevo |
| `aCTUALIZARmovimiento` | SP | Actualiza movimiento existente |
| `ListarrECEPCION` | SP | Lista recepciones |
| `eliminarMovimiento` | SP | Elimina movimiento |
| `RecuperaEnvio` | SP | Recupera datos de envío |

### Observaciones

- Uso intensivo de SPs (a diferencia de otros forms que usan SQL inline).
- Contiene lógica de negocio mezclada con acceso a datos (no hay separación de capas).

---

## CDetalleMovimiento.vb (348 líneas)

### Métodos

| Método | SP / SQL | Propósito |
|--------|----------|-----------|
| `InsertarDetalleMovimiento` | SP | Inserta línea de detalle |
| `ModificarDetalleMovimiento` | SP | Modifica línea de detalle |

### Observaciones

Clase pequeña y enfocada. Sin bugs evidentes.

---

## Cgas.vb

Clase con operaciones sobre pedidos, historial de estados y consulta de envases.

### Métodos

| Método | SP / SQL | Propósito |
|--------|----------|-----------|
| `InsertarECabeceraPedido` | SP | Crea cabecera de pedido |
| `InsertardetallePedido` | SP | Crea detalle de pedido |
| `InsertarHistorialEstadoTraslado` | SP | Registra cambio de estado de traslado |
| `consultar_envase_venta` | SP | Consulta envase para venta |
| `Insertarrepdetenv` | SP | Inserta reporte detalle envase |

### Observaciones

- `InsertarHistorialEstadoTraslado` es uno de los SPs más utilizados — llamado desde al menos 5 forms diferentes.
- La clase agrupa responsabilidades de pedido + estado + envase (baja cohesión).

---

## CProducto.vb

### Métodos

| Método | SP / SQL | Propósito |
|--------|----------|-----------|
| `BuscarProductoxns` | SP | Busca producto por número de serie |
| `BuscarProductoxnsCilindro` | SP | Busca producto por serie de cilindro |

### Observaciones

Consultas de producto asociadas a series y cilindros. Ambas devuelven datos de producto + tipo de gas + presentación.

---

## CPaciente.vb

### Métodos

| Método | SP / SQL | Propósito |
|--------|----------|-----------|
| `Mostrar_persona_xcargo` | SP | Lista personas por cargo (repartidores, choferes) |
| `BuscarPersonaxNombregasguiaContacto` | SP | Busca persona para guía de contacto |

### Observaciones

- `Mostrar_persona_xcargo` es usado por múltiples ComboBox en `FrmMovPlanificacionOperaciones`, `FrmAgendaRepartidor` y otros.
- El nombre del método combina español e inglés (inconsistencia de naming).

---

## CAgenda.vb (246 líneas)

### Métodos

| Método | SP | Propósito |
|--------|----|-----------|
| `InsertarAgenda` | `sp_Agenda_Insertar` | Inserta agenda básica |
| `InsertarAgendaDesdePlus` | `usp_Agenda_InsertServicioDesdePlus` | Inserta agenda desde módulo Plus |

### Observaciones

Clase pequeña y enfocada. Buen ejemplo de cómo debería estructurarse el resto de la DAL.

---

## CSucursal.vb

### Métodos

| Método | SP / SQL | Propósito |
|--------|----------|-----------|
| `MOSTRAR_ANEXOS` | SP | Lista sucursales anexas |
| `BuscarSucursalxcb` | SP | Lista sucursales para ComboBox |

### Observaciones

`BuscarSucursalxcb` es el método más usado para poblar ComboBox de sucursales en todo el módulo logístico.

---

## CComprobante.vb

### Métodos

| Método | SP / SQL | Propósito |
|--------|----------|-----------|
| `ACTUALIZAR_ESTADORECEP` | SP | Actualiza estado de recepción en comprobante |

### Observaciones

Método único, llamado desde el flujo de recepción para marcar comprobantes como recibidos.
