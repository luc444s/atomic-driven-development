# ADR 0004 - Runtime de Plugins

## Estado

Aceptado

## Contexto

SYSTUTOR OSS será una plataforma modular. Para que esto funcione, los plugins deben tener un contrato explícito, versionable y verificable.

La meta es evitar módulos acoplados informalmente, cargados mediante convenciones ambiguas o dependientes de detalles internos del core.

El runtime de plugins debe permitir que SYSTUTOR OSS evolucione como plataforma, donde los módulos de negocio puedan instalarse, habilitarse, deshabilitarse y evolucionar sin convertir el kernel en un monolito.

## Decisión

SYSTUTOR OSS tendrá un runtime de plugins basado en manifiestos explícitos.

Cada plugin debe tener como mínimo:

```text
plugin/
├── plugin.json
├── backend/
├── frontend/
├── migrations/
├── permissions/
├── events/
└── README.md
```

## Contrato `plugin.json`

El archivo `plugin.json` será obligatorio y deberá seguir este contrato base:

```json
{
  "id": "logistics",
  "name": "Logistics",
  "version": "0.1.0",
  "api_version": "1",
  "requires": [],
  "backend_entrypoint": "backend.plugin:register",
  "frontend_entrypoint": "frontend/register.ts",
  "permissions": [
    "logistics.delivery.read"
  ],
  "events": [
    "logistics.delivery.created"
  ],
  "description": "Modulo de logistica para SYSTUTOR OSS"
}
```

## Campos obligatorios

### `id`

Identificador único del plugin.

Reglas:

* debe ser único en todo el sistema;
* debe estar en minúsculas;
* debe usar formato `snake_case` o palabra simple;
* no debe cambiar después de publicado.

Ejemplos válidos:

```text
logistics
inventory
billing
customers
```

### `name`

Nombre legible del plugin.

### `version`

Versión del plugin siguiendo SemVer cuando sea posible.

Ejemplo:

```text
0.1.0
1.0.0
1.2.3
```

### `api_version`

Versión del contrato del runtime de plugins con el que el plugin es compatible.

Ejemplo:

```json
"api_version": "1"
```

Si el core rompe compatibilidad con plugins existentes, deberá elevarse la versión de API o crearse un ADR nuevo.

### `requires`

Lista de plugins requeridos.

Ejemplo:

```json
"requires": ["customers", "inventory"]
```

El runtime debe validar que las dependencias estén instaladas y habilitadas antes de cargar el plugin.

### `backend_entrypoint`

Punto de entrada backend del plugin.

Ejemplo:

```json
"backend_entrypoint": "backend.plugin:register"
```

Este entrypoint podrá registrar:

* rutas API;
* permisos;
* eventos;
* listeners;
* tareas;
* servicios;
* migraciones;
* configuración del plugin.

### `frontend_entrypoint`

Punto de entrada frontend del plugin.

Ejemplo:

```json
"frontend_entrypoint": "frontend/register.ts"
```

Este entrypoint podrá registrar:

* rutas frontend;
* navegación;
* páginas;
* widgets;
* paneles;
* acciones UI;
* permisos visuales.

### `permissions`

Lista de permisos declarados por el plugin.

Ejemplo:

```json
"permissions": [
  "logistics.delivery.read",
  "logistics.delivery.create",
  "logistics.delivery.update"
]
```

Todo permiso usado por el plugin debe estar declarado.

### `events`

Lista de eventos publicados o consumidos por el plugin.

Ejemplo:

```json
"events": [
  "logistics.delivery.created",
  "logistics.delivery.completed",
  "logistics.route.assigned"
]
```

Los eventos deben ser explícitos y documentados.

## Estados de un plugin

Un plugin podrá estar en uno de estos estados:

```text
discovered
installed
enabled
disabled
failed
uninstalled
```

### `discovered`

El runtime encontró el plugin en el sistema de archivos, pero aún no fue instalado.

### `installed`

El plugin fue registrado en la base de datos y sus metadatos fueron validados.

### `enabled`

El plugin está activo y sus capacidades están cargadas.

### `disabled`

El plugin está instalado, pero no activo.

### `failed`

El plugin falló durante validación, carga, migración o inicialización.

### `uninstalled`

El plugin fue retirado del sistema.

## Ciclo de vida

El runtime deberá soportar, como mínimo, estas operaciones:

