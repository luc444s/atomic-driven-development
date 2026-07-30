# SPEC 0031 — Coherencia serial-stock en operaciones de ruta

## Estado

Propuesta — v3 (2026-07-28). Aprobada para implementación.

## Contexto

SPEC 0030 ancló el estado de cilindro a la sesión operativa. Pero el flujo de ruta (`DELIVERY`, `PICKUP`, `RETURN`) sigue sin transicionar seriales porque `_build_movement_payload` nunca setea `cylinder_id` en los `MovementItem`.

El sistema **ya tiene** los datos para resolver esto: `lg_load_serial_assignments` contiene exactamente qué cilindros están asignados a qué sesión. El gap es puramente de integración: nadie lee esa tabla durante las operaciones de ruta.

### Impacto actual

| Operación | Stock | Serial | Consecuencia |
|---|---|---|---|
| DELIVERY | `sale_out_stock` ✅ | No transiciona | Cilindro sigue en `EN_RUTA`, no en `EN_CLIENTE_LLENO` |
| PICKUP | `return_in_stock` ✅ | No transiciona | Cilindro en `EN_CLIENTE_VACIO`, no en `EN_ALMACEN_VACIO` |
| EXCHANGE | Ambos ✅ | Ninguno | SC e IC operan sobre stock, seriales no se mueven |
| Retorno | `transfer()` mobile→origen ✅ | No transiciona | Cilindros en tránsito tras sesión cerrada |

### Causa raíz

`LogisticsRouteOperationItem` no tiene `cylinder_id`. `_build_movement_payload` no consulta `lg_load_serial_assignments`. `apply_cylinder_effects_for_movement` requiere `cylinder_id` y no lo encuentra.

---

## Principio

**Cuando hay identidad física → no se trabaja en agregados.** Si `moves_cylinders=True`, cada serial es un `MovementItem` individual con `quantity=1`.

## Invariante global (formal)

```
∀ movement:
    Δstock(product, warehouse) == Σ serial_transitions(session, product)
```

Esto habilita reconciliación automática, auditoría contable real y detección de anomalías.

---

## Solución

### Flujo corregido

```
RouteOperationItem (product_id, quantity)
    │
    ▼ (moves_cylinders=True: expandir a 1 item por serial)
_resolve_serial_ids(db, session_id, product_id, quantity, movement_type)
    │  SELECT lsa.cylinder_id
    │  FROM lg_load_serial_assignments lsa
    │  JOIN lg_cylinders c ON c.id = lsa.cylinder_id
    │  WHERE lsa.session_id = S AND lsa.product_id = P
    │    AND lsa.assignment_status = 'CONFIRMED'
    │    AND c.current_state IN (states_for_movement_type)
    │  ORDER BY lsa.created_at ASC
    │  LIMIT quantity
    │
    ▼ (N seriales → N MovementItems, quantity=1 cada uno)
MovementItem[0] (cylinder_id=C1, quantity=1) ✅
MovementItem[1] (cylinder_id=C2, quantity=1) ✅
    │
    ▼
apply_cylinder_effects_for_movement()
    │  transition_cylinder(C1, EN_RUTA → EN_CLIENTE_LLENO)
    │  transition_cylinder(C2, EN_RUTA → EN_CLIENTE_LLENO)
    ▼
stock == serial ✅
```

### Resolución de seriales

Fuente de verdad: `movement_type` (SC/IC), no `direction` (DELIVERY/PICKUP). Orden determinista.

```python
_STATE_BY_MOVEMENT_TYPE: dict[str, tuple[str, ...]] = {
    "SC": ("CARGA_EN_VEHICULO", "EN_RUTA"),
    "IC": ("EN_CLIENTE_VACIO",),
    "SP": (
        "EN_ALMACEN_VACIO", "EN_ALMACEN_LLENO",
        "OBSERVADO", "PARA_REPARACION",
    ),
}

def _resolve_serial_ids(
    db: Session,
    *,
    session_id: str,
    product_id: str,
    quantity: int,
    movement_type: str,
) -> list[str]:
    states = _STATE_BY_MOVEMENT_TYPE.get(movement_type)
    if states is None:
        return []

    return list(db.scalars(
        select(LogisticsLoadSerialAssignment.cylinder_id)
        .join(LogisticsCylinder,
              LogisticsCylinder.id == LogisticsLoadSerialAssignment.cylinder_id)
        .where(
            LogisticsLoadSerialAssignment.session_id == session_id,
            LogisticsLoadSerialAssignment.product_id == product_id,
            LogisticsLoadSerialAssignment.assignment_status == "CONFIRMED",
            LogisticsCylinder.current_state.in_(states),
        )
        .order_by(
            LogisticsLoadSerialAssignment.created_at.asc(),
            LogisticsLoadSerialAssignment.cylinder_id.asc(),
        )
        .with_for_update(skip_locked=True)
        .limit(quantity)
    ).all())
```

