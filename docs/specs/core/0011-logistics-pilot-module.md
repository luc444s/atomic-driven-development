# SPEC 0011 — Logistics Pilot Module

## Estado

En implementacion

## Contexto

SYSTUTOR OSS dispone de:

- kernel completo: auth JWT, multi-tenant, RBAC, auditoria, event bus, outbox, tareas asincronas
- plugin runtime: mounting de routers, lifecycle hooks, sync de permisos, SDK de eventos
- frontend shell: sidebar tenant-aware, PermissionBoundary, componentes compartidos (DataTable, Dialog, Card, Badge, Button, Input, Alert)
- documentacion del negocio GLP: ciclo de vida del cilindro, flujo de reparto, maquina de estados, reglas ADR/PH

El proyecto es una reescritura completa desde cero. No existe SQL Server, no existen stored procedures, no existen triggers. Todo es PostgreSQL + Python + React.

## Objetivo

Construir el plugin `logistics` como primer plugin de negocio real: maquina de estados de cilindros GLP, planificacion de rutas, preparacion de carga, despacho, entrega, devolucion.

## No objetivos

- migracion de datos historicos (solo datos frescos)
- facturacion electronica (Nubefact / Hacienda CR)
- CRM completo
- compras / ordenes de compra
- inventario general (Stock_Actual)
- caja / finanzas / cobranza
- reportes BI
- asistencia / vacaciones / horarios
- contabilidad
- marketplace de plugins
- integracion con hardware (escaner, bascula, GPS)
- firma digital

## Alcance

Toca:

- `plugins/logistics/` — plugin completo
- `apps/api/tests/`
- `apps/web/src/features/plugins/` — solo integracion/runtime si hiciera falta
- `apps/web/src/shared/` — solo componentes compartidos si hiciera falta extender props
- `docs/specs/core/`
- `docs/contracts/logistics-api.md`

No debe romper kernel, plugin runtime, frontend shell, tenant isolation, RBAC, componentes compartidos.

## Corte implementado actual

La implementacion activa en el repositorio cubre:

- catalogo de estados;
- transiciones permitidas;
- CRUD minimo de cilindros (crear, listar, detalle);
- state machine de cilindros;
- trazabilidad de cambios de estado;
- revisiones PH y garantias basicas;
- almacenes, zonas, vehiculos y puntos de entrega;
- pedidos con lineas;
- rutas con paradas;
- carga por ruta;
- movimientos con confirmacion de estado;
- agenda manual y agenda generada desde ruta;
- frontend multi-pantalla del plugin;
- widget de resumen en dashboard del sistema.

Siguen pendientes para iteraciones futuras:

- retimbrado detallado;
- reportes avanzados;
- integracion con inventory/crm/billing;
- automatizaciones async mas profundas;
- importacion legacy del dominio logistics.

Completado despues del corte original:

- **envase completo (SPEC 0012)**: barcodes, ADR completo, gas product, marca, retimbrados,
  custodia, servicios, escaneo movil y etiquetas

Nota posterior de arquitectura:

- `gas product` y `marca` en este corte describen el estado implementado de `logistics`, no el destino final del catálogo maestro.
- Desde ADR 0015 y SPEC 0015, `lg_gas_products` y `lg_brands` quedan como catálogos transitorios hasta migrar a `prod_products` y `prod_brands` del plugin `productos`.
- Este documento no debe interpretarse como autorización para mantener pricing o catálogo maestro dentro de `logistics` a largo plazo.

---

## Arquitectura del plugin

```
plugins/logistics/
├── plugin.json
├── backend/
│   ├── __init__.py
│   ├── plugin.py
│   ├── router.py
│   ├── schemas.py
│   ├── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cylinders.py
│   │   ├── state_machine.py        # nucleo: validacion de transiciones + reglas
│   │   ├── orders.py
│   │   ├── routes.py
│   │   ├── loads.py
│   │   ├── movements.py
│   │   └── catalog.py
│   └── adr.py                      # validacion ADR
├── frontend/
│   ├── register.ts
│   ├── LogisticsPage.tsx
│   ├── pages/
│   └── components/
├── migrations/
│   └── 001_initial.py
├── permissions/
│   └── __init__.py
├── events/
│   └── __init__.py
└── README.md
```

Reglas:

- backend importa desde `packages/sdk` y, cuando el SDK aun no expone una dependencia necesaria,
  puede importar de `apps/api/app/` solo infraestructura estable del core (auth, tenant, db, modelos core)
  sin modificarla
- frontend se registra via `plugins/logistics/frontend/register.ts` y consume tipos publicos de `@systutor/sdk/frontend`
- el codigo UI del modulo vive en `plugins/logistics/frontend/`, no en `apps/web/src/features/logistics/`
- usa dependencias del core: DB session, auth, tenant, audit, event bus, task dispatcher
- no existe SQL Server, no existen SPs, no existen triggers
- toda accion importante es auditable y emite evento

---

## Modelo de datos PostgreSQL

Schema: tabla normal dentro del mismo schema publico del core. Prefijo: `lg_`.
IDs: `String(36)` con formato UUID v4 para mantener compatibilidad con el kernel actual.
Timestamps: `created_at`, `updated_at`.

### Maquina de estados

#### lg_cylinder_states

| columna | tipo | descripcion |
|---------|------|-------------|
| code | VARCHAR(50) PK | codigo unico del estado |
| is_final | BOOLEAN | true = estado terminal |
| description | TEXT | |

Se siembra con 18 estados:

| code | is_final |
|------|----------|
| CREADO_VACIO | false |
| EN_ALMACEN_VACIO | false |
| EN_LLENADO | false |
| LLENADO_OK | false |
| CARGA_EN_VEHICULO | false |
| EN_RUTA | false |
| EN_CLIENTE_LLENO | false |
| EN_CLIENTE_VACIO | false |
| VACIO_EN_ALMACEN | false |
| DESCARGADO_POR_RECEPCIONAR | false |
| RECEPCIONADO | false |
| EN_MANTENIMIENTO | false |
| PARA_REPARACION | false |
| PARA_TRASLADO | false |
| BLOQUEADO | true |
| OBSERVADO | true |
| DE_BAJA | true |
| PERDIDO | true |

