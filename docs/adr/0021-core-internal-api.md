# SPEC 0024 — Core Internal API: comunicación inter-plugin via HTTP

## Estado

Propuesta — 2026-07-06

## Problema

Hoy los plugins se comunican entre sí imports directos de modelos:

- `logistics` importa `Product`, `ProductBrand`, `ProductCondition` desde `productos` en 7 archivos
- `stock` lee `lg_warehouses` y `prod_products` con query directa a la misma BD (ADR 0016)
- No hay un único punto de acceso a datos de otros plugins

Resultado: acoplamiento frágil, imposibilidad de separar servicios, riesgo de regresiones silenciosas.

## Relación con ADRs existentes

### ADR 0016 (Stock)

ADR 0016 establece que stock lee `lg_warehouses` y `prod_products` con query directa (misma BD, FKs reales). **SPEC 0024 no modifica esa decisión.** `core/internal_api` aplica solo cuando:

- No existe FK real entre las tablas
- El consumidor no comparte base de datos con el fuente
- Se requiere resolución de nombres/catálogos, no consulta transaccional

Stock mantiene su acceso directo a DB. Esta spec cubre únicamente los casos que hoy usan import directo de modelos sin FK real.

### ADR 0019 (Catálogos via REST desde productos)

ADR 0019 estableció el patrón de consumo REST de catálogos. SPEC 0024 formaliza ese patrón en una capa reutilizable. Una vez implementado 0024, el código existente de logistics que implementa 0019 debe migrarse a `core.internal_api`.

## Solución

Crear `core/internal_api/` como el **único punto de comunicación entre plugins via HTTP**. Cada plugin expone endpoints REST públicos; los demás los consumen via este core, nunca imports directos.

```
┌──────────┐   ┌──────────────────────┐   ┌───────────┐
│ logistics │──→│ core/internal_api    │──→│ productos │
│ stock     │──→│ (httpx.AsyncClient)  │──→│ crm       │
│ ventas    │──→│                      │   │ ...       │
└──────────┘   └──────────────────────┘   └───────────┘
```

## Diseño

### 1. Estructura

```
apps/api/app/core/internal_api/
├── __init__.py        → exporta funciones públicas async
├── client.py          → httpx.AsyncClient singleton
├── catalog.py         → resolución de catálogos (brands, products, conditions)
├── errors.py          → InternalApiError, NotFound, Timeout
```

### 2. Configuración

```python
# apps/api/app/core/config.py (agregar)
internal_api_base_url: str = "http://localhost:8000"
internal_api_key: str = ""  # service-to-service auth
```

### 3. Cliente HTTP

- Singleton `httpx.AsyncClient` (async, compatible con event loop de FastAPI)
- Timeout: 5s por defecto
- Retry: 1 reintento en errores 5xx
- Header `X-Internal-Api-Key` si está configurado
- Base URL desde settings
- Propaga `correlation_id` como header en requests internas

### 4. Propagación de tenant_id

El cliente pasa `tenant_id` como **query parameter** en toda llamada a endpoints que requieran contexto de tenant. El router de productos debe aceptar `tenant_id` como query param opcional además del `TenantContext` de JWT.

```
GET /catalog/brands?tenant_id={tenant_id}
GET /products/{id}/basic?tenant_id={tenant_id}
```

### 5. Autenticación interna

1. `SYSTUTOR_INTERNAL_API_KEY` se configura como env var
2. Las rutas de productos detectan `X-Internal-Api-Key` via middleware
3. Si el header coincide con la clave configurada:
   - Se crea un `TenantContext` de sistema (`actor_type="system"`, `actor_id="core-internal-api"`)
   - Las validaciones de permiso se **saltan** (la clave es el permiso)
   - La acción se registra en audit_log con `actor_type="system"`
4. Si el header no está presente, se usa el flujo normal de JWT + permisos

### 6. DTOs (contracts explícitos)

```python
class BrandDTO(BaseModel):
    id: str
    name: str
    code: str
    is_active: bool

class GasProductDTO(BaseModel):
    id: str
    name: str
    code: str
    content_kg: float | None
    is_active: bool

class ProductDTO(BaseModel):
    id: str
    name: str
    sku: str
    brand_id: str | None
    brand_name: str | None
    line_id: str | None
    condition_code: str | None
    is_active: bool
    weight_kg: float | None

class ConditionDTO(BaseModel):
    code: str
    name: str
    description: str | None
```

