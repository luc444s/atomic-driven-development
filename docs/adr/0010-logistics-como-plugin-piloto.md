# ADR 0010 - Logistics como Plugin Piloto

## Estado

Aceptado

## Contexto

SYSTUTOR OSS ya dispone de kernel, runtime persistente de plugins, RBAC, auditoria, event bus y shell frontend.

Hace falta validar esa arquitectura con un modulo de negocio real, no con un plugin placeholder.

El dominio prioritario del proyecto es `logistics`, y su complejidad operativa lo convierte en el mejor modulo piloto para probar:

- tablas propias de plugin;
- permisos propios de plugin;
- eventos de dominio;
- rutas backend montadas por runtime;
- rutas frontend registradas por runtime;
- auditoria y tenancy dentro de un plugin real.

## Decisión

`logistics` será el primer plugin de negocio real de SYSTUTOR OSS.

Reglas:

- vive en `plugins/logistics/`;
- usa el contrato estandar de plugins (`plugin.json`, `backend/`, `frontend/`, `migrations/`, `permissions/`, `events/`, `README.md`);
- su primera iteracion implementa el slice vertical de `cylinders + state machine + trace + dashboard basico`;
- rutas backend se montan bajo `/api/v1/plugins/logistics/...`;
- rutas frontend se registran via `frontend/register.ts`;
- el plugin es tenant-aware desde el inicio;
- toda accion relevante emite evento y auditoria;
- el kernel no absorbe logica de negocio de logistics.

## Consecuencias

- el runtime de plugins deja de validarse solo con scaffolds y empieza a validarse con un caso de negocio real;
- `logistics` define el patron de implementacion para futuros plugins como `inventory`, `billing` y `crm`;
- la primera entrega del plugin se enfoca en un corte pequeno y operativo, no en cubrir todo el dominio de una sola vez;
- nuevas capacidades del dominio se agregaran por iteraciones sobre el mismo plugin, manteniendo el contrato del runtime.