#### lg_state_transitions

| columna | tipo |
|---------|------|
| id | UUID PK |
| from_state | VARCHAR(50) FK |
| to_state | VARCHAR(50) FK |
| requires_adr | BOOLEAN |
| requires_hydrotest | BOOLEAN |
| description | TEXT |

Transiciones:

| desde | hacia | adr | ph |
|-------|-------|-----|----|
| CREADO_VACIO | EN_ALMACEN_VACIO | false | false |
| EN_ALMACEN_VACIO | LLENADO_OK | true | true |
| EN_ALMACEN_VACIO | EN_MANTENIMIENTO | false | false |
| EN_ALMACEN_VACIO | PARA_REPARACION | false | false |
| EN_ALMACEN_VACIO | DE_BAJA | false | false |
| EN_ALMACEN_VACIO | PERDIDO | false | false |
| EN_ALMACEN_VACIO | PARA_TRASLADO | false | false |
| EN_ALMACEN_VACIO | EN_LLENADO | false | false |
| EN_LLENADO | LLENADO_OK | false | false |
| LLENADO_OK | CARGA_EN_VEHICULO | false | false |
| LLENADO_OK | EN_CLIENTE_LLENO | false | false |
| CARGA_EN_VEHICULO | EN_RUTA | false | false |
| EN_RUTA | EN_CLIENTE_LLENO | false | false |
| EN_RUTA | DESCARGADO_POR_RECEPCIONAR | false | false |
| DESCARGADO_POR_RECEPCIONAR | RECEPCIONADO | false | false |
| RECEPCIONADO | EN_ALMACEN_VACIO | false | false |
| EN_CLIENTE_LLENO | EN_CLIENTE_VACIO | false | false |
| EN_CLIENTE_LLENO | VACIO_EN_ALMACEN | false | false |
| EN_CLIENTE_LLENO | EN_RUTA | false | false |
| EN_CLIENTE_VACIO | EN_RUTA | false | false |
| EN_CLIENTE_VACIO | PERDIDO | false | false |
| EN_CLIENTE_VACIO | VACIO_EN_ALMACEN | false | false |
| VACIO_EN_ALMACEN | EN_ALMACEN_VACIO | false | false |
| EN_MANTENIMIENTO | EN_ALMACEN_VACIO | false | false |
| PARA_REPARACION | EN_MANTENIMIENTO | false | false |
| PARA_REPARACION | DE_BAJA | false | false |
| PARA_TRASLADO | EN_RUTA | false | false |
| PARA_TRASLADO | EN_ALMACEN_VACIO | false | false |
| EN_CLIENTE_VACIO | PARA_REPARACION | false | false |
| BLOQUEADO | EN_ALMACEN_VACIO | false | false |
| OBSERVADO | EN_ALMACEN_VACIO | false | false |
| OBSERVADO | DE_BAJA | false | false |

### Cilindros

#### lg_cylinders

```sql
CREATE TABLE logistics.lg_cylinders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    branch_id VARCHAR(36) REFERENCES branches(id),
    serial VARCHAR(50) NOT NULL,
    current_state VARCHAR(50) NOT NULL REFERENCES logistics.lg_cylinder_states(code)
        DEFAULT 'CREADO_VACIO',
    product_id UUID,
    manufacturer_date DATE,
    manufacturer_code VARCHAR(50),
    manufacture_year INTEGER,
    weight_origin NUMERIC(10,2),
    weight_current NUMERIC(10,2),
    service_pressure NUMERIC(10,2),
    test_pressure NUMERIC(10,2),
    last_hydrotest_date DATE,
    next_hydrotest_date DATE,
    adr_category VARCHAR(50),
    adr_un_number VARCHAR(10),
    adr_label VARCHAR(50),
    adr_tunnel VARCHAR(10),
    adr_points INTEGER,
    adr_weight_kg NUMERIC,
    adr_volume_m3 NUMERIC,
    approval_number VARCHAR(50),
    danger_class VARCHAR(50),
    marking_1 VARCHAR(50),
    marking_2 VARCHAR(50),
    location VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, serial)
);

CREATE INDEX idx_lg_cylinders_state ON logistics.lg_cylinders(current_state);
CREATE INDEX idx_lg_cylinders_tenant ON logistics.lg_cylinders(tenant_id);
```

#### lg_cylinder_state_log

```sql
CREATE TABLE logistics.lg_cylinder_state_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    cylinder_id UUID NOT NULL REFERENCES logistics.lg_cylinders(id),
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,
    changed_by VARCHAR(36) NOT NULL REFERENCES users(id),
    movement_id UUID,
    origin VARCHAR(100),
    reason_code VARCHAR(30),
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lg_state_log_cylinder ON logistics.lg_cylinder_state_log(cylinder_id, created_at DESC);
```

#### lg_hydrostatic_tests

```sql
CREATE TABLE logistics.lg_hydrostatic_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cylinder_id UUID NOT NULL REFERENCES logistics.lg_cylinders(id),
    test_date DATE NOT NULL,
    previous_test_date DATE,
    status VARCHAR(50),
    movement_id UUID,
    modified_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (cylinder_id, test_date)
);
```

#### lg_cylinder_warranties

