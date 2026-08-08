---
id: "0044"
title: "Planning Form — Clientes de la jornada en planificación"
domain: logistics
module: planning
status: vigente
---

# SPEC 0044 — Planning Form: Clientes de la jornada

## Contexto

El formulario de nueva planificación (`PlanningReservationForm`) actualmente usa un campo `Select` de "Ruta" como única forma de asociar destinos. Esto fuerza al usuario a crear una ruta primero, cuando el flujo natural es: agregar clientes → seleccionar direcciones → ruta se auto-genera.

El formulario de nueva jornada (`CreateJornadaDialog`) ya tiene esta UX: se agregan clientes, se seleccionan direcciones en mapa, y la ruta se crea automáticamente. La planificación debe replicar este patrón.

## Solución

Reemplazar el campo "Ruta" por una sección "Clientes de la jornada" idéntica a `CreateJornadaDialog`. La ruta se auto-genera desde las direcciones seleccionadas. El campo `route_id` se mantiene como fallback opcional.

---

## 1. Modelo de datos

### Campos nuevos en `lg_planning_reservations`

| Campo | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `customer_ids_json` | `JSON` | `NULL` | Lista de IDs de clientes seleccionados |
| `address_ids_json` | `JSON` | `NULL` | Lista de IDs de direcciones seleccionadas |

### Campos nuevos en `PlanningReservationCreateRequest`

```python
customer_ids: list[str] = Field(default_factory=list)
address_ids: list[str] = Field(default_factory=list)
```

Ambos opcionales. Si vienen vacíos, se comporta como antes (solo `route_id`).

---

## 2. Backend: auto-creación de ruta

### Regla

Si `address_ids` tiene elementos pero `route_id` es `None`:
1. Buscar las `LogisticsDeliveryPoint` correspondientes a `address_ids`
2. Crear una `LogisticsRoute` con `status=DRAFT`
3. Crear `LogisticsRouteStop` para cada dirección (ordenados por `stop_order`)
4. Asignar la ruta creada a `reservation.route_id`

### Función auxiliar

```python
def _auto_create_route_from_addresses(
    db: Session,
    *,
    tenant_id: str,
    address_ids: list[str],
    origin_warehouse_id: str,
) -> LogisticsRoute:
```

Ubicación: `plugins/logistics/backend/services/planning_reservations.py`

### Flujo de creación

```python
def create_planning_reservation(db, *, tenant_id, payload, action_context):
    # ... validaciones existentes ...
    
    route_id = payload.route_id
    customer_ids = payload.customer_ids  # nuevo
    address_ids = payload.address_ids    # nuevo
    
    if not route_id and address_ids:
        route_id = _auto_create_route_from_addresses(
            db, tenant_id=tenant_id, address_ids=address_ids,
            origin_warehouse_id=payload.origin_warehouse_id,
        )
    
    # ... crear reserva con route_id ...
```

---

## 3. Frontend: formulario

### Cambios en `PlanningReservationForm`

**Eliminar:**
- `<Select>` de "Ruta" (líneas 132-135)

**Agregar:**
- Sección "Clientes de la jornada" (misma UX que `CreateJornadaDialog`):
  - Botón "Agregar cliente" → abre `CustomerSearchDialog`
  - Chips de clientes seleccionados (con × para quitar)
  - Query `listCustomerAddressesByCustomers` para cargar direcciones
  - `LocationMap` con marcadores de direcciones
  - Lista de direcciones clickeables para seleccionar
  - Mensaje: "La ruta se creará automáticamente con las direcciones seleccionadas"

**Mantener:**
- `route_id` en el form type (para fallback si el usuario quiere seleccionar ruta existente)
- Si no hay clientes ni ruta, mostrar select de ruta como fallback

### Tipo actualizado

```typescript
type PlanningReservationFormValues = {
  vehicle_id: string;
  origin_warehouse_id: string;
  planned_start_at: string;
  planned_end_at: string;
  driver_id: string;
  route_id: string;
  customer_ids: string[];      // nuevo
  address_ids: string[];       // nuevo
  customer_names: Record<string, string>;  // nuevo (local state)
  items: PlanningReservationProductLine[];
  notes: string;
  permit_override: boolean;
  override_reason: string;
};
```

### Props necesarias

Agregar al componente:
- `customers` (opcional, para CustomerSearchDialog)

---

## 4. Migración Alembic

```python
def upgrade(db):
    db.add_column("lg_planning_reservations", "customer_ids_json", JSON, nullable=True)
    db.add_column("lg_planning_reservations", "address_ids_json", JSON, nullable=True)

def downgrade(db):
    db.drop_column("lg_planning_reservations", "address_ids_json")
    db.drop_column("lg_planning_reservations", "customer_ids_json")
```

---

## 5. Criterios de aceptación

- [ ] Formulario muestra sección "Clientes de la jornada" en vez de Select de Ruta
- [ ] Botón "Agregar cliente" abre CustomerSearchDialog
- [ ] Clientes seleccionados aparecen como chips con opción de quitar
- [ ] Direcciones de clientes aparecen en LocationMap
- [ ] Direcciones clickeables se marcan como asignadas
- [ ] Si hay direcciones seleccionadas pero no ruta, backend auto-crea ruta
- [ ] Si no hay clientes ni ruta, se muestra select de ruta como fallback
- [ ] Reserva guardada tiene `route_id` (auto-creado o manual)
- [ ] Al activar reserva, jornada creada con la ruta correcta
- [ ] Migración crea columnas JSON sin problemas
- [ ] Código existente sin clientes sigue funcionando (backward compatible)

---

## 6. Archivos afectados

### Nuevos
- `migrations/NNN_add_planning_customer_address_ids.py`

### Modificados — Backend
- `plugins/logistics/backend/schemas.py` — agregar campos al request
- `plugins/logistics/backend/models/planning.py` — agregar columnas JSON
- `plugins/logistics/backend/services/planning_reservations.py` — auto-creación de ruta

### Modificados — Frontend
- `plugins/logistics/frontend/planning/dialogs/planning-reservation-form.tsx` — UI de clientes
- `plugins/logistics/frontend/planning/PlanningWorkspace.tsx` — tipo y payload

### Sin cambios
- `plugins/logistics/backend/services/sessions.py` — create_vehicle_session ya acepta route_id
- `plugins/logistics/frontend/components/vehicle-sessions/CreateJornadaDialog.tsx` — referencia de UX
