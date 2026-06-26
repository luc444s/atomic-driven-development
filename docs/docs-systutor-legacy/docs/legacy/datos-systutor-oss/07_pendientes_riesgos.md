# 07 — Pendientes, Riesgos y Supuestos de Migración

## 1. Datos y Tablas No Documentadas

| # | Ítem | Riesgo | Acción Recomendada |
|---|------|--------|-------------------|
| 1 | Tablas `borrar1`, `Borrar2`, `borrador1`, `ELIMINAR`, `temporal`, `importar`, `Xdemo` | Son tablas de prueba/legado. Probablemente vacías o con datos residuales. | No migrar. Verificar que ninguna SP las referencie. |
| 2 | Tabla `sysdiagrams` | Diagramas de BD de SQL Server. | No migrar. |
| 3 | Tabla `pruebaDigitalPersona` | No referenciada en SPs de negocio. | No migrar a menos que se confirme uso. |
| 4 | Tabla `Dist_Caotica` | Nombre sugiere datos desordenados/no críticos. | Investigar antes de migrar. |
| 5 | Backups `Producto_Backup_2025`, `Edetalle_Producto_Bombona_Backup_2025` | Backups de migración anterior. | No migrar. |
| 6 | Vistas `chiki`, `VPRUEBASA`, `Borrar` | Vistas de prueba. | No migrar. |
| 7 | Tabla `CV` | Sin contexto claro. | Verificar referencias. |

## 2. Riesgos Técnicos de la Migración

### 2.1 Riesgos de Base de Datos

| # | Riesgo | Impacto | Mitigación |
|---|--------|---------|-----------|
| R1 | **Concurrencia en correlativos**: legacy no usa UPDLOCK. Dos transacciones simultáneas pueden obtener el mismo número. | Duplicados en documentos fiscales. | Usar `SELECT ... FOR UPDATE` o secuencias PostgreSQL con `CYCLE`. |
| R2 | **Fugas de conexiones en legacy**: métodos viejos retornan DataReader abierto. Si el form no llama a DesConnectar(), la conexión queda abierta. | En OSS no aplica (conexiones de pool). Legacy pudo tener leaks que afectaban rendimiento. | No replicar el patrón. Usar siempre `async with` en OSS. |
| R3 | **Transacciones implícitas en SPs**: algunos SPs no usan BEGIN TRAN explícito (ej: ActualizarEquipoTransporte, EliminarEquipoTransporte). | Si falla a mitad, datos inconsistentes. | Envolver todas las operaciones multi-tabla en transacciones en OSS. |
| R4 | **SQL inyección potencial en BuscarTarifaCliente**: usa texto plano SQL en Cgas.vb. | Bajo (usa parámetros), pero es anti-patrón. | En OSS, usar siempre ORM con parámetros. |
| R5 | **Duplicación de SPs**: `consulta_detalle_envase` vs `consultar_detalle_envase` llaman a SPs distintos con firma similar. | Bug potencial si se llama al equivocado. | Unificar en un solo endpoint con parámetros opcionales. |
| R6 | **v_CilindrosDisponibles y vistas similares**: dependen de datos actuales. La lógica en OSS debe replicar exactamente la consulta. | Reportes incorrectos si la lógica diffiere. | Migrar vistas clave como vistas PostgreSQL o consultas SQLAlchemy. |

### 2.2 Riesgos de Migración de Datos

| # | Riesgo | Impacto | Mitigación |
|---|--------|---------|-----------|
| R7 | **Passwords en MD5**: Persona_Nuevo.Pass_Persona usa hash MD5 (inseguro). | No se pueden migrar directamente a bcrypt. | Migrar con flag `password_reset_required = true`. Forzar cambio en primer login. |
| R8 | **Datos maestros duplicados**: No hay constraints UNIQUE fuertes en nombres de producto, cliente, etc. | Datos sucios en OSS. | Limpiar datos antes de migrar o agregar validaciones en API. |
| R9 | **IDs auto-incrementales**: Legacy usa `@@IDENTITY` / `SCOPE_IDENTITY()`. PostgreSQL usa `GENERATED ALWAYS AS IDENTITY`. | Migración de IDs requiere cuidado con referencias FK. | Mantener IDs legacy como `id_legacy` y usar nuevos IDs en OSS, o migrar con `setval()` para mantener secuencia. |

### 2.3 Riesgos de Arquitectura