```sql
CREATE TABLE logistics.lg_cylinder_warranties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    cylinder_id UUID NOT NULL REFERENCES logistics.lg_cylinders(id),
    customer_id UUID NOT NULL,
    warranty_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'INGRESO',
    description TEXT,
    return_date TIMESTAMP,
    created_by VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Pedidos

#### lg_orders

```sql
CREATE TABLE logistics.lg_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    branch_id VARCHAR(36) REFERENCES branches(id),
    order_date TIMESTAMP NOT NULL DEFAULT NOW(),
    customer_id UUID NOT NULL,
    movement_type VARCHAR(50) NOT NULL,
    document_series VARCHAR(50),
    document_number INTEGER,
    warehouse_id UUID REFERENCES logistics.lg_warehouses(id),
    carrier VARCHAR(100),
    commitment_date TIMESTAMP,
    time_window_start TIMESTAMP,
    time_window_end TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',
    notes TEXT,
    created_by VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### lg_order_items

```sql
CREATE TABLE logistics.lg_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES logistics.lg_orders(id),
    product_id UUID,
    reason VARCHAR(50),
    condition VARCHAR(50),
    quantity_requested NUMERIC(19,4) NOT NULL DEFAULT 0,
    quantity_planned NUMERIC(19,4) DEFAULT 0,
    status INTEGER DEFAULT 0,
    location VARCHAR(50),
    description VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Logistica

#### lg_warehouses

```sql
CREATE TABLE logistics.lg_warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    address VARCHAR(200),
    phone VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### lg_vehicles

```sql
CREATE TABLE logistics.lg_vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    plate VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(50),
    brand VARCHAR(50),
    model VARCHAR(50),
    capacity_weight NUMERIC,
    capacity_volume NUMERIC,
    useful_load NUMERIC,
    adr_class VARCHAR(50),
    status VARCHAR(20) DEFAULT 'DISPONIBLE',
    warehouse_id UUID REFERENCES logistics.lg_warehouses(id),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### lg_delivery_points

```sql
CREATE TABLE logistics.lg_delivery_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    customer_id UUID NOT NULL,
    contact_name VARCHAR(100),
    address VARCHAR(200) NOT NULL,
    phone VARCHAR(50),
    zone_id UUID REFERENCES logistics.lg_zones(id),
    is_primary BOOLEAN NOT NULL DEFAULT false,
    delivery_day VARCHAR(50),
    gps_link VARCHAR(200),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### lg_zones

```sql
CREATE TABLE logistics.lg_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### lg_routes

```sql
CREATE TABLE logistics.lg_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    branch_id VARCHAR(36) REFERENCES branches(id),
    route_date DATE NOT NULL,
    driver_id VARCHAR(36) NOT NULL REFERENCES users(id),
    vehicle_id UUID REFERENCES logistics.lg_vehicles(id),
    status VARCHAR(50) NOT NULL DEFAULT 'PLANIFICADO',
    notes TEXT,
    created_by VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lg_routes_date ON logistics.lg_routes(route_date);
CREATE INDEX idx_lg_routes_driver ON logistics.lg_routes(driver_id);
```

#### lg_route_stops

```sql
CREATE TABLE logistics.lg_route_stops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID NOT NULL REFERENCES logistics.lg_routes(id),
    delivery_point_id UUID NOT NULL REFERENCES logistics.lg_delivery_points(id),
    stop_order INTEGER NOT NULL,
    scheduled_time TIME,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',
    arrival_time TIMESTAMP,
    departure_time TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (route_id, stop_order)
);
```

#### lg_loads

```sql
CREATE TABLE logistics.lg_loads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id UUID NOT NULL REFERENCES logistics.lg_routes(id),
    cylinder_id UUID NOT NULL REFERENCES logistics.lg_cylinders(id),
    stop_id UUID REFERENCES logistics.lg_route_stops(id),
    status VARCHAR(50) NOT NULL DEFAULT 'ASIGNADO',
    loaded_at TIMESTAMP,
    unloaded_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lg_loads_route ON logistics.lg_loads(route_id);
CREATE INDEX idx_lg_loads_cylinder ON logistics.lg_loads(cylinder_id);
```

### Movimientos

#### lg_movement_types

Tabla semilla con los tipos de documento que controlan la maquina de estados:

| code | name | category | moves_cylinders | origin_state | target_state |
|------|------|----------|----------------|--------------|--------------|
| SC | Albaran Entrega cliente | EGRESO | true | EN_ALMACEN_VACIO | EN_CLIENTE_LLENO |
| IC | Albaran Recepcion cliente | INGRESO | true | EN_CLIENTE_VACIO | EN_ALMACEN_VACIO |
| IP | Albaran Recepcion proveedor | INGRESO | true | CREADO_VACIO | EN_ALMACEN_VACIO |
| SP | Albaran Entrega proveedor | EGRESO | true | EN_ALMACEN_VACIO | EN_RUTA |
| TR | Traslado entre almacenes | TRASLADO | true | EN_ALMACEN_VACIO | EN_ALMACEN_VACIO |
| MV | Mantenimiento | EGRESO | true | EN_ALMACEN_VACIO | EN_MANTENIMIENTO |

#### lg_movements

```sql
CREATE TABLE logistics.lg_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    branch_id VARCHAR(36) REFERENCES branches(id),
    movement_type VARCHAR(50) NOT NULL REFERENCES logistics.lg_movement_types(code),
    document_series VARCHAR(20),
    document_number VARCHAR(50),
    full_document VARCHAR(27),
    order_id UUID REFERENCES logistics.lg_orders(id),
    route_id UUID REFERENCES logistics.lg_routes(id),
    customer_id UUID,
    warehouse_id UUID REFERENCES logistics.lg_warehouses(id),
    driver_id VARCHAR(36) REFERENCES users(id),
    vehicle_id UUID REFERENCES logistics.lg_vehicles(id),
    total NUMERIC(19,4),
    tax NUMERIC(19,4),
    discount NUMERIC(19,4),
    currency VARCHAR(10) DEFAULT 'PEN',
    exchange_rate NUMERIC(19,4) DEFAULT 1,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE',
    payment_status VARCHAR(50),
    carrier VARCHAR(100),
    plate VARCHAR(20),
    destination_place VARCHAR(200),
    destination_address VARCHAR(500),
    notes TEXT,
    parent_movement_id UUID REFERENCES logistics.lg_movements(id),
    created_by VARCHAR(36) NOT NULL REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lg_movements_tenant ON logistics.lg_movements(tenant_id);
