# Riesgos de Migración — Módulo Logística

Priorización: **CRÍTICO** > ALTO > MEDIO > BAJO

---

## CRÍTICOS

### R1 — Recursión infinita en `ExisteAgendaAbierta()`

| Atributo | Valor |
|---|---|
| **Ubicación** | `PlanificacionADR.vb`, `FrmPlanificacion (Antiguo).vb`, `ZZZFrmRegPlanificacionPro.vb` |
| **Descripción** | La función `ExisteAgendaAbierta()` se llama a sí misma sin condición de salida clara en ciertos escenarios. En el form Antiguo y Pro, se invoca en cascada desde `cboAlmacen_SelectedIndexChanged`, `GenerarAgenda` y otros eventos. |
| **Impacto** | Stack overflow, congelamiento del form, pérdida de datos no guardados. |
| **Solución propuesta** | Refactorizar para evitar llamada recursiva. Agregar flag de guarda o separar responsabilidades. |

### R2 — Credenciales `sa` hardcodeadas en Crystal Reports

| Atributo | Valor |
|---|---|
| **Ubicación** | `CR_AgendaRutaDia.rpt`, `vTICKETGUIA1.rpt`, `CRReporteProfalbaranCarga.rpt` |
| **Descripción** | Los archivos `.rpt` contienen usuario `sa` y contraseña `password` en texto claro para conexión a BD. |
| **Impacto** | Exposición total de la base de datos si un `.rpt` es interceptado. |
| **Solución propuesta** | Migrar a autenticación integrada de Windows o usar usuario con permisos mínimos. |

### R3 — SQL directo a `ECilindroEstadoLog` y `ECilindroEstadoActual` en `FrmRecepcion`

| Atributo | Valor |
|---|---|
| **Ubicación** | `FrmRecepcion.vb` |
| **Descripción** | El form ejecuta INSERT/UPDATE directos mediante comandos SQL en código, sin pasar por stored procedures. |
| **Impacto** | Bypass total de validaciones y reglas de negocio. Riesgo de inconsistencia de datos. |
| **Solución propuesta** | Reemplazar con llamadas a `usp_Cilindro_CambiarEstado` y `usp_Cilindro_Estado_LogSingle`. |

### R4 — Coordenadas GPS fijas en `(0, 0)`

| Atributo | Valor |
|---|---|
| **Ubicación** | `GeocodingProvider.vb`, `FrmAgendaRepartidor.vb` |
| **Descripción** | El sistema siempre registra `Latitud=0` y `Longitud=0` porque el proveedor de geocodificación no está implementado. |
| **Impacto** | Sin valor geoespacial real. Reportes de ruta con coordenadas inválidas. Imposible tracking real. |
| **Solución propuesta** | Implementar geocodificación real o eliminar columnas si no se usará. |

### R5 — `sp_CargaRepartidor_Eliminar` no existe en repositorio

| Atributo | Valor |
|---|---|
| **Ubicación** | Llamado desde `FrmCargaRepartidor.vb` o similar |
| **Descripción** | El SP `sp_CargaRepartidor_Eliminar` se referencia en código pero no se encuentra en la base de datos ni en scripts. |
| **Impacto** | Error en runtime al intentar eliminar un cilindro de la carga del repartidor. |
| **Solución propuesta** | Crear el SP faltante o reemplazar la llamada con lógica inline. |

---

## ALTOS

### R6 — `UPDATE` directo a `DetalleMovimiento` sin SP en planificación

| Atributo | Valor |
|---|---|
| **Ubicación** | `PlanificacionADR.vb`, `FrmPlanificacion (Antiguo).vb` |
| **Descripción** | Actualizan `CantPlanificada` con SQL directo en vez de usar `usp_Plan_GuardarCantidad`. |
| **Impacto** | Inconsistencia si se agregan validaciones futuras. Duplicación de lógica. |
| **Solución propuesta** | Reemplazar con llamadas al SP correspondiente. |

### R7 — Transacción ausente en `btnGenerarAgenda` de `ZZZFrmRegPlanificacionPro`

| Atributo | Valor |
|---|---|
| **Ubicación** | `ZZZFrmRegPlanificacionPro.vb` — evento `btnGenerarAgenda.Click` |
| **Descripción** | Se ejecutan múltiples INSERTS (agenda, detalle, servicios) sin una transacción explícita. |
| **Impacto** | Inconsistencia de datos si falla alguno de los pasos intermedios. |
| **Solución propuesta** | Envolver en `SqlTransaction` con commit/rollback. |

### R8 — Criterios inconsistentes para listar repartidores

| Atributo | Valor |
|---|---|
| **Ubicación** | `PlanificacionADR.vb`, `FrmPlanificacion (Antiguo).vb`, `ZZZFrmRegPlanificacionPro.vb` |
| **Descripción** | Cada form usa un criterio distinto para listar repartidores disponibles (diferentes JOINs, filtros y tablas). |
| **Impacto** | Resultados diferentes según el form usado. Confusión operativa. |
| **Solución propuesta** | Unificar en un solo SP con lógica de negocio centralizada. |

### R9 — Conexiones no cerradas en `GetADRInfo`

| Atributo | Valor |
|---|---|
| **Ubicación** | Posiblemente en módulo ADR o clase utilitaria |
| **Descripción** | Las conexiones SQL se abren pero no se cierran explícitamente en ciertas rutas de error. |
| **Impacto** | Conexiones colgadas en pool, eventual agotamiento de conexiones. |
| **Solución propuesta** | Usar bloques `Using` para garantizar cierre. |

### R10 — 5 formularios de planificación con código duplicado