### 7. Funciones async

```python
async def resolve_brand(brand_id: str, tenant_id: str) -> BrandDTO | None
async def resolve_product(product_id: str, tenant_id: str) -> ProductDTO | None
async def resolve_condition(code: str) -> ConditionDTO | None
async def list_brands(tenant_id: str) -> list[BrandDTO]
async def list_gas_products(tenant_id: str) -> list[GasProductDTO]
async def list_conditions() -> list[ConditionDTO]
```

Cada función llama al endpoint REST correspondiente de productos. Los DTOs son Pydantic models definidos en `core/internal_api/` — namespace separado para evitar acoplamiento de schema.

### 8. Nuevos endpoints en productos

| Endpoint | Método | Response Schema | Permiso |
|----------|--------|----------------|---------|
| `GET /catalog/brands/{id}` | GET | `NamedCatalogRead` | `productos.catalog.read` |
| `GET /catalog/conditions/{code}` | GET | `ProductConditionRead` | `productos.catalog.read` |
| `GET /products/{id}/basic` | GET | `ProductBasicRead` (nuevo) | `productos.product.read` |

`ProductBasicRead` incluye: id, name, sku, brand_id, line_id, condition_code, is_active, weight_kg, created_at, updated_at. Sin precios, costos, ADR, barcodes ni media.

### 9. Observabilidad

Toda llamada a `core/internal_api` debe:
- Propagar `correlation_id` como header en la request interna
- Registrar latencia de la llamada (log DEBUG)
- Registrar errores de timeout/404 con level WARNING
- NO registrar el `X-Internal-Api-Key` en ningún log

## Migración completa de imports directos

| Archivo en logistics | Importa de productos | Acción |
|---------------------|---------------------|--------|
| `services/product_bridge.py` | Product, ProductBrand, ProductCondition | Migrar a `core.internal_api.catalog` |
| `services/envase.py` | Product | Reemplazar con `resolve_product` |
| `services/cylinders.py` | Product | Reemplazar con `resolve_product` |
| `services/planning.py` | Product | Reemplazar con `resolve_product` |
| `services/extensions.py` | Product | Reemplazar con `resolve_product` |
| `services/documents.py` | Product, ProductAdr | Reemplazar (extender catalog si falta ADR) |
| `migrations/010_*.py` | Product | No migrar (migración histórica, no código activo) |

## No objetivos

- Crear un bus de eventos o message broker
- Reemplazar Dramatiq para tareas async
- Sincronizar datos entre plugins (solo consulta)
- Validación transaccional entre plugins
- Modificar el patrón de acceso directo a DB de stock (ADR 0016)

## Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Llamada HTTP intra-proceso agrega latencia vs import directo | Bajo | AsyncClient no bloquea. Si escala, cachear en el core |
| Error 404 de catálogo deja al plugin sin datos | Medio | Retornar None, el caller decide cómo manejar |
| Dependencia circular si core necesita datos de plugins | Bajo | core es solo infraestructura, no tiene lógica de negocio |
| Token de API interno expuesto en logs | Alto | No loggear header. Usar env var, no hardcodear |
| Sync httpx bloquea event loop | Alto | Solucionado: usar `httpx.AsyncClient` |

## Criterios de aceptación

1. `core/internal_api/client.py` existe con `httpx.AsyncClient`, timeout 5s, retry 1
2. `core/internal_api/catalog.py` resuelve brand, product, condition por ID (async)
3. `core/internal_api/catalog.py` lista brands, gas products, conditions (async)
4. Endpoints individuales (`GET /brands/{id}`, `GET /conditions/{code}`, `GET /products/{id}/basic`) existen en productos
5. `product_bridge.py` usa `core.internal_api` sin imports directos a productos
6. `envase.py`, `cylinders.py`, `planning.py`, `extensions.py`, `documents.py` migrados
7. `tenant_id` se propaga como query param en todas las llamadas
8. `X-Internal-Api-Key` autentica calls internas sin requerir JWT
9. DTOs definidos con campos explícitos
10. Todos los tests existentes pasan

## Dependencias

- httpx >=0.27 (ya en pyproject.toml)
- Consolidación de catálogos (0023AN + migración 0014)
- ADR 0019 (precedente de consumo REST de catálogos)
- ADR 0021 (nuevo — documentar patrón de internal API)
