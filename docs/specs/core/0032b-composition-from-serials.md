# SPEC 0032b — Composición desde seriales reales, no stock genérico

## Estado

Implementado (2026-07-28)

## Contexto

La carta porte y la composición calculan `total_packages` desde `stk_balance.quantity` (stock abstracto en el almacén mobile). Para productos serializados, esto diverge de la realidad: el stock puede decir 52 pero los seriales asignados son 2.

SPEC 0031 ya estableció el invariante `stock movement == serial movement`. Pero la composición aún no lo respeta — sigue leyendo de la fuente incorrecta.

## Solución

En `build_current_composition`, para cada producto detectar si es serializado (`product_requires_serial_capture`). Si lo es, calcular `quantity`, `weight_kg`, y `adr_points` desde los cilindros reales asignados a la sesión (`lg_load_serial_assignments` + `lg_cylinders`). Si no lo es, usar `stk_balance` como hasta ahora.

### Cambio en `build_current_composition`

```python
# Para cada balance, si el producto es serializado:
if product_requires_serial_capture(db, ...):
    # Leer de seriales reales
    serials = db.execute(
        select(func.count(), func.sum(c.weight_current), func.sum(c.adr_points))
        .join(LogisticsCylinder, ...)
        .where(assignment_status == 'CONFIRMED', session_id = S, product_id = P)
    )
    quantity = serials[0]          # count real
    weight_kg = serials[1]         # peso real de los cilindros
    adr_points = serials[2]        # ADR real de los cilindros
else:
    # Leer de stk_balance (sin cambios)
    quantity = balance.quantity
```

## Archivos afectados

```
plugins/logistics/backend/services/route_operations.py — build_current_composition
```

## Criterios de aceptación

1. Producto serializado con 2 cilindros CONFIRMED y stock de 52 → composición muestra `quantity = 2`.
2. Producto no serializado → composición sigue usando `stk_balance.quantity` (sin cambios).
3. Carta porte refleja los mismos valores que la composición.
4. ADR points y weight_kg para serializados vienen de los cilindros reales.
5. Tests existentes siguen pasando.

## Riesgos

- **Rendimiento**: una query adicional por producto serializado. Con ~5 productos por sesión, son ~5 queries extra. Aceptable.
- **Producto serializado sin seriales asignados**: se muestra con `quantity = 0` en la composición, aunque tenga stock. Esto es correcto — si no hay seriales, no hay nada que transportar.