`.with_for_update(skip_locked=True)` bloquea los seriales seleccionados dentro de la transacción. Evita que dos requests concurrentes seleccionen el mismo serial. `skip_locked` omite filas ya bloqueadas por otra transacción, evitando deadlocks.

`.order_by(created_at, cylinder_id)` garantiza orden 100% determinista incluso cuando hay timestamps idénticos.

### Error de dominio

```python
class SerialResolutionError(ValueError):
    """Seriales insuficientes o en estado incorrecto para la operación."""
```

`ValueError` genérico → `SerialResolutionError` para logs claros y API responses consistentes.

### Construcción de items: 1 por serial + cache

```python
def _build_items_for_operation(
    db, *, session, items, movement_type,
):
    mt = get_movement_type(db, code=movement_type)
    serial_cache: dict[tuple[str, str], bool] = {}
    result = []

    for item in items:
        if mt and mt.moves_cylinders:
            cache_key = (session.id, item.product_id)
            if cache_key not in serial_cache:
                serial_cache[cache_key] = product_requires_serial_capture(
                    db, tenant_id=session.tenant_id,
                    session_id=session.id,
                    product_id=item.product_id,
                    source_warehouse_id=None,
                )
            requires_serials = serial_cache[cache_key]

            if not requires_serials:
                result.append(_build_item_dict(item, movement_type))
                continue

            serials = _resolve_serial_ids(
                db, session_id=session.id,
                product_id=item.product_id,
                quantity=int(item.quantity),
                movement_type=movement_type,
            )

            if not serials:
                raise SerialResolutionError(
                    f"Seriales insuficientes | producto={item.product_name} | "
                    f"requeridos={int(item.quantity)} | disponibles=0 | "
                    f"movement_type={movement_type} | session={session.id}"
                )
            if len(serials) < int(item.quantity):
                raise SerialResolutionError(
                    f"Seriales insuficientes | producto={item.product_name} | "
                    f"requeridos={int(item.quantity)} | "
                    f"disponibles={len(serials)} | "
                    f"movement_type={movement_type} | session={session.id}"
                )

            for cyl_id in serials:
                result.append(_build_item_dict(
                    item, movement_type, cylinder_id=cyl_id, quantity=1,
                ))
        else:
            result.append(_build_item_dict(item, movement_type))
    return result
```

### Retorno (Gap 3) — orden estricto: stock → serial

```python
# En return_remaining_stock:
# 1. PRIMERO: transferir stock mobile → origen
confirm_transfer_in(db, session=session, ...)

# 2. DESPUÉS: transicionar seriales
#    TODO(0031.1): bulk transition para N > 100
cylinders = list(db.scalars(
    select(LogisticsCylinder).where(
        LogisticsCylinder.session_id == session.id,
        LogisticsCylinder.current_state.in_(
            ("CARGA_EN_VEHICULO", "EN_RUTA",
             "EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO")
        ),
    )
).all())
for cylinder in cylinders:
    transition_cylinder(
        db, tenant_id=session.tenant_id,
        cylinder_id=cylinder.id,
        payload=CylinderTransitionRequest(
            to_state="EN_ALMACEN_VACIO",
            origin="SESSION_RETURN",
            notes=f"Retorno sesión {session.id}",
        ),
        action_context=action_context,
    )
```

### Cierre de sesión — invariante antes de limpiar

