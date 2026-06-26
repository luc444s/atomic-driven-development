# SPEC 0009 - Core Management APIs + Frontend Minimal

## Estado

Propuesta

---

# Contexto

SYSTUTOR OSS ya dispone de:

## Arquitectura

* ADR 0001-0009 aprobados
* Core backend persistente
* Auth JWT
* RBAC
* Active tenant isolation
* Audit log
* Event log
* Outbox
* Plugin runtime completo
* Plugin lifecycle persistente
* Plugin migrations
* Event bus
* Frontend Shell v0.2 tenant-aware

## Frontend existente

Ya existe sidebar funcional con:

* Dashboard
* Plugins
* Settings

  * Users
  * Roles
  * Branches

Estas vistas existen como shell visual, pero todavia no tienen funcionalidad real.

Actualmente:

* no hay APIs administrativas completas del core
* Users es placeholder
* Roles es placeholder
* Branches es placeholder
* Plugins no tiene management real desde UI

---

# Objetivo

Implementar el **Core Management Layer**.

Esto incluye:

## Backend

APIs administrativas tenant-scoped para:

* users
* roles
* branches
* plugins

## Frontend

UI minima funcional para:

* listar
* crear
* editar
* activar/desactivar

---

# Motivacion arquitectonica

El core NO es un modulo de negocio.

El core administra entidades transversales.

Regla:

Si una entidad sigue siendo necesaria aunque logistics desaparezca, pertenece al core.

Ejemplos core:

* tenant
* branch
* user
* role
* permission
* plugin registry

Ejemplos NO core:

* delivery
* route
* cylinder
* pickup
* manifest

Eso pertenece a plugins.

---

# No objetivos

No implementar:

* logistics plugin
* CRM
* inventory
* billing
* analytics
* reports
* advanced dashboards
* SaaS onboarding
* SSO
* MFA
* plugin marketplace
* bulk import/export
* advanced search
* server-side pagination compleja
* websockets

---

# Alcance

Puede modificar:

* apps/api
* apps/web
* apps/api/tests
* apps/web tests
* docs/specs/core

No introducir dependencias nuevas sin justificacion.

---

# Arquitectura backend requerida

Separar por dominios:

```text
apps/api/app/api/v1/core/
├── users.py
├── roles.py
├── branches.py
└── plugins.py
```

Mantener logica en:

```text
router
→ service
→ repository
```

NO colocar logica pesada dentro de routers.

Incorrecto:

* routers de 100+ lineas con logica de negocio

Correcto:

* router fino
* service layer explicito
* helpers tenant-aware reutilizables

---

# 1. Users Management API

## Endpoints

```text
GET    /api/v1/core/users
GET    /api/v1/core/users/{id}
POST   /api/v1/core/users
PATCH  /api/v1/core/users/{id}
POST   /api/v1/core/users/{id}/disable
POST   /api/v1/core/users/{id}/enable
```

---

## Response esperado

Cada usuario debe exponer:

* id
* tenant_id
* branch_id
* name
* email
* active
* roles
* created_at
* updated_at

---

## Reglas

* tenant-scoped
* no cross-tenant access
* branch debe pertenecer al tenant
* usuario desactivado no autentica

---

## Permisos

* core.users.read
* core.users.create
* core.users.update
* core.users.disable

---

# 2. Roles Management API

## Endpoints

```text
GET    /api/v1/core/roles
GET    /api/v1/core/roles/{id}
POST   /api/v1/core/roles
PATCH  /api/v1/core/roles/{id}
POST   /api/v1/core/roles/{id}/disable
POST   /api/v1/core/roles/{id}/enable
```

---

## Modelo

Role debe exponer:

* id
* tenant_id
* name
* permissions
* active

---

## Reglas

* roles son tenant-scoped
* permisos provienen del catalogo global
* roles no cruzan tenants

---

## Permisos

* core.roles.read
* core.roles.manage

---

# 3. Branches Management API

## Endpoints

```text
GET    /api/v1/core/branches
GET    /api/v1/core/branches/{id}
POST   /api/v1/core/branches
PATCH  /api/v1/core/branches/{id}
POST   /api/v1/core/branches/{id}/disable
POST   /api/v1/core/branches/{id}/enable
```

---

## Modelo

Branch:

* id
* tenant_id
* name
* active

---

## Reglas

* branch pertenece a un tenant
* no cross-tenant
* usuarios solo pueden pertenecer a branches del tenant

---

## Permisos

* core.branches.read
* core.branches.manage

---

# 4. Plugins Management API

Ya existe runtime.

Exponer management administrativo.

## Endpoints