CREATE INDEX idx_lg_movements_route ON logistics.lg_movements(route_id);
```

#### lg_movement_items

```sql
CREATE TABLE logistics.lg_movement_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movement_id UUID NOT NULL REFERENCES logistics.lg_movements(id),
    cylinder_id UUID NOT NULL REFERENCES logistics.lg_cylinders(id),
    quantity_in NUMERIC(19,4) DEFAULT 0,
    quantity_out NUMERIC(19,4) DEFAULT 0,
    quantity INTEGER DEFAULT 0,
    quantity_planned NUMERIC(19,4) DEFAULT 0,
    unit_price NUMERIC(19,4),
    total_item NUMERIC(19,4),
    discount NUMERIC(19,4) DEFAULT 0,
    item_status VARCHAR(20) DEFAULT 'R',
    state_before VARCHAR(50),
    state_after VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### lg_movement_status_history

```sql
CREATE TABLE logistics.lg_movement_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    movement_id UUID NOT NULL REFERENCES logistics.lg_movements(id),
    field_name VARCHAR(50) NOT NULL,
    from_value VARCHAR(50),
    to_value VARCHAR(50) NOT NULL,
    changed_by VARCHAR(36) NOT NULL REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Agenda

#### lg_agenda_task_types

Tabla semilla:

| code | description |
|------|-------------|
| ENTREGA | Llevar cilindros llenos |
| RECOJO | Recoger cilindros vacios |
| SERVICIO | Mantenimiento en sitio |
| VISITA | Visita programada |
| COBRO | Cobranza |

#### lg_agenda_tasks

```sql
CREATE TABLE logistics.lg_agenda_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(36) NOT NULL REFERENCES tenants(id),
    route_id UUID REFERENCES logistics.lg_routes(id),
    driver_id VARCHAR(36) NOT NULL REFERENCES users(id),
    customer_id UUID,
    delivery_point_id UUID REFERENCES logistics.lg_delivery_points(id),
    task_type VARCHAR(50) NOT NULL,
    description VARCHAR(500),
    scheduled_date DATE NOT NULL,
    scheduled_time TIME,
    status VARCHAR(50) NOT NULL DEFAULT 'PROGRAMADO',
    priority INTEGER DEFAULT 0,
    order_id UUID REFERENCES logistics.lg_orders(id),
    quantity_requested INTEGER,
    quantity_served INTEGER,
    cylinder_serial VARCHAR(50),
    customer_confirmed BOOLEAN DEFAULT false,
    requires_signature BOOLEAN DEFAULT false,
    evidence_url VARCHAR(300),
    delivery_location VARCHAR(200),
    gps_coordinates JSONB,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lg_agenda_driver_date ON logistics.lg_agenda_tasks(driver_id, scheduled_date);
CREATE INDEX idx_lg_agenda_route ON logistics.lg_agenda_tasks(route_id);
```

---

## Logica de negocio (StateMachineService)

### Validacion de transiciones

```python
class StateMachineService:
    def transition(self, cylinder_id, to_state, *, movement_id=None,
                   origin=None, reason_code=None, notes=None, metadata=None):
        # 1. Cilindro existe y pertenece al tenant
        # 2. Estado actual no es final
        # 3. Transicion existe en lg_state_transitions
        # 4. Si requires_adr: validar ADR vigente
        # 5. Si requires_hydrotest: validar next_hydrotest_date >= today
        # 6. Registrar en lg_cylinder_state_log
        # 7. Actualizar lg_cylinders.current_state
        # 8. Emitir evento logistics.cylinder.state_changed
```

### Flujo de reparto completo

```
PEDIDO (lg_orders + items)
  → MOVIMIENTO (lg_movements, tipo segun origen/destino)
    → AGENDA (lg_agenda_tasks por repartidor)
      → RUTA (lg_routes + lg_route_stops)
        → CARGA (lg_loads, transicion LLENADO_OK → CARGA_EN_VEHICULO)
          → DESPACHO (transicion CARGA_EN_VEHICULO → EN_RUTA)
            → ENTREGA (transicion EN_RUTA → EN_CLIENTE_LLENO)
              → RETORNO (movimiento completado, ruta completada)
                → DEVOLUCION (transicion EN_CLIENTE_VACIO → VACIO_EN_ALMACEN)
