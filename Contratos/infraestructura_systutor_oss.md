# SYSTUTOR OSS - Infraestructura Técnica Completa

**Documento:** Infraestructura base del proyecto  
**Proyecto:** SYSTUTOR OSS  
**Empresa futura:** Censoria / TutoraBusiness Group  
**Estado:** Documento inicial de arquitectura  
**Objetivo:** Definir la estructura tecnológica, distribución de archivos, arquitectura modular y preparación del proyecto para desarrollo humano + IA.

---

# 1. Objetivo del documento

Este documento define cómo se organizará técnicamente SYSTUTOR OSS desde el inicio.

La meta es evitar que el nuevo sistema repita los problemas del legacy:

- lógica oculta en Stored Procedures;
- triggers difíciles de rastrear;
- reglas de negocio mezcladas en la interfaz;
- formularios gigantes;
- dependencia fuerte de SQL Server, VB y Crystal Reports;
- poca observabilidad;
- dificultad para que varios programadores trabajen en paralelo;
- dificultad para que agentes de IA colaboren sin romper el proyecto.

SYSTUTOR OSS debe nacer como una plataforma:

- modular;
- observable;
- auditable;
- preparada para IA;
- preparada para plugins;
- preparada para migración progresiva desde SYSTUTOR Legacy;
- preparada para trabajo en equipo;
- preparada para operar globalmente.

---

# 2. Principios técnicos base

## 2.1. El kernel no conoce el negocio

El núcleo de SYSTUTOR OSS no debe saber qué es una venta, una factura, una entrega, un cliente o un cilindro.

El kernel solo provee infraestructura:

- autenticación;
- permisos;
- auditoría;
- eventos;
- runtime de plugins;
- configuración;
- almacenamiento;
- tareas en segundo plano;
- WebSockets;
- observabilidad;
- APIs base.

La lógica empresarial vive en módulos instalables.

---

## 2.2. La lógica debe vivir en código auditable

La lógica de negocio debe estar en servicios Python, no escondida en la base de datos.

Se evitará crear nueva lógica en:

- Stored Procedures;
- triggers;
- funciones SQL complejas;
- lógica dentro de componentes React;
- lógica dentro de formularios.

La base de datos debe persistir información, no ocultar reglas de negocio.

---

## 2.3. Todo cambio importante debe ser observable

Cada operación relevante debe poder responder:

- quién hizo la acción;
- cuándo ocurrió;
- desde dónde ocurrió;
- qué entidad fue afectada;
- qué datos cambiaron;
- qué módulo ejecutó la acción;
- qué evento se generó;
- si hubo error, dónde ocurrió.

---

## 2.4. Modularidad real

Cada módulo debe poder desarrollarse, probarse, instalarse y evolucionar de manera independiente.

Ejemplos de módulos:

- `crm`
- `customers`
- `inventory`
- `logistics`
- `billing`
- `reports`
- `ai_assistant`
- `migration_legacy`
- `librefact_connector`

---

## 2.5. Preparado para IA desde el día cero

El proyecto debe estar documentado y estructurado para que agentes de IA puedan:

- leer especificaciones;
- entender límites de módulos;
- generar código sin romper arquitectura;
- crear tests;
- crear migraciones;
- documentar cambios;
- revisar impacto;
- proponer mejoras;
- trabajar sobre tareas pequeñas y bien definidas.

---

# 3. Stack tecnológico

## 3.1. Backend

Tecnologías principales:

- Python 3.12+ o 3.13+;
- FastAPI;
- Pydantic;
- SQLAlchemy 2.x;
- Alembic;
- PostgreSQL;
- Redis;
- Uvicorn;
- Celery, RQ o Dramatiq para tareas en segundo plano;
- WebSockets para eventos en tiempo real;
- Pytest para pruebas;
- Ruff para linting;
- Mypy o Pyright para tipado gradual;
- Structlog o logging estructurado;
- OpenTelemetry en una fase posterior.

### Rol del backend

El backend será responsable de:

