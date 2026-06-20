# ADR 0005 - Event Bus y Auditoría

## Estado

Aceptado

## Contexto

SYSTUTOR OSS necesita desacoplar módulos y construir trazabilidad fuerte desde el inicio.

La plataforma no debe depender de llamadas directas entre dominios cuando un evento de negocio puede expresar mejor la transición de estado.

SYSTUTOR OSS también debe evitar lógica oculta. Por eso, los eventos, sus consumidores y sus efectos deben ser observables, auditables y testeables.

## Decisión

SYSTUTOR OSS usará un Event Bus interno como mecanismo principal de comunicación entre módulos cuando el caso sea asincrónico, transversal o desacoplable.

Toda acción importante deberá generar auditoría.

## Principios

* Los módulos pueden emitir eventos de dominio.
* Otros módulos pueden suscribirse a esos eventos.
* Los eventos relevantes deben quedar registrados.
* La auditoría debe registrar actor, contexto, acción y resultado.
* No se debe esconder lógica crítica en listeners opacos sin trazabilidad.
* La auditoría aplica tanto a acciones humanas como a procesos automáticos relevantes.
* Los eventos deben ser explícitos, nombrados, documentados y testeables.
* El Event Bus no debe convertirse en una caja negra.

## Diferencia entre Event Log y Audit Log

### `event_log`

Registra eventos ocurridos dentro del sistema.

Ejemplos:

```text
logistics.delivery.created
logistics.delivery.completed
inventory.stock.adjusted
billing.invoice.generated
```

Sirve para:

* trazabilidad técnica;
* integración entre módulos;
* debugging;
* reconstrucción de flujos;
* automatizaciones;
* ejecución de listeners.

### `audit_log`

Registra acciones relevantes desde el punto de vista operativo, humano o administrativo.

Ejemplos:

```text
user.login
user.created_customer
admin.enabled_plugin
system.imported_legacy_file
```

Sirve para:

* auditoría empresarial;
* seguridad;
* cumplimiento;
* revisión de operaciones;
* análisis de responsabilidades.

Un evento puede generar auditoría, pero no todo evento es necesariamente una auditoría.

## Estructura mínima de un evento

Todo evento registrado debe incluir como mínimo:

```json
{
  "event_id": "uuid",
  "event_name": "logistics.delivery.created",
  "version": "1",
  "occurred_at": "2026-06-20T10:30:00Z",
  "module": "logistics",
  "tenant_id": "tenant_001",
  "branch_id": "branch_001",
  "actor_type": "user",
  "actor_id": "user_001",
  "entity_type": "delivery",
  "entity_id": "delivery_001",
  "correlation_id": "uuid",
  "causation_id": "uuid",
  "payload": {},
  "metadata": {}
}
```

## Campos importantes

### `event_id`

Identificador único del evento.

Debe permitir idempotencia.

### `event_name`

Nombre del evento.

Debe seguir formato:

```text
<module>.<resource>.<past_action>
```

Ejemplos:

```text
logistics.delivery.created
logistics.delivery.completed
inventory.stock.adjusted
customers.customer.updated
```

### `version`

Versión del contrato del evento.

Permite evolucionar payloads sin romper consumidores.

### `correlation_id`

Identifica el flujo completo.

Ejemplo:

Una importación legacy puede generar múltiples eventos, pero todos comparten el mismo `correlation_id`.

### `causation_id`

Identifica el evento o acción que causó este evento.

Permite reconstruir cadenas de causa y efecto.

### `payload`

Contiene datos necesarios para los consumidores.

No debe convertirse en un dump completo de la base de datos.

### `metadata`

Puede incluir información técnica adicional:

* origen;
* IP;
* user agent;
* proceso;
* job_id;
* import_id.

## Estructura mínima de auditoría

Todo registro de auditoría debe incluir:

```json
{
  "audit_id": "uuid",
  "occurred_at": "2026-06-20T10:30:00Z",
  "tenant_id": "tenant_001",
  "branch_id": "branch_001",
  "actor_type": "user",
  "actor_id": "user_001",
  "module": "logistics",
  "action": "delivery.create",
  "entity_type": "delivery",
  "entity_id": "delivery_001",
  "result": "success",
  "correlation_id": "uuid",
  "details": {}
}
```

