# SPEC 0029C — Corrección de visibilidad de almacenes MOBILE

## Estado

Implementado (2026-07-28)

## Contexto

SPEC 0029 Gap 4 estableció: "Filtrar `warehouse_type != 'MOBILE'` en las funciones de catálogo visibles al usuario." Esto se implementó correctamente en las funciones de catálogo, pero **incorrectamente** en `balances.py`, que es consumido por funciones internas de negocio:

- `build_current_composition` → lee composición del vehículo en ruta
- `build_session_snapshot` → lee stock actual de la jornada
- `return_remaining_stock` → transfiere remanente mobile→origen

Todas estas funciones **deben** ver los almacenes MOBILE porque son su razón de existir.

## 🔴 Problema: balances.py filtra MOBILE

### Código actual

`plugins/stock/backend/services/balances.py` (4 ocurrencias, líneas 88, 151, 225, 327):

```python
select(...)
.where(
    ...
    LogisticsWarehouse.warehouse_type != "MOBILE",
)
```

### Impacto

| Función consumidora | Qué rompe | Evidencia |
|---|---|---|
| `build_session_snapshot` | `current_stock.total_units = 0` siempre | `test_vehicle_session_load_cycle: assert 0.0 == 5` |
| `build_current_composition` | `product_lines` vacío post-operación | `test_route_operation_changes_composition_and_outdates_waybill: IndexError` |
| `return_remaining_stock` | No detecta stock a retornar, deja unidades fantasmas en mobile | No cubierto por tests aún |
| `get_warehouse_balances` | Cualquier consulta de stock en mobile devuelve vacío | General |

### Causa raíz

Gap 4 se sobre-aplicó. La spec original decía "funciones de catálogo visibles al usuario". `balances.py` **no es un catálogo de UI** — es una consulta interna de negocio. Al aplicarle el filtro, el sistema se volvió ciego a sus propios almacenes operativos.

## Solución

### Principio

**MOBILE no es visible en selectores de UI. MOBILE SÍ es visible en consultas internas de stock.**

### Archivos a modificar

```
plugins/stock/backend/services/balances.py  — ELIMINAR filtro warehouse_type != "MOBILE" (4 ocurrencias)
```

### Archivos que NO se tocan (correctos)

```
plugins/stock/backend/services/catalog.py       — list_warehouses (catálogo UI) — mantener filtro
plugins/logistics/backend/services/catalog.py    — list_warehouses_catalog (catálogo UI) — mantener filtro
plugins/logistics/backend/services/resources.py  — list_warehouses (catálogo UI) — mantener filtro
```

### Verificación

Eliminar `warehouse_type != "MOBILE"` solo de `balances.py`. Las 4 funciones de consulta de balance deben incluir MOBILE:

1. `list_balances` (main query)
2. `get_balance_detail` 
3. `_paginated_balances` (si existe)
4. Cualquier query interna que una a `lg_warehouses`

## Tests afectados

Al corregir, estos tests deben pasar:

| Test | Esperado |
|---|---|
| `test_vehicle_session_load_cycle` | `total_units == 5` tras `confirm-and-ready` |
| `test_route_operation_changes_composition_and_outdates_waybill` | `product_lines[0].quantity == 3` tras DELIVERY de 2 |
| `test_operational_summary_*` | `current_stock` no vacío en mobile |
| `test_exchange_incident_and_route_stop_progress` | Composición refleja EXCHANGE correctamente |
| `test_route_stop_results_*` | Resultados de parada ven stock mobile |

## Riesgos

- **Ninguno**: los almacenes MOBILE ya están filtrados en los catálogos de UI. Este cambio solo restaura visibilidad interna.
- Si algún reporte o dashboard consumía `list_balances` y ahora muestra MOBILE, es aceptable — son almacenes reales con stock real.

## No incluye

- No modifica la creación de almacenes MOBILE
- No modifica `transfer_stock` ni `confirm_transfer_out`
- No agrega nuevos filtros ni endpoints
- No cambia la semántica de `warehouse_type`

## Criterios de aceptación

1. `POST /confirm-and-ready` → snapshot muestra `current_stock.total_units > 0` para productos cargados.
2. `GET /composition/current` → `product_lines` incluye productos en mobile.
3. `POST /return-remaining` → detecta y transfiere stock desde mobile a origen.
4. Catálogos de UI (`/catalog/warehouses`, `/stock/catalog/warehouses`) NO muestran MOBILE (sin cambios).
5. Tests existentes de `test_logistics_vehicle_sessions_v1.py` pasan (excepto los que requieren fix de `unit_cost` — cubierto en 0029B).

## Referencias

- SPEC 0029 Gap 4 — filtro MOBILE en catálogos
- SPEC 0029B — stock bridge transaccional (descubrió el bug)
- `plugins/stock/backend/services/balances.py:88,151,225,327`
- `plugins/logistics/backend/integrations/stock.py:20` — `get_warehouse_balances` (consumidor)
- `plugins/logistics/backend/services/route_operations.py:574` — `build_current_composition` (consumidor)
- `plugins/logistics/backend/services/snapshots.py:63` — `build_session_snapshot` (consumidor)
