# SYSTUTOR OSS

Primera base operativa del proyecto SYSTUTOR OSS.

Este repositorio arranca con:

- ADRs base aceptados;
- `AGENTS.md` para colaboradores y agentes;
- monorepo inicial;
- backend `FastAPI` con core persistente inicial;
- runtime interno de eventos con outbox basico;
- frontend shell `React + Vite` para login y estado del sistema;
- aislamiento tenant activo a nivel aplicacion para auth, RBAC, auditoria y eventos;
- contrato inicial de plugins;
- entorno local con `PostgreSQL` y `Redis`.

## Estado actual

Esta version no implementa todavia modulos de negocio grandes.

La prioridad actual es:

1. consolidar el core;
2. dejar estructura estable para agentes;
3. fijar contratos del kernel;
4. habilitar el futuro modulo piloto `logistics`.

## Estructura

```text
apps/
  api/                Backend FastAPI (app huesped del kernel)
  web/                Frontend shell React + Vite
packages/
  ui/                 Componentes UI compartidos
plugins/
  logistics/          Plugin de negocio
  crm/                Plugin de negocio
  productos/          Plugin de negocio
  stock/              Plugin de negocio
  ventas/             Plugin de negocio
  commerce/           Plugin de negocio
vendor/
  systutor-core/      Kernel OSS (submodule git, MIT, ADR 0029)
tools/
  migrator/           Migrador legacy
  legacy-analyzer/    Analizador del legacy
docs/
  adr/                Decisiones de arquitectura
  specs/              Especificaciones funcionales
  contracts/          Contratos humanos del sistema
infra/
  compose/            Documentacion de entorno local
```

El kernel vive en `vendor/systutor-core` (repo publico MIT). Los plugins
importan infraestructura desde `systutor.*`; la config de negocio se resuelve
en `apps/api/app/config.py` (`GasSettings`). Ver ADR 0029.

## Backend local

Requisitos esperados:

- Termux
- Python 3.12 o 3.13 local

### Nota sobre Python

La base objetivo del proyecto sigue siendo **Python 3.12**.

En Termux se acepta **Python 3.13** para desarrollo local, siempre que no se introduzcan features exclusivas de 3.13.

### Nota sobre infraestructura local

En este repositorio, **Termux es el entorno local primario**.

Por eso:

- el flujo recomendado no depende de Docker;
- `docker-compose.yml` queda como soporte secundario para entornos fuera de Termux;
- PostgreSQL y Redis pueden correr como servicios nativos de tu setup Termux o como servicios remotos accesibles por URL.

Variables base:

```bash
cp .env.example .env
```

El backend carga automáticamente el `.env` del root del proyecto al resolver `get_settings()`.

Crear entorno virtual e instalar dependencias:

 ```bash
 python3 -m venv .venv
 . .venv/bin/activate
 python3 -m pip install --upgrade pip
 python3 -m pip install -e ".[termux-dev]"
 python3 -m pip install -e vendor/systutor-core
 ```

El submodule del kernel se instala editable para que `systutor.*` apunte al
checkout de `vendor/systutor-core`. El pin del submodule se actualiza por
version explicita (ver AGENTS.md).

En Termux, `ruff` se instala por sistema para evitar compilarlo en cada `pip install`:

```bash
pkg install ruff
```

No usar en Termux:

```bash
python3 -m pip install -e ".[dev]"
```

si ese extra incluye `ruff`.

Si necesitas un entorno Python completo fuera de Termux o en CI, usa:

```bash
python3 -m pip install -e ".[dev]"
```

Instalar frontend con pnpm:

```bash
pnpm install
```

### PostgreSQL y Redis en Termux


Configura en `.env` URLs alcanzables desde tu entorno Termux :

- `SYSTUTOR_DATABASE_URL`
- `SYSTUTOR_REDIS_URL`

Configura el frontend en `apps/web/.env` a partir de `apps/web/.env.example`:

- `VITE_API_BASE_URL`

Flujo recomendado:

- usar PostgreSQL y Redis ya disponibles en tu entorno;
- o usar servicios remotos/de otra maquina de desarrollo;
- usar `docker-compose.yml` solo si trabajas fuera de Termux o en un entorno auxiliar.

### Docker Compose secundario

Si estas trabajando fuera de Termux o usando un entorno auxiliar compatible, puedes levantar servicios con:

```bash
docker compose up -d postgres redis
```



Ejecutar migraciones:

```bash
python3 -m alembic -c apps/api/alembic.ini upgrade head
```


```bash
python3 -m apps.api.app.commands.seed_demo
```

Levantar la API:

```bash
uvicorn apps.api.app.main:app --reload
```

