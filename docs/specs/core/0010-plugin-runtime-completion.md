# SPEC 0010 - Plugin Runtime Completion

## Estado

Aprobada

## Contexto

El runtime de plugins de SYSTUTOR OSS ya cubre las bases del contrato y del lifecycle persistente:

- discovery de `plugin.json`;
- validacion estructural y de `api_version`;
- orden topologico de carga;
- `plugin_registry` persistente;
- migraciones por plugin con upgrade/downgrade/rollback;
- runtime frontend con `import.meta.glob`;
- `PluginRouteBoundary`;
- RBAC base en backend y frontend;
- event bus con `event_log`, `event_outbox` y dispatcher async.

Sin embargo, todavia existen gaps que impiden que un plugin de negocio real funcione de punta a punta:

- los routers backend registrados por plugins no se montan realmente en FastAPI;
- el SDK backend no expone una forma oficial de emitir eventos de plugin;
- los hooks `on_install`, `on_enable`, `on_disable` y `on_uninstall` no se ejecutan como transiciones reales;
- los permisos declarados por plugins no se sincronizan a la tabla `permissions`;
- los eventos `core.plugin.*` del lifecycle no se emiten;
- `task_dispatcher` llega como `None`;
- el frontend del plugin sigue importando internals de `apps/web/src`.

Estos gaps deben cerrarse antes de construir el plugin real `logistics` para no convertir el core en un runtime incompleto o acoplado.

## Objetivo

Completar el runtime de plugins del core para que un plugin instalable del monorepo pueda:

- instalarse y habilitarse con lifecycle real;
- exponer rutas backend reales bajo prefijo deterministico;
- emitir eventos de dominio via SDK oficial;
- registrar y consumir listeners via event bus oficial;
- sincronizar permisos declarados hacia RBAC del core;
- emitir eventos `core.plugin.*` del lifecycle;
- recibir un `task_dispatcher` minimo y testeable;
- registrar frontend via contrato publico, sin importar internals del shell.

## No objetivos

Queda fuera de alcance en esta iteracion:

- implementar el modulo real `logistics`;
- CRUDs de negocio (`deliveries`, `routes`, etc.);
- marketplace de plugins;
- instalacion remota desde internet;
- hot reload productivo del runtime;
- sandbox OS-level;
- aislamiento de seguridad fuerte entre plugins no confiables;
- billing/licenciamiento de plugins;
- permisos avanzados por tenant especificos del runtime de plugins.

## Alcance

Toca:

- `apps/api`;
- `apps/web`;
- `packages/sdk`;
- `plugins/`;
- `docs/specs/core`.

Puede actualizar pruebas backend y frontend existentes.

No debe introducir logica de negocio de `logistics` ni refactors amplios ajenos al runtime.

## Router Mounting

Los routers backend registrados por plugins deben montarse realmente en la app FastAPI.

Reglas:

- solo plugins `enabled` exponen rutas;
- plugins `disabled`, `failed` o `uninstalled` no exponen rutas;
- el prefijo es deterministico:

```text
/api/v1/plugins/<plugin_id>/...
```

- no se deben duplicar rutas al reconstruir el runtime;
- no se deben romper rutas core existentes;
- errores de mounting relevantes deben quedar logueados y auditables cuando aplique;
- el mounting no reemplaza auth/RBAC del core: cada router de plugin debe seguir usando dependencias del core.

## Event Emission SDK

`PluginContext` debe exponer un metodo oficial:

```python
ctx.publish_event(...)
```

Contrato minimo:

```python
ctx.publish_event(
    event_name: str,
    payload: dict,
    tenant_id: str | None = None,
    branch_id: str | None = None,
    actor_user_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
)
```

Reglas:

- `event_name` debe pertenecer al namespace del plugin;
- eventos fuera de namespace deben fallar explicitamente;
- la emision debe pasar por el event bus oficial;
- debe persistirse en `event_log` y `event_outbox`;
- debe conservar `tenant_id`, `branch_id` y `correlation_id`;
- debe poder probarse sin Redis real.

