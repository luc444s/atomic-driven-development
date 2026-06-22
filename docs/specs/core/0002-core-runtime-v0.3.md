# SPEC 0002 - SYSTUTOR OSS Core v0.3 Runtime Operativo

## Estado

Aprobada

## Contexto

El core v0.2 ya resolvio persistencia, auth JWT, tenancy base, RBAC minimo, auditoria, event log, plugin registry y seed demo.

Todavia falta convertir esa base en un runtime operativo para plugins y eventos que permita evolucionar modulos desacoplados, jobs async y procesamiento controlado sin introducir logica de negocio en el kernel.

## Objetivo

Implementar `SYSTUTOR OSS Core v0.3` con:

- event bus interno funcional;
- outbox persistente basico;
- worker base con Dramatiq;
- runtime de plugins mas estricto y deterministico;
- SDK minimo para plugins;
- contracts publicos minimos para eventos, auditoria y manifiestos;
- pruebas del runtime y del dispatcher.

## No objetivos

Queda fuera de alcance en esta iteracion:

- logistica funcional;
- frontend completo;
- migrador legacy real;
- integracion con SQL Server;
- listeners de negocio complejos;
- RLS PostgreSQL;
- marketplace o instalacion remota de plugins.

## Alcance

Toca:

- `apps/api`
- `packages/sdk`
- `packages/contracts`
- `plugins/logistic`
- `docs/specs/core`
- `README.md`
- `.env.example`

## Reglas de negocio

- el kernel sigue siendo infraestructura, no negocio;
- todo evento relevante debe persistirse antes de ser despachado;
- el outbox no reemplaza `event_log`, lo complementa;
- los listeners deben ser explicitos, registrables y testeables;
- los errores de listeners no borran el evento original;
- los plugins deben registrarse via SDK publico y no via imports internos del kernel;
- la carga de plugins debe ser deterministica y respetar dependencias declaradas;
- todo evento de negocio asociado a empresa debe incluir `tenant_id` cuando aplique;
- no se crean stored procedures ni triggers de negocio.

## Permisos

Permisos base relevantes en esta iteracion:

- `core.plugin.read`
- `core.plugin.manage`
- `core.event.read`
- `core.audit.read`

No se agregan permisos de negocio reales nuevos en esta iteracion.

## Eventos

Eventos minimos esperados:

- `core.plugin.discovered`
- `core.plugin.enabled`
- `core.plugin.failed`
- `core.event.dispatched`
- `core.event.listener_failed`
- `logistics.delivery.created` como ejemplo declarado por plugin

## Datos

Entidades y contratos involucrados:

- `event_logs`
- `event_outbox`
- `plugin_registry`
- contract base de evento
- contract base de auditoria
- contract base de plugin manifest

## Migraciones

Esta iteracion requiere:

- migracion nueva para outbox y ajustes de plugin registry si aplica.

## Auditoria y observabilidad

Debe registrarse como minimo:

- emision de evento;
- error de listener;
- carga exitosa o fallida de plugin;
- `correlation_id`;
- `tenant_id` y `branch_id` cuando aplique;
- `retry_count` y `error_message` de outbox.

## Riesgos

- acoplar plugins al kernel en vez de al SDK;
- sobredisenar el event bus antes de necesitar mas casos;
- mezclar descubrimiento, instalacion y habilitacion de plugins sin trazabilidad;
- depender de Redis real para pruebas del dispatcher;
- romper compatibilidad futura de contratos publicos sin versionado claro.

## Criterios de aceptacion

- existe spec versionada para core v0.3;
- el event bus registra listeners y emite eventos persistiendo `event_log` y outbox;
- el outbox soporta `pending`, `processed` y `failed`;
- los fallos de listeners incrementan `retry_count` y guardan `error_message`;
- existe dispatcher reutilizable y testeable sin Redis real;
- Dramatiq queda configurado con Redis broker y tarea base documentada;
- el runtime de plugins valida manifiestos, resuelve dependencias y carga de forma deterministica;
- el plugin ejemplo declara permisos y eventos, pero no negocio real;
- existen contracts minimos en `packages/contracts` y SDK minimo en `packages/sdk`;
- Ruff, Pyright y Pytest pasan.

## Pruebas requeridas

- emision de evento;
- persistencia en `event_log`;
- outbox pendiente/procesado/fallido;
- listener ejecutado correctamente;
- listener fallido registrado;
- validacion de manifest;
- dependencia faltante de plugin;
- carga del plugin `logistics`;
- dispatcher o worker testeable sin Redis real.

## Notas para agentes

- leer `AGENTS.md`, ADRs y esta spec antes de tocar codigo;
- mantener plugins consumiendo SDK publico;
- no introducir logica de negocio en listeners del core;
- no agregar dependencias fuera del stack aprobado;
- mantener cambios pequenos, auditables y cubiertos por pruebas.