- lógica de negocio;
- APIs;
- permisos;
- auditoría;
- eventos;
- jobs;
- migraciones;
- integración con plugins;
- integración con IA;
- integración con legacy cuando sea necesario.

---

## 3.2. Frontend

Tecnologías principales:

- React;
- Vite;
- TypeScript;
- React Router;
- TanStack Query;
- Zustand;
- Tailwind CSS;
- shadcn/ui o sistema de componentes equivalente;
- Zod para validación en frontend cuando aplique;
- Vitest para pruebas unitarias;
- Playwright para pruebas end-to-end.

### Rol del frontend

El frontend debe ser:

- rápido;
- modular;
- mantenible;
- compatible con plugins;
- preparado para pantallas empresariales complejas;
- preparado para dashboards;
- preparado para paneles de IA;
- preparado para notificaciones en tiempo real.

La lógica pesada no debe vivir en React. React consume APIs, muestra estados y ejecuta flujos de usuario.

---

## 3.3. Base de datos principal

Base de datos objetivo:

- PostgreSQL.

PostgreSQL será el centro de datos de SYSTUTOR OSS.

Se usará para:

- usuarios;
- tenants;
- permisos;
- módulos;
- auditoría;
- eventos;
- configuración;
- datos de negocio migrados;
- nuevas funcionalidades.

---

## 3.4. SYSTUTOR Legacy

SYSTUTOR Legacy continuará usando:

- VB.NET;
- SQL Server;
- Crystal Reports;
- Stored Procedures existentes;
- triggers existentes;
- vistas existentes.

El nuevo sistema no debe intentar controlar directamente toda la base legacy desde el día uno.

La migración será progresiva y controlada.

---

## 3.5. Migración de datos

Tecnologías recomendadas:

- CSV explícito;
- manifest JSON;
- Python;
- pandas;
- openpyxl para reportes humanos de errores;
- PostgreSQL como destino;
- tablas de auditoría de importación.

No se recomienda iniciar con sincronización directa DB-to-DB debido a:

- falta de documentación;
- cientos de SP;
- triggers desconocidos;
- lógica en UI;
- riesgo de efectos secundarios invisibles.

---

## 3.6. Infraestructura

Tecnologías recomendadas:

- Docker;
- Docker Compose para desarrollo;
- Traefik o Nginx como reverse proxy;
- PostgreSQL;
- Redis;
- almacenamiento local al inicio;
- S3/R2 compatible en fases posteriores;
- Linux como ambiente principal;
- CI/CD con GitHub Actions o equivalente.

---

# 4. Arquitectura general

```text
systutor-oss/
├── apps/
│   ├── api/                  # Backend FastAPI
│   ├── web/                  # Frontend React
│   └── worker/               # Workers de tareas async
│
├── packages/
│   ├── sdk/                  # SDK para plugins
│   ├── contracts/            # Contratos compartidos
│   ├── config/               # Configuración común
│   └── ui/                   # Componentes UI compartidos
│
├── plugins/
│   ├── customers/
│   ├── logistics/
│   ├── inventory/
│   ├── billing/
│   ├── reports/
│   ├── ai_assistant/
│   └── legacy_migration/
│
├── tools/
│   ├── legacy_analyzer/      # Analizador de SQL Server / VB legacy
│   ├── migrator/             # Motor de importación CSV -> PostgreSQL
│   ├── codegen/              # Generadores internos
│   └── devops/               # Scripts de infraestructura
│
├── specs/
│   ├── kernel/
│   ├── plugins/
│   ├── migration/
│   └── ai/
│
├── docs/
│   ├── contrato.md
│   ├── infraestructura.md
│   ├── philosophy.md
│   ├── architecture/
│   ├── adr/
│   ├── migration/
│   └── development/
│
├── tests/
│   ├── backend/
│   ├── frontend/
│   ├── integration/
│   └── migration/
│
├── infra/
│   ├── docker/
│   ├── compose/
│   ├── nginx/
│   ├── traefik/
│   └── scripts/
│
├── .github/
│   └── workflows/
│
├── AGENTS.md
├── README.md
├── CONTRIBUTING.md
├── docker-compose.yml
├── pyproject.toml
├── package.json
└── pnpm-workspace.yaml
```

