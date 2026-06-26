# SPEC 0009 - Core Management APIs

## Estado

Propuesta

## Contexto

SYSTUTOR OSS ya dispone de:

- ADR 0001-0009 aprobados;
- core backend persistente;
- auth JWT;
- active tenant isolation;
- RBAC;
- audit log;
- event log;
- outbox;
- event bus;
- Dramatiq worker;
- plugin runtime completo;
- plugin lifecycle persistente;
- plugin migrations;
- router mounting real para plugins;
- `ctx.publish_event(...)` en `PluginContext`;
- frontend shell v0.2 tenant-aware.

En frontend ya existe un shell funcional con sidebar y rutas base para:

- dashboard;
- plugins;
- settings:
  - users;
  - roles;
  - branches.

Sin embargo, la capa de administracion del core sigue incompleta:

- las vistas de settings son placeholder;
- plugins no tiene management administrativo real desde UI;
- las APIs existentes no cubren el contrato operativo minimo esperado para users, roles, branches y plugin management bajo `/api/v1/core/...`.

## Objetivo

Implementar la capa minima de administracion del core para que el sistema sea operable antes del primer plugin de negocio real.

Debe incluir:

- APIs backend tenant-aware para `users`, `roles`, `branches` y `plugins`;
- validacion RBAC consistente;
- auditoria y eventos minimos para operaciones administrativas;
- frontend minimal funcional para settings y plugins management.

## No objetivos

Queda fuera de alcance:

- `logistics` real;
- inventory;
- CRM;
- billing;
- analytics;
- reportes avanzados;
- marketplace;
- SaaS onboarding;
- SSO;
- MFA;
- multi-tenant switching;
- import/export CSV;
- busqueda avanzada;
- paginacion compleja;
- rediseño visual grande;
- nuevas dependencias sin justificacion.

## Alcance

Puede modificar:

- `apps/api`;
- `apps/web`;
- `apps/api/tests`;
- `apps/web` tests;
- `docs/specs/core`.

No debe romper:

- plugin runtime existente;
- frontend shell actual;
- aislamiento tenant-aware;
- RBAC actual.

## Arquitectura backend

La superficie nueva debe organizarse en routers finos bajo:

```text
apps/api/app/api/v1/core/
├── users.py
├── roles.py
├── branches.py
└── plugins.py
```

La logica debe seguir:

```text
router
-> service
-> repository/helper tenant-aware
```

Reglas:

- no poner logica pesada en routers;
- no usar queries tenant-scoped sin filtro por tenant;
- reusar helpers y servicios existentes del kernel cuando sea posible.

## Users Management

Endpoints:

```text
GET    /api/v1/core/users
GET    /api/v1/core/users/{id}
POST   /api/v1/core/users
PATCH  /api/v1/core/users/{id}
POST   /api/v1/core/users/{id}/disable
POST   /api/v1/core/users/{id}/enable
```

Response minimo:

- `id`
- `tenant_id`
- `branch_id`
- `name`
- `email`
- `active`
- `roles`
- `created_at`
- `updated_at`

Reglas:

- tenant-scoped;
- no cross-tenant access;
- branch debe pertenecer al tenant;
- user desactivado no autentica;
- password siempre se persiste hasheado;
- nunca exponer `password_hash`.

Permisos:

- `core.users.read`
- `core.users.create`
- `core.users.update`
- `core.users.disable`

## Roles Management

Endpoints:

```text
GET    /api/v1/core/roles
GET    /api/v1/core/roles/{id}
POST   /api/v1/core/roles
PATCH  /api/v1/core/roles/{id}
POST   /api/v1/core/roles/{id}/disable
POST   /api/v1/core/roles/{id}/enable
```

Response minimo:

- `id`
- `tenant_id`
- `name`
- `permissions`
- `active`
- `created_at`
- `updated_at`

Reglas:

- roles tenant-scoped;
- permissions siguen siendo catalogo global;
- un permiso global no autoriza por si solo;
- un role desactivado no debe otorgar permisos efectivos;
- roles de un tenant no pueden asignarse a users de otro tenant.

Permisos:

- `core.roles.read`
- `core.roles.manage`

## Branches Management

Endpoints:

```text
GET    /api/v1/core/branches
GET    /api/v1/core/branches/{id}
POST   /api/v1/core/branches
PATCH  /api/v1/core/branches/{id}
POST   /api/v1/core/branches/{id}/disable
POST   /api/v1/core/branches/{id}/enable
```

Response minimo:

- `id`
- `tenant_id`
- `name`
- `active`
- `created_at`
- `updated_at`

Reglas:

- branch pertenece a un solo tenant;
- no cross-tenant;
- users solo pueden pertenecer a branches de su tenant.

Permisos:

- `core.branches.read`
- `core.branches.manage`

## Plugins Management

Endpoints:

```text
GET  /api/v1/core/plugins
GET  /api/v1/core/plugins/{plugin_id}
POST /api/v1/core/plugins/{plugin_id}/install
POST /api/v1/core/plugins/{plugin_id}/enable
POST /api/v1/core/plugins/{plugin_id}/disable
POST /api/v1/core/plugins/{plugin_id}/uninstall
POST /api/v1/core/plugins/{plugin_id}/migrate
```

Reglas:

- reutilizar runtime persistente existente;
- no duplicar logica de lifecycle ya implementada;
- plugins failed deben seguir visibles para debugging;
- `last_error` debe exponerse cuando exista;
- acciones administrativas deben auditarse.

Permisos:

- lectura runtime: `core.plugin.runtime.read`
- administracion: `core.plugin.manage`

