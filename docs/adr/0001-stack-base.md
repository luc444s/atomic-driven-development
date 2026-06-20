# ADR 0001 - Stack Base

## Estado
Aceptado

## Contexto

SYSTUTOR OSS necesita un stack técnico base cerrado para evitar ambigüedad al iniciar el desarrollo del core, plugins, tooling interno y CI/CD.

El proyecto requiere una base moderna, auditable, modular y adecuada para desarrollo humano + IA.

## Decisión

El stack oficial base de SYSTUTOR OSS será:

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL 16
- Redis
- Dramatiq con Redis como broker
- Pydantic v2

### Calidad backend

- Pyright para typing
- Ruff para lint y format
- Pytest para testing

### Frontend

- React
- Vite
- TypeScript
- Zustand para estado local
- TanStack Query para server state
- React Router para routing
- Tailwind CSS
- shadcn/ui como base de componentes

### Infraestructura

- Docker Compose para desarrollo local
- Traefik como reverse proxy en producción
- GitHub Actions para CI/CD


### Ru  ntime / tooling adicional

- Backend server: Uvicorn
- Driver PostgreSQL: asyncpg
- Driver Redis: redis-py
- Package manager Python: uv
- Package manager frontend: pnpm
- Node.js: LTS actual


## Consecuencias

- El proyecto evita discusiones repetidas sobre herramientas base.
- La documentación, el scaffold y la automatización deberán alinearse con este stack.
- Nuevas propuestas que cambien herramientas base requerirán ADR adicional.
- PostgreSQL se fija en versión 16 para mantener consistencia en desarrollo, CI y despliegue.