```

### Efecto de movimientos sobre estados

Al crear un `lg_movement` con un `lg_movement_type` que tiene `moves_cylinders=true`:

| tipo | desde | hacia | efecto |
|------|-------|-------|--------|
| SC | almacen | cliente | cilindros pasan a EN_CLIENTE_LLENO |
| IC | cliente | almacen | cilindros pasan a EN_ALMACEN_VACIO |
| IP | proveedor | almacen | cilindros nuevos pasan a EN_ALMACEN_VACIO |
| SP | almacen | proveedor | cilindros pasan a EN_RUTA |
| TR | almacen | almacen | cambia ubicacion, mismo estado |
| MV | almacen | taller | cilindros pasan a EN_MANTENIMIENTO |

---

## Permisos

| permiso | descripcion |
|---------|-------------|
| `logistics.cylinder.read` | Ver catalogo de cilindros |
| `logistics.cylinder.create` | Registrar cilindro |
| `logistics.cylinder.update` | Editar cilindro |
| `logistics.cylinder.delete` | Eliminar cilindro (logico) |
| `logistics.cylinder.transition` | Ejecutar transicion de estado |
| `logistics.cylinder.trace` | Ver historial completo |
| `logistics.order.read` | Ver pedidos |
| `logistics.order.create` | Crear pedido |
| `logistics.order.manage` | Editar/cancelar pedidos |
| `logistics.route.read` | Ver rutas |
| `logistics.route.manage` | Crear/editar rutas |
| `logistics.load.manage` | Preparar carga |
| `logistics.movement.read` | Ver movimientos |
| `logistics.movement.create` | Registrar movimiento |
| `logistics.movement.confirm` | Confirmar entrega |
| `logistics.delivery.read` | Ver entregas |
| `logistics.delivery.confirm` | Confirmar entrega |
| `logistics.warehouse.read` | Ver almacenes |
| `logistics.warehouse.manage` | Gestionar almacenes |
| `logistics.vehicle.read` | Ver vehiculos |
| `logistics.vehicle.manage` | Gestionar vehiculos |
| `logistics.agenda.read` | Ver agenda |
| `logistics.agenda.manage` | Gestionar agenda |
| `logistics.adr.read` | Ver datos ADR |
| `logistics.adr.manage` | Gestionar ADR |
| `logistics.maintenance.read` | Ver mantenimiento |
| `logistics.maintenance.manage` | Registrar mantenimiento |

---

## Eventos

| evento | cuando |
|--------|--------|
| `logistics.cylinder.created` | Cilindro registrado |
| `logistics.cylinder.updated` | Datos modificados |
| `logistics.cylinder.state_changed` | Transicion de estado |
| `logistics.cylinder.hydrotest_registered` | PH registrada |
| `logistics.cylinder.lost` | Cilindro perdido |
| `logistics.cylinder.scrapped` | Cilindro dado de baja |
| `logistics.order.created` | Pedido creado |
| `logistics.order.updated` | Pedido modificado |
| `logistics.route.created` | Ruta planificada |
| `logistics.route.started` | Ruta iniciada |
| `logistics.route.completed` | Ruta completada |
| `logistics.load.assigned` | Cilindro asignado a carga |
| `logistics.load.prepared` | Carga lista |
| `logistics.movement.created` | Movimiento registrado |
| `logistics.movement.completed` | Movimiento completado |
| `logistics.movement.cancelled` | Movimiento cancelado |
| `logistics.delivery.confirmed` | Entrega confirmada |
| `logistics.agenda.task_completed` | Tarea realizada |
| `logistics.warranty.created` | Garantia registrada |
| `logistics.warranty.resolved` | Garantia cerrada |

Cada evento incluye: `tenant_id`, `branch_id`, `actor_user_id`, `entity_type`, `entity_id`, `correlation_id`.

---

## API endpoints

Prefijo: `/api/v1/plugins/logistics`

### Cilindros

```
GET    /cylinders                           ?search,state,warehouse,is_active
GET    /cylinders/{id}
GET    /cylinders/by-serial/{serial}
POST   /cylinders
PATCH  /cylinders/{id}
DELETE /cylinders/{id}
POST   /cylinders/{id}/transition           body: { to_state, movement_id?, origin?, reason_code?, notes? }
GET    /cylinders/{id}/trace
GET    /cylinders/{id}/hydrotests
POST   /cylinders/{id}/hydrotests
GET    /cylinders/{id}/warranties
POST   /cylinders/{id}/warranties
GET    /cylinders/allowed-transitions/{id}
GET    /cylinders/summary
```

### Pedidos

```
GET    /orders                              ?customer,date_from,date_to,status
GET    /orders/{id}
POST   /orders
PATCH  /orders/{id}
POST   /orders/{id}/items
PATCH  /orders/{id}/items/{item_id}
DELETE /orders/{id}/items/{item_id}
GET    /orders/pending                      ?warehouse_id
```

### Rutas

```
GET    /routes                              ?date,driver,status
GET    /routes/{id}
POST   /routes
PATCH  /routes/{id}
POST   /routes/{id}/start
POST   /routes/{id}/complete
POST   /routes/{id}/cancel
POST   /routes/{id}/stops
PATCH  /routes/{id}/stops/{stop_id}
DELETE /routes/{id}/stops/{stop_id}
POST   /routes/{id}/stops/{stop_id}/deliver
```

### Carga

```
GET    /loads                               ?route_id
POST   /loads                               body: { route_id, cylinder_id, stop_id? }
DELETE /loads/{id}
POST   /loads/confirm                       body: { route_id }
POST   /loads/bulk                          body: { route_id, cylinder_ids[], stop_id? }
```

### Movimientos

```
GET    /movements                           ?type,status,date_from,date_to,customer
GET    /movements/{id}
POST   /movements
POST   /movements/{id}/confirm
POST   /movements/{id}/cancel               body: { reason }
PATCH  /movements/{id}
GET    /movements/{id}/items
POST   /movements/{id}/items
DELETE /movements/{id}/items/{item_id}
GET    /movements/pending-inbound           ?warehouse_id
GET    /movements/pending-outbound          ?warehouse_id
```

### Agenda

```
GET    /agenda/tasks                        ?driver,date,task_type,status
GET    /agenda/tasks/{id}
POST   /agenda/tasks
PATCH  /agenda/tasks/{id}
POST   /agenda/tasks/{id}/complete
POST   /agenda/tasks/{id}/cancel
GET    /agenda/tasks/by-driver/{driver_id}
```

### Catalogos

```
GET    /catalog/cylinder-states
GET    /catalog/transitions
GET    /catalog/movement-types
GET    /catalog/task-types
GET    /catalog/warehouses
GET    /catalog/vehicles
GET    /catalog/delivery-points
GET    /catalog/zones
```

### CRUD catalogos

```
GET    /warehouses
POST   /warehouses
PATCH  /warehouses/{id}

GET    /vehicles
POST   /vehicles
PATCH  /vehicles/{id}
DELETE /vehicles/{id}

