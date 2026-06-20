# ADR 0007 - Observabilidad

## Estado

Aceptado

## Contexto

SYSTUTOR OSS necesita responder de forma consistente:

* qué pasó;
* cuándo ocurrió;
* quién lo hizo;
* desde qué tenant ocurrió;
* qué entidad fue afectada;
* qué cambió;
* qué proceso se disparó;
* qué error ocurrió;
* qué importación o job lo originó.

La observabilidad no debe quedar postergada hasta una fase tardía porque afecta al core, jobs, migraciones, auditoría, eventos, plugins, permisos y operación diaria.

SYSTUTOR Legacy tiene lógica repartida entre SQL Server, VB.NET, Crystal Reports, stored procedures, triggers y formularios. Esa realidad obliga a que SYSTUTOR OSS nazca con trazabilidad superior desde el inicio.

## Decisión

La observabilidad será una capacidad base del sistema desde el core inicial.

No será tratada como un agregado posterior.

SYSTUTOR OSS deberá implementar observabilidad mínima en:

* API HTTP;
* jobs async;
* migrador legacy;
* runtime de plugins;
* eventos;
* auditoría;
* autenticación;
* permisos;
* errores relevantes;
* operaciones críticas de negocio.

## Componentes mínimos

La primera versión deberá incluir:

* logging estructurado;
* `request_id`;
* `correlation_id`;
* `job_id` cuando aplique;
* auditoría funcional;
* registro de eventos;
* registro de errores relevantes;
* trazabilidad por tenant;
* trazabilidad por sucursal cuando aplique;
* trazabilidad de importaciones legacy;
* trazabilidad de cambios en plugins;
* trazabilidad de permisos.

## Diferencia entre logs, eventos y auditoría

### Logs técnicos

Sirven para diagnóstico técnico.

Ejemplos:

* request recibido;
* error inesperado;
* job iniciado;
* job fallido;
* plugin falló al cargar;
* archivo CSV inválido;
* conexión externa fallida.

### Eventos

Representan hechos del sistema o del dominio.

Ejemplos:

```text
logistics.delivery.created
legacy.import.completed
core.plugin.enabled
customers.customer.updated
```

### Auditoría

Representa acciones relevantes desde el punto de vista operativo, administrativo o de seguridad.

Ejemplos:

```text
user.created_customer
admin.disabled_plugin
system.imported_legacy_bundle
user.denied_permission
```

Regla:

Los logs no reemplazan auditoría.
La auditoría no reemplaza eventos.
Los eventos no reemplazan logs técnicos.

Cada uno tiene propósito distinto.

## Logging estructurado

Los logs deberán ser estructurados, preferentemente en JSON.

Ejemplo conceptual:

```json
{
  "timestamp": "2026-06-20T15:30:00Z",
  "level": "INFO",
  "message": "Legacy import completed",
  "service": "migrator",
  "tenant_id": "tenant_001",
  "correlation_id": "uuid",
  "job_id": "job_001",
  "import_job_id": "import_001",
  "domain": "customers",
  "rows_inserted": 1500,
  "rows_rejected": 3
}
```

## Identificadores de trazabilidad

### `request_id`

Identifica una petición HTTP individual.

### `correlation_id`

Identifica un flujo completo que puede cruzar múltiples procesos.

Ejemplo:

```text
HTTP request
-> crea operación
-> emite evento
-> ejecuta listener
-> dispara job
-> genera auditoría
```

Todo ese flujo debe compartir el mismo `correlation_id`.

### `job_id`

Identifica un job async.

### `import_job_id`

Identifica una importación legacy.

Debe permitir rastrear:

```text
manifest.json
-> CSV
-> validación
-> importación
-> eventos
-> auditoría
```

## Alcance mínimo

Se deberán registrar al menos:

* requests relevantes;
* respuestas con error;
* jobs async;
* errores internos;
* validaciones fallidas importantes;
* eventos de negocio;
* cambios de permisos;
* instalación de plugins;
* activación de plugins;
* desactivación de plugins;
* fallos de plugins;
* importaciones legacy;
* rechazos en migración;
* autenticación;
* accesos denegados relevantes.

## Niveles de logs

Se usarán niveles estándar:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Reglas:

* `DEBUG`: diagnóstico local o desarrollo.
* `INFO`: operación normal relevante.
* `WARNING`: condición anómala no fatal.
* `ERROR`: fallo que impide completar una operación.
* `CRITICAL`: fallo grave del sistema o riesgo operativo.

## Datos sensibles

Los logs no deben exponer innecesariamente datos sensibles.

Evitar registrar:

* contraseñas;
* tokens;
* claves API;
* documentos completos si no es necesario;
* datos personales excesivos;
* payloads completos de clientes sin justificación.

Cuando sea necesario registrar contexto, usar valores parciales, IDs internos o datos anonimizados.

## Observabilidad en migraciones legacy

Cada importación legacy debe registrar:

* `import_job_id`;
* bundle usado;
* checksum;
* dominio;
* schema version;
* cantidad de filas leídas;
* cantidad de filas aceptadas;
* cantidad de filas rechazadas;
* warnings;
* errores;
* duración;
* usuario o proceso ejecutor.

Esto debe permitir explicar una migración después de ejecutada.

## Observabilidad en plugins

El runtime de plugins debe registrar:

* plugin descubierto;
* plugin instalado;
* plugin habilitado;
* plugin deshabilitado;
* plugin fallido;
* migración de plugin ejecutada;
* error de compatibilidad;
* dependencia faltante.

Cada evento relevante debe incluir:

* plugin_id;
* plugin_version;
* api_version;
* resultado;
* error si aplica.

## Observabilidad en permisos

El sistema debe poder registrar accesos denegados relevantes.

Ejemplo:

```text
user_001 intentó logistics.delivery.cancel sin permiso suficiente
```

No todos los denegados triviales deben saturar logs, pero los eventos relevantes de seguridad deben quedar trazables.

## Retención

La primera versión deberá definir una política mínima de retención.

Regla inicial:

* logs técnicos: retención configurable;
* auditoría: retención prolongada;
* eventos de negocio: retención según dominio;
* errores críticos: retención prioritaria;
* importaciones legacy: conservar historial suficiente para soporte y verificación.

La política exacta podrá ajustarse por despliegue.

## OpenTelemetry

OpenTelemetry no será obligatorio en la primera etapa.

Sin embargo, la estructura debe dejar espacio para incorporarlo después sin rediseñar el sistema.

Por eso, desde el inicio deberán existir conceptos compatibles:

* `trace_id`;
* `correlation_id`;
* contexto de ejecución;
* logs estructurados;
* separación entre servicios;
* instrumentación de jobs y requests.

## Testing

Las pruebas deberán cubrir:

* generación de `request_id`;
* propagación de `correlation_id`;
* auditoría de acciones críticas;
* registro de eventos;
* logs de errores importantes;
* trazabilidad de jobs;
* trazabilidad de importaciones legacy;
* aislamiento por tenant en registros observables.

## Consecuencias

* El core deberá manejar IDs de correlación y contexto de ejecución.
* Las rutas HTTP, jobs y procesos de migración deberán emitir logs consistentes.
* Los modelos de auditoría y eventos no podrán ser agregados improvisadamente después.
* La operación del sistema será más costosa de instrumentar al inicio, pero mucho más segura de sostener.
* El sistema será más fácil de depurar, auditar y operar.
* Los agentes de IA y programadores deberán respetar la trazabilidad al implementar nuevas features.
* La observabilidad será una ventaja estructural frente a SYSTUTOR Legacy.