---

# 5. Distribución del backend

```text
apps/api/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   ├── logging.py
│   │   ├── errors.py
│   │   └── lifecycle.py
│   │
│   ├── kernel/
│   │   ├── auth/
│   │   ├── permissions/
│   │   ├── tenants/
│   │   ├── audit/
│   │   ├── events/
│   │   ├── plugins/
│   │   ├── storage/
│   │   ├── tasks/
│   │   ├── notifications/
│   │   └── websocket/
│   │
│   ├── api/
│   │   ├── v1/
│   │   └── deps.py
│   │
│   ├── modules/
│   │   └── README.md
│   │
│   ├── infrastructure/
│   │   ├── db/
│   │   ├── redis/
│   │   ├── mail/
│   │   └── external/
│   │
│   └── shared/
│       ├── schemas/
│       ├── utils/
│       └── types/
│
├── migrations/
├── tests/
└── pyproject.toml
```

---

# 6. Distribución de un módulo backend

Cada módulo debe seguir una estructura clara:

```text
plugins/logistics/backend/
├── plugin.json
├── domain/
│   ├── entities.py
│   ├── value_objects.py
│   ├── events.py
│   ├── policies.py
│   └── errors.py
│
├── application/
│   ├── commands/
│   ├── queries/
│   ├── services.py
│   └── use_cases/
│
├── infrastructure/
│   ├── models.py
│   ├── repositories.py
│   ├── mappers.py
│   └── migrations/
│
├── api/
│   ├── routes.py
│   ├── schemas.py
│   └── deps.py
│
├── events/
│   ├── handlers.py
│   └── subscribers.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
└── README.md
```

## Reglas de módulos backend

- El dominio no importa FastAPI.
- El dominio no importa SQLAlchemy.
- La lógica vive en `domain/` y `application/`.
- La base de datos vive en `infrastructure/`.
- Las rutas HTTP viven en `api/`.
- Los eventos viven en `events/`.
- Cada módulo debe tener tests propios.

---

# 7. Distribución del frontend

```text
apps/web/
├── src/
│   ├── main.tsx
│   ├── app/
│   │   ├── router.tsx
│   │   ├── providers.tsx
│   │   └── layout.tsx
│   │
│   ├── kernel/
│   │   ├── auth/
│   │   ├── permissions/
│   │   ├── modules/
│   │   ├── navigation/
│   │   ├── notifications/
│   │   ├── realtime/
│   │   └── settings/
│   │
│   ├── modules/
│   │   └── README.md
│   │
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   └── shared/
│   │
│   ├── hooks/
│   ├── lib/
│   ├── stores/
│   ├── services/
│   └── types/
│
├── public/
├── tests/
└── package.json
```

---

# 8. Distribución de un módulo frontend

```text
plugins/logistics/frontend/
├── module.ts
├── routes.tsx
├── menu.ts
├── pages/
│   ├── LogisticsDashboardPage.tsx
│   ├── DeliveryOrdersPage.tsx
│   └── RoutesPage.tsx
│
├── components/
│   ├── DeliveryOrderTable.tsx
│   ├── DeliveryStatusBadge.tsx
│   └── RouteTimeline.tsx
│
├── hooks/
│   ├── useDeliveryOrders.ts
│   └── useLogisticsEvents.ts
│
├── api/
│   └── logisticsApi.ts
│
├── stores/
│   └── logisticsStore.ts
│
├── schemas/
│   └── logisticsSchemas.ts
│
├── tests/
└── README.md
```

## Reglas de módulos frontend

- Cada módulo registra sus rutas.
- Cada módulo registra su menú.
- Cada módulo consume APIs mediante servicios dedicados.
- React no debe contener lógica de negocio pesada.
- TanStack Query manejará datos remotos.
- Zustand manejará estado local o UI state.

---

# 9. Kernel de SYSTUTOR OSS

El kernel será el núcleo mínimo de la plataforma.

## Componentes del kernel

