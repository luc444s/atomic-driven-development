# SPEC 0023AO — Envases en posesión del cliente (Customer cylinder summary)

> Nota de vigencia: revisar junto con `0023AD.2` y `0023AD.3`.
> La parte contractual de este documento debe interpretarse bajo el criterio actual de contrato por derecho/cupo, no como vínculo fijo por bombona.

## Estado

Propuesta — 2026-07-10

## Problema

Hoy el sistema permite:

- contratar una cantidad fija de envases por cliente (`lg_cylinder_contracts.quantity`);
- registrar cambios de custodia por cilindro (`lg_cylinder_ownership`);
- conocer el estado físico actual de cada cilindro (`lg_cylinders.current_state`);
- ejecutar movimientos de entrega y recojo (`SC`, `IC`, `movements`, `routes`, `mobile_warehouses`).

Pero **no existe una vista agregada** que responda la pregunta operativa más frecuente:

> "¿Cuántos envases tiene el cliente X en este momento, y eso coincide con su contrato?"

Cada vez que un cliente llama, un vendedor necesita ver rápido si hay faltantes, excesos o inconsistencias entre lo contratado, lo asignado y lo que físicamente está en el cliente.

Hoy esa respuesta requiere cruce manual de datos en tres dominios distintos (contratos, custodia, estado físico) sin una vista unificada.

## Objetivo

Construir una vista de solo lectura `CustomerCylinderSummary` que muestre tres dimensiones separadas y sus desviaciones:

1. **Compromiso contractual**: cuántos envases tiene contratados el cliente
2. **Asignación contractual**: cuántos están bajo responsabilidad activa del cliente
3. **Posesión física actual**: cuántos están realmente en el cliente

Sin mezclar las fuentes, sin crear una segunda fuente de verdad, sin acoplar al motor de stock.

## No objetivos

- no modificar `lg_cylinder_ownership` (sigue siendo append-only histórico);
- no agregar columnas nuevas a tablas existentes;
- no persistiendo el resultado (la vista siempre se computa);
- no listar seriales individuales en la respuesta principal;
- no involucrar `stk_balance` ni `stk_ledger`;
- no escribir lógica de negocio transaccional (es solo lectura);
- no reemplazar el módulo de contratos (0023AD) ni el de trazabilidad (0023C).

## Modelo conceptual

### Las tres dimensiones

| Dimensión | Pregunta que responde | Naturaleza | Fuente de verdad |
|---|---|---|---|
| **Compromiso contractual** | ¿Cuántos envases debería tener? | Estática (cambia por renovación/vencimiento) | `lg_cylinder_contracts.quantity` |
| **Asignación contractual** | ¿Cuántos están bajo responsabilidad del cliente? | Semidinámica (entregados - devueltos) | `lg_cylinder_contract_items` donde `delivered_at IS NOT NULL AND returned_at IS NULL` |
| **Posesión física actual** | ¿Cuántos están realmente en el cliente? | Dinámica (cambia con cada entrega/recojo) | `lg_cylinders.current_state` + último `lg_cylinder_ownership` |

### Reglas semánticas

**Assigned** (asignación contractual) ≠ físico. Assigned es obligación contractual activa. Un cilindro asignado puede estar en cliente, en ruta, en planta o perdido — sigue siendo responsabilidad del cliente hasta que el contrato lo libere.

**Fuente exacta de `assigned` en esta spec:**

- `assigned` se calcula **solo** desde `lg_cylinder_contract_items` activos del contrato;
- un item contractual activo es aquel con `delivered_at IS NOT NULL AND returned_at IS NULL`;
- `lg_cylinder_contracts.quantity` expresa el compromiso esperado, pero **no materializa por sí solo** cilindros asignados;
- si un contrato tiene `quantity > 0` pero todavía no tiene `contract_items` activos, entonces:
  - `contracted > 0`
  - `assigned = 0`
  - la diferencia se reporta como faltante contractual pendiente de materializar.