## Resultados posibles de auditoría

```text
success
failure
denied
conflict
partial
```

## Reglas de emisión de eventos

* No emitir eventos antes de confirmar una transacción crítica.
* No emitir eventos que representen estados no persistidos.
* No usar eventos para esconder reglas de negocio críticas.
* No publicar eventos ambiguos como `updated` sin contexto suficiente cuando el cambio sea importante.
* Todo evento consumido por otro módulo debe estar documentado.
* Todo evento crítico debe tener pruebas.

## Outbox Pattern

Para evitar eventos inconsistentes, SYSTUTOR OSS deberá favorecer un patrón tipo Outbox para eventos persistentes.

Flujo esperado:

```text
operación de negocio
-> persistencia en PostgreSQL
-> registro en outbox/event_log
-> commit
-> worker procesa evento
-> listeners ejecutan acciones
```

Esto evita que el sistema emita eventos de operaciones que luego fallan.

## Manejo de listeners

Los listeners deben ser explícitos y registrados por el runtime.

Reglas:

* un listener debe declarar qué evento consume;
* un listener debe ser idempotente cuando sea posible;
* un error en un listener no debe borrar el evento original;
* los fallos deben registrarse;
* los retries deben ser controlados;
* un listener no debe generar efectos secundarios invisibles.

## Idempotencia

Los eventos deben poder procesarse más de una vez sin duplicar efectos críticos.

Ejemplo:

Si `logistics.delivery.completed` se procesa dos veces, no debe duplicar movimiento de inventario ni auditoría de negocio.

## Comunicación entre módulos

Permitido:

```text
plugin A -> event bus -> plugin B
plugin A -> contrato público -> plugin B
plugin A -> SDK público -> core
```

Evitar:

```text
plugin A -> import interno directo -> plugin B
plugin A -> update directo en tablas internas de plugin B
plugin A -> listener oculto sin registro
```

## Eventos y permisos

La emisión de eventos no reemplaza las validaciones de permisos.

Antes de ejecutar una acción que emite eventos, el sistema debe validar autorización.

## Eventos y tenancy

Todo evento de negocio asociado a una empresa debe incluir `tenant_id`.

Si aplica, también debe incluir:

* `branch_id`;
* `warehouse_id`;
* `user_id`;
* `source_system`.

## Eventos legacy

Los eventos generados por migración legacy deben indicar origen.

Ejemplo:

```json
{
  "event_name": "legacy.customer.imported",
  "source_system": "systutor_legacy",
  "import_job_id": "import_001"
}
```

Estos eventos deben poder rastrearse hasta el archivo CSV y `manifest.json` que los originó.

## Alcance mínimo del registro

El sistema debe registrar:

* quién ejecutó la acción;
* cuándo ocurrió;
* sobre qué entidad ocurrió;
* qué módulo la ejecutó;
* qué evento se emitió;
* cuál fue el resultado;
* desde qué tenant ocurrió;
* desde qué sucursal ocurrió cuando aplique;
* qué proceso automático participó cuando aplique.

## Testing

El testing deberá cubrir:

* emisión de eventos;
* persistencia en `event_log`;
* generación de auditoría;
* consumo de eventos relevantes;
* idempotencia;
* manejo de errores en listeners;
* rechazo por permisos;
* aislamiento por tenant.

## Consecuencias

* El core necesitará componentes explícitos para `event_log`, `audit_log` y outbox.
* Los plugins deberán declarar sus eventos y emitirlos de forma consistente.
* Parte del comportamiento de negocio se articulará como flujo observable, no como acoplamiento directo.
* El testing deberá cubrir emisión, consumo y auditoría de eventos relevantes.
* Los listeners deberán ser visibles y registrados por el runtime.
* La auditoría será una capacidad base del sistema, no un agregado posterior.
* Los eventos ayudarán a integrar módulos, IA, automatizaciones, migradores y observabilidad.