```text
kernel/
├── auth
├── tenants
├── users
├── roles
├── permissions
├── audit
├── events
├── plugins
├── config
├── storage
├── tasks
├── notifications
├── websocket
└── observability
```

## Responsabilidades

### Auth

- login;
- sesiones;
- tokens;
- usuarios;
- seguridad.

### Tenants

- empresas;
- organizaciones;
- aislamiento de datos.

### Permissions

- permisos declarativos;
- permisos por módulo;
- permisos por acción.

### Audit

- registro de operaciones;
- cambios de entidades;
- acciones de usuario;
- errores relevantes.

### Events

- eventos internos;
- comunicación entre módulos;
- integración con WebSockets;
- integración futura con IA.

### Plugins

- descubrir módulos;
- instalar módulos;
- habilitar módulos;
- deshabilitar módulos;
- registrar rutas;
- registrar permisos;
- registrar eventos.

### Tasks

- jobs async;
- importaciones;
- reportes;
- reintentos;
- tareas programadas.

---

# 10. Runtime de plugins

Cada plugin debe incluir un archivo `plugin.json`.

Ejemplo:

```json
{
  "name": "logistics",
  "display_name": "Logistics",
  "version": "0.1.0",
  "description": "Módulo de logística para entregas, rutas y eventos operativos.",
  "backend": true,
  "frontend": true,
  "dependencies": ["customers"],
  "permissions": [
    "logistics.read",
    "logistics.create",
    "logistics.update",
    "logistics.dispatch"
  ],
  "events": [
    "logistics.delivery.created",
    "logistics.delivery.dispatched",
    "logistics.delivery.completed"
  ]
}
```

## Ciclo de vida de un plugin

Cada plugin podrá tener:

- `on_install`
- `on_enable`
- `on_disable`
- `on_uninstall`
- `on_migrate`

---

# 11. Sistema de eventos

SYSTUTOR OSS debe comunicarse internamente mediante eventos.

Ejemplos:

```text
customer.created
customer.updated
logistics.delivery.created
logistics.delivery.completed
inventory.stock.changed
billing.invoice.created
migration.import.completed
migration.import.failed
```

## Reglas

- Los módulos no deben llamarse directamente entre sí cuando no sea necesario.
- Un módulo emite eventos.
- Otros módulos pueden escuchar eventos.
- Los eventos deben ser auditables.
- Los eventos deben poder enviarse al frontend si aplica.

---

# 12. API

Todas las funcionalidades deben exponerse por API.

La interfaz React será un consumidor de la API, no una excepción.

Estructura recomendada:

```text
/api/v1/auth
/api/v1/users
/api/v1/tenants
/api/v1/plugins
/api/v1/audit
/api/v1/events
/api/v1/customers
/api/v1/logistics
/api/v1/migration
```

## Reglas de API

- Versionar APIs desde el inicio.
- Usar schemas Pydantic.
- No devolver modelos internos directamente.
- Documentar endpoints.
- Usar errores consistentes.
- Registrar acciones importantes en auditoría.

---

# 13. Preparación para IA

La IA debe poder trabajar con el proyecto sin depender de conocimiento oculto.

## Archivos obligatorios para IA

```text
AGENTS.md
specs/
docs/architecture/
docs/adr/
docs/development/
docs/migration/
```

---

## 13.1. AGENTS.md

Archivo principal para agentes de IA.

Debe explicar:

- filosofía del proyecto;
- stack;
- estructura de carpetas;
- reglas de arquitectura;
- qué está prohibido;
- cómo crear módulos;
- cómo escribir tests;
- cómo generar migraciones;
- cómo trabajar con specs.

---

## 13.2. Spec-Driven Development

Cada característica nueva debe empezar con una especificación.

```text
specs/plugins/logistics/create-delivery-order.md
```

Estructura mínima:

```markdown
# Feature: Crear orden de entrega

## Objetivo

## Contexto de negocio

## Alcance

## Fuera de alcance

## Entidades afectadas

## Eventos generados

## Permisos requeridos

## API esperada

## UI esperada

## Casos de prueba

## Riesgos

## Criterios de aceptación
```