Esta decisión evita contar como asignados cilindros que nunca fueron realmente vinculados al cliente.

**Clasificación operativa de cada cilindro asignado:**

```
ASSIGNED (contract_items activos)
│
├── AT_CUSTOMER (current_state EN_CLIENTE_* Y ownership.customer_id = X)
│   ├── CILPRO (propio de la empresa)
│   ├── CILCLI (del cliente)
│   └── CILGAR (en garantía)
│
├── AT_CUSTOMER_UNKNOWN (current_state EN_CLIENTE_* PERO ownership ≠ X o NULL)
│   └── → ALERTA CRITICAL: cilindro mal rastreado
│
├── PIPELINE (asignado pero NO en cliente)
│   ├── IN_VEHICLE (current_state CARGA_EN_VEHICULO)
│   ├── IN_TRANSIT (current_state EN_RUTA)
│   ├── IN_WAREHOUSE (current_state EN_ALMACEN_*, LLENADO_OK, etc.)
│   └── UNKNOWN (cualquier otro estado no contemplado)
│
└── LOST (asignado pero sin current_state válido o sin tracking por N días)
    └── → ALERTA WARNING: posible pérdida
```

### Regla de consistencia — "está en el cliente"

Un cilindro está físicamente en el cliente si y solo si se cumplen **ambas** condiciones:

```
cylinder.current_state IN ('EN_CLIENTE_LLENO', 'EN_CLIENTE_VACIO')
AND latest_ownership(cylinder).customer_id = <customer_id>
```

La clasificación de cada cilindro sigue esta precedencia:

```
1. ¿current_state IN ('EN_CLIENTE_LLENO', 'EN_CLIENTE_VACIO')?
   ├── Sí → ¿ownership.customer_id = <customer_id>?
   │   ├── Sí → AT_CUSTOMER
   │   └── No → AT_CUSTOMER_UNKNOWN
   └── No → PIPELINE
```

**LOST** no se asigna por estado del cilindro. Se deriva matemáticamente como la diferencia de cierre:

```
lost = assigned - (at_customer + pipeline + at_customer_unknown)
```

Esto garantiza consistencia aritmética: **assigned = at_customer + at_customer_unknown + pipeline + lost**.

| Estado | Ownership | Clasificación | Alerta |
|---|---|---|---|
| `EN_CLIENTE_*` | customer_id = X | `AT_CUSTOMER` | — |
| `EN_CLIENTE_*` | customer_id ≠ X o NULL | `AT_CUSTOMER_UNKNOWN` | CRITICAL |
| No `EN_CLIENTE_*` | customer_id = X | `PIPELINE` | INFO si pipeline > tolerancia |
| — | — | `LOST` (derivado) | WARNING si `lost > 0` |

**Umbral de alerta para LOST:** el sistema dispara WARNING cuando `lost > 0`. Adicionalmente, si un cilindro clasificado como `PIPELINE` supera **N días** sin cambio de estado, se marca internamente como sospechoso de pérdida. El valor de `N` es configurable por tenant con default de 90 días. Esta marca no altera la clasificación (sigue siendo pipeline), pero alimenta alertas y el dashboard de conciliación.

### Prioridad de fuentes ante conflicto

| Conflicto | Fuente ganadora | Razón |
|---|---|---|
| Ownership dice "cliente X" pero estado es `EN_ALMACEN_*` | **current_state** | El cilindro salió del cliente pero ownership aún no se actualizó. Se cuenta como pipeline, no como "en cliente". |
| Ownership dice "sin cliente" pero estado es `EN_CLIENTE_*` | **ownership** (ausencia) | No se sabe de quién es; el cilindro está mal rastreado. Alerta CRITICAL. |
| Contract_items dice "entregado" pero ownership no existe | **contract_items** | El contrato asigna pero el tracking no registró. Inconsistencia operativa. Alerta. |

