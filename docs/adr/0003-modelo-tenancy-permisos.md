# ADR 0003 - Modelo Tenancy y Permisos

## Estado

Aceptado

## Contexto

SYSTUTOR OSS debe soportar operación multiempresa sin introducir una complejidad innecesaria en la primera versión.

El sistema necesita permitir que múltiples empresas, sucursales y usuarios trabajen dentro de la misma plataforma sin mezclar información ni permisos.

También necesita un modelo de autorización suficientemente expresivo para módulos empresariales, pero simple de operar en el core inicial.

El objetivo no es crear un motor de permisos excesivamente complejo desde el día uno, sino definir una base clara, auditable y extensible.

## Decisión

## Tenancy

La primera versión usará modelo lógico por fila con `tenant_id` en tablas aplicables.

### Reglas base

* El aislamiento se aplicará desde la aplicación.
* No se usará inicialmente esquema por tenant.
* No se usará inicialmente base de datos por tenant.
* PostgreSQL Row Level Security podrá evaluarse después como refuerzo opcional.
* Toda tabla de negocio debe incluir `tenant_id`, salvo justificación explícita.
* Las tablas globales del sistema podrán no tener `tenant_id` cuando representen configuración compartida del core.

### Tablas con `tenant_id`

Deben incluir `tenant_id`:

* clientes;
* productos;
* operaciones;
* logística;
* inventario;
* facturación;
* auditoría de negocio;
* documentos;
* archivos;
* configuraciones por empresa;
* tablas propias de plugins.

### Tablas potencialmente globales

Podrán no incluir `tenant_id` cuando corresponda:

* catálogo de plugins disponibles;
* versiones del sistema;
* configuración técnica global;
* catálogos internos del core;
* migraciones;
* países, monedas o catálogos universales cuando sean realmente globales.

Cualquier excepción debe estar documentada.

## Permisos

La primera versión usará RBAC + claims.

Modelo inicial:

* `user`: usuario autenticado;
* `role`: grupo de permisos asignable a usuarios;
* `permission`: acción declarativa que puede ejecutarse;
* `claim`: restricción contextual de alcance.

Ejemplo:

```text
role: admin
permission: logistics.delivery.create
claim: tenant_id
claim: branch_id
```

## Nomenclatura de permisos

Los permisos deberán seguir el formato:

```text
<module>.<resource>.<action>
```

Ejemplos:

```text
logistics.delivery.read
logistics.delivery.create
logistics.delivery.update
logistics.delivery.cancel

customers.customer.read
customers.customer.create

inventory.stock.read
inventory.stock.adjust

core.user.manage
core.plugin.install
```

Acciones comunes:

* `read`
* `create`
* `update`
* `delete`
* `cancel`
* `approve`
* `export`
* `import`
* `manage`

No se deben crear permisos con nombres ambiguos.

## Claims

Los claims no reemplazan a los permisos.

Los claims restringen el alcance del permiso.

Ejemplos de claims:

```text
tenant_id
branch_id
warehouse_id
region_id
```

Ejemplo práctico:

Un usuario puede tener:

```text
permission: logistics.delivery.read
claim: tenant_id = tenant_001
claim: branch_id = branch_003
```

Esto significa que puede leer entregas, pero solo dentro de la empresa y sucursal asignadas.

## Superadmin y administración global

El sistema podrá tener usuarios con alcance global para administración técnica.

Reglas:

* El superadmin no debe ser usado para operación diaria.
* Las acciones del superadmin deben auditarse.
* El acceso global debe ser explícito, no accidental.
* Los módulos no deben asumir que todos los usuarios pertenecen a un único tenant.

## Aplicación del aislamiento

La capa de aplicación será responsable de aplicar filtros por tenant y claims.

Reglas:

* Las APIs deben validar `tenant_id`.
* Los repositorios o servicios deben aplicar filtros de tenant.
* Las queries directas que ignoren tenant deben estar justificadas.
* Los plugins no deben acceder a datos de otros tenants salvo permiso explícito.
* Las pruebas deben cubrir acceso permitido y acceso denegado.

## Criterios de diseño

* El sistema no debe arrancar con una política excesivamente compleja.
* Los permisos deben ser declarativos y orientados a módulo.
* Los claims deben servir como filtro de alcance, no como reemplazo del modelo de permisos.
* El core debe poder aplicar autorización por tenant y por sucursal cuando corresponda.
* El modelo debe permitir crecer hacia reglas más avanzadas sin romper compatibilidad.
* El sistema debe ser auditable desde el inicio.

## Auditoría

Las acciones relevantes deben registrar:

* usuario;
* tenant;
* sucursal si aplica;
* acción;
* módulo;
* recurso afectado;
* resultado;
* fecha/hora.

Los accesos denegados relevantes también podrán registrarse cuando representen riesgo o intento de operación no permitida.

## Consecuencias

* Las tablas del core y de plugins deberán definir `tenant_id` cuando aplique.
* La capa de aplicación deberá filtrar y validar acceso por tenant.
* La seguridad dependerá inicialmente de disciplina de aplicación, contratos claros y testing.
* Los plugins deberán declarar permisos de forma explícita.
* Los permisos deberán ser estables y legibles.
* Si más adelante se activa PostgreSQL Row Level Security, deberá hacerse sin romper el modelo lógico ya adoptado.
* Cualquier cambio mayor al modelo de tenancy o permisos requerirá un nuevo ADR.
