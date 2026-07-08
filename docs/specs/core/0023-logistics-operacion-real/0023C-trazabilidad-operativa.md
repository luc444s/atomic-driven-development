# SPEC 0023C — Trazabilidad operativa extendida

## Estado

Propuesta — 2026-07-06

## Problema

Los datos de trazabilidad del cilindro existen en 8 tablas pero no hay una vista unificada que muestre la línea de tiempo completa: "dónde estuvo, cuándo, en qué estado, en qué vehículo, con qué cliente".

`FullDetailInfoDialog` hoy las muestra como 10 DataTables independientes apiladas verticalmente.

## Solución

Endpoint unificado `GET /cylinders/{id}/traceability` con paginación + botón "Ver trazabilidad completa" en el detalle que abre una timeline vertical.

```
┌─ Ficha del envase ──────────────────────────────┐
│  [Datos grales]  [PH]  [Servicios]  ...          │
├─────────────────────────────────────────────────┤
│  Trazabilidad de estado                          │
│  ┌───────────────────────────────────────────┐  │
│  │ Fecha    │ Cambio           │ Origen      │  │
│  │ 10/07    │ VACIO→ALMACEN    │ RECEPCION   │  │
│  └───────────────────────────────────────────┘  │
│  [Ver trazabilidad completa →]                  │
└─────────────────────────────────────────────────┘
```

## Diseño

### 1. Backend — Endpoint unificado con paginación

`GET /cylinders/{cylinder_id}/traceability?page=1&per_page=20`

en `routers/traceability.py` (no en `router.py`)

```json
{
  "cylinder_id": "123",
  "serial": "GL-200001",
  "events": [
    {
      "timestamp": "2026-07-10T10:30:00Z",
      "event_type": "state_change",
      "description": "EN_CLIENTE_VACIO → EN_ALMACEN_VACIO",
      "actor": "Juan Pérez",
      "metadata": {
        "from_state": "EN_CLIENTE_VACIO",
        "to_state": "EN_ALMACEN_VACIO",
        "origin": "RECEPCION_ALMACEN"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3
  },
  "summary": {
    "total_events": 45,
    "first_event": "2026-01-10T09:00:00Z",
    "last_event": "2026-07-10T10:30:00Z",
    "current_state": "EN_ALMACEN_VACIO",
    "current_location": "Almacén Central"
  }
}
```

### 2. Tipos de evento (16)

| event_type | Fuente | Descripción |
|-----------|--------|-------------|
| `created` | `lg_cylinders.created_at` | Alta del cilindro |
| `state_change` | `lg_cylinder_state_log` | Cambio de estado |
| `scan` | `lg_scan_log` | Escaneo con GPS |
| `loaded` | `lg_loads` o `lg_movement_items` | Cargado en ruta/vehículo |
| `unloaded` | `lg_loads` o `lg_movement_items` | Descargado de ruta/vehículo |
| `moved` | `lg_movement_items` | Movimiento entre almacenes |
| `hydrotest` | `lg_hydrostatic_tests` | Prueba hidrostática |
| `retimbrado` | `lg_cylinder_retimbrados` | Retimbrado |
| `service` | `lg_cylinder_services` | Servicio técnico |
| `warranty` | `lg_cylinder_warranties` | Garantía |
| `ownership` | `lg_cylinder_ownership` | Cambio de custodia |
| `label_print` | `lg_cylinder_label_history` | Impresión de etiqueta |
| `weight_updated` | `lg_cylinders` (audit trail) | Actualización de peso |
| `medical_flag_changed` | `lg_cylinders` (audit trail) | Cambio de flag medicinal |
| `contract_assigned` | `lg_cylinder_contracts` | Asignado a contrato |
| `contract_released` | `lg_cylinder_contract_items` | Liberado de contrato |

### 3. Servicio

`services/traceability.py`:
- `get_cylinder_traceability(db, *, tenant_id, cylinder_id, page=1, per_page=20)` — UNION de todas las tablas ordenado por timestamp DESC con paginación
- `get_traceability_summary(db, *, tenant_id, cylinder_id, cylinder)` — resumen estadístico

### 4. Permisos

- `REQUIRE_CYLINDER_TRACE` (existe)
- Evento audit: `logistics.cylinder.traceability_viewed`

### 5. Frontend

**Nuevo componente Core**: `TraceabilityTimeline` en `shared/ui/`

Timeline vertical con:
- Separadores de día
- Ícono por `event_type`
- Descripción en bold
- Línea secundaria: hora + actor
- Evento expandible para metadata
- Paginación: "Cargar más" al final

**Wrapper de dominio**: `CylinderTraceabilityTimeline` en logistics frontend

**Integración**: Botón "Ver trazabilidad completa" en `FullDetailInfoDialog` que abre la timeline. No reemplaza la tabla de state_log actual.

## Archivos

| Archivo | Propósito |
|---------|-----------|
| `plugins/logistics/backend/routers/traceability.py` | Endpoint paginado |
| `plugins/logistics/backend/services/traceability.py` | Lógica de consulta |
| `apps/web/src/shared/ui/traceability-timeline.tsx` | Componente Core |
| `plugins/logistics/frontend/traceability/CylinderTraceabilityTimeline.tsx` | Wrapper de dominio |

## Criterios de aceptación

1. `GET /cylinders/{id}/traceability` devuelve eventos paginados
2. Cada evento tiene: `event_type`, `timestamp`, `description`, `actor`, `metadata`
3. Pagination devuelve: `page`, `per_page`, `total`, `total_pages`
4. Summary incluye: `total_events`, `first_event`, `last_event`, `current_state`, `current_location`
5. `TraceabilityTimeline` renderiza timeline vertical con íconos por tipo
6. Botón "Ver trazabilidad completa" existe en `FullDetailInfoDialog`
7. Evento `logistics.cylinder.traceability_viewed` emitido y declarado en `plugin.json`
8. `ruff check` y tests pasan