## Separación de responsabilidades

```
┌─────────────────────────────────────────────────────────────┐
│              CustomerCylinderSummary                         │
│                  (read model)                                │
│                                                              │
│  Solo LEE. No persiste. No escribe. No es fuente de verdad.  │
│                                                              │
│  contracts.quantity    → compromiso (dueño: contracts)       │
│  contract_items        → asignación (dueño: contracts)       │
│  lg_cylinders          → estado actual (dueño: logistics)    │
│  lg_cylinder_ownership → custodia (dueño: logistics)         │
│                                                              │
│  stk_balance / stk_ledger → NO participan (son warehouse)    │
└─────────────────────────────────────────────────────────────┘
```

**Stock no tiene dimensión cliente.** El read model cruza contracts + logistics pero nunca involucra al motor de stock. Eso asegura desacoplamiento total.

### ¿Por qué el endpoint vive en logistics?

El dato más costoso de obtener son los cilindros (10k+ registros por tenant). Contracts devuelve un `quantity` escalar. Poner el endpoint en contracts obligaría a ese módulo a importar lógica de logistics (cilindros, estados, ownership). Ponerlo en logistics permite que logistics consulte contracts vía query directa (misma BD, mismo tenant, FK real).

### ¿Por qué no composición en frontend?

La lógica de cruce (qué cuenta como "asignado" vs "en cliente", derivación de pipeline, clasificación de `at_customer_unknown`, cálculo de alertas) es lógica de dominio, no de presentación. El frontend solo renderiza.

## Arquitectura de lectura

### Regla de contrato activo

Para `0023AO`, un contrato se considera **activo** si su `status = 'ACTIVE'`.

Semántica operativa:

- puede haber **múltiples contratos activos** para un mismo cliente;
- la respuesta del summary **acumula** los valores de todos los contratos activos del cliente;
- la agregación mínima es por `customer_id + product_id`;
- si en el futuro el negocio exige unicidad por producto, esa restricción debe resolverse en `0023AD` y no en esta vista.

La vista no impone una regla nueva de unicidad contractual; solo refleja el estado contractual realmente existente.

### Endpoint

```
GET /customers/{customer_id}/cylinders/summary
```

Permiso: `logistics.cylinder.read`

Query params opcionales:

| Param | Tipo | Default | Descripción |
|---|---|---|---|
| `include_serials` | boolean | `false` | Incluye lista de seriales individuales en cada grupo |
| `as_of` | datetime | ahora | Computa el summary a una fecha/hora específica (para conciliación histórica) |
| `product_id` | string | — | Filtra por producto específico |

### Proceso interno

El endpoint ejecuta dos queries independientes en la misma transacción:

**Query 1 — Contracts:**
```sql
SELECT c.id, c.status, ci.product_id, c.quantity AS contracted,
       COUNT(ci.id) FILTER (WHERE ci.returned_at IS NULL) AS assigned
FROM lg_cylinder_contracts c
LEFT JOIN lg_cylinder_contract_items ci ON ci.contract_id = c.id
WHERE c.customer_id = :customer_id AND c.status = 'ACTIVE'
GROUP BY c.id, ci.product_id
```

Si existen varios contratos activos para el mismo `product_id`, el read model suma `contracted` y `assigned` antes de cruzarlos con logistics.

**Query 2 — Logistics (por cilindro):**
```sql
SELECT c.id, c.current_state, c.product_id, o.customer_id, o.condition
FROM lg_cylinders c
JOIN LATERAL (
    SELECT o2.customer_id, o2.condition
    FROM lg_cylinder_ownership o2
    WHERE o2.cylinder_id = c.id AND o2.customer_id IS NOT NULL
    ORDER BY o2.change_date DESC, o2.created_at DESC
    LIMIT 1
) o ON true
WHERE o.customer_id = :customer_id
```

### Pipeline y LOST