Atajo recomendado para Termux: iniciar PostgreSQL local y backend en un solo comando:

```bash
npm run services
```

Atajos adicionales:

```bash
npm run postgres
npm run psql
npm run status:services
```

Levantar el frontend:

```bash
cp apps/web/.env.example apps/web/.env
npm run frontend
```

Alternativa directa con pnpm en Termux:

```bash
cp apps/web/.env.example apps/web/.env
node "/data/data/com.termux/files/usr/lib/node_modules/pnpm/bin/pnpm.cjs" --filter @systutor/web dev
```

Levantar worker base de eventos:

```bash
dramatiq apps.api.app.kernel.events.tasks
```

Despachar eventos pendientes desde Python:

```bash
python3 -c "from apps.api.app.kernel.events.tasks import dispatch_pending_events; print(dispatch_pending_events.fn())"
```

API base:

- `GET /api/v1/system/health`
- `GET /api/v1/system/ready`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/system/plugins`

## Aislamiento tenant activo

Desde `Core v0.3.1`, el aislamiento multi-tenant ya no es solo estructural.

Reglas activas:

- un usuario autenticado opera dentro del `tenant_id` persistido en DB;
- el JWT se valida contra usuario, tenant, branch e `is_superadmin` persistidos;
- los permisos se resuelven solo mediante roles validos dentro del tenant correcto;
- `Permission` sigue siendo catalogo global declarativo, pero no autoriza por si sola;
- `PluginRegistry` sigue siendo global tecnico;
- `health` y `ready` siguen siendo endpoints globales.

En terminos practicos:

```text
Un usuario de Tenant A no puede leer, modificar, usar permisos ni roles de Tenant B.
```

Rutas frontend base:

- `/login`
- `/app/system`
- `/app/plugins`

Credenciales demo por defecto:

- email: `admin@example.com`
- password: `ChangeMe123!`

Ejecutar pruebas:

```bash
python3 -m pytest apps/api/tests -q
```

Build frontend:

```bash
pnpm build
```

Validar calidad:

```bash
ruff check .
python3 -m pyright
python3 -m pytest apps/api/tests -q
pnpm --dir apps/web build
```

Si usas `.venv`:

```bash
ruff check .
./.venv/bin/python -m pyright
./.venv/bin/python -m pytest apps/api/tests -q
pnpm --dir apps/web build
```

## Login demo

1. Iniciar PostgreSQL y backend:
   ```bash
   npm run services
   ```

2. Sembrar usuario admin (solo la primera vez):
   ```bash
   .venv/bin/python -m apps.api.app.commands.seed_demo
   ```

3. En otra terminal, iniciar el frontend:
   ```bash
   npm run frontend
   ```

4. Abrir `http://127.0.0.1:5173/login` e ingresar:
   - **email:** `admin@example.com`
   - **password:** `ChangeMe123!`

5. Validar `/app/system` (dashboard) y `/app/plugins` (runtime).

## Flujo de prueba multi-tenant

1. Levantar backend y frontend.
2. Iniciar sesion con el usuario demo.
3. Verificar `GET /api/v1/auth/me` y confirmar `tenant_id` y `branch_id` correctos.
4. Verificar dashboard y layout.
5. Hacer logout.
6. Intentar entrar a `/app` sin token.
7. Verificar redireccion a login.
8. Probar un token invalido o manipulado contra `/api/v1/auth/me`.
9. Confirmar que `GET /api/v1/system/health` y `GET /api/v1/system/ready` siguen funcionando sin tenant.

## Documentos obligatorios

Antes de desarrollar:

- `AGENTS.md`
- `docs/adrs/`

## Regla operativa

No introducir logica de negocio grande en el kernel. El kernel solo provee infraestructura comun para modulos y plugins.

## Driver PostgreSQL

Para compatibilidad con Termux se usa `psycopg` sin dependencia binaria obligatoria.

No asumir `psycopg[binary]` como camino principal en Android/Termux.

## Runtime v0.3

El core v0.3 agrega:

- event bus interno con listeners registrados;
- `event_log` persistente con `event_outbox`;
- dispatcher reutilizable y testeable sin Redis real;
- worker base con Dramatiq + Redis;
- runtime de plugins con validacion estricta, dependencias y carga deterministica.

## Frontend Shell v0.1

El shell frontend agrega:

- login con JWT contra `/api/v1/auth/login`;
- sesion simple con rehidratacion desde `localStorage`;
- rutas protegidas para `/app/*`;
- dashboard de sistema usando `health` y `ready`;
- vista inicial del runtime de plugins usando `/api/v1/system/plugins`.