GET    /delivery-points                     ?customer,zone
POST   /delivery-points
PATCH  /delivery-points/{id}
```

---

## Frontend

### Stack

React 18, TypeScript, Vite, TanStack Query, Zustand (solo sesion), Tailwind, shadcn/ui.

La integracion con el shell ocurre exclusivamente a traves del runtime de plugins ya existente.

### Archivos

```
plugins/logistics/frontend/
├── register.ts                # entrypoint requerido por el runtime actual
├── api.ts                     # fetch + query keys del plugin
├── types.ts
├── pages/
│   ├── DashboardPage.tsx
│   ├── CylindersPage.tsx
│   ├── CylinderDetailPage.tsx
│   ├── CylinderTracePage.tsx
│   ├── OrdersPage.tsx
│   ├── OrderDetailPage.tsx
│   ├── RoutesPage.tsx
│   ├── RouteDetailPage.tsx
│   ├── LoadsPage.tsx
│   ├── MovementsPage.tsx
│   ├── MovementDetailPage.tsx
│   ├── AgendaPage.tsx
│   ├── WarehousesPage.tsx
│   ├── VehiclesPage.tsx
│   └── DeliveryPointsPage.tsx
├── components/
│   ├── CylinderStateBadge.tsx     # badge coloreado por estado
│   ├── CylinderStateTimeline.tsx  # timeline vertical de historial
│   ├── CylinderForm.tsx
│   ├── CylinderTransitionDialog.tsx
│   ├── CylinderScannerInput.tsx   # input para escanear serie
│   ├── OrderForm.tsx
│   ├── RouteForm.tsx
│   ├── RouteStopList.tsx
│   ├── LoadCylinderSelector.tsx
│   ├── MovementForm.tsx
│   ├── MovementTypeSelect.tsx
│   ├── ConfirmDeliveryDialog.tsx
│   ├── AgendaTaskCard.tsx
│   ├── HydrotestForm.tsx
│   ├── WarrantyForm.tsx
│   └── LogisticsDashboardWidget.tsx
└── LogisticsPage.tsx           # pagina raiz registrada en navigation/routes
```

`register.ts` debe exportar `registerPlugin(ctx)` para que el runtime actual lo descubra con `import.meta.glob(...)`.

### DashboardPage (`/app/logistics`)

Resumen visual del modulo:
- cilindros por estado (grafico de torta, filtrable por almacen)
- rutas del dia (tabla con estado y % de carga)
- agenda del dia para el usuario logueado
- alertas: PH proxima a vencer (<30d), recepciones pendientes
- ultimos 10 movimientos

### CylindersPage (`/app/logistics/cylinders`)

```
┌───────────────────────────────────────────────────────────┐
│ Cilindros                                     [+ Crear]   │
├───────────────────────────────────────────────────────────┤
│ [🔍 Buscar por serie...]   [Estado: Todos ▼]              │
│ [Almacen: Todos ▼]         [Solo activos ✔]              │
│ Total: 1,234  |  VACIO: 456  LLENO: 345  EN_CLIENTE: 200 │
│ ┌───────────┬───────────┬───────────┬──────────┬────────┐ │
│ │ Serie     │ Estado    │ PH vence  │ Cliente  │ Accion │ │
│ ├───────────┼───────────┼───────────┼──────────┼────────┤ │
│ │ GL-00123  │ [LLENO]   │ 2028-06   │ GLP Norte│ [Ver]  │ │
│ │ GL-00124  │ [CLIENTE] │ 2027-03   │ Gas Cent│ [Ver]  │ │
│ │ GL-00125  │ [VACIO]   │ 2029-11   │ —        │ [Ver]  │ │
│ └───────────┴───────────┴───────────┴──────────┴────────┘ │
└───────────────────────────────────────────────────────────┘
```

**Botones:** [+ Crear] solo con permiso create. [Ver] navega a detalle.

**Filtros:** busqueda por serie (debounce 300ms), dropdown estado, dropdown almacen, checkbox solo activos. Todos sincronizados con query params.

### CylinderDetailPage (`/app/logistics/cylinders/:id`)

```
┌───────────────────────────────────────────────────────────────┐
│ ← Volver                                      [Editar] [▸]   │
│ Cilindro GL-00123                                              │
├───────────────────────────────────────────────────────────────┤
│ ┌─ Datos generales ─────────────────────────────────────────┐ │
│ │ Serie: GL-00123           Estado: [LLENO]                  │ │
│ │ Producto: GLP 10kg        Condicion: NUEVO                │ │
│ │ Fabricacion: 2023         Peso: 10.5 kg                   │ │
│ │ Ubicacion: Almacen Principal                               │ │
│ └───────────────────────────────────────────────────────────┘ │
│ ┌─ ADR ─────────────────────────────────────────────────────┐ │
│ │ Categoria: 2F   UN: 1047   Etiqueta: GLP   Tunel: B/D    │ │
│ └───────────────────────────────────────────────────────────┘ │
│ ┌─ PH ──────────────────────────── [+ Registrar] ──────────┐ │
│ │ Ultima: 2023-06-15   Vence: 2028-06-15   (OK)            │ │
│ └───────────────────────────────────────────────────────────┘ │
│ ┌─ Timeline ────────────────────────────────────────────────┐ │
│ │ ● 2026-06-25  VACIO → LLENO  (Planta Norte)              │ │
│ │ ● 2026-06-20  CREADO → VACIO  (admin)                    │ │
│ │ [Ver historial completo →]                                │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│ [Transicionar ▼]  [Registrar PH]  [Registrar garantia]       │
└───────────────────────────────────────────────────────────────┘
```

**Botones:** [▸] accion rapida de transicion. [Editar] solo con update. [Transicionar ▼] dropdown con estados destino validos. [Registrar PH], [Registrar garantia] segun permisos.

### RoutesPage (`/app/logistics/routes`)

```
┌────────────────────────────────────────────────────────────┐
│ Rutas                                          [+ Crear]   │
├────────────────────────────────────────────────────────────┤
│ [📅 Fecha ▼]  [Repartidor: Todos ▼]  [Estado: Todos ▼]    │
│ ┌──────────┬───────────┬─────────┬───────┬───────┬───────┐ │
│ │ Fecha    │ Repartidor│ Vehiculo│ Stops │ Carga │ Accion│ │
│ ├──────────┼───────────┼─────────┼───────┼───────┼───────┤ │
│ │ 26/06    │ Juan Perez│ ABC-123 │ 12    │ 100%  │ [Ver] │ │
│ │ 26/06    │ Maria Lopez│ DEF-456│ 8     │ 100%  │ [Ver] │ │
│ │ 25/06    │ Juan Perez│ ABC-123 │ 10    │ —     │ [Ver] │ │
│ └──────────┴───────────┴─────────┴───────┴───────┴───────┘ │
└────────────────────────────────────────────────────────────┘
```

**Filtros:** fecha (date picker), repartidor (dropdown usuarios), estado.

### RouteDetailPage (`/app/logistics/routes/:id`)

```
┌───────────────────────────────────────────────────────────────┐
│ ← Volver         [Editar] [Cargar] [Iniciar] [Completar]     │
│ Ruta: 26/06/2026 - Juan Perez                     [EN_RUTA]  │
│ Vehiculo: ABC-123 (Camion GLP)                               │
├───────────────────────────────────────────────────────────────┤
│ ┌─ Stops ──────────────────────────── [Agregar] ───────────┐ │
│ │ #  Cliente        Cilindros  Estado           Accion     │ │
│ │ 1  GLP Norte      3/3        [ENTREGADO]  ✓              │ │
│ │ 2  Gas Center     2/2        [ENTREGADO]  ✓              │ │
│ │ 3  Ferre Ruiz     4/4        [CARGADO]    □              │ │
│ │ 4  Distribuidora  0/0        [PENDIENTE]  □              │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                               │
│ Carga: 9/12 cilindros  |  [Ver detalle de carga →]          │
└───────────────────────────────────────────────────────────────┘
```

### LoadsPage (`/app/logistics/loads?route_id=X`)

```
┌───────────────────────────────────────────────────────────────┐
│ ← Volver  (Ruta: 26/06 - Juan Perez)    [Confirmar carga]   │
│ Preparacion de carga                        (9/12 cargados) │
├───────────────────────────────────────────────────────────────┤
│ ┌─ Cilindros disponibles ──────────────────────────────────┐ │
│ │ [🔍 Buscar...]  [Filtrar estado ▼]                       │ │
│ │ ☐ GL-00123  LLENO   GLP Norte    Stop #1                │ │
│ │ ☐ GL-00124  LLENO   Gas Center   Stop #2                │ │
│ │ ☐ GL-00125  LLENO   —            Sin asignar            │ │
│ │ [Agregar seleccionados]  [Asignar a stop ▼]             │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌─ Carga actual ──────────────────────────────────────────┐ │
│ │ Serie    | Stop          | Estado     | Accion          │ │
│ │ GL-00123 | GLP Norte     | [CARGADO]  | [Quitar]       │ │
│ │ GL-00124 | Gas Center    | [CARGADO]  | [Quitar]       │ │
│ └──────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