```text
GET  /api/v1/core/plugins
GET  /api/v1/core/plugins/{plugin_id}
POST /api/v1/core/plugins/{plugin_id}/enable
POST /api/v1/core/plugins/{plugin_id}/disable
POST /api/v1/core/plugins/{plugin_id}/install
POST /api/v1/core/plugins/{plugin_id}/uninstall
POST /api/v1/core/plugins/{plugin_id}/migrate
```

---

## Reglas

* solo admin autorizado
* usar runtime persistente existente
* respetar lifecycle actual

---

## Permisos

Separar permisos:

Lectura runtime:

* core.plugin.runtime.read

Administracion:

* core.plugin.manage

NO reutilizar `core.plugin.read`.

Crear permiso especifico.

---

# Auditoria

Toda operacion debe registrar:

* tenant_id
* branch_id
* actor_user_id
* action
* entity_type
* entity_id
* result
* correlation_id si existe

Operaciones auditables:

* create user
* update user
* disable user
* create role
* update role
* create branch
* update branch
* plugin enable
* plugin disable
* plugin install
* plugin uninstall

Obligatorio.

---

# Eventos

Emitir eventos minimos:

* core.user.created
* core.user.updated
* core.user.disabled
* core.role.created
* core.role.updated
* core.branch.created
* core.branch.updated

Todos deben incluir tenant_id.

---

# Frontend Minimal

No rehacer shell.

Reusar:

* sidebar
* auth store
* tenant context
* plugin runtime

Solo reemplazar placeholders.

---

# Users Page

Ruta existente:

Settings → Users

Implementar tabla minima.

Columnas:

* Name
* Email
* Branch
* Roles
* Status

Acciones:

* Create
* Edit
* Enable
* Disable

UI minima:

* table
* modal/dialog
* form simple

No usar grid compleja.

---

# Roles Page

Tabla:

* Role
* Permissions count
* Status

Acciones:

* Create
* Edit
* Enable
* Disable

---

# Branches Page

Tabla:

* Branch name
* Status

Acciones:

* Create
* Edit
* Enable
* Disable

---

# Plugins Page

Expandir page existente.

Tabla:

* Plugin ID
* Version
* State
* Installed
* Enabled

Acciones:

* Install
* Enable
* Disable
* Uninstall
* Migrate

Mostrar:

* lifecycle state
* last_error si existe

---

# Arquitectura frontend

Usar TanStack Query.

Preferir:

```typescript
useQuery(...)
useMutation(...)
```

Evitar crear stores gigantes.

Mantener:

* auth store
* plugin runtime store

No mover CRUD completo a Zustand.

---

# Permission-aware rendering

Mantener PermissionBoundary.

Ejemplos:

Users:

* core.users.read

Roles:

* core.roles.read

Branches:

* core.branches.read

Plugins:

* core.plugin.runtime.read

Admin actions:

* core.plugin.manage

Usuario sin permisos:

* no ve menu
* no ve botones de accion

---

# Tenant isolation obligatorio

Toda API debe ser tenant-aware.

Prohibido:

```python
session.query(User).all()
```

Correcto:

* tenant-scoped repository
* tenant-aware helpers

Debe garantizar:

Tenant A nunca accede a:

* users de B
* roles de B
* branches de B

---

# Tests obligatorios

## Backend

Agregar tests para:

### Users

* create user
* update user
* disable user
* tenant isolation

### Roles

* create role
* assign permissions
* tenant isolation

### Branches

* create branch
* update branch
* tenant isolation

### Plugins

* list plugins
* enable plugin
* disable plugin
* permission checks

### Seguridad

* Tenant A no accede a Tenant B
* branch cross-tenant falla
* role cross-tenant falla

### Auditoria

Verificar audit_log en cambios criticos.

---

## Frontend

Agregar tests para:

* Users page renderiza
* Roles page renderiza
* Branches page renderiza
* Plugins page renderiza
* usuario sin permisos no ve menu
* disable action refresca tabla
* logout sigue funcionando

---

# Validaciones finales

Ejecutar:

```bash
ruff check .
python -m pyright
python -m pytest apps/api/tests -q
pnpm --dir apps/web build
npm run test:web
```

Todo debe pasar.

---

# Criterios de aceptacion

La spec se considera cumplida cuando:

* Users API funcional
* Roles API funcional
* Branches API funcional
* Plugins management API funcional
* todo es tenant-scoped
* permisos se validan correctamente
* audit logs registran cambios
* frontend Settings es funcional
* frontend Plugins permite management
* tests backend pasan
* tests frontend pasan
* build frontend pasa

---

# Entrega esperada

Al finalizar reportar:

* spec creada
* archivos creados
* archivos modificados
* tests agregados
* comandos ejecutados
* resultados de ruff
* resultados de pyright
* resultados de pytest
* resultado build frontend
* gaps pendientes
* posibles ADR futuros
