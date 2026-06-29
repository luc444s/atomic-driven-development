# Extracción BD — Módulo Logística SYSTUTOR Legacy

**Base de datos:** ACONCAGUA.Sys_GMS_ES
**Fecha extracción:** 2026-06-27

---

## Resumen de objetos identificados

| Tipo | Cantidad | Notas |
|------|----------|-------|
| Tablas logísticas | 27 | Incluye tablas propias + compartidas con uso logístico intensivo |
| Triggers | 4 | Ver detalle abajo |
| Índices no clúster | 27 | Distribuidos entre tablas de movimiento y agenda |
| FK (Foreign Keys) | 18 | Relaciones entre tablas logísticas |
| CHECK constraints | 2 | CK_Agenda_Estado, CK_Vehiculo_Dvisita |
| Vistas | 52 | Vistas específicas del módulo logístico |
| Stored Procedures | 135 | SPs del esquema logístico |
| Funciones escalares | 14 | Mayoría para cadenas de dirección y cálculos de ruta |
| TVPs (Table-Valued Parameters) | 6 | CilindroEstadoTVP, Ruta_Reorden_TVP, TipoListaSeries, TVP_CargaBombonas, TVP_Series, TipoListaProductos |
| SQL Agent Jobs | 0 | Sin automatización programada |

---

## Triggers detectados

| Trigger | Tabla | Propósito |
|---------|-------|-----------|
| `trg_CilLog_AfterInsert` | ECilindroEstadoLog | Dispara después de insertar un registro de estado de cilindro |
| `trg_Movimiento_LogEstadoTraslado` | Movimiento | Sincroniza automáticamente estados de traslado al insertar/actualizar movimientos |
| `tr_RegistroCoordenadas_ToDireccion` | Registro_Coordenadas | Convierte coordenadas en dirección textual |
| `TR_VehiculoCliente_SyncDireccionFiscal` | Vehiculo_cliente_nuevo | Sincroniza dirección fiscal del vehículo-cliente |

### Hallazgo clave: `trg_Movimiento_LogEstadoTraslado`

Este trigger es crítico para la integridad del flujo logístico: cada vez que se inserta o modifica un registro en `Movimiento`, el trigger actualiza automáticamente el estado del traslado en `HistorialEstadosTraslados`. Cualquier cambio en el flujo de `Movimiento` puede tener efectos en cascada no evidentes.

### Hallazgo clave: tabla espejo `Agenda_Repartidor_Resp`

Se detectó una réplica (`Agenda_Repartidor_Resp`) de la tabla principal `AGENDA_REPARTIDOR`. No tiene triggers propios. Se desconoce el mecanismo de sincronización. **Pendiente de investigar.**

---

## Vistas principales

Las 52 vistas cubren:

- `v_ResumenCarga_Repartidor` — resumen de carga por repartidor
- `V_DetalleMovimiento_*` — variantes sobre detalle de movimiento
- `V_Agenda_*` — proyecciones de agenda y repartidor
- `V_Ruta_*` — información de rutas y puntos de entrega
- `V_Cilindro_*` — estado actual e histórico de cilindros

---

## Notas sobre la extracción

- La extracción se realizó desde la BD de producción `ACONCAGUA` esquema `Sys_GMS_ES`.
- No se detectaron jobs del SQL Agent relacionados con logística.
- La mayoría de los SPs (≈80%) realizan operaciones de CRUD directo sin manejo transaccional explícito.
- 6 SPs usan TVP para operaciones batch (carga de bombonas, series, estados de cilindro).
