# Plan de Trabajo: 1 Mes — Trazabilidad de Cilindros

**Fecha:** 26/06/2026
**Duración:** 4 semanas
**Objetivo:** Tener 7 módulos de trazabilidad funcionando con arquitectura limpia (sin SPs nuevos)

---

## Semana 1: Fundación (Domain + Interfaces + DbContext)

| Día | Actividad | Archivos a crear |
|---|---|---|
| **Lun** | Crear estructura de carpetas `Trazabilidad/Domain/Entities/` + `Trazabilidad/Domain/Enums/` | `Cilindro.vb`, `AgendaRepartidor.vb`, `Cliente.vb`, `PuntoEntrega.vb`, `MovimientoCilindro.vb`, `EstadoCilindro.vb`, `EstadoCilindroEnum.vb` |
| **Mar** | Escribir interfaces de repositorio en `Trazabilidad/Application/Interfaces/` | `ICilindroRepository.vb`, `IAgendaRepository.vb`, `IMovimientoRepository.vb`, `IClienteRepository.vb` |
| **Mié** | Escribir DTOs en `Trazabilidad/Application/DTOs/` | `SalidaCilindroDto.vb`, `PlanificacionDiariaDto.vb`, `HistorialCilindroDto.vb`, `NuevaTareaDto.vb` |
| **Jue** | Crear `DbContext.vb` (factory de conexión usando `ClsConexion.ConnectionString`) + `EntityMappings.vb` | `DbContext.vb`, `EntityMappings.vb` |
| **Vie** | Validar que las entidades cubren todos los campos de las tablas reales. Revisar `03_columnas.txt` para `AGENDA_REPARTIDOR`, `ECilindroEstadoActual`, `Movimiento`. | Ajustes a entidades |

**Entregable:** Capa `Domain` completa + interfaces + DbContext conectado a BD real.

---

## Semana 2: Agenda + Planificación

| Día | Actividad | Archivos a crear/modificar |
|---|---|---|
| **Lun** | Implementar `AgendaRepository` (Dapper): `ObtenerTareasDelDia`, `InsertarTarea`, `ActualizarEstado`, `ObtenerPorId` | `AgendaRepository.vb` |
| **Mar** | Implementar `AgendaService`: `InsertarTarea`, `MarcarRealizado`, `MarcarEnRuta`, `ObtenerPlanificacionDelDia` | `AgendaService.vb` |
| **Mié** | Revisar legacy: activar inserción de agenda en los 7 puntos comentados. Reemplazar llamadas a SPs por `AgendaService`. | Modificaciones a `FrmMovIntercambioCliente.vb`, `FrmOrdenSalida.vb`, `FrmOrdenIngresoC.vb` |
| **Jue** | Implementar use case `PlanificarRuta` + `ObtenerCargaDelDia` | `PlanificarRuta.vb`, `ObtenerCargaDelDia.vb` (en `UseCases/`) |
| **Vie** | Crear `FrmPlanificacionDiaria.vb` (form nuevo para planificar rutas) | `FrmPlanificacionDiaria.vb`, `FrmPlanificacionDiaria.Designer.vb` |

**Entregable:** Agenda funcionando centralizadamente. Inserción activa en todos los módulos. Form de planificación básico.

---

## Semana 3: Salida + Ingreso + Traslado

| Día | Actividad | Archivos a crear/modificar |
|---|---|---|
| **Lun** | Implementar `CilindroRepository` (Dapper) | `CilindroRepository.vb` |
| **Mar** | Implementar `MovimientoRepository` (Dapper) | `MovimientoRepository.vb` |
| **Mié** | Implementar use cases: `RegistrarSalidaCilindro`, `RegistrarIngresoCilindro` | `RegistrarSalidaCilindro.vb`, `RegistrarIngresoCilindro.vb` |
| **Jue** | Crear `FrmSalidaConAgenda.vb` — integra `PlanificacionDiaria` + `RegistrarSalidaCilindro`. Conectar traslado con planificación del día. | `FrmSalidaConAgenda.vb`, `FrmSalidaConAgenda.Designer.vb` |
| **Vie** | Implementar use case `ConfirmarTraslado` + integrar con `FrmMovTrasladoAlmacen` (o nuevo form de traslado) | `ConfirmarTraslado.vb` |

**Entregable:** Flujo planificación → carga → salida funcionando. Traslado muestra planificación del día.

---

## Semana 4: Carga + Historial + Cierre

| Día | Actividad | Archivos a crear/modificar |
|---|---|---|
| **Lun** | Implementar use case `PrepararCarga` + integrar con `FrmMovPreparacionCarga` | `PrepararCarga.vb` |
| **Mar** | Crear `FrmCargaCamion.vb` (nuevo form de carga con planificación visible) | `FrmCargaCamion.vb`, `FrmCargaCamion.Designer.vb` |
| **Mié** | Implementar use case `ConsultarHistorialCilindro`. Mejorar `FrmHistorialCilindro.vb`. | `ConsultarHistorialCilindro.vb`, `FrmHistorialCilindro.vb` |
| **Jue** | Validación cruzada: probar flujo completo: planificación → carga → salida → traslado → ingreso → historial. Corregir bugs. | Varios |
| **Vie** | Documentación final. Escribir `README.md` de la carpeta `Trazabilidad/`. Registrar cambios en `docs/legacy/changes/`. | Documentación |

**Entregable:** Sistema completo de trazabilidad funcionando. 7 módulos operativos.

---

## Resumen de archivos a crear

| Capa | Archivos |
|---|---|
| Domain (6) | `Cilindro.vb`, `AgendaRepartidor.vb`, `Cliente.vb`, `PuntoEntrega.vb`, `MovimientoCilindro.vb`, `EstadoCilindro.vb`, `EstadoCilindroEnum.vb` |
| Application Interfaces (4) | `ICilindroRepository.vb`, `IAgendaRepository.vb`, `IMovimientoRepository.vb`, `IClienteRepository.vb` |
| Application DTOs (4) | `SalidaCilindroDto.vb`, `PlanificacionDiariaDto.vb`, `HistorialCilindroDto.vb`, `NuevaTareaDto.vb` |
| Application UseCases (6) | `RegistrarSalidaCilindro.vb`, `RegistrarIngresoCilindro.vb`, `PlanificarRuta.vb`, `PrepararCarga.vb`, `ConfirmarTraslado.vb`, `ConsultarHistorialCilindro.vb` |
| Infrastructure (6) | `DbContext.vb`, `EntityMappings.vb`, `CilindroRepository.vb`, `AgendaRepository.vb`, `MovimientoRepository.vb`, `ClienteRepository.vb`, `AgendaService.vb`, `TrazabilidadService.vb` |
| Forms (4) | `FrmPlanificacionDiaria.vb`, `FrmSalidaConAgenda.vb`, `FrmCargaCamion.vb` + mejoras a `FrmHistorialCilindro.vb` |
| **Total** | **~30 archivos nuevos + modificaciones legacy** |

## Archivos legacy a modificar

| Archivo | Cambio |
|---|---|
| `FrmMovIntercambioCliente.vb` | Activar agenda comentada (líneas 3851-3856, 7082) → usar `AgendaService` |
| `FrmOrdenSalida.vb` | Agregar integración con `AgendaService` |
| `FrmOrdenIngresoC.vb` | Agregar integración con `AgendaService` |
| `FrmMovTrasladoAlmacen.vb` | Conectar con planificación del día (mostrar lo planificado antes de cargar) |
