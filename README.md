# SYSTUTOR OSS

Sistema operativo multi-tenant para la gestion de una empresa de gas
envasado: envases, planificacion, despacho, clientes, stock, productos,
cotizaciones y compras.

El kernel de infraestructura vive en su propio repositorio publico
[systutor-core](https://github.com/luc444s/systutor-core) (MIT) y este
repositorio lo consume como submodule. Los modulos de negocio viven aqui
como plugins.

## Estado actual

La **version 1.0.0** quedo cerrada el 2026-08-10 (ver
`docs/changelogs/2026-08-10-v1.0.0.md`): `logistics`, `stock`,
`productos`, `crm` y el shell forman un sistema usable end-to-end. El
trabajo posterior es `v1.1+` y deuda tecnica no bloqueante.

## Modulos de negocio

| Plugin | Version | Alcance |
|---|---|---|
| `logistics` | 0.5.0 | Envases (cilindros y tanques criogenicos), planificacion, rutas y despacho, recepcion, jornadas/sesiones operativas, carta porte, contratos de envases, ADR, consola operativa |
| `crm` | 1.0.0 | Clientes con datos fiscales, direcciones, contactos, catalogos y geografia |
| `productos` | 0.1.0 | Catalogo maestro de productos con catalogos base, precios, costos, ADR, media y promociones |
| `stock` | 0.2.0 | Ledger de inventario con reservas, costeo promedio ponderado y operaciones transaccionales |
| `ventas` | 0.1.0 | Cotizaciones via consola DSL y formulario visual. Flujo cotizacion → planificacion |
| `commerce` | 0.1.0 | Compras: proveedores, ordenes y recepcion con integracion a stock |

Cada plugin declara identidad, version, permisos, eventos y migraciones
propias (`plugin.json` + `backend/plugin.py`). El estado por modulo se
documenta en `plugins/<modulo>/README.md` y `docs/avances/<modulo>.md`.

## Estructura

```text
apps/
  api/                Backend FastAPI (aplicacion huesped del kernel)
  web/                Frontend shell React + Vite (host modular)
packages/
  ui/                 Componentes UI compartidos
plugins/
  logistics/          Envases, planificacion, operacion, jornadas
  crm/                Clientes
  productos/          Catalogo maestro
  stock/              Inventario
  ventas/             Cotizaciones
  commerce/           Compras
vendor/
  systutor-core/      Kernel OSS (submodule git, MIT, ADR 0029)
ADD/                  Disciplina ADD (submodule git: canon, skills y task-tools)
tools/
  migrator/           Migrador legacy (CSV + manifest)
  legacy-analyzer/    Analizador del legacy
  dev/                Utilidades locales (servicios, benchmarks)
docs/
  adr/                Decisiones de arquitectura
  specs/              Especificaciones funcionales
  contracts/          Contratos humanos del sistema
  avances/            Estado actual por modulo
  changelogs/         Cierres por fecha
infra/
  compose/            Entorno local fuera de Termux
```

## Kernel externo (systutor-core)

La infraestructura (auth, RBAC, tenancy, auditoria, eventos/outbox,
runtime de plugins, documentos, firmas) vive en `vendor/systutor-core`.

- Los plugins importan infraestructura **solo** desde `systutor.*`.
- La configuracion de negocio se resuelve en `apps/api/app/config.py`
  (`GasSettings`), que registra su factory en el kernel.
- El pin del submodule se actualiza por version explicita. Ver seccion
  "Core externo" en `AGENTS.md` y `docs/adr/0029-extraccion-core-mit-multirepo.md`.

## Entorno local

Entorno primario: **Termux**. Python 3.12 base (3.13 aceptado en Termux
mientras el codigo siga compatible con 3.12). Docker Compose queda como
respaldo para entornos fuera de Termux.

### Instalacion

```bash
cp .env.example .env              # configurar URLs de PostgreSQL y Redis
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e ".[termux-dev]"
python3 -m pip install -e vendor/systutor-core
pkg install ruff                  # solo Termux: ruff por sistema
```

No usar `.[dev]` en Termux (incluye `ruff` que compila por pip). En CI o
fuera de Termux: `pip install -e ".[dev]"`.

Frontend con pnpm:

```bash
pnpm install
cp apps/web/.env.example apps/web/.env   # VITE_API_BASE_URL
```

### Migraciones

```bash
npm run migrate                      # alembic upgrade head
npm run migrate:plugins              # migraciones por plugin
.venv/bin/python -m apps.api.app.commands.seed_demo
```

### Ejecucion

```bash
npm run services          # PostgreSQL + backend en un comando (Termux)
npm run frontend          # shell React en 5173
npm run psql              # consola PostgreSQL
npm run status:services
```

Backend directo:

```bash
uvicorn apps.api.app.main:app --reload
```

Worker de eventos (Dramatiq + Redis):

```bash
dramatiq systutor.kernel.events.tasks
python3 -c "from systutor.kernel.events.tasks import dispatch_pending_events; print(dispatch_pending_events.fn())"
```

### API base

- `GET /api/v1/system/health`
- `GET /api/v1/system/ready`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/system/plugins`

Los endpoints de cada modulo viven bajo `/api/v1/plugins/<plugin_id>/...`.

## Aislamiento multi-tenant

- Un usuario autenticado opera dentro del `tenant_id` persistido en DB.
- El JWT se valida contra usuario, tenant, branch e `is_superadmin`.
- Los permisos se resuelven solo mediante roles validos del tenant.
- `health` y `ready` son globales; todo lo demas exige contexto de tenant.

En la practica: un usuario del Tenant A no puede leer, modificar ni usar
permisos o roles del Tenant B.

## Login demo

1. `npm run services`
2. Seed (primera vez): `.venv/bin/python -m apps.api.app.commands.seed_demo`
3. `npm run frontend`
4. `http://127.0.0.1:5173/login` — `admin@example.com` / `ChangeMe123!`

## Consola operativa

El sistema incluye una consola operativa embebida (Monaco) con DSL de
comandos para flujos operativos y cotizaciones. Ver ADR 0022 y 0023.

## Pruebas y calidad

```bash
.venv/bin/python -m pytest apps/api/tests -q
ruff check .
.venv/bin/python -m pyright
node /data/data/com.termux/files/usr/lib/node_modules/pnpm/bin/pnpm.cjs --filter @systutor/web build
```

Los tests usan SQLite + `TestClient`. Los tests del kernel viven en
`systutor-core` (su propia suite).

## Documentacion obligatoria antes de desarrollar

1. `AGENTS.md` + `ADD/QUICKSTART.md` — reglas operativas, orden de lectura y
   modo de ejecución por defecto de agentes (**extreme-poverty**: ciclo ADD en
   hilo principal, 0–1 toolcall, canon §4.2 Modo D)
2. `docs/adr/` (decisiones de arquitectura vigentes)
3. Spec activa del dominio (`docs/specs/core/`)
4. Contrato de datos/API si aplica (`docs/contracts/`)

## Migracion legacy

La migracion desde el sistema legacy es por dominio: CSV + `manifest.json`
→ validacion → transformacion → PostgreSQL → auditoria. El migrador vive
en `tools/migrator/` y no comparte runtime con el backend principal.

## Nota de drivers

En Termux se usa `psycopg` sin binario obligatorio. No asumir
`psycopg[binary]` como camino principal en Android/Termux.