Ningún programador o agente debe implementar una característica importante sin spec.

---

## 13.3. ADRs

Cada decisión técnica importante debe guardarse como ADR.

```text
docs/adr/0001-use-fastapi.md
docs/adr/0002-use-postgresql.md
docs/adr/0003-plugin-runtime.md
docs/adr/0004-csv-migration-protocol.md
```

Formato:

```markdown
# ADR 0001 - Decisión

## Estado
Aceptado

## Contexto

## Decisión

## Consecuencias
```

---

## 13.4. Reglas para IA

Los agentes de IA deben:

- leer el spec antes de modificar código;
- tocar la menor cantidad de archivos posible;
- no modificar arquitectura sin ADR;
- no crear lógica en SQL;
- no crear triggers;
- no crear SP;
- no acoplar módulos;
- crear tests cuando agreguen lógica;
- actualizar documentación si cambian comportamiento;
- explicar los cambios en el PR.

---

# 14. Trabajo en equipo

## Flujo recomendado

```text
1. Se crea spec
2. Se revisa spec
3. Se divide en tareas
4. Programador o agente implementa
5. Se crean tests
6. Se revisa arquitectura
7. Se abre PR
8. Se valida CI
9. Se mergea
10. Se actualiza documentación
```

---

## Ramas Git

```text
main
  └── develop
        ├── feature/logistics-delivery-orders
        ├── feature/customers-import
        ├── fix/audit-events
        └── refactor/plugin-loader
```

## Convenciones de commits

```text
feat: agregar módulo de logística
fix: corregir validación de clientes
refactor: separar repositorio de auditoría
docs: actualizar contrato técnico
test: agregar pruebas de importación
chore: actualizar dependencias
```

---

# 15. Migración desde SYSTUTOR Legacy

## Problema actual

SYSTUTOR Legacy contiene:

- VB.NET;
- SQL Server;
- Crystal Reports;
- Stored Procedures;
- triggers;
- views;
- lógica en UI;
- poca o ninguna documentación.

Por eso no se recomienda una sincronización automática directa entre SQL Server y PostgreSQL.

---

## Estrategia elegida

La estrategia recomendada es:

```text
Legacy Export Engine
    ↓
CSV + manifest JSON
    ↓
Migrator Python
    ↓
Validación
    ↓
Transformación
    ↓
PostgreSQL
    ↓
SYSTUTOR OSS
```

---

## Reglas de migración

- No migrar tablas crudas.
- Migrar dominios.
- Usar CSV explícitos.
- Usar manifest JSON.
- Registrar cada importación.
- Validar antes de insertar.
- Rechazar datos ambiguos.
- Generar reportes de errores.
- No sobrescribir silenciosamente.
- Mantener `legacy_id` para trazabilidad.

---

## Ejemplo de bundle

```text
migration_bundle_2026_06_18_190000/
├── manifest.json
├── customers.csv
├── credits.csv
├── logistics_orders.csv
└── checksums.txt
```

---

## Ejemplo de manifest

```json
{
  "domain": "customers",
  "schema_version": "1.0.0",
  "source": "systutor_legacy",
  "generated_at": "2026-06-18T19:00:00Z",
  "files": [
    {
      "name": "customers.csv",
      "rows": 15000,
      "checksum": "sha256:..."
    }
  ]
}
```

---

## Auditoría de importación

Tabla sugerida:

```text
migration_jobs
├── id
├── domain
├── source
├── schema_version
├── file_name
├── file_hash
├── started_at
├── finished_at
├── status
├── rows_total
├── rows_inserted
├── rows_updated
├── rows_rejected
└── error_summary
```

---

## Reportes humanos

Cuando existan errores, se podrán generar archivos Excel con openpyxl:

```text
migration_errors_2026_06_18.xlsx
```

Con hojas como:

- errores;
- duplicados;
- advertencias;
- registros rechazados;
- resumen.

---

# 16. Legacy Analyzer

Debido a que el legacy no está documentado, se recomienda crear una herramienta interna:

```text
tools/legacy_analyzer/
```