```python
# En close_vehicle_session, ANTES de limpiar session_id:
transit_remaining = db.scalar(
    select(func.count(LogisticsCylinder.id)).where(
        LogisticsCylinder.session_id == session.id,
        LogisticsCylinder.current_state.in_(
            ("CARGA_EN_VEHICULO", "EN_RUTA")
        ),
    )
)
if transit_remaining and transit_remaining > 0:
    raise SerialResolutionError(
        f"No se puede cerrar la sesión: {transit_remaining} cilindros "
        f"aún en tránsito. Ejecuta el retorno primero."
    )

# Solo después de verificar: limpiar session_id
db.execute(
    update(LogisticsCylinder)
    .where(LogisticsCylinder.session_id == session.id)
    .values(session_id=None)
)
```

---

## Archivos afectados

```
plugins/logistics/backend/services/route_operations.py — _build_movement_payload + _resolve_serial_ids
                                                           + _build_items_for_operation + SerialResolutionError
plugins/logistics/backend/services/load_plans.py         — return_remaining_stock (transicionar seriales post-transfer)
plugins/logistics/backend/services/reconciliation.py     — close_vehicle_session (invariante + cleanup session_id)
plugins/logistics/backend/models/route_operations.py     — (sin cambios)
```

## Criterios de aceptación

1. DELIVERY de 2 unidades de producto P serializado → 2 `MovementItem` (uno por serial, `quantity=1`). Ambos transicionan de `EN_RUTA` a `EN_CLIENTE_LLENO`.
2. PICKUP de 3 unidades de producto P serializado → 3 `MovementItem`, transicionan de `EN_CLIENTE_VACIO` a `EN_ALMACEN_VACIO`.
3. EXCHANGE (2 OUT + 1 IN) → OUT expande 2 items (SC), IN expande 1 item (IC). Seriales con estados correctos por movement_type.
4. Producto serializado con 0 seriales → `SerialResolutionError`, operación rechazada.
5. Producto serializado con seriales insuficientes → `SerialResolutionError`.
6. Producto NO serializado → 1 `MovementItem` sin `cylinder_id`, solo afecta stock. Sin error.
7. `mark-returning`: stock transferido ANTES de transicionar seriales. Todos los cilindros en `EN_ALMACEN_VACIO`.
8. `close_vehicle_session`: rechazado si hay cilindros en tránsito. Si pasa, `session_id = NULL`.
9. Mismo `(session_id, product_id)` no consulta `product_requires_serial_capture` más de una vez por request (cache).
10. Orden de selección de seriales determinista (`created_at ASC`).
11. Tests existentes de vehicle sessions y stock siguen pasando.

## No incluye

- No modifica `LogisticsRouteOperationItem` (no agrega `cylinder_id` al modelo)
- No cambia el contrato del frontend (el operador sigue seleccionando producto + cantidad)
- No modifica el state machine (ya tiene las transiciones)
- No modifica `apply_cylinder_effects_for_movement` (ya funciona, solo le faltan datos)
- No hace bulk transition en retorno (TODO 0031.1)

## Riesgos

- **Concurrencia**: `.with_for_update(skip_locked=True)` previene doble selección. Si todos los seriales están bloqueados por otra transacción, la query devuelve menos filas → `SerialResolutionError`. La otra transacción los libera al hacer commit/rollback.
- **Orden de seriales**: determinista por `(created_at, cylinder_id)`. A prueba de timestamps idénticos.
- **Cache inválido**: si `product_requires_serial_capture` cambia durante el request (imposible en práctica), el cache serviría datos stale. Aceptable para el scope de un request HTTP.
- **Rendimiento retorno**: N transiciones individuales para M cilindros. Con 150 cilindros son 150 queries. Aceptable para retorno (no es hot path). Cubierto por TODO 0031.1.

## Referencias

- SPEC 0030 — cylinder session invariant
- `plugins/logistics/backend/services/route_operations.py:340` — `_build_movement_payload`
- `plugins/logistics/backend/services/movements.py:287` — `apply_cylinder_effects_for_movement`
- `plugins/logistics/backend/services/load_serials.py:419` — `confirm_selected_serials_for_operation`
- `plugins/logistics/backend/models/load_serial_assignments.py` — `LogisticsLoadSerialAssignment`
- `plugins/logistics/backend/services/load_plans.py:214` — `return_remaining_stock`
- `plugins/logistics/backend/services/reconciliation.py:218` — `close_vehicle_session`
