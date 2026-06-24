# SPEC 0004 - Core v0.3.1 Active Tenant Isolation

## Estado

Aprobada

## Contexto

El core v0.3 ya dispone de auth JWT, tenancy estructural, RBAC minimo, auditoria, event log, outbox y runtime base de plugins.

Sin embargo, el aislamiento multi-tenant sigue siendo mayormente estructural:

- existen `tenant_id` y `branch_id` en entidades clave;
- el JWT incluye claims de tenant y branch;
- `request.state.current_tenant_id` ya existe;
- pero las queries tenant-scoped no se fuerzan de forma centralizada;
- la resolucion de permisos no valida con suficiente fuerza el tenant activo;
- no existe una abstraccion clara y reutilizable de tenant context.

Esto deja riesgo de acceso ambiguo o cruce accidental entre tenants, especialmente en RBAC, helpers internos y logs operativos.

## Objetivo

Implementar `Core v0.3.1 - Active Tenant Isolation` a nivel aplicacion para que:

- el backend resuelva un tenant context explicito por request autenticado;
- las queries tenant-scoped se centralicen y sean testeables;
- RBAC valide permisos dentro del tenant correcto;
- auditoria y eventos con actor tenant-scoped registren el tenant correcto;
- el frontend shell actual siga funcionando sin rediseño.

## No objetivos

Queda fuera de alcance en esta iteracion:

- RLS de PostgreSQL;
- multi-schema por tenant;
- nuevos modulos de negocio;
- logistica funcional;
- migracion legacy;
- stored procedures;
- triggers;
- refactor masivo del backend o frontend;
- rediseño del plugin runtime.

## Alcance

Toca:

- `apps/api`
- `docs/specs/core`
- `README.md`
- `pyproject.toml`

El frontend solo se ajusta si algun contrato de auth cambia de forma estrictamente necesaria.

## Entidades globales

Se consideran globales en esta iteracion:

- `Tenant`: catalogo raiz de tenants;
- `Permission`: catalogo global de permisos declarativos;
- `PluginRegistry`: catalogo tecnico global de plugins instalados/habilitados;
- endpoints globales de salud y metadata tecnica:
  - `GET /api/v1/system/health`
  - `GET /api/v1/system/ready`
  - aliases de health/ready;
- metadata tecnica no sensible del sistema.

`PluginRegistry` se mantiene global porque representa estado tecnico de la plataforma, no datos operativos de negocio por tenant.

## Entidades tenant-scoped

Se consideran tenant-scoped en esta iteracion:

- `Branch`
- `User`
- `Role`
- `UserRole`
- `RolePermission` por herencia del `Role`
- `AuditLog` cuando la accion pertenece a un tenant
- `EventLog` cuando el evento pertenece a un tenant
- `EventOutbox` cuando el evento pertenece a un tenant

`Permission` no es tenant-scoped en el modelo actual, pero su uso debe resolverse a traves de roles del tenant correcto.

## Reglas de aislamiento

- un usuario autenticado opera dentro de su `tenant_id` efectivo;
- un usuario de Tenant A no puede leer, modificar, usar permisos ni roles de Tenant B;
- no se debe consultar una entidad tenant-scoped sin filtrar por `tenant_id` de forma explicita o via helper centralizado;
- `branch_id` solo es valido si pertenece al mismo tenant del usuario o de la accion registrada;
- claims de JWT (`tenant_id`, `branch_id`, `sub`, `email`, `is_superadmin`) deben validarse contra el usuario persistido antes de construir contexto autenticado;
- si el token esta manipulado o sus claims no coinciden con el usuario persistido, la request protegida falla;
- las queries globales deben ser explicitas y justificadas;
- no se introduce RLS en esta fase.

## Reglas de permisos

- la resolucion de permisos debe ser tenant-aware;
- `require_permission(...)` debe validar sobre el tenant del usuario autenticado;
- un `UserRole` que apunte a un `Role` de otro tenant no debe otorgar permisos efectivos;
- un permiso global del catalogo no otorga acceso por si solo: necesita estar asociado a un rol del tenant correcto;
- `is_superadmin` conserva su semantica actual solo si ya existe en el modelo; su uso debe seguir siendo explicito y auditado.

## Tenant Context

Debe existir una abstraccion reusable de tenant context con al menos:

