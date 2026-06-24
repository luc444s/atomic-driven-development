# SPEC 0005 - Core v0.3.2 Tenant Scoped Core APIs

## Estado

Aprobada

## Contexto

El core ya dispone de persistencia, auth JWT, RBAC minimo, auditoria, event log, outbox, runtime de plugins y aislamiento activo por tenant en capa de aplicacion.

Todavia falta exponer APIs REST del core que permitan operar esas entidades de forma segura sin romper el aislamiento multi-tenant ya implementado.

Sin estas APIs, el core tiene capacidades persistentes pero todavia no ofrece una superficie funcional suficiente para administracion tenant-scoped de usuarios, roles y sucursales.

## Objetivo

Implementar `Core v0.3.2 - Tenant Scoped Core APIs` con endpoints REST seguros para:

- `users` tenant-scoped;
- `roles` tenant-scoped;
- asignacion de roles a usuarios dentro del mismo tenant;
- `branches` tenant-scoped;
- catalogo global de `permissions` en solo lectura;
- `audit_logs` tenant-scoped en solo lectura;
- catalogo tecnico global de `plugin_registry` en solo lectura.

## No objetivos

Queda fuera de alcance en esta iteracion:

- frontend nuevo o refactor del shell existente;
- logistica funcional;
- runtime de plugins nuevo;
- migracion legacy;
- RLS de PostgreSQL;
- event log API publica;
- stored procedures;
- triggers;
- refactor masivo del kernel.

## Alcance

Toca:

- `apps/api`
- `docs/specs/core`
- `README.md` solo si hiciera falta documentacion menor asociada

No deberia requerir cambios frontend mientras se conserve el contrato actual de auth y sistema.

## Reglas de negocio

- toda query tenant-scoped debe usar `TenantContext` o helpers centralizados con `tenant_id` explicito;
- un usuario de Tenant A no puede ver ni modificar entidades tenant-scoped de Tenant B;
- no se puede asignar a un usuario un rol de otro tenant;
- no se puede asociar a un usuario una branch de otro tenant;
- `Permission` sigue siendo catalogo global declarativo;
- `Permission` no autoriza por si sola: solo mediante roles validos del tenant correcto;
- `PluginRegistry` sigue siendo catalogo tecnico global;
- `health` y `ready` siguen siendo globales;
- toda accion relevante de escritura del core debe ser auditable.

## Permisos

Permisos esperados en esta iteracion:

- `core.users.read`
- `core.users.create`
- `core.users.update`
- `core.users.delete`
- `core.roles.read`
- `core.roles.manage`
- `core.branches.manage`
- `core.audit.read`
- `core.permission.manage` para catalogo global read-only de permisos
- `core.plugin.read` para catalogo tecnico global de plugins

No se agregan permisos de negocio de plugins o modulos verticales.

## Eventos

No se agregan eventos nuevos obligatorios del sistema en esta iteracion.

Las escrituras del core deben seguir siendo compatibles con el modelo de auditoria y trazabilidad existente.

## Datos

Entidades involucradas:

- `users`
- `roles`
- `user_roles`
- `branches`
- `permissions`
- `audit_logs`
- `plugin_registry`

Entidades globales explicitamente mantenidas:

- `tenants`
- `permissions`
- `plugin_registry`

Entidades tenant-scoped explicitamente usadas por API:

- `users`
- `roles`
- `user_roles`
- `branches`
- `audit_logs`

## APIs esperadas

### Users

- `GET /api/v1/users`
- `POST /api/v1/users`
- `GET /api/v1/users/{user_id}`
- `PATCH /api/v1/users/{user_id}`
- `DELETE /api/v1/users/{user_id}`

### Roles

- `GET /api/v1/roles`
- `POST /api/v1/roles`
- `GET /api/v1/roles/{role_id}`
- `PATCH /api/v1/roles/{role_id}`
- `DELETE /api/v1/roles/{role_id}`

### Role assignments

- `POST /api/v1/users/{user_id}/roles`
- `DELETE /api/v1/users/{user_id}/roles/{role_id}`

### Branches

- `GET /api/v1/branches`
- `POST /api/v1/branches`
- `GET /api/v1/branches/{branch_id}`
- `PATCH /api/v1/branches/{branch_id}`
- `DELETE /api/v1/branches/{branch_id}`

### Permissions

- `GET /api/v1/permissions`
- `GET /api/v1/permissions/{permission_id}`

### Audit logs

- `GET /api/v1/audit-logs`
- `GET /api/v1/audit-logs/{audit_log_id}`

### Plugin registry

- `GET /api/v1/plugin-registry`
- `GET /api/v1/plugin-registry/{plugin_id}`

## Migraciones

No requiere migracion de base de datos obligatoria en esta iteracion.

## Auditoría y observabilidad

Debe registrarse como minimo:

- creacion, actualizacion y eliminacion de `users`;
- creacion, actualizacion y eliminacion de `roles`;
- asignacion y remocion de roles;
- creacion, actualizacion y eliminacion de `branches`;
- accesos denegados relevantes ya cubiertos por `require_permission`;
- `tenant_id`, `branch_id`, `actor_user_id`, `correlation_id` y `request_id` cuando aplique.

No deben registrarse secretos ni passwords en logs o auditoria.

## Riesgos

- introducir queries directas sin filtro tenant en handlers nuevos;
- borrar entidades con referencias y devolver errores de DB no controlados;
- mezclar catalogos globales con datos tenant-scoped;
- romper el frontend shell por cambios innecesarios de auth o system;
- duplicar logica de tenant filter en muchos handlers en lugar de centralizarla.

## Criterios de aceptación

- existe esta spec versionada;
- existen APIs REST para `users`, `roles`, `role assignments`, `branches`, `permissions`, `audit_logs` y `plugin_registry`;
- las entidades tenant-scoped no se consultan sin filtro de tenant;
- Tenant A no puede ver `users` de Tenant B;
- Tenant A no puede asignar roles de Tenant B;
- un branch de otro tenant no puede asociarse a un usuario de Tenant A;
- `audit_logs` solo exponen registros del tenant autenticado;
- `permissions` siguen siendo catalogo global read-only;
- `plugin_registry` sigue siendo catalogo tecnico global read-only;
- tests nuevos y existentes pasan;
- `ruff check`, `pyright`, `pytest` y `pnpm build` pasan.

## Pruebas requeridas

- Tenant A no ve users de Tenant B;
- Tenant A no asigna roles de Tenant B;
- branch cross-tenant falla;
- audit cross-tenant falla;
- permission checks funcionan en endpoints nuevos;
- tests previos siguen pasando.

## Notas para agentes

- no rehacer frontend;
- no introducir logica de negocio nueva en el kernel;
- preferir helpers y servicios tenant-scoped reusables;
- mantener `permissions` y `plugin_registry` como catalogos globales explicitamente documentados;
- no tocar runtime de plugins ni migracion legacy en esta iteracion.