## Lifecycle Hooks

El runtime debe ejecutar hooks backend reales:

- `on_install`;
- `on_enable`;
- `on_disable`;
- `on_uninstall`.

Reglas:

- se ejecutan una vez por transicion valida;
- no se ejecutan si la transicion falla antes;
- reciben `PluginContext`;
- si un hook falla, el plugin debe quedar en `failed` o en estado seguro equivalente;
- el error debe persistirse en `plugin_registry.last_error`;
- el error debe ser auditable y trazable;
- los hooks deben poder probarse sin infraestructura externa real.

## Permission Sync

Los permisos declarados por un plugin deben sincronizarse a la tabla `permissions` al instalar o habilitar.

Reglas:

- no duplicar permisos existentes;
- no borrar permisos historicos automaticamente;
- validar namespace del plugin;
- si el modelo no soporta `source`, no agregar migracion solo por metadata decorativa;
- los permisos sincronizados deben quedar utilizables por RBAC del core.

Permisos globales del runtime:

- esta iteracion reutiliza `core.plugin.read` para lectura del runtime visible;
- `core.plugin.manage` sigue siendo el permiso de administracion.

No se introduce `core.plugin.runtime.read` en esta iteracion para evitar expandir permisos globales sin necesidad funcional adicional.

## Lifecycle Events

El core debe emitir como minimo:

- `core.plugin.installed`;
- `core.plugin.enabled`;
- `core.plugin.disabled`;
- `core.plugin.uninstalled`;
- `core.plugin.failed`.

Reglas:

- se persisten en `event_log`;
- generan `event_outbox`;
- incluyen `plugin_id`;
- incluyen `version`;
- incluyen estado anterior y nuevo estado cuando aplique;
- incluyen `error` cuando aplique;
- incluyen `correlation_id` si existe;
- deben convivir con auditoria administrativa, no reemplazarla.

## Task Dispatcher

`PluginContext.task_dispatcher` ya no debe llegar como `None`.

Se implementa un dispatcher minimo con contrato conceptual:

```python
ctx.task_dispatcher.enqueue(task_name: str, payload: dict) -> str
```

Reglas:

- usa Dramatiq cuando el broker esta disponible;
- es mockeable y testeable sin Redis real;
- si el broker no esta disponible, falla explicitamente con error controlado;
- no oculta errores criticos.

## Frontend SDK Minimo

El frontend del plugin no debe importar internals de `apps/web/src`.

Se crea un contrato publico minimo para frontend en `packages/sdk/frontend/` o equivalente dentro del monorepo.

Debe exponer como minimo:

- `PluginFrontendContext`;
- `PluginFrontendRegistration`;
- `PluginRoute`;
- `PluginNavigationItem`.

Puede exponer tipos adicionales minimos si el runtime actual los necesita, por ejemplo widgets.

Reglas:

- no rediseñar el runtime frontend completo;
- solo romper el acoplamiento mas peligroso;
- no introducir dependencias externas nuevas;
- el build frontend debe seguir pasando.

## Datos

Entidades y contratos afectados:

- `plugin_registry`;
- `permissions`;
- `event_logs`;
- `event_outbox`;
- `PluginContext`;
- `PluginRegistration`;
- runtime frontend y contratos de registro.

No se requiere nueva entidad de negocio.

## Migraciones

No se planifica migracion de schema obligatoria en esta iteracion.

Si durante la implementacion aparece una necesidad real de persistencia adicional no cubierta por el modelo actual, debe justificarse explicitamente.

## Auditoria y observabilidad

Debe quedar trazable como minimo:

- router mounting de plugins habilitados;
- install/enable/disable/uninstall;
- fallos de hooks;
- fallos de runtime que lleven a `failed`;
- sincronizacion de permisos;
- eventos `core.plugin.*`;
- `correlation_id` cuando exista;
- `plugin_id`, `state`, `last_error` y `migration_version` en puntos de fallo relevantes.

## Riesgos

