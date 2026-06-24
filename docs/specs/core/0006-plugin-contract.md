# SPEC 0006 - Plugin Contract

## Estado

Aprobada

## Contexto

SYSTUTOR OSS ya dispone de un runtime base de plugins y un `plugin_registry` funcional dentro del core.

Actualmente el sistema soporta:

* discovery de plugins;
* lectura de `plugin.json`;
* registro básico en runtime;
* plugin scaffold inicial.

Sin embargo, el contrato de plugins todavía es incompleto.

Existen varias decisiones críticas aún no formalizadas:

* lifecycle de plugins;
* contrato backend ejecutable;
* contrato frontend ejecutable;
* compatibilidad entre core y plugins;
* dependencias entre plugins;
* estrategia de migraciones;
* namespaces de permisos;
* namespaces de eventos;
* reglas de aislamiento.

Sin estas reglas, cada módulo podría implementar convenciones propias y degradar la modularidad del sistema.

---

## Objetivo

Formalizar el contrato oficial de plugins de SYSTUTOR OSS.

El contrato debe permitir:

* descubrimiento determinístico;
* validación estructural;
* carga segura;
* wiring backend;
* wiring frontend;
* registro de permisos;
* registro de eventos;
* migraciones aisladas;
* versionado compatible con el core.

---

## No objetivos

Fuera de alcance:

* marketplace de plugins;
* instalación remota desde internet;
* sandbox de seguridad OS-level;
* ejecución distribuida;
* plugins externos de terceros no confiables.

En esta fase, todos los plugins viven dentro del monorepo oficial.

---

## Estructura mínima obligatoria

Todo plugin debe seguir esta estructura:

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

---

## Manifest

El archivo `plugin.json` es obligatorio.

Contrato mínimo:

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
  ]
}
```

---

## Reglas del manifest

### id

* obligatorio;
* único globalmente;
* inmutable luego de publicar.

Formato:

```text
[a-z0-9_-]+
```

---

### version

Usa semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Ejemplo:

```text
1.2.0
```

---

### api_version

Representa compatibilidad con el runtime del core.

Reglas:

* mismo major = compatible;
* major distinto = incompatible;
* minor puede introducir extensiones backward-compatible.

---

## Plugin Lifecycle

Todo plugin debe seguir lifecycle formal.

Estados permitidos:

```text
discovered
validated
installed
enabled
disabled
failed
```

---

### discovered

El runtime encontró el plugin en filesystem.

---

### validated

Manifest y estructura fueron validados.

---

### installed

Migraciones y bootstrap completados.

---

### enabled

Plugin operativo y expuesto en runtime.

---

### disabled

Plugin instalado pero no activo.

---

### failed

Error de carga, wiring o migración.

---

## Reglas de lifecycle

* plugins inválidos no avanzan a `validated`;
* plugins con dependencias faltantes no avanzan a `installed`;
* plugins en estado `failed` no exponen rutas;
* un plugin roto no debe impedir boot del core salvo dependencia crítica explícita.

---

## Dependencias entre plugins

`requires` define dependencias.

Ejemplo:

```json
{
  "requires": ["inventory"]
}
```

Reglas:

* dependencias deben existir;
* ciclos están prohibidos;
* resolver orden de carga topológicamente.

Ejemplo inválido:

```text
A -> B
B -> A
```

---

## Backend Contract

Todo plugin backend debe exponer entrypoint:

```python
backend.plugin:register
```

Firma conceptual:

```python
def register(ctx: PluginContext) -> PluginRegistration:
    ...
```

---

## PluginContext

Debe exponer al menos:

* config
* router registry
* event bus
* audit service
* db/session provider
* task dispatcher
* plugin metadata

---

## PluginRegistration

Debe devolver al menos:

* routers
* permissions
* event_handlers
* startup_hooks
* shutdown_hooks

---

## Frontend Contract

Todo plugin frontend debe exponer:

```text
frontend/register.ts
```

Contrato conceptual:

```ts
registerPlugin(ctx): PluginFrontendRegistration
```

Debe poder registrar:

* routes
* navigation entries
* menu groups
* widgets
* feature flags

---

## Frontend Registration

Debe permitir:

* sidebar items
* route protection
* permission-aware rendering

---

## Permisos

Todo permiso de plugin debe seguir namespace obligatorio:

```text
plugin.resource.action
```

Ejemplos:

```text
logistics.delivery.read
logistics.delivery.create
logistics.route.assign
```

Formato inválido:

```text
read_delivery
```

---

## Eventos

Todo evento de plugin debe seguir namespace:

```text
plugin.aggregate.event
```

Ejemplos:

```text
logistics.delivery.created
logistics.delivery.dispatched
```

---

## Event Handlers

Reglas:

* handlers deben declararse;
* handlers deben ser auditables;
* handlers no deben ocultar lógica crítica.

---

## Migraciones

Cada plugin mantiene migraciones aisladas.

Ubicación:

```text
plugins/<plugin>/migrations/
```

Reglas:

* no mezclar migraciones entre plugins;
* migraciones deben ser idempotentes cuando aplique;
* instalación de plugin puede requerir migración;
* rollback debe ser explícito.

---

## Aislamiento

Plugins no deben acoplarse arbitrariamente.

Reglas:

* evitar acceso directo a internals de otros plugins;
* preferir eventos o contratos explícitos;
* no importar módulos internos privados de otros plugins.

Permitido:

```text
plugin -> core
plugin -> contracts públicos
plugin -> eventos públicos
```

Evitar:

```text
plugin -> internals privados de otro plugin
```

---

## Observabilidad

Todo plugin debe integrarse con:

* audit log
* event log
* correlation IDs
* tenant context

---

## Seguridad

Todo plugin debe respetar:

* tenancy
* RBAC
* auditoría
* aislamiento tenant-aware

Un plugin nunca debe bypassar auth del core.

---

## Testing obligatorio

Cada plugin debe incluir:

* unit tests
* integration tests
* permission tests
* event tests
* migration tests cuando aplique

---

## Criterios de aceptación

El contrato se considera implementado cuando:

* runtime valida manifest;
* lifecycle está implementado;
* dependencias se resuelven;
* plugins pueden registrar backend;
* plugins pueden registrar frontend;
* permisos siguen namespace oficial;
* eventos siguen namespace oficial;
* migraciones por plugin están soportadas;
* plugin inválido entra en `failed`;
* tests cubren rutas críticas.

---

## Primer consumidor

El primer plugin que implementará este contrato será:

```text
logistics
```

Toda desviación necesaria detectada durante la implementación de `logistics` deberá generar revisión de esta spec o nuevo ADR.