| Atributo | Valor |
|---|---|
| **Ubicación** | `PlanificacionADR.vb`, `FrmPlanificacion (Antiguo).vb`, `ZZZFrmRegPlanificacionPro.vb`, `FrmPlanificacionOperaciones.vb`, más 1 |
| **Descripción** | Existen 5 formularios de planificación con lógica prácticamente idéntica pero con ligeras variaciones. |
| **Impacto** | Mantenimiento costoso. Bugs corregidos en uno pueden persistir en otros. |
| **Solución propuesta** | Consolidar en un solo formulario parametrizable. |

---

## MEDIOS

### R11 — SQL inline en agenda (17 consultas directas)

| Atributo | Valor |
|---|---|
| **Ubicación** | `FrmAgendaRepartidor.vb` |
| **Descripción** | 17 consultas SQL construidas como strings en código, sin usar SPs. |
| **Impacto** | Difícil mantenimiento, riesgo de SQL injection, lógica dispersa. |
| **Solución propuesta** | Migrar a SPs existentes del módulo agenda. |

### R12 — `cboAlmacen_SelectedIndexChanged` vacío en `PlanificacionOperaciones`

| Atributo | Valor |
|---|---|
| **Ubicación** | `PlanificacionOperaciones.vb` |
| **Descripción** | El evento existe pero su manejador está vacío (ninguna línea de código). |
| **Impacto** | Confusión al leer el código. Posible funcionalidad faltante. |
| **Solución propuesta** | Eliminar el manejador vacío o implementar la lógica necesaria. |

### R13 — `FrmRepartoSuc` accede a controles de otro form

| Atributo | Valor |
|---|---|
| **Ubicación** | `FrmRepartoSuc.vb` |
| **Descripción** | El form accede directamente a controles de otro formulario mediante `Forms("FrmOtroForm").Controls...` |
| **Impacto** | Alto acoplamiento. Difícil de mantener y probar. |
| **Solución propuesta** | Usar eventos o interfaz para comunicación entre forms. |

### R14 — Código comentado masivo (~30-40% en algunos forms)

| Atributo | Valor |
|---|---|
| **Ubicación** | Varios forms del módulo logística |
| **Descripción** | Grandes bloques de código comentado (30-40% del archivo). Dificulta la lectura y navegación. |
| **Impacto** | Mantenimiento más lento. Riesgo de des-comentar código obsoleto. |
| **Solución propuesta** | Limpiar código comentado y usar control de versiones como historial. |

### R15 — Sin logging centralizado

| Atributo | Valor |
|---|---|
| **Ubicación** | Todo el módulo |
| **Descripción** | No hay un sistema de logging unificado. Cada form maneja errores con `MsgBox` o `Debug.Print`. |
| **Impacto** | Imposible rastrear errores en producción. Diagnóstico lento. |
| **Solución propuesta** | Implementar logging con Serilog/NLog o similar en la migración. |

---

## BAJOS

### R16 — `Label7` con texto descriptivo de SP visible en runtime

| Atributo | Valor |
|---|---|
| **Ubicación** | Formulario de planificación |
| **Descripción** | Un `Label7` muestra el texto de un SP directamente visible para el usuario en ciertas condiciones. |
| **Impacto** | Confusión del usuario. Exposición de lógica interna. |
| **Solución propuesta** | Ocultar el label o cambiar su propósito. |

### R17 — `ComboBox` con items hardcoded sobrescritos en runtime

| Atributo | Valor |
|---|---|
| **Ubicación** | Formulario de planificación o agenda |
| **Descripción** | ComboBox se llena con items hardcodeados en el IDE, pero se sobrescriben al cargar el form. |
| **Impacto** | Items fantasma en diseño que no aparecen en runtime. Confusión. |
| **Solución propuesta** | Limpiar items en tiempo de diseño o en `Load`. |

### R18 — Variables de conexión global compartidas (`objcn`)

| Atributo | Valor |
|---|---|
| **Ubicación** | Módulos globales del proyecto |
| **Descripción** | La variable `objcn` se usa como conexión global compartida entre múltiples forms y módulos. |
| **Impacto** | Riesgo de conflictos de conexión en operaciones concurrentes. |
| **Solución propuesta** | Usar patrón `Using` con conexiones locales. |

---

## Matriz de Priorización

| ID | Riesgo | Impacto | Probabilidad | Prioridad |
|---|---|---|---|---|
| R1 | Recursión infinita | Alto | Media | **CRÍTICO** |
| R2 | Credenciales SA en .rpt | Alto | Alta | **CRÍTICO** |
| R3 | SQL directo en recepción | Alto | Alta | **CRÍTICO** |
| R4 | Coordenadas GPS 0,0 | Medio | Alta | **CRÍTICO** |
| R5 | SP faltante | Alto | Media | **CRÍTICO** |
| R6 | UPDATE directo sin SP | Medio | Alta | ALTO |
| R7 | Transacción ausente | Alto | Media | ALTO |
| R8 | Criterios inconsistentes | Medio | Alta | ALTO |
| R9 | Conexiones no cerradas | Medio | Media | ALTO |
| R10 | 5 forms duplicados | Medio | Alta | ALTO |
| R11 | SQL inline agenda | Bajo | Alta | MEDIO |
| R12 | Evento vacío | Bajo | Alta | MEDIO |
| R13 | Acoplamiento forms | Medio | Media | MEDIO |
| R14 | Código comentado | Bajo | Alta | MEDIO |
| R15 | Sin logging | Medio | Alta | MEDIO |
| R16 | Label7 visible | Bajo | Baja | BAJO |
| R17 | ComboBox sobrescrito | Bajo | Media | BAJO |
| R18 | Conexión global | Bajo | Media | BAJO |