| # | Riesgo | Impacto | Mitigación |
|---|--------|---------|-----------|
| R10 | **Crystal Reports (~50 rpt)**: Legacy depende de Crystal Reports para todos los reportes impresos. | Sin reportes al migrar. | Crear endpoints JSON para cada reporte. Usar herramientas modernas (Power BI, Metabase, T-Soft) como frontend de reportes. |
| R11 | **Facturación electrónica multi-país**: Legacy soporta Perú (Nubefact) y Costa Rica (Hacienda). | Lógica de FE está en forms VB.NET, no en SPs. | Implementar como servicio separado con strategy pattern por país. |
| R12 | **Menú dinámico hardcoded en forms**: MDIMenu abre forms por nombre en `trv_DoubleClick`. | 218 forms VB.NET no se traducen a frontend web. | La API de menú solo da la estructura. El frontend debe implementar sus propios componentes. |

## 3. Supuestos y Decisiones Tomadas

| # | Supuesto | Base |
|---|----------|------|
| S1 | **El producto se identifica por `cod_producto`** (int PK). `Nro_Producto` es usado como SERIE del cilindro físico. | Confirmado en SPs y vistas. |
| S2 | **`Producto.cod_grupo`** apunta a otro Producto que representa el gas padre. | Confirmado en Producto y vw_EdetPB_Vigente. |
| S3 | **Los 18 estados de ECilindroEstadoCatalogo** son completos y vigentes. | Extraído directamente de la BD. |
| S4 | **Solo 4 TipoDoc tienen MueveEnvases=1** (#5, #13, #14, #41). | Confirmado en BD. |
| S5 | **El endpoint `/auth/menu` reemplaza la tabla Menu + SubMenu + SUBMENU1**. | Datos extraídos de la BD. |
| S6 | **Los roles son fijos**: Administrador, Contabilidad, Almacén, Sistemas, Ventas. | Basado en estructura de tabla Permiso. |
| S7 | **La tabla MovimientoSeries no existe** en esta BD. El escaneo en el SP usa tabla temporal `@Carga dbo.TVP_CargaBombonas READONLY`. | Confirmado: no hay tabla MovimientoSeries. |

## 4. Funcionalidades Legacy que NO se Migran (scope out)

| Funcionalidad | Motivo |
|--------------|--------|
| **Crystal Reports** | Se reemplaza por endpoints de datos + frontend moderno |
| **Forms VB.NET** | Se reemplaza por frontend web (no parte de este backend) |
| **Tablas de prueba** (borrar*, temporal, etc.) | Sin valor de negocio |
| **Módulo de Asistencia/Vacaciones** (Asistencia_vacaciones, Horarios) | No es core del negocio GLP |
| **CP_* (Códigos Postales España)** | Datos geo-regionales de España; evaluar si se necesita |
| **Backups de tablas** (Backup_2025) | Datos históricos temporales |

## 5. Dependencias Externas a Configurar

| Dependencia | Propósito | Configuración Requerida |
|------------|-----------|------------------------|
| **Nubefact API** | FE Perú | API URL + Token |
| **Hacienda CR API** | FE Costa Rica | API URL + Certificado Digital |
| **SUNAT** | Consulta RUC Perú | Token SUNAT (opcional) |
| **Correos SMTP** | Envío de comprobantes por email | Servidor SMTP + credenciales |

## 6. Orden de Migración Recomendado

```
Fase 1 — Core (día 1-3):
  Auth → Personas → Productos → Almacenes

Fase 2 — Catálogos (día 3-5):
  Líneas → SubLíneas → Marcas → Unidades → TipoDoc → ConfigRegional

Fase 3 — Transaccional (día 5-10):
  Movimiento + DetalleMovimiento → ECabeceraPedido → EDetalle_cpedido

Fase 4 — Cilindros/GLP (día 7-14):
  ECilindroEstadoLog → ECilindroEstadoActual → Garantías → Retimbrado → PH

Fase 5 — Logística (día 10-18):
  Agenda → Planificación → Despacho/Escaneo → Flota → ADR

Fase 6 — Facturación (día 14-21):
  Comprobantes → FE Perú → FE Costa Rica → Cancelaciones

Fase 7 — SOLYGAS (día 18-25):
  Servicios → Carga Peligrosa → Carta Porte → Reportes operativos

Fase 8 — Reportes y Migración de Datos (día 25-35):
  Endpoints de reportes → Scripts de migración → Validación de datos
```