**Pipeline** se deriva directamente de los cilindros clasificados como `PIPELINE` (asignados, no `EN_CLIENTE_*`). La subclasificación (`in_vehicle`, `in_transit`, `in_warehouse`, `unknown`) se determina por `current_state` del cilindro.

**LOST** se deriva matemáticamente como la diferencia de cierre para mantener consistencia aritmética:

```
lost = assigned - (at_customer + at_customer_unknown + pipeline)
```

Esta fórmula garantiza que la identidad siempre se cumpla:

```
assigned = at_customer + at_customer_unknown + pipeline + lost
```

LOST captura cilindros que están asignados contractualmente pero no aparecen en ninguna categoría operativa (ej: cilindros devueltos en sistema pero aún marcados como assigned, o pérdidas reales no registradas). Si `lost > 0`, se dispara alerta WARNING para investigar.

**Umbral de alerta por inactividad:** adicionalmente, los cilindros clasificados como `PIPELINE` que superen **N días** sin cambio de estado en `lg_cylinder_state_log` se marcan como sospechosos de pérdida. El valor de `N` es configurable por tenant con default de 90 días. Esta marca no reclasifica el cilindro a `LOST` (ese valor solo se deriva matemáticamente), pero alimenta alertas complementarias y el dashboard de conciliación.

### Alertas

Se derivan automáticamente de los datos:

| Severidad | Condición | Mensaje |
|---|---|---|
| **CRITICAL** | `at_customer_unknown > 0` | "Hay cilindros en cliente sin ownership correcto" |
| **CRITICAL** | `at_customer > assigned` | "Hay más cilindros en cliente de los asignados por contrato" |
| **ERROR** | `assigned > contracted` | "Hay más cilindros asignados que los contratados" |
| **WARNING** | `assigned < contracted` | "Faltan cilindros por asignar respecto al contrato" |
| **WARNING** | `lost > 0` | "Hay cilindros asignados sin tracking reciente (posible pérdida)" |
| **INFO** | `pipeline > 0` | "Cilindros en rotación normal (pipeline activo)" |

### Comportamiento cuando no hay contrato activo

La vista **igual debe responder** aunque el cliente no tenga contratos activos.

Reglas:

- si no existe contrato activo, `contracted = 0` y `assigned = 0`;
- si aun así existen cilindros en `AT_CUSTOMER`, `AT_CUSTOMER_UNKNOWN` o `PIPELINE`, la vista los muestra como realidad operativa actual;
- esa situación genera alerta de inconsistencia contractual, porque hay posesión o rastro operativo sin respaldo contractual activo.

Esto permite que la vista sirva también para auditoría y regularización, no solo para operación nominal.

## Diseño de la respuesta

```json
{
  "customer_id": "uuid",
  "customer_name": "Razón social o nombre comercial",
  "contract": {
    "contract_id": "uuid",
    "status": "ACTIVE"
  },
  "summary": {
    "contracted": 50,
    "assigned": 48,
    "at_customer": 40,
    "at_customer_unknown": 0,
    "pipeline": 8,
    "lost": 0,
    "deviation": -2
  },
  "by_product": [
    {
      "product_id": "uuid",
      "product_name": "Bombona 27kg",
      "contracted": 50,
      "assigned": 48,
      "at_customer": 40,
      "at_customer_unknown": 0,
      "pipeline": {
        "total": 8,
        "in_vehicle": 2,
        "in_transit": 3,
        "in_warehouse": 3,
        "unknown": 0
      },
      "lost": 0,
      "by_condition": {
        "CILPRO": {
          "assigned": 40,
          "at_customer": 33,
          "pipeline": 7,
          "lost": 0
        },
        "CILCLI": {
          "assigned": 8,
          "at_customer": 7,
          "pipeline": 1,
          "lost": 0
        },
        "CILGAR": {
          "assigned": 0,
          "at_customer": 0,
          "pipeline": 0,
          "lost": 0
        }
      }
    }
  ],
  "alerts": [
    {
      "severity": "warning",
      "category": "shortage",
      "message": "Asignados 48 de 50 contratados (faltan 2)"
    },
    {
      "severity": "info",
      "category": "pipeline",
      "message": "8 cilindros en pipeline: 2 en vehículo, 3 en tránsito, 3 en almacén"
    }
  ]
}
```

