# SPEC 0023AM — Envases: pesos, trazabilidad y contratos

## Estado

Parcialmente obsoleta — 2026-07-07

> Nota: el capítulo `0023B` quedó descartado.
> `lg_cylinder_average_weights` se reemplazó por `prod_products.default_weight_kg`.
> `0023AD` ahora tiene spec standalone autoritativa para contratos, incluyendo numeración legacy y workflow documental.
> Los capítulos `0023C` y `0023AD` aquí quedan solo como referencia parcial.

## Contexto

Después de cerrar `0023A` (ficha técnica completa), los gaps restantes del dominio envases se concentran en tres áreas que comparten el mismo owner natural (`logistics`) y que dependen de la misma entidad base (`lg_cylinders`):

> **Nota:** `0023D` (trazabilidad medicinal) permanece abierta según el INDEX (prioridad #1 de Fase 1). Esta spec no la cubre. La vista de trazabilidad (0023C) debe diseñarse para incorporar flags medicinales cuando 0023D se implemente.

- **peso promedio**: hoy no existe fallback cuando un cilindro no tiene peso real;
- **trazabilidad extendida**: los datos están dispersos en 7+ tablas pero no hay una vista operativa unificada que muestre por dónde pasó cada envase (almacén, vehículo, ruta, cliente);
- **contratos de envases**: no existe absolutamente nada — ni modelos, ni endpoints, ni UI — y es uno de los gaps más grandes del dominio logístico según `Grab2` y el legacy.

Esta spec las consolida como una sola lectura de dominio porque:

1. las tres operan sobre el mismo agregado (`lg_cylinders`);
2. las tres son prerequisito para Fase 2 (carga/reparto);
3. las tres comparten riesgos de integración con `stock`, `crm` y futura facturación;
4. separarlas en specs individuales fragmentaría el backlog sin aportar independencia real de implementación.

## Objetivo

Cerrar los tres gaps restantes del dominio envases:

- `0023B` — peso real y promedio (modelo de fallback + backend + UI admin);
- `0023C` — trazabilidad operativa extendida (vista unificada por cilindro);
- `0023AD` — contratos de envases (submódulo completo: modelo, CRUD, workflow, integración).

## No objetivos
    
Esta spec NO cubre:

- `0023AE` — firma contractual (se aborda post-contratos como mejora);
- `0023E/0023F/0023G` — almacén móvil, agenda→carga, stock libre (Fase 2);
- `0023H/0023I` — escaneo de carga y confirmación de conductor;
- `0023J/0023K` — carta porte digital y albarán operativo;
- `0023M/0023N/0023O/0023P` — ADR y peso de transporte;
- reportes gerenciales o consistencia documental.

## Fuentes base

- `docs/specs/core/0023-logistics-operacion-real/index.md`
- `docs/avances/logistics.md`
- `grabaciones/Grab2/` — contratos de envases, pesos operativos, trazabilidad
- `plugins/logistics/backend/models/cylinder.py`
- `plugins/logistics/backend/services/extensions.py` — `_cylinder_weight()`
- `plugins/logistics/backend/router.py` — endpoints existentes de peso
- `plugins/logistics/frontend/cylinders/hooks/use-cylinder-data.ts`

---

> **Convención de nomenclatura:** Todos los permisos usan el prefijo `logistics.` y todos los eventos usan el prefijo `logistics.` conforme a ADR 0003 y ADR 0005. Deben declararse en `plugins/logistics/plugin.json`.
>
> **OpenAPI como fuente de verdad:** Los schemas Pydantic de esta spec generan el contrato OpenAPI. El frontend no escribe tipos a mano — `openapi-typescript` genera `api-types.ts` desde `/openapi.json`. Los schemas listados abajo son Pydantic; los tipos TypeScript se derivan automáticamente.
>
> **Core First:** Todo componente UI nuevo se crea primero como genérico en `apps/web/src/shared/ui/` si tiene potencial de reuso. Los componentes listados en frontend son wrappers finos que componen componentes Core con props/fetchFn del dominio.

## Capítulo 1: 0023B — Peso real y promedio

### Problema actual

Hoy `lg_cylinders` tiene `weight_origin` y `weight_current`. Si ambos son `NULL`, `_cylinder_weight()` devuelve `0` — no hay fallback a un peso promedio por tipo/material/capacidad.

El spec index documenta: *"Si no hay peso real, usar un peso promedio por tipo/material/capacidad"* — y lo marca como gap fuerte.

### Solución propuesta

#### 1. Modelo `lg_cylinder_average_weights`

```python
class LogisticsCylinderAverageWeight(Base):
    __tablename__ = "lg_cylinder_average_weights"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("core_tenants.id"))
    brand_id: Mapped[int | None] = mapped_column(ForeignKey("lg_brands.id"))
    gas_group_id: Mapped[int | None] = mapped_column(ForeignKey("lg_gas_groups.id"))
    condition: Mapped[str | None] = mapped_column(ForeignKey("lg_cylinder_conditions.code"))
    material: Mapped[str | None]   # ej. "ACERO", "ALUMINIO"
    capacity_kg: Mapped[Decimal | None]  # rango de capacidad
    weight_kg: Mapped[Decimal]     # peso promedio en kg
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

Reglas de matching (en orden de precedencia):
1. `brand_id + gas_group_id + condition + material` — el más específico
2. `brand_id + gas_group_id + condition` — sin material
3. `gas_group_id + condition` — sin marca
4. `condition + material` — sin gas
5. `condition` — fallback genérico por estado (LLENA/VACÍA)

#### 2. Migración

`<NN>_cylinder_average_weights.py` — crear tabla + seed data inicial desde valores operativos conocidos. (NN = próximo número de migración disponible)

#### 3. Endpoints (en `routers/average_weights.py` — no agregar a `router.py`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/cylinders/average-weights` | Listar pesos promedio (filtrable por tenant) |
| `GET` | `/cylinders/average-weights/{id}` | Detalle |
| `POST` | `/cylinders/average-weights` | Crear |
| `PATCH` | `/cylinders/average-weights/{id}` | Actualizar |
| `DELETE` | `/cylinders/average-weights/{id}` | Desactivar (soft) |

Permisos: `logistics.average_weight.view`, `logistics.average_weight.create`, `logistics.average_weight.update`, `logistics.average_weight.delete`.

#### 4. Lógica de fallback

Modificar `_cylinder_weight()` en `services/extensions.py`:

```python
def _cylinder_weight(cylinder) -> Decimal:
    if cylinder.weight_current:
        return cylinder.weight_current
    if cylinder.weight_origin:
        return cylinder.weight_origin
    # fallback a peso promedio
    return _get_average_weight(
        brand_id=cylinder.brand_id,
        gas_group_id=cylinder.gas_group_id,
        condition=cylinder.condition,
    )
```

`_get_average_weight()` debe:
1. buscar el match más específico en `lg_cylinder_average_weights`;
2. `material` y `capacity_kg` se resuelven internamente desde `cylinder.material` y `cylinder.capacity_kg` — si el cilindro no tiene esos datos, se omiten del matching;
3. cachear en Redis (TTL: 1 hora) para no golpear DB en cada cálculo de carga;
4. si Redis no está disponible, degradar gracefulmente a DB query directa sin caché;
5. devolver `0` si no hay match (comportamiento actual como último recurso).

#### 5. Frontend

Componentes Core que se reusan directamente: `DataTable`, `Dialog`, `Combobox`, `Select`, `Input`, `Badge`, `ConfirmDialog`, `Pagination`, `EmptyState`.

- **Admin section** en LogisticsPage o página separada: `DataTable` + `Dialog` para CRUD de pesos promedio
  - Columnas: marca, grupo gas, condición, material, capacidad, peso
  - Filtros por marca (`Combobox`), gas (`Combobox`), condición (`Select`)
  - Wrapper mínimo `AverageWeightsSection` que inyecta columnas y fetchFn
- **Indicador visual** en detalle de cilindro: `Badge` que muestra "(peso promedio)" vs "(peso real)" según `weightSource`

#### 6. Eventos

- `logistics.cylinder_average_weight.created`
- `logistics.cylinder_average_weight.updated`
- `logistics.cylinder_average_weight.deleted`

#### 7. Tests

- Unitario: `_get_average_weight()` con diferentes combinaciones de matching
- Unitario: `_cylinder_weight()` con prioridad peso real > origen > promedio > 0
- Integración: CRUD de pesos promedio
- Integración: cálculo de carga con fallback

---

## Capítulo 2: 0023C — Trazabilidad operativa extendida

### Problema actual

Hoy los datos de trazabilidad existen en 7+ tablas:

| Tabla | Datos |
|-------|-------|
| `lg_cylinder_state_log` | Cambios de estado (CREATE, ACTIVO, INACTIVO, etc.) |
| `lg_scan_log` | Escaneos |
| `lg_cylinder_retimbrados` | Retimbrados |
| `lg_hydrostatic_tests` | Pruebas hidrostáticas |
| `lg_cylinder_services` | Servicios |
| `lg_cylinder_ownership` | Custodia / pertenencia |
| `lg_load_details` | Cargas en rutas |
| `lg_movement_details` | Movimientos entre almacenes |
| `lg_label_history` | Historial de etiquetas |

Pero no existe una **vista unificada** que muestre la línea de tiempo completa de un cilindro: "dónde estuvo, cuándo, en qué estado, en qué vehículo, en qué ruta, con qué cliente".

### Solución propuesta

#### 1. Endpoint unificado de trazabilidad

`GET /cylinders/{cylinder_id}/traceability` (en `routers/traceability.py` — no agregar a `router.py`)

Response:

```json
{
  "cylinder_id": 1,
  "serial": "B-12345",
  "events": [
    {
      "timestamp": "2026-06-15T08:30:00Z",
      "type": "LOADED",
      "description": "Cargado en ruta R-2026-001",
      "location": "Vehículo MAT-1234",
      "route_name": "R-2026-001",
      "customer_name": "Cliente XYZ",
      "user": "Juan Pérez",
      "metadata": {}
    },
    {
      "timestamp": "2026-06-14T10:00:00Z",
      "type": "SCANNED",
      "description": "Escaneado en almacén principal",
      "location": "Almacén Central",
      "user": "María García",
      "metadata": { "action": "VERIFY" }
    }
  ],
  "summary": {
    "total_events": 24,
    "first_event": "2025-01-10T09:00:00Z",
    "last_event": "2026-06-15T08:30:00Z",
    "current_state": "ACTIVO",
    "current_location": "Almacén Central"
  }
}
```

Tipos de evento a incluir:
- `CREATED` — alta del cilindro
- `STATE_CHANGED` — cambio de estado (incluye estado anterior → nuevo)
- `SCANNED` — escaneo con ubicación
- `LOADED` — cargado en ruta/vehículo
- `UNLOADED` — descargado de ruta/vehículo
- `MOVED` — movimiento entre almacenes
- `HYDROTESTED` — prueba hidrostática
- `RETIMBRADO` — retimbrado
- `SERVICED` — servicio técnico
- `OWNERSHIP_CHANGED` — cambio de custodia
- `LABEL_PRINTED` — impresión de etiqueta
- `WEIGHT_UPDATED` — actualización de peso
- `MEDICAL_FLAG_CHANGED` — cambio de flag medicinal
- `CONTRACT_ASSIGNED` — asignado a un contrato
- `CONTRACT_RELEASED` — liberado de un contrato

#### 2. Servicio de trazabilidad

Crear `services/traceability.py` con:

- `get_cylinder_traceability(cylinder_id, filters?)` — consulta unificada que UNION de las 7+ tablas, ordenado por timestamp descendente
- `paginate_events(page, per_page)` — soporte de paginación
- `build_event_summary(events)` — resumen estadístico

Optimización: para cilindros con muchos eventos (>1000), usar consultas paginadas con cursor por timestamp + cache por 5 minutos.

#### 3. Frontend

Componentes Core que se reusan directamente: `Tabs`, `Badge`, `Popover`, `EmptyState`, `Skeleton`, `Select`, `DatePicker` (si existe en shared/ui).

**Nuevo componente: `TraceabilityTimeline`** — timeline vertical genérica en `shared/ui/` (reusable para cualquier entidad con eventos). Props: `events: TraceabilityEvent[]`, `filters`, `onEventClick`.

- Vista de timeline vertical
- Cada evento muestra: icono por tipo, timestamp, descripción, ubicación, usuario
- Filtros por tipo de evento y rango de fechas
- Expandible para ver metadata adicional
- Badge de conteo por tipo de evento

**Wrapper de dominio: `CylinderTraceabilityTimeline`** en logistics:
- Inyecta fetchFn (`apiRequest` a `GET /cylinders/{id}/traceability`)
- Inyecta columnas y filtros del dominio
- Sin lógica interna de timeline — delega en `TraceabilityTimeline`

**Integración en `FullDetailInfoDialog`:**

- Reemplazar tablas sueltas usando `Tabs` + `TraceabilityTimeline`
- Pestaña "Trazabilidad" con timeline + resumen
- Pestañas separadas solo para edición (retimbrados, PH, servicios)

#### 4. Eventos

- `logistics.cylinder.traceability_viewed` — auditoría de consulta

#### 5. Tests

- Unitario: `get_cylinder_traceability()` con datos mock de múltiples tablas
- Unitario: paginación y filtros por tipo/fecha
- Integración: endpoint devuelve estructura correcta con cilindro real
- Integración: rendimiento con >100 eventos simulados

---

## Capítulo 3: 0023AD — Contratos de envases

### Problema actual

No existe absolutamente nada en código: 0 modelos, 0 endpoints, 0 UI. Es uno de los gaps más grandes de todo el dominio logístico según el INDEX y `Grab2`.

El legacy y `Grab2` describen:

- contrato anual pagado por adelantado, renovable por facturación;
- contrato diario como modalidad alternativa;
- el contrato termina al devolver la bombona (no tiene fecha fija);
- se amarra al tipo/cantidad de envases, no a una serie específica;
- puede generarse antes de la entrega física;
- puede requerir firma (física primero, digital después).

### Solución propuesta

#### 1. Modelo `lg_cylinder_contracts`

```python
class LogisticsCylinderContract(Base):
    __tablename__ = "lg_cylinder_contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("core_tenants.id"))
    branch_id: Mapped[int | None] = mapped_column(ForeignKey("core_branches.id"))

    # Identidad
    contract_number: Mapped[str] = mapped_column(unique=True)
    contract_type: Mapped[str]    # ContractType: ANNUAL | DAILY
    status: Mapped[str]           # ContractStatus: DRAFT | ACTIVE | TERMINATED | CANCELLED

    # Partes
    customer_id: Mapped[int] = mapped_column(ForeignKey("crm_customers.id"))
    customer_snapshot: Mapped[str]  # JSON congelado al activar

    # Términos
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    renewal_type: Mapped[str | None]  # AUTO | MANUAL | NONE

    # Envases (cantidad y precio por unidad — logistics owned)
    cylinder_type_id: Mapped[int | None] = mapped_column(ForeignKey("lg_gas_groups.id"))
    cylinder_condition: Mapped[str | None] = mapped_column(ForeignKey("lg_cylinder_conditions.code"))
    quantity: Mapped[int]
    unit_price: Mapped[Decimal]

    # Firma
    signed_at: Mapped[datetime | None]
    signed_by: Mapped[str | None]
    signature_type: Mapped[str | None]  # PHYSICAL | DIGITAL (futuro)

    # Control
    notes: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("core_users.id"))
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    terminated_at: Mapped[datetime | None]
    termination_reason: Mapped[str | None]
```

> **Nota:** `total_amount`, `tax_rate`, `tax_amount`, `grand_total`, `billing_frequency`, `billing_day` e `invoice_id` se excluyen deliberadamente del modelo. Pertenecen al futuro módulo de facturación, no a logistics. Cuando facturación exista, consumirá `quantity * unit_price` desde aquí y añadirá sus propios campos en una extensión propia.
>
> `customer_snapshot` incluye: `legal_name`, `commercial_name`, `document_number`, `fiscal_address`, `phone`, `email`. Se captura al activar el contrato y no se actualiza automáticamente. Sirve para preservar el contexto comercial del contrato independientemente de cambios futuros en la ficha del cliente.

#### 2. Modelo `lg_cylinder_contract_items`

Para contratos que especifican cilindros individuales (opcional, no obligatorio):

```python
class LogisticsCylinderContractItem(Base):
    __tablename__ = "lg_cylinder_contract_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("core_tenants.id"))
    contract_id: Mapped[int] = mapped_column(ForeignKey("lg_cylinder_contracts.id"))
    cylinder_id: Mapped[int | None] = mapped_column(ForeignKey("lg_cylinders.id"))
    serial: Mapped[str | None]          # si no está en sistema aún
    quantity: Mapped[int] = 1
    unit_price: Mapped[Decimal]
    delivered_at: Mapped[datetime | None]
    returned_at: Mapped[datetime | None]
```

#### 3. Migración

`<NN+1>_cylinder_contracts.py` — crear `lg_cylinder_contracts` + `lg_cylinder_contract_items`.

#### 4. Endpoints (en `routers/contracts.py` — no agregar a `router.py`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/cylinders/contracts` | Listar contratos (filtros: customer, status, type, date range) |
| `GET` | `/cylinders/contracts/{id}` | Detalle con items |
| `POST` | `/cylinders/contracts` | Crear contrato |
| `PATCH` | `/cylinders/contracts/{id}` | Actualizar (solo si DRAFT) |
| `POST` | `/cylinders/contracts/{id}/activate` | Activar contrato |
| `POST` | `/cylinders/contracts/{id}/terminate` | Terminar contrato (requiere motivo) |
| `POST` | `/cylinders/contracts/{id}/renew` | Renovar (crea nuevo período) |
| `GET` | `/cylinders/contracts/{id}/items` | Listar items del contrato |
| `POST` | `/cylinders/contracts/{id}/items` | Agregar item (cilindro) |
| `PATCH` | `/cylinders/contracts/{id}/items/{item_id}` | Marcar como entregado/devuelto |
| `GET` | `/customers/{customer_id}/contracts` | Contratos de un cliente |

Permisos: `logistics.contract.view`, `logistics.contract.create`, `logistics.contract.update`, `logistics.contract.activate`, `logistics.contract.terminate`, `logistics.contract.renew`.

#### 5. Workflow de estados

```
DRAFT ──→ ACTIVE ──→ TERMINATED
  │                     │
  └──→ CANCELLED        └──→ (histórico)
```

- **DRAFT**: recién creado, editable
- **ACTIVE**: vigente, facturable, no editable excepto items
- **TERMINATED**: finalizado por devolución o cancelación
- **CANCELLED**: cancelado antes de activar

Transiciones:
- `activate()`: DRAFT → ACTIVE (valida datos mínimos: customer, quantity, dates)
- `terminate(reason)`: ACTIVE → TERMINATED (requiere motivo)
- `cancel()`: DRAFT → CANCELLED

#### 6. Reglas de negocio

1. Un cliente puede tener múltiples contratos activos (distinto tipo/grupo);
2. Un cilindro puede pertenecer a un solo contrato activo a la vez (validar en backend);
3. Al terminar un contrato, los cilindros asignados quedan libres;
4. El contrato diario no requiere fecha de fin (se termina al devolver);
5. El contrato anual puede configurarse con renovación automática o manual;
6. El correlativo `contract_number` se genera automáticamente con formato `CT-{tenant}-{YYYY}-{NNNNNN}`.

#### 7. Integración con cilindros

- En el detalle del cilindro debe verse: "Contrato: CT-2026-000001 (ACTIVO)"
- Al crear/mover cilindros, verificar que el contrato destino esté activo
- El contrato debe poder precargarse desde el form de cilindro (campo `contract_id` opcional)

#### 8. Frontend

Componentes Core que se reúsan directamente: `DataTable`, `Dialog`, `Combobox` (cliente, tipo), `Select` (estado, renovación), `Input`, `Badge`, `ConfirmDialog`, `Pagination`, `Card`, `Tabs`, `EmptyState`.

**Sección "Contratos" en LogisticsPage:**

| Componente | Tipo | Descripción |
|------------|------|-------------|
| `ContractsSection` | Wrapper dominio | `DataTable` + filtros (cliente vía `SearchDialog`, estado vía `Select`, tipo, rango fechas) |
| `ContractFormDialog` | Wrapper dominio | `Dialog` + `Combobox` cliente + `Input` cantidad/precio + `Select` tipo/renovación + `DatePicker` fechas |
| `ContractDetailDialog` | Wrapper dominio | `Dialog` con `Tabs`: items, timeline, acciones |
| `ContractStatusBadge` | Wrapper dominio | `Badge` con color map por estado |
| `ContractItemForm` | Wrapper dominio | mini-form con `Combobox` cilindro + `Input` serial + fechas |
| `ContractCard` | Wrapper dominio | `Card` para sección en CRM |

**UX workflow:**

1. Oficina crea contrato en DRAFT con: cliente, tipo, cantidad, precio, fechas
2. Agrega cilindros específicos (opcional — puede agregarse después)
3. Activa el contrato → pasa a ACTIVE
4. Se genera correlativo automático
5. Al devolver cilindros, se registra `returned_at` en items
6. Si todos los cilindros fueron devueltos, ofrecer terminar contrato

**En ficha de cliente (CRM):**

- Sección "Contratos de envases activos" con cards resumen
- Link a detalle completo en logistics

#### 9. Permisos

| Permiso | Alcance |
|---------|---------|
| `logistics.contract.view` | Ver contratos y detalle |
| `logistics.contract.create` | Crear contratos en DRAFT |
| `logistics.contract.update` | Editar contratos DRAFT |
| `logistics.contract.activate` | Activar contratos (pasa a ACTIVE) |
| `logistics.contract.terminate` | Terminar contratos activos |
| `logistics.contract.renew` | Renovar contratos |

#### 10. Eventos

- `logistics.cylinder_contract.created`
- `logistics.cylinder_contract.updated`
- `logistics.cylinder_contract.activated`
- `logistics.cylinder_contract.terminated`
- `logistics.cylinder_contract.renewed`
- `logistics.cylinder_contract_item.delivered`
- `logistics.cylinder_contract_item.returned`

#### 11. Tests

- Unitario: validación de reglas de negocio
- Unitario: transiciones de estado
- Unitario: generación de correlativo
- Integración: CRUD completo
- Integración: workflow DRAFT → ACTIVE → TERMINATED
- Integración: integración con cilindros (asignación, liberación)

---

## Dependencias entre capítulos

```
0023B (pesos)  →  ninguno (independiente)
0023C (trazabilidad)  →  ninguno (solo lectura)
0023AD (contratos)  →  ninguno (submódulo nuevo)
```

Los tres capítulos son independientes entre sí y pueden implementarse en cualquier orden o en paralelo.

## Orden de implementación sugerido

| Orden | Capítulo | Esfuerzo | Justificación |
|-------|----------|----------|---------------|
| 1 | 0023B — Pesos promedio | Bajo | Modelo pequeño, cambio localizado en backend, impacto visible inmediato |
| 2 | 0023C — Trazabilidad extendida | Bajo–Medio | Solo consulta, no modifica datos existentes, mejora UX significativa |
| 3 | 0023AD — Contratos de envases | Alto | Submódulo completo, requiere más ciclos de diseño y pruebas |

## Cambios de datos

### Nuevas tablas

| Tabla | Capítulo | Descripción |
|-------|----------|-------------|
| `lg_cylinder_average_weights` | 0023B | Pesos promedio por marca/gas/condición/material |
| `lg_cylinder_contracts` | 0023AD | Contratos de envases |
| `lg_cylinder_contract_items` | 0023AD | Items (cilindros) por contrato |

### Sin cambios en tablas existentes

Ninguno de los tres capítulos modifica tablas existentes. Son aditivos.

## API / contrato esperado

Los schemas Pydantic son la fuente de verdad. Los tipos TypeScript se generan automáticamente vía `openapi-typescript`. Aquí los Pydantic schemas correspondientes:

### 0023B

```python
class CylinderAverageWeightRead(BaseModel):
    id: int
    brand_id: int | None
    gas_group_id: int | None
    condition: str | None
    material: str | None
    capacity_kg: Decimal | None
    weight_kg: Decimal
    is_active: bool

class CylinderAverageWeightCreate(BaseModel):
    brand_id: int | None = None
    gas_group_id: int | None = None
    condition: str | None = None
    material: str | None = None
    capacity_kg: Decimal | None = None
    weight_kg: Decimal

class CylinderWithWeightRead(CylinderRead):
    used_weight: Decimal       # peso efectivo (real, origen, promedio o 0)
    weight_source: str         # REAL | ORIGIN | AVERAGE | DEFAULT
    average_weight_id: int | None = None
```

### 0023C

```python
class TraceabilityEventRead(BaseModel):
    timestamp: datetime
    type: str
    description: str
    location: str | None = None
    route_name: str | None = None
    customer_name: str | None = None
    user: str | None = None
    metadata: dict[str, Any] = {}

class TraceabilitySummary(BaseModel):
    total_events: int
    first_event: datetime
    last_event: datetime
    current_state: str
    current_location: str | None = None

class CylinderTraceabilityRead(BaseModel):
    cylinder_id: int
    serial: str
    events: list[TraceabilityEventRead]
    summary: TraceabilitySummary
```

### 0023AD

```python
from enum import StrEnum

class ContractStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    TERMINATED = "TERMINATED"
    CANCELLED = "CANCELLED"

class ContractType(StrEnum):
    ANNUAL = "ANNUAL"
    DAILY = "DAILY"

class CylinderContractRead(BaseModel):
    id: int
    contract_number: str
    contract_type: ContractType
    status: ContractStatus
    customer_id: int
    customer_name: str
    start_date: date
    end_date: date | None = None
    renewal_type: str | None = None  # AUTO | MANUAL | NONE
    cylinder_type_id: int | None = None
    quantity: int
    unit_price: Decimal
    signed_at: datetime | None = None
    signed_by: str | None = None
    notes: str | None = None
    items: list[CylinderContractItemRead] = []

class CylinderContractItemRead(BaseModel):
    id: int
    contract_id: int
    cylinder_id: int | None = None
    serial: str | None = None
    quantity: int = 1
    unit_price: Decimal
    delivered_at: datetime | None = None
    returned_at: datetime | None = None

class CylinderContractCreate(BaseModel):
    contract_type: ContractType
    customer_id: int
    start_date: date
    end_date: date | None = None
    renewal_type: str | None = None
    cylinder_type_id: int | None = None
    cylinder_condition: str | None = None
    quantity: int
    unit_price: Decimal
    notes: str | None = None
```

## Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| 0023AD requiere integración con facturación futura | Alto | El futuro módulo de facturación añadirá su propia FK a `lg_cylinder_contracts`. Logistics no necesita `invoice_id`. |
| Pesos promedio pueden no reflejar la realidad operativa si seed data es incorrecta | Medio | Hacer editable desde UI; revisar seed data con datos legacy reales |
| Trazabilidad puede ser lenta con muchos eventos | Medio | Cache + paginación por cursor desde el inicio |
| Contratos sin firma digital pueden quedar incompletos | Bajo | Firmar físicamente y registrar `signature_type: PHYSICAL`; versión digital queda para 0023AE |
| Redis no disponible para caché de pesos promedio | Bajo | Fallback a DB query directa sin caché |

## Auditoría y observabilidad

Cada operación debe registrar evento de auditoría con: `timestamp`, `user_id`, `action`, `resource_type`, `resource_id`, `metadata` (cambios aplicados).

| Operación | Evento de auditoría | Metadata |
|-----------|-------------------|----------|
| Crear peso promedio | `logistics.cylinder_average_weight.created` | valores del nuevo registro |
| Actualizar peso promedio | `logistics.cylinder_average_weight.updated` | diff de campos cambiados |
| Eliminar peso promedio | `logistics.cylinder_average_weight.deleted` | id y weight_kg |
| Consultar trazabilidad | `logistics.cylinder.traceability_viewed` | cylinder_id, filtros aplicados |
| Crear contrato (DRAFT) | `logistics.cylinder_contract.created` | customer_id, contract_type, quantity |
| Actualizar contrato DRAFT | `logistics.cylinder_contract.updated` | diff de campos |
| Activar contrato | `logistics.cylinder_contract.activated` | contract_number, start_date |
| Terminar contrato | `logistics.cylinder_contract.terminated` | contract_number, motivo |
| Renovar contrato | `logistics.cylinder_contract.renewed` | contract_number anterior → nuevo |
| Entregar cilindro en contrato | `logistics.cylinder_contract_item.delivered` | contract_id, cylinder_id |
| Devolver cilindro de contrato | `logistics.cylinder_contract_item.returned` | contract_id, cylinder_id |

Retención: los eventos de auditoría se conservan según política global del core (mínimo 2 años).

## Criterios de aceptación

### 0023B — Pesos promedio

1. existe `lg_cylinder_average_weights` con los campos definidos;
2. `GET /cylinders/average-weights` lista y filtra correctamente;
3. `_cylinder_weight()` usa peso real → origen → promedio → 0 en ese orden;
4. el frontend muestra "(peso promedio)" cuando se usa fallback;
5. existe UI admin para CRUD de pesos promedio;
6. `ruff check` y `pyright` pasan.

### 0023C — Trazabilidad extendida

1. `GET /cylinders/{id}/traceability` devuelve eventos unificados de todas las tablas fuente;
2. la respuesta incluye `summary` con total, first/last event, estado y ubicación actual;
3. soporta paginación y filtros por tipo de evento y rango de fechas;
4. `CylinderTraceabilityTimeline` reemplaza las tablas sueltas en `FullDetailInfoDialog`;
5. `ruff check` y `pyright` pasan.

### 0023AD — Contratos de envases

1. existe `lg_cylinder_contracts` y `lg_cylinder_contract_items`;
2. CRUD completo de contratos con las transiciones de estado definidas;
3. workflow DRAFT → ACTIVE → TERMINATED funciona con validaciones;
4. un cilindro no puede pertenecer a dos contratos activos simultáneamente;
5. el correlativo se genera automáticamente;
6. existe UI para listar, crear, editar, activar y terminar contratos;
7. el detalle de cilindro muestra el contrato activo si aplica;
8. `ruff check` y `pyright` pasan;
9. hay tests para cada regla de negocio crítica:
   - no se puede activar un contrato sin `customer_id` y `quantity > 0`;
   - un cilindro no puede pertenecer a dos contratos activos simultáneamente;
   - no se puede editar un contrato ACTIVE (excepto items);
   - terminar un contrato libera los cilindros asignados;
   - el correlativo `contract_number` es único por tenant.

## Entregables

0. Setup `openapi-typescript` + script npm para regenerar tipos desde `/openapi.json` (prerrequisito)
1. Migración `<NN>_cylinder_average_weights.py` + modelo + endpoints (en `routers/average_weights.py`) + UI admin
2. Servicio `services/traceability.py` + endpoint (en `routers/traceability.py`) + `CylinderTraceabilityTimeline`
3. Migración `<NN+1>_cylinder_contracts.py` + modelos + endpoints (en `routers/contracts.py`) + workflow + UI completa
4. Tests para los tres capítulos
5. Actualización de `plugins/logistics/plugin.json` con nuevos permisos y eventos
6. Actualización de `docs/avances/logistics.md`
7. Actualización del INDEX `0023-logistics-operacion-real/index.md` — referencias 0023B/0023C/0023AD → 0023AM

## Referencias

- `docs/specs/core/0023-logistics-operacion-real/index.md` — tabla maestra secciones 1 y 9
- `docs/avances/logistics.md`
- `grabaciones/Grab2/hecho/Grabacion Dia 15 marzo con GEMA mostrando su sistema_transcripcion.txt`
- `grabaciones/Grab2/hecho/Grabacion28ENE2025_transcripcion.txt`
- `plugins/logistics/backend/services/extensions.py`
- `plugins/logistics/backend/models/cylinder.py`