- `current_tenant_id`
- `current_branch_id`
- `current_user_id`
- `current_permissions`
- `is_superadmin`

El tenant context debe poder consumirse desde dependencies, endpoints, servicios, auditoria, eventos y helpers tenant-scoped.

## Auditoria

Toda auditoria relevante debe registrar:

- `tenant_id`
- `branch_id` si aplica;
- `actor_user_id` si aplica;
- `action`
- `result`
- `entity_type`
- `entity_id`
- `correlation_id` si existe;
- `request_id` cuando venga de HTTP.

Los accesos denegados relevantes por permisos o mismatch de tenant deben quedar auditados cuando ya exista un actor autenticado resoluble.

## Eventos

Todo evento asociado a tenant debe registrar:

- `tenant_id`
- `branch_id` si aplica;
- `actor_user_id` si aplica;
- `correlation_id`
- `causation_id` si aplica.

El outbox debe conservar el `tenant_id` del evento persistido.

## Impacto en frontend

- no se rehace el frontend shell;
- `login`, `/me`, layout, dashboard, logout y pantalla de plugins deben seguir funcionando;
- si `/me` conserva el mismo contrato, no se requiere cambio frontend;
- si cambia el contrato, el ajuste debe ser minimo y acotado al cliente auth.

## Migraciones

No requiere migracion de base de datos obligatoria para esta iteracion si el aislamiento activo puede imponerse desde la capa de aplicacion con helpers, dependencies y validaciones centralizadas.

## Riesgos

- dejar helpers directos sin tenant filter en nuevas rutas futuras;
- asumir que `Permission` global implica autorizacion global;
- aceptar tokens con claims inconsistentes respecto al usuario persistido;
- registrar auditoria o eventos con `tenant_id` nulo cuando existe actor tenant-scoped;
- endurecer auth sin cubrir regresiones del frontend shell.

## Criterios de aceptacion

- existe esta spec versionada;
- existe tenant context reusable y testeable;
- `require_permission` resuelve permisos dentro del tenant correcto;
- las queries tenant-scoped relevantes usan helpers o servicios centralizados;
- un usuario de Tenant A no puede resolver datos tenant-scoped de Tenant B;
- `branch_id` cruzado entre tenants se rechaza por helpers o validaciones activas;
- `audit_log` registra `tenant_id` correcto para acciones tenant-scoped;
- `event_log` y `event_outbox` registran `tenant_id` correcto para eventos tenant-scoped;
- `health` y `ready` siguen siendo globales;
- `/auth/me` devuelve tenant y branch correctos del usuario autenticado;
- tokens manipulados o con tenant inconsistente fallan;
- pruebas nuevas y existentes pasan;
- `ruff check`, `pyright`, `pytest` y `pnpm build` pasan en entorno compatible.

## Pruebas obligatorias

- usuario de Tenant A no accede a usuario de Tenant B mediante helper tenant-scoped;
- permisos no cruzan tenants;
- permisos correctos dentro del mismo tenant;
- branch no cruza tenant;
- `audit_log` registra tenant correcto;
- `event_log` registra tenant correcto;
- `event_outbox` registra tenant correcto;
- endpoints globales `health` y `ready` siguen funcionando sin tenant;
- `/auth/me` devuelve tenant y branch correctos;
- token manipulado o tenant inexistente falla;
- usuario desactivado no accede;
- `PluginRegistry` se documenta y prueba como global tecnico sin exponer datos tenant-scoped;
- las pruebas existentes de regresion siguen pasando.

## Checklist manual

1. Levantar backend.
2. Levantar frontend.
3. Iniciar sesion con usuario demo.
4. Verificar que `/me` muestra tenant correcto.
5. Verificar dashboard.
6. Hacer logout.
7. Intentar entrar a `/app` sin token.
8. Verificar redireccion a login.
9. Probar token invalido.
10. Confirmar que endpoints globales `health` y `ready` siguen funcionando.

## Notas para agentes

- mantener cambios pequenos y centrados en auth, tenancy, permisos, auditoria y eventos;
- no introducir RLS ni cambios grandes de arquitectura;
- no rehacer frontend;
- preferir servicios y helpers reutilizables antes que duplicar filtros manuales;
- documentar explicitamente cualquier entidad global mantenida por decision tecnica.