### Lo que se omite (para no saturar)

- Listado individual de seriales de cilindros (va como expansión con `?include_serials=true`)
- Historial de movimientos (ya está en movements)
- Fechas de entrega/recojo (están en contract_items)
- Detalle financiero (precios, facturación)

### Alcance del primer slice

Para la primera entrega de `0023AO`:

- `include_serials=true` queda **fuera de alcance**;
- la respuesta principal solo devuelve agregados por producto, condición y clasificación operativa;
- el detalle por serial se deja como segunda iteración o vista secundaria, una vez validado el uso real del summary por operaciones/comercial.

La prioridad del primer slice es que el usuario vea rápidamente:

1. cuánto debería tener el cliente;
2. cuánto está bajo su responsabilidad;
3. cuánto está realmente en cliente;
4. si hay desvíos o tracking inconsistente.

## UX conceptual

### Ubicación

La vista se integra en `CustomerDetailPage` (CRM) como una sección/dialog adicional "Envases", accesible desde los botones de gestión del cliente.

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  CustomerInfoCard    │  Resumen del cliente                 │
│                      │                                      │
│                      │  ┌─ Envases ───────────────────────┐ │
│                      │  │ Contrato: 50   ════════════════ │ │
│                      │  │ Asignados: 48  ████████████░░░░░ │ │
│                      │  │ En cliente: 40 ██████████░░░░░░░ │ │
│                      │  │ Pipeline: 8    ██░░░░░░░░░░░░░░░ │ │
│                      │  │ Desviación: -2 ⚠️                │ │
│                      │  └──────────────────────────────────┘ │
│                      │                                      │
│                      │  [⬇️ Ver detalle] [📋 Contratos]    │
│                      │  [🔄 Conciliar]                       │
└─────────────────────────────────────────────────────────────┘
```

### Visual cues

- **Verde**: deviation = 0 o dentro de tolerancia natural por pipeline
- **Amarillo**: deviation < 0 (faltan) o > 5% del contratado
- **Rojo**: `at_customer_unknown > 0` o `lost > 0`
- **Barra de progreso**: `[████████░░░░] 40/50 en cliente` con color según estado
- **Tooltip** en cada métrica con desglose por condición (CILPRO/CILCLI/CILGAR)

### Dialog expandido "Ver detalle"

```
┌─────────────────────────────────────────────────────────────┐
│  Producto     │ Cont │ Asig │ Cliente │ Pipeline │ ⚠️ │
│  Bombona 27kg │ 50   │ 48   │ 40      │ 8        │ -2 │
│               │      │      │         │          │    │
│  ▼ Condición               │ Cliente │ Pipeline │    │
│    Propios (CILPRO) 40     │ 33      │ 7        │    │
│    Del cliente (CILCLI) 8  │ 7       │ 1        │    │
│    Garantía (CILGAR) 0     │ 0       │ 0        │    │
│               │      │      │         │          │    │
│  ▼ Pipeline detalle        │         │          │    │
│    En vehículo: 2          │         │          │    │
│    En tránsito: 3          │         │          │    │
│    En almacén: 3           │         │          │    │
│               │      │      │         │          │    │
│  Ver seriales → │      │      │         │          │    │
└─────────────────────────────────────────────────────────────┘
```

## Escalabilidad y futuro

### Conciliación histórica

El query param `?as_of=timestamp` permite computar el summary a una fecha/hora específica. Útil para:
- cierres diarios;
- responder "¿cómo estaba el balance la semana pasada?";
- auditoría retrospectiva.

Para soportarlo, las queries deben usar `created_at <= as_of` en vez de filtros en tiempo real.

### Auditoría

Cada dimensión es trazable individualmente desde sus propias tablas de historial:

| Dimensión | Tabla de auditoría |
|---|---|
| Compromiso contractual | `lg_cylinder_contracts.updated_at` + event log |
| Asignación contractual | `lg_cylinder_contract_items` (delivered_at / returned_at) |
| Posesión física | `lg_cylinder_state_log` + `lg_cylinder_ownership` |
| Alertas | No se persisten (se derivan en cada request) |

### Control de pérdidas

El dashboard de "cilindros no ubicados" se alimenta de dos fuentes:

1. **LOST (derivado):** `lost = assigned - (at_customer + at_customer_unknown + pipeline)`. Este valor es siempre la diferencia de cierre y garantiza consistencia aritmética. Si `lost > 0`, hay cilindros que el contrato da por asignados pero el tracking operativo no logra ubicar.

2. **Pipeline inactivo (alerta por tiempo):** cilindros en `PIPELINE` que llevan **más de N días** sin cambio de estado en `lg_cylinder_state_log`. El umbral `N` es configurable por tenant (default: 90 días). Esta métrica no reclasifica el cilindro — sigue siendo pipeline — pero alimenta una alerta separada de "sospecha de pérdida" para que el operador investigue.

La conciliación manual puede aclarar la ubicación real (ej: "el cilindro está en almacén pero no se actualizó el estado"), pero no modifica las tablas de origen — la corrección debe hacerse actualizando el estado del cilindro en logistics.

### Tracking por serial

El detail `by_product` puede expandirse con `?include_serials=true` para listar los seriales individuales con su clasificación actual. Esto no va en la respuesta principal por razones de volumen.

## Dependencias

- `plugins/logistics` — dueño de `lg_cylinders`, `lg_cylinder_ownership`, `lg_cylinder_state_log`
- `plugins/logistics` + contracts submódulo (0023AD) — dueño de `lg_cylinder_contracts`, `lg_cylinder_contract_items`
- `plugins/crm` — consumidor de la vista (CustomerDetailPage)

## Permisos sugeridos

| Permiso | Recurso |
|---|---|
| `logistics.cylinder.read` | Lectura del endpoint summary |

Reusa el permiso existente de lectura de cilindros. No requiere permiso nuevo.

## Criterios de aceptación

1. El endpoint `GET /customers/{id}/cylinders/summary` retorna las tres dimensiones (contracted, assigned, at_customer) correctamente pobladas.
2. `assigned` se calcula exclusivamente desde `lg_cylinder_contract_items` activos (`delivered_at IS NOT NULL AND returned_at IS NULL`).
3. Si existe `quantity` contratada pero no hay items activos, la vista muestra `contracted > 0` y `assigned = 0`.
4. La vista acumula múltiples contratos activos por `customer_id + product_id` sin imponer unicidad artificial.
5. La clasificación `at_customer` solo cuenta cilindros con `current_state IN ('EN_CLIENTE_LLENO', 'EN_CLIENTE_VACIO')` Y `ownership.customer_id = <id>`.
6. `at_customer_unknown` captura cilindros en estado `EN_CLIENTE_*` sin ownership correcto.
7. `lost` se deriva siempre como `assigned - (at_customer + at_customer_unknown + pipeline)`.
8. Las alertas se derivan correctamente con la severidad adecuada.
9. Si el cliente no tiene contratos activos, el endpoint responde igual y muestra `contracted = 0`, `assigned = 0` y la realidad operativa si existe.
10. `?as_of=timestamp` retorna el estado histórico a esa fecha.
11. `?include_serials=true` no forma parte del primer slice implementable de `0023AO`.
12. La vista no impacta el rendimiento de escritura de contracts ni logistics (es solo lectura).
