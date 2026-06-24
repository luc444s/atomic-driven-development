# SPEC 0007 - Persistent Plugin Runtime

## Estado

Aprobada

## Contexto

El core ya dispone de un runtime base de plugins, contrato de manifest, validacion estructural y carga backend deterministica.

Tambien existe un `plugin_registry` inicial y un shell frontend capaz de listar plugins declarados.

Sin embargo, el runtime actual todavia tiene limitaciones importantes:

- el lifecycle no queda persistido de forma suficiente;
- la habilitacion o deshabilitacion no sobrevive reinicios de la app;
- las migraciones por plugin no existen como mecanismo operativo;
- el frontend no consume un runtime persistente para rutas, sidebar y widgets;
- la administracion del runtime todavia no tiene endpoints de debug operables.

Esto impide que los plugins se comporten como modulos realmente instalables, trazables y gobernables desde el core.

## Objetivo

Implementar `Core v0.3.3` con runtime de plugins persistente, migrable y utilizable desde frontend.

Debe incluir:

- plugin registry persistente con lifecycle formal;
- engine de migraciones por plugin con version tracking;
- reconstruccion del runtime tras reinicios usando estado persistido;
- runtime frontend para rutas, sidebar y widgets;
- endpoints admin de debug para operar el runtime.

## No objetivos

Queda fuera de alcance en esta iteracion:

- marketplace de plugins;
- instalacion remota desde internet;
- sandbox OS-level;
- distribucion multi-node del runtime;
- modulos de negocio grandes del piloto `logistics`.

## Alcance

Toca:

- `apps/api`
- `apps/web`
- `plugins/`
- `docs/specs/core`
- `README.md` si cambia el flujo operativo

## Reglas de negocio

- el lifecycle persistido debe soportar `discovered`, `validated`, `installed`, `enabled`, `disabled`, `failed`, `uninstalled`;
- un plugin `disabled` no debe exponerse en runtime frontend;
- un plugin `failed` no debe registrar rutas ni handlers operativos;
- el estado persistido debe sobrevivir reinicios del backend;
- las migraciones por plugin deben ejecutarse en orden deterministico;
- una migracion fallida debe hacer rollback y dejar trazabilidad del error;
- `enable` no debe bypassar validacion, dependencias ni migraciones;
- el frontend no debe renderizar elementos de plugin si el plugin no esta `enabled` o si faltan permisos;
- el core sigue siendo la autoridad de auth, tenancy y RBAC.

## Permisos

Permisos implicados:

- `core.plugin.read`
- `core.plugin.manage`

No se agregan permisos globales nuevos fuera del namespace aprobado.

## Eventos

Eventos minimos relevantes:

- `core.plugin.installed`
- `core.plugin.enabled`
- `core.plugin.disabled`
- `core.plugin.failed`
- `core.plugin.migrated`

## Datos

El registry persistente debe guardar como minimo:

- `plugin_id`
- `version`
- `api_version`
- `state`
- `installed_at`
- `enabled_at`
- `disabled_at`
- `last_error`
- `migration_version`

Tambien debe conservar metadata util del manifest ya existente:

- `backend_entrypoint`
- `frontend_entrypoint`
- `requires`
- `permissions`
- `events`
- `description`

## Migraciones

Esta iteracion requiere:

- migracion del schema de `plugin_registry`;
- engine de migraciones por plugin;
- soporte de `upgrade`, `downgrade`, `rollback` e idempotencia.

Ubicacion de migraciones por plugin:

```text
plugins/<plugin>/migrations/
```

## Auditoria y observabilidad

Debe quedar trazable como minimo:

- descubrimiento y validacion de plugins;
- instalacion;
- habilitacion;
- deshabilitacion;
- desinstalacion logica;
- migracion aplicada;
- rollback o downgrade;
- fallos de carga o migracion;
- `correlation_id` cuando aplique;
- estado persistido y ultimo error.

## Riesgos

- acoplar el frontend a un runtime demasiado especifico del plugin piloto;
- romper bootstrap del backend si el registry persistente depende de una DB no migrada;
- aplicar migraciones parciales sin rollback adecuado;
- habilitar plugins sin respetar dependencias o permisos;
- exponer rutas frontend de plugins deshabilitados por incoherencia entre backend y frontend.

## Criterios de aceptacion

- el lifecycle de plugins queda persistido en DB;
- el estado de un plugin sobrevive reinicios del backend;
- existe engine de migraciones por plugin con tracking de version;
- `upgrade`, `downgrade` y `rollback` funcionan y son idempotentes cuando corresponde;
- un plugin fallido queda en `failed` y no se expone operativamente;
- existen endpoints admin de debug para instalar, habilitar, deshabilitar y migrar plugins;
- el frontend registra rutas, sidebar y widgets desde runtime frontend;
- el frontend oculta plugins deshabilitados;
- el frontend aplica rendering sensible a permisos;
- Ruff, Pyright, Pytest, build frontend y tests frontend pasan.

## Pruebas requeridas

Backend registry:

- install;
- enable;
- disable;
- failed plugin;
- persistence after reboot.

Backend migrations:

- apply migration;
- ordering;
- rollback on failure;
- downgrade;
- idempotency.

Frontend runtime:

- route registration;
- nav registration;
- permission protection;
- disabled plugin hidden;
- enabled plugin visible.

## Notas para agentes

- mantener cambios pequenos y centrados en runtime, migraciones y shell frontend;
- no mover logica de negocio al core;
- no introducir marketplace ni instalacion remota;
- reutilizar el contrato `0006` como base del runtime persistente;
- si una limitacion del plugin piloto obliga a cambiar el contrato, actualizar spec o proponer ADR nuevo.