Objetivo:

- listar tablas;
- listar columnas;
- listar SP;
- listar triggers;
- listar views;
- detectar dependencias;
- detectar tablas activas;
- detectar tablas muertas;
- generar reportes;
- generar grafos de dependencias.

Outputs:

```text
legacy_report/
├── tables.csv
├── views.csv
├── procedures.csv
├── triggers.csv
├── dependencies.csv
├── risk_matrix.csv
└── graph.dot
```

---

# 17. Observabilidad

Desde el inicio se deben registrar:

- requests importantes;
- errores;
- eventos de negocio;
- importaciones;
- cambios de permisos;
- instalación de plugins;
- acciones de usuario;
- jobs async;
- fallos de validación.

## Tablas sugeridas

```text
audit_log
event_log
job_log
migration_jobs
plugin_events
security_events
```

---

# 18. Testing

## Backend

- pruebas unitarias de dominio;
- pruebas de servicios;
- pruebas de API;
- pruebas de permisos;
- pruebas de migración;
- pruebas de eventos.

## Frontend

- pruebas de componentes;
- pruebas de hooks;
- pruebas de flujos críticos;
- pruebas end-to-end.

## Migración

Casos obligatorios:

- CSV válido;
- CSV con columnas faltantes;
- duplicados;
- IDs legacy repetidos;
- relaciones inexistentes;
- fechas inválidas;
- encoding incorrecto;
- importación repetida;
- rollback de importación.

---

# 19. Infraestructura de desarrollo

## Docker Compose inicial

Servicios mínimos:

```text
api
web
worker
postgres
redis
mailpit
```

Ejemplo:

```text
localhost:8000  -> FastAPI
localhost:5173  -> React/Vite
localhost:5432  -> PostgreSQL
localhost:6379  -> Redis
```

---

# 20. Seguridad

Desde el inicio:

- passwords hasheados;
- permisos por módulo;
- roles declarativos;
- sesiones seguras;
- logs de seguridad;
- protección de endpoints;
- validación de inputs;
- rate limit en endpoints sensibles;
- separación por tenant cuando aplique.

---

# 21. Etapas de implementación

## Etapa 0 - Documentación base

- `contrato.md`
- `infraestructura.md`
- `AGENTS.md`
- primeros ADRs
- estructura del monorepo

---

## Etapa 1 - Kernel mínimo

- FastAPI base;
- React base;
- PostgreSQL;
- auth;
- usuarios;
- permisos;
- auditoría básica;
- plugin registry básico.

---

## Etapa 2 - Runtime de plugins

- carga de plugins;
- rutas backend por plugin;
- rutas frontend por plugin;
- permisos por plugin;
- eventos por plugin.

---

## Etapa 3 - Migrador legacy

- protocolo CSV + manifest;
- migrador Python;
- validaciones;
- auditoría de imports;
- reportes Excel de errores;
- primer dominio migrado.

---

## Etapa 4 - Primer módulo real

Recomendado:

- customers;
- logistics;
- o legacy_migration.

El primer módulo debe servir para validar arquitectura completa.

---

## Etapa 5 - Logística OSS

- órdenes;
- estados;
- eventos;
- dashboard;
- trazabilidad;
- integración progresiva con legacy.

---

## Etapa 6 - IA nativa

- panel de asistente;
- búsqueda en documentación;
- análisis de eventos;
- ayuda para migración;
- generación de reportes;
- asistencia a programadores.

---

# 22. Conclusión

SYSTUTOR OSS debe construirse como una plataforma empresarial moderna, no como una copia del sistema legacy.

La infraestructura debe permitir:

- crecer por módulos;
- trabajar con varios programadores;
- trabajar con agentes de IA;
- migrar datos de forma controlada;
- auditar cada cambio;
- evitar lógica oculta;
- proteger la operación actual;
- absorber progresivamente SYSTUTOR Legacy.

La meta no es simplemente reemplazar VB y SQL Server.

La meta es transformar SYSTUTOR en una plataforma abierta, modular, observable y preparada para las próximas décadas.