### MovementsPage (`/app/logistics/movements`)

```
┌───────────────────────────────────────────────────────────────┐
│ Movimientos                                  [+ Registrar]   │
├───────────────────────────────────────────────────────────────┤
│ [Tipo: Todos ▼]  [Estado: Todos ▼]  [📅 Rango fechas]       │
│ ┌──────────┬────────┬───────────┬──────────┬──────────┬─────┐ │
│ │ Fecha    │ Tipo   │ Documento │ Cliente  │ Estado   │ Acc │ │
│ ├──────────┼────────┼───────────┼──────────┼──────────┼─────┤ │
│ │ 26/06    │ SALIDA │ SC-000123 │ GLP Norte│ ENTREGADO│ [Ver]│ │
│ │ 25/06    │ INGRES │ IC-000045 │ —        │ COMPLETO │ [Ver]│ │
│ │ 24/06    │ TRASL  │ TR-000067 │ —        │ EN_RUTA  │ [Ver]│ │
│ └──────────┴────────┴───────────┴──────────┴──────────┴─────┘ │
└───────────────────────────────────────────────────────────────┘
```

### AgendaPage (`/app/logistics/agenda`)

```
┌──────────────────────────────────────────────────────────────┐
│ Agenda de reparto            [Mi dia ▼]  [📅 26/06/2026]   │
├──────────────────────────────────────────────────────────────┤
│ ┌─ Repartidor: Juan Perez ────────────────────────────────┐ │
│ │ 08:00  ENTREGA  GLP Norte       12 cil  [ENRUTA]        │ │
│ │ 09:30  ENTREGA  Gas Center       8 cil  [REALIZADO]     │ │
│ │ 11:00  RECOJO   Ferre Ruiz       4 cil  [PENDIENTE]     │ │
│ │ 14:00  ENTREGA  Distribuidora    6 cil  [PENDIENTE]     │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                               │
│ [08:00] ●───● [09:30] ●───○ [11:00] ○───○ [14:00]          │
│        CARG   RUTA    RUTA    PENDIENTE  PENDIENTE           │
└──────────────────────────────────────────────────────────────┘
```

### API layer

```typescript
// plugins/logistics/frontend/api.ts
export const logisticsKeys = {
  all: ["logistics"] as const,
  cylinders: {
    all: () => [...logisticsKeys.all, "cylinders"] as const,
    list: (filters?) => [...logisticsKeys.cylinders.all(), "list", filters] as const,
    detail: (id: string) => [...logisticsKeys.cylinders.all(), id] as const,
    trace: (id: string) => [...logisticsKeys.cylinders.detail(id), "trace"] as const,
    allowedTransitions: (id: string) =>
      [...logisticsKeys.cylinders.detail(id), "allowed-transitions"] as const,
    summary: () => [...logisticsKeys.cylinders.all(), "summary"] as const,
  },
  orders: {
    all: () => [...logisticsKeys.all, "orders"] as const,
    list: (filters?) => [...logisticsKeys.orders.all(), "list", filters] as const,
    detail: (id: string) => [...logisticsKeys.orders.all(), id] as const,
  },
  routes: {
    all: () => [...logisticsKeys.all, "routes"] as const,
    list: (filters?) => [...logisticsKeys.routes.all(), "list", filters] as const,
    detail: (id: string) => [...logisticsKeys.routes.all(), id] as const,
  },
  loads: (routeId: string) => [...logisticsKeys.all, "loads", routeId] as const,
  movements: {
    all: () => [...logisticsKeys.all, "movements"] as const,
    list: (filters?) => [...logisticsKeys.movements.all(), "list", filters] as const,
    detail: (id: string) => [...logisticsKeys.movements.all(), id] as const,
  },
  agenda: {
    all: () => [...logisticsKeys.all, "agenda"] as const,
    tasks: (filters?) => [...logisticsKeys.agenda.all(), "tasks", filters] as const,
  },
};
```

