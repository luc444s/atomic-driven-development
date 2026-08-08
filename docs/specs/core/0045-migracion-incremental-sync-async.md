---
id: "0045"
title: "Migración incremental Sync → Async por router"
domain: infrastructure
module: backend
status: vigente
---

# SPEC 0045 — Migración incremental Sync → Async por router

## Contexto

El backend usa FastAPI con endpoints sync (`def`) y SQLAlchemy sync (`create_engine`, `Session`). Con 10+ usuarios concurrentes, cada request sync bloquea un thread del pool mientras espera I/O de PostgreSQL.

**Stack actual:**
- FastAPI endpoints sync (`def`)
- SQLAlchemy sync (`create_engine`, `sessionmaker[Session]`)
- Driver: `psycopg` (sync)
- Pool: ~40 threads

**Stack objetivo:**
- FastAPI endpoints async (`async def`)
- SQLAlchemy async (`create_async_engine`, `async_sessionmaker[AsyncSession]`)
- Driver: `asyncpg`
- Pool: event loop (1 thread, non-blocking)

## Solución

Migración **incremental** por router. Sync y async coexisten. Cada router migra independiente sin romper los demás.

---

## 1. Infraestructura dual (Paso 1)

### `apps/api/app/core/database.py`

Agregar al lado del sync existente:

```python
def _to_async_url(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql+asyncpg://")

def build_async_engine(settings: Settings) -> AsyncEngine | None:
    """Solo PostgreSQL. SQLite retorna None."""
    if not settings.database_url.startswith("postgresql"):
        return None
    return create_async_engine(_to_async_url(settings.database_url), ...)

def build_async_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession] | None:
    engine = build_async_engine(settings)
    if engine is None:
        return None
    return async_sessionmaker(bind=engine, ...)

async def async_db_session_scope(factory) -> AsyncGenerator[AsyncSession, None]:
    async with factory() as session:
        yield session
```

### `apps/api/app/api/deps.py`

Agregar `get_async_db_session`:
```python
async def get_async_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    factory = ensure_async_session_factory(request.app)
    async for session in async_db_session_scope(factory):
        yield session
```

### `apps/api/app/core/lifecycle.py`

- `bootstrap_app_state`: crear `async_session_factory` eagerly
- `ensure_async_session_factory`: lazy init

### `pyproject.toml`

```toml
"sqlalchemy[asyncio]>=2.0,<2.1",
"asyncpg>=0.30,<1.0",
```

**Resultado:** infraestructura async lista. Sin cambios en endpoints existentes.

---

## 2. Patrón de migración por router (Paso 2)

### Regla

Service layer se queda **sync**. Router crea `Session` sync fresca por request via `asyncio.to_thread`.

### Helpers (en cada router migrado)

```python
def _make_sync_session(request: Request) -> Session:
    factory = ensure_session_factory(request.app)
    return factory()

async def _run_sync_readonly[T](request, fn, *args, **kwargs) -> T:
    def _call():
        db = _make_sync_session(request)
        try:
            return fn(db, *args, **kwargs)
        finally:
            db.close()
    return await asyncio.to_thread(_call)

async def _run_mutation_with_snapshot[T](request, mutation_fn, snapshot_fn, *args, **kwargs) -> T:
    def _call():
        db = _make_sync_session(request)
        try:
            result = mutation_fn(db, *args, **kwargs)
            db.commit()
            return snapshot_fn(db, result)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    return await asyncio.to_thread(_call)
```

### Endpoint migrado

```python
# ANTES (sync)
@router.get("")
def get_items(db: Session = DB_SESSION):
    return list_items(db)

# DESPUÉS (async)
@router.get("")
async def get_items(request: Request):
    return await _run_sync_readonly(request, list_items)
```

---

## 3. Orden de migración (Paso 3)

### Fase 1 — Críticos (1-2 días)

| Router | Endpoints | Por qué |
|--------|-----------|---------|
| `sessions.py` | 12 | Jornadas — más uso |
| `session_waybills.py` | 3 | Carta porte |
| `route_operations.py` | 13 | Operaciones de ruta |

### Fase 2 — Importantes (2-3 días)

| Router | Endpoints |
|--------|-----------|
| `load_plans.py` | 9 |
| `load_serials.py` | 7 |
| `reconciliation.py` | 5 |

### Fase 3 — Baja prioridad (3-5 días)

| Router | Endpoints |
|--------|-----------|
| `crm/backend/router.py` | 42 |
| `stock/backend/router.py` | 25 |
| `productos/backend/router.py` | 64 |
| Core APIs | ~30 |

### Fase 4 — Limpieza (1 día)

- Eliminar `get_db_session` sync
- Eliminar `build_engine` sync
- Renombrar `get_async_db_session` → `get_db_session`

---

## 4. Testing

### Cada fase

```bash
# Lint
ruff check plugins/[module]/backend/routers/[router].py

# Type check
pyright plugins/[module]/backend/routers/[router].py

# Tests existentes
pytest apps/api/tests/ -x -q
```

### Validación por router

```python
# Test async endpoint
async def test_get_sessions_async():
    response = await client.get("/api/v1/plugins/logistics/vehicle-sessions")
    assert response.status_code == 200
```

---

## 5. Rollback

Cada router es independiente. Si algo falla:
1. Revertir el router específico
2. Los demás siguen funcionando
3. El service layer sync nunca se toca

---

## 6. Criterios de aceptación

- [ ] `asyncpg` instalado
- [ ] `build_async_engine` funciona con PostgreSQL
- [ ] `build_async_engine` retorna None con SQLite
- [ ] Sessions router migrado (12 endpoints)
- [ ] Carta porte router migrado (3 endpoints)
- [ ] Route operations router migrado (13 endpoints)
- [ ] Tests existentes pasan
- [ ] Pyright sin errores
- [ ] Ruff sin errores
- [ ] Sync endpoints originales eliminados al final

---

## 7. Archivos afectados

### Nuevos
- Ninguno (modificaciones existentes)

### Modificados — Core
- `apps/api/app/core/database.py`
- `apps/api/app/api/deps.py`
- `apps/api/app/core/lifecycle.py`
- `pyproject.toml`

### Modificados — Logistics
- `plugins/logistics/backend/routers/sessions.py`
- `plugins/logistics/backend/routers/session_waybills.py`
- `plugins/logistics/backend/routers/route_operations.py`

### Sin cambios
- Service layer (sessions.py, route_operations.py, etc.)
- Models
- Migrations
- Frontend