`core.plugin.read` sigue sirviendo para visibilidad funcional de plugins habilitados para navegacion, pero no debe cubrir toda la administracion del runtime.

## Reglas de tenant isolation

Todas las APIs de `users`, `roles` y `branches` deben usar `TenantContext` activo.

Debe garantizar:

- Tenant A no accede a users de Tenant B;
- Tenant A no accede a roles de Tenant B;
- Tenant A no accede a branches de Tenant B;
- branch cross-tenant falla;
- role cross-tenant falla;
- user-role cross-tenant falla.

Prohibido:

```python
session.query(User).all()
```

Correcto:

- servicios tenant-scoped;
- helpers tenant-aware reutilizables.

## RBAC

La capa frontend debe ser permission-aware, pero el backend sigue siendo la autoridad final.

Reglas:

- users page visible con `core.users.read`;
- acciones users segun `create`, `update`, `disable`;
- roles page visible con `core.roles.read`;
- acciones roles con `core.roles.manage`;
- branches page visible con `core.branches.read`;
- acciones branches con `core.branches.manage`;
- plugins page visible con `core.plugin.runtime.read` o `core.plugin.manage`;
- acciones plugins con `core.plugin.manage`.

## Auditoría

Operaciones auditables obligatorias:

- create user;
- update user;
- disable user;
- enable user;
- create role;
- update role;
- disable role;
- enable role;
- create branch;
- update branch;
- disable branch;
- enable branch;
- plugin install;
- plugin enable;
- plugin disable;
- plugin uninstall;
- plugin migrate.

Cada `audit_log` debe incluir:

- `tenant_id`
- `branch_id` si aplica
- `actor_user_id`
- `action`
- `entity_type`
- `entity_id`
- `result`
- `correlation_id` si existe.

## Eventos

Eventos minimos:

Users:

- `core.user.created`
- `core.user.updated`
- `core.user.disabled`
- `core.user.enabled`

Roles:

- `core.role.created`
- `core.role.updated`
- `core.role.disabled`
- `core.role.enabled`

Branches:

- `core.branch.created`
- `core.branch.updated`
- `core.branch.disabled`
- `core.branch.enabled`

Plugins:

- reutilizar lifecycle events existentes:
  - `core.plugin.installed`
  - `core.plugin.enabled`
  - `core.plugin.disabled`
  - `core.plugin.uninstalled`
  - `core.plugin.failed`

Todo evento tenant-scoped debe incluir `tenant_id`.

## Frontend minimal

No rehacer shell.

Reusar:

- sidebar;
- auth store;
- tenant context actual;
- plugin runtime store;
- TanStack Query;
- componentes compartidos existentes.

Reemplazar placeholders de:

- `Settings > Users`
- `Settings > Roles`
- `Settings > Branches`
- `Plugins`

UI minima esperada:

- tablas simples;
- dialog/form simple;
- badges de estado;
- acciones enable/disable/install/uninstall segun permisos.

## Pruebas obligatorias

Backend:

- users: list, create, update, disable, enable, tenant isolation, no `password_hash`, branch cross-tenant fail, user disabled no autentica;
- roles: list, create, update, assign permissions, disable, enable, tenant isolation, role cross-tenant fail;
- branches: list, create, update, disable, enable, tenant isolation;
- plugins: list, detail, install, enable, disable, uninstall, migrate, permission checks;
- audit log en cambios criticos;
- event log para `core.user.created`, `core.role.created`, `core.branch.created`, `core.plugin.enabled`.

Frontend:

- users page renderiza;
- roles page renderiza;
- branches page renderiza;
- plugins page renderiza;
- usuario sin `core.users.read` no ve Users;
- usuario sin `core.roles.read` no ve Roles;
- usuario sin `core.branches.read` no ve Branches;
- usuario sin `core.plugin.manage` no ve acciones admin de plugins;
- crear user refresca tabla;
- disable user refresca tabla;
- logout sigue limpiando contexto;
- rutas protegidas siguen funcionando.

## Criterios de aceptación

- existe `docs/specs/core/0009-core-management-apis.md`;
- Users API funciona;
- Roles API funciona;
- Branches API funciona;
- Plugins Management API funciona;
- todo es tenant-scoped;
- RBAC se valida correctamente;
- `audit_log` registra cambios administrativos;
- `event_log` registra eventos administrativos;
- Settings > Users funciona;
- Settings > Roles funciona;
- Settings > Branches funciona;
- Plugins Page permite management minimo;
- tests backend pasan;
- tests frontend pasan;
- build frontend pasa;
- Ruff pasa;
- Pyright pasa.

## Checklist manual

1. Iniciar sesion con usuario demo admin.
2. Entrar a Settings > Users y crear un usuario nuevo.
3. Editar el usuario y verificar refresh de tabla.
4. Deshabilitar el usuario y confirmar que ya no autentica.
5. Crear role con permissions validos.
6. Deshabilitar role y confirmar que deja de otorgar permisos.
7. Crear branch y editar su metadata minima.
8. Deshabilitar branch y verificar estado en UI.
9. Abrir Plugins page con permiso de runtime read.
10. Ejecutar install/enable/disable/uninstall sobre plugin de prueba.
11. Confirmar `last_error` visible cuando el plugin falla.
12. Verificar que `health`/`ready` siguen operativos.

## Gaps fuera de alcance

- dominio real de `logistics`;
- plugin marketplace;
- busqueda avanzada;
- paginacion server-side compleja;
- onboarding SaaS;
- import/export masivo;
- MFA/SSO;
- UX avanzada de tablas o filtros;
- politicas de tenant switching.