```text
discover
install
enable
disable
migrate
validate
uninstall
```

En el backend, el plugin podrá exponer hooks de ciclo de vida:

```python
def register(context):
    ...

def on_install(context):
    ...

def on_enable(context):
    ...

def on_disable(context):
    ...

def on_uninstall(context):
    ...
```

Estos hooks deben ser explícitos, trazables y auditables.

## Orden de carga

El orden de carga debe ser determinístico.

Reglas:

* primero se cargan plugins sin dependencias;
* luego se cargan plugins dependientes;
* si existe dependencia circular, la carga debe fallar;
* si una dependencia requerida no existe o está deshabilitada, el plugin no debe habilitarse;
* el error debe quedar registrado en auditoría/logs.

## Manejo de errores

Si un plugin falla durante la carga:

* no debe romper todo el sistema;
* debe marcarse como `failed`;
* debe registrar causa del error;
* debe impedirse su uso hasta corregir el problema;
* el core debe continuar funcionando si el plugin no es crítico.

Si el plugin es requerido por otros plugins, esos plugins dependientes no deben habilitarse.

## Migraciones por plugin

Cada plugin debe mantener sus migraciones dentro de su propia carpeta:

```text
plugin/
└── migrations/
```

Reglas:

* las migraciones deben ser pequeñas y revisables;
* las migraciones no deben modificar tablas de otros plugins salvo contrato explícito;
* las migraciones deben ejecutarse mediante el sistema oficial definido por el core;
* el estado de migración del plugin debe quedar registrado;
* una migración fallida debe impedir la habilitación del plugin.

## Aislamiento

Los plugins no deben depender de detalles internos del core.

Reglas:

* los plugins deben interactuar con el sistema mediante SDK, contratos públicos o eventos;
* los plugins no deben importar módulos internos privados de `apps/api`;
* los plugins no deben modificar directamente estructuras internas del kernel;
* los plugins no deben escribir en tablas de otros plugins sin contrato explícito;
* los plugins no deben crear lógica oculta en stored procedures o triggers.

## Comunicación entre plugins

La comunicación entre plugins debe preferir eventos o contratos explícitos.

Permitido:

```text
plugin A -> event bus -> plugin B
plugin A -> SDK publico -> core
plugin A -> contrato declarado -> plugin B
```

Evitar:

```text
plugin A -> import interno directo -> plugin B
plugin A -> acceso directo a tablas internas de plugin B
plugin A -> dependencia implícita no declarada
```

## Registro backend

El backend del plugin podrá registrar:

* routers FastAPI;
* servicios;
* permisos;
* eventos;
* event handlers;
* tareas Dramatiq;
* configuraciones;
* migraciones.

El registro debe hacerse únicamente mediante el contexto entregado por el runtime.

Ejemplo conceptual:

```python
def register(context):
    context.register_router(router)
    context.register_permissions([...])
    context.register_events([...])
```

## Registro frontend

El frontend del plugin podrá registrar:

* rutas;
* páginas;
* menú lateral;
* widgets;
* acciones;
* configuraciones visuales.

Ejemplo conceptual:

```ts
registerPlugin({
  id: "logistics",
  routes: [],
  navigation: [],
  widgets: []
})
```

## Auditoría

El runtime debe auditar acciones importantes sobre plugins:

* instalación;
* habilitación;
* deshabilitación;
* migración;
* fallo de carga;
* actualización;
* desinstalación.

Cada registro debe incluir:

* plugin;
* versión;
* usuario o proceso;
* acción;
* resultado;
* fecha/hora;
* error si aplica.

## Seguridad

Un plugin no debe recibir acceso ilimitado al sistema por defecto.

Reglas:

* debe declarar permisos;
* debe declarar eventos;
* debe declarar dependencias;
* debe usar APIs públicas;
* debe respetar tenancy;
* debe respetar auditoría;
* no debe omitir validaciones de permisos.

## Consecuencias

* El core podrá descubrir y validar plugins de forma uniforme.
* La carga de plugins será determinística y auditable.
* El runtime deberá implementar validación de manifiesto, resolución de dependencias y control de compatibilidad.
* Los plugins tendrán límites claros frente al kernel y otros plugins.
* Los plugins podrán crecer sin convertir el core en un monolito.
* Cambios incompatibles en el contrato del plugin requerirán elevar `api_version` o crear un nuevo ADR.