- duplicar rutas al reconstruir el runtime;
- dejar rutas expuestas para plugins deshabilitados;
- ejecutar hooks mas de una vez por transicion;
- permitir eventos fuera del namespace del plugin;
- introducir acoplamiento nuevo entre plugin frontend y shell;
- romper bootstrap si el runtime intenta usar infraestructura no disponible;
- ocultar errores reales tras dispatchers noop silenciosos.

## Criterios de aceptacion

- existe `docs/specs/core/0010-plugin-runtime-completion.md`;
- los routers backend de plugins enabled se montan realmente en FastAPI;
- plugins `disabled` y `failed` no exponen rutas;
- `PluginContext` permite emitir eventos via `publish_event`;
- los eventos emitidos por plugins quedan en `event_log` y `event_outbox`;
- los hooks `on_install`, `on_enable`, `on_disable` y `on_uninstall` se ejecutan;
- errores de hooks quedan persistidos en `plugin_registry.last_error`;
- permisos declarados por plugins se sincronizan a la tabla `permissions`;
- el core emite `core.plugin.installed`, `core.plugin.enabled`, `core.plugin.disabled`, `core.plugin.uninstalled` y `core.plugin.failed`;
- `task_dispatcher` ya no es `None`;
- el plugin frontend deja de importar internals de `apps/web/src`;
- existe SDK frontend minimo utilizable por el runtime actual;
- existe test backend end-to-end del ciclo completo del plugin;
- pruebas backend relevantes y build frontend siguen pasando.

## Pruebas requeridas

Backend runtime:

- router de plugin enabled responde;
- router de plugin disabled no responde;
- plugin failed no expone rutas;
- core `health` y `ready` siguen funcionando;
- plugin no puede bypassar auth/RBAC al usar dependencias del core.

Backend eventos:

- plugin emite evento valido;
- evento queda en `event_log`;
- outbox se crea;
- evento fuera de namespace falla;
- `tenant_id` y `correlation_id` se conservan;
- listener de plugin consume evento registrado.

Backend lifecycle:

- `on_install` se ejecuta al instalar;
- `on_enable` se ejecuta al habilitar;
- `on_disable` se ejecuta al deshabilitar;
- `on_uninstall` se ejecuta al desinstalar;
- hook fallido registra error y deja estado seguro;
- lifecycle events `core.plugin.*` se emiten.

Backend permisos:

- permisos del plugin se sincronizan a tabla `permissions`;
- re-instalar o re-habilitar no duplica;
- namespace invalido falla;
- RBAC puede usar permiso sincronizado.

Backend end-to-end obligatorio:

1. descubrir plugin de prueba;
2. instalar plugin;
3. aplicar migraciones si existen;
4. sincronizar permisos;
5. ejecutar `on_install`;
6. habilitar plugin;
7. ejecutar `on_enable`;
8. montar router;
9. llamar endpoint del router;
10. emitir evento desde plugin;
11. validar `event_log`;
12. deshabilitar plugin;
13. ejecutar `on_disable`;
14. validar que el router deja de estar disponible;
15. desinstalar plugin;
16. ejecutar `on_uninstall`.

Frontend:

- plugin frontend compila usando el SDK publico;
- runtime carga registro de plugin;
- plugin enabled muestra navigation;
- plugin disabled no muestra navigation.

## Gaps fuera de alcance

Siguen fuera de alcance despues de esta spec:

- plugin `logistics` real y su dominio;
- carga dinamica remota de plugins;
- aislamiento fuerte entre plugins de terceros;
- marketplace/catalogo de plugins;
- politicas avanzadas de multi-tenant por plugin;
- estrategia final de versionado externo para plugins fuera del monorepo.

## Notas para agentes

- mantener el kernel pequeno y centrado en infraestructura del runtime;
- no mover logica de negocio de plugins al core;
- preferir cambios pequenos y testeables sobre refactors amplios;
- reutilizar el contrato de `0006` y el runtime persistente de `0007` como base;
- si durante la implementacion aparece una necesidad arquitectonica duradera no prevista, proponer ADR en lugar de improvisar atajos permanentes.