### Colores de CylinderStateBadge

| estado | color |
|--------|-------|
| EN_ALMACEN_VACIO | gris |
| LLENADO_OK | verde |
| EN_CLIENTE_LLENO | azul |
| EN_RUTA | amarillo |
| EN_MANTENIMIENTO | naranja |
| BLOQUEADO, OBSERVADO | rojo |
| DE_BAJA, PERDIDO | gris|
| resto | slate |

### Sidebar

```
Logistica  (visible con cualquier permiso logistics.*)
├── Dashboard         → /app/logistics
├── Cilindros         → /app/logistics/cylinders     (cylinder.read)
├── Pedidos           → /app/logistics/orders         (order.read)
├── Rutas             → /app/logistics/routes         (route.read)
├── Carga             → /app/logistics/loads          (load.manage)
├── Movimientos       → /app/logistics/movements      (movement.read)
├── Agenda            → /app/logistics/agenda         (agenda.read)
├── Almacenes         → /app/logistics/warehouses     (warehouse.read)
├── Vehiculos         → /app/logistics/vehicles       (vehicle.read)
└── Puntos entrega    → /app/logistics/delivery-points (delivery.read)
```

---

## Pruebas

- StateMachineService: cada transicion valida e invalida
- ADR: validacion de fechas PH, categorias
- Movimientos: calculo de estados segun tipo de movimiento
- Integracion: ciclo completo crear cilindro → transicion → historial
- Permisos: cada endpoint retorna 403 sin permiso
- Eventos: cada accion emite el evento esperado
- Tenant isolation: tenant A no ve datos de tenant B
- Frontend: renderizado de cada pagina con datos mock
- Frontend: formularios con validacion
- Frontend: badges con color correcto

---

## Orden de implementacion

El corte actual cubre lo planificado originalmente. Ver SPEC 0012 para la siguiente fase (envase completo + escaneo movil).

```
Implementado:
  - Modelos PostgreSQL (20 tablas) + migraciones (001, 002, 003)
  - Catalogo de estados + transiciones (seed)
  - StateMachineService + ADR/PH validation
  - API CRUD cilindros + transiciones + trace
  - lg_warehouses, lg_vehicles, lg_delivery_points, lg_zones
  - API catalogos + CRUD almacenes/vehiculos/puntos
  - lg_orders + lg_order_items
  - API pedidos + lineas
  - lg_routes + lg_route_stops + lg_loads
  - lg_movements + items + status_history
  - lg_agenda_tasks + lg_agenda_task_types
  - lg_hydrostatic_tests + lg_cylinder_warranties
  - Frontend: todas las paginas (cilindros, pedidos, rutas, carga,
    movimientos, agenda, almacenes, vehiculos, puntos entrega)
  - Widget dashboard + sidebar
  - Tests de integracion (flujo cilindros + operaciones)

Siguiente fase (SPEC 0012):
  - Envase completo: barcodes, ADR, gas, marca, precio, etc.
  - Retimbrados, custodia, servicios, escaneo movil, etiquetas
```

---

## Criterios de aceptacion

1. Usuario con permisos `logistics.*` puede crear cilindros, listarlos con filtros, ver detalle y ejecutar transiciones
2. Transiciones solo permiten estados destino validos segun `lg_state_transitions`
3. Transicion a `LLENADO_OK` requiere PH vigente y ADR vigente
4. Cada transicion se registra en `lg_cylinder_state_log` con contexto completo
5. Usuario puede crear pedido, vincularlo a movimiento y generar ruta
6. Usuario puede planificar ruta con stops, vehiculo y repartidor
7. Usuario puede preparar carga asignando cilindros a cada stop
8. Al confirmar carga, cilindros transicionan a `CARGA_EN_VEHICULO`
9. Al iniciar ruta, cilindros transicionan a `EN_RUTA`
10. Al confirmar entrega, cilindros transicionan a `EN_CLIENTE_LLENO`
11. Cada accion emite su evento en `event_log`
12. Todo es tenant-scoped
13. Sidebar muestra logistica solo con permisos
14. Plugin se instala/habilita/deshabilita desde PluginsPage sin romper el core
15. API retorna 403 sin permiso
16. Frontend oculta botones segun permisos

---

## Plugins futuros

| plugin | dominio | depende de |
|--------|---------|-----------|
Nota: Antes de iniciar nuevos plugins, logistics requiere completar su fase de envase (SPEC 0012)
para cubrir barcodes, ADR completo, retimbrados, custodia, servicios, escaneo movil y etiquetas.

| plugin | dominio | depende de |
|--------|---------|-----------|
| `inventory` | Stock, kardex, inventario fisico | logistics (eventos de movimiento) |
| `crm` | Clientes, contactos, historial | kernel |
| `billing` | Facturacion electronica Peru/CR | logistics + crm |
| `purchasing` | Compras, proveedores, OC | inventory |
| `hr` | Empleados, asistencia, vacaciones | kernel |
| `pricing` | Tarifas, listas de precios | crm + billing |
| `analytics` | Dashboard, metricas, reportes | todos |

Cada plugin sigue el mismo contrato: `plugin.json`, backend, frontend, migrations, permissions, events.
