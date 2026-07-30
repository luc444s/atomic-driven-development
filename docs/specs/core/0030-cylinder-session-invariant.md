# SPEC 0030 — Anclaje de estado de cilindro a sesión operativa

## Estado

Implementado — Fase 1 (2026-07-28)

## Contexto

El modelo `lg_cylinders` persiste `current_state` como un string editable sin ninguna restricción de integridad referencial. Estados que implican presencia en un vehículo (`CARGA_EN_VEHICULO`, `EN_RUTA`) pueden existir sin que haya una sesión activa, un movimiento, ni trazabilidad alguna.

Esto no es un bug — es una **violación del invariante fundamental del dominio**: el estado físico de un cilindro no es un atributo, es la consecuencia de eventos. Al tratarlo como atributo editable, el sistema acepta estados imposibles que corrompen silenciosamente stock, composición, reconciliación y auditoría.

### Evidencia real

Base de datos actual (3000 cilindros, 0 sesiones):

| `current_state` | Cantidad | ¿Existe sesión? |
|---|---|---|
| `CARGA_EN_VEHICULO` | 150 | No |
| `EN_RUTA` | 150 | No |

300 cilindros "en tránsito" en un sistema donde nunca se creó una sola jornada.

### Principio

```
estado físico ≠ atributo
estado físico = consecuencia de eventos
```

El state machine existente es correcto en su lógica de transiciones, pero no está protegido a nivel de datos. Esta spec blinda el modelo sin reescribir el state machine.

---

## Fase 1 — Hardening (esta spec)

### 1.1 FK opcional a sesión

```sql
ALTER TABLE lg_cylinders ADD COLUMN session_id VARCHAR(36);
ALTER TABLE lg_cylinders ADD CONSTRAINT fk_cylinder_session
    FOREIGN KEY (session_id) REFERENCES lg_vehicle_sessions(id);
```

Nulleable. Solo se puebla cuando el cilindro está operativamente asociado a una jornada.

### 1.2 Constraint lógico

Regla refinada: `session_id` persiste durante todo el ciclo de vida de la sesión, no solo en tránsito.

```
LOADING       → CARGA_EN_VEHICULO  → session_id = S
OUTBOUND      → EN_RUTA            → session_id = S
DELIVERY      → EN_CLIENTE_LLENO   → session_id = S  (aún parte de la sesión)
PICKUP        → EN_RUTA            → session_id = S  (vuelve al camión)
RETURNING     → EN_ALMACEN_VACIO   → session_id = S
CLOSED        →                    → session_id = NULL
```

Estados que **exigen** sesión activa:

```
CARGA_EN_VEHICULO
EN_RUTA
```

Estados que **retienen** sesión sin exigirla (trazabilidad):

```
EN_CLIENTE_LLENO   — si fue entregado en esta sesión
EN_CLIENTE_VACIO   — si fue recogido en esta sesión
EN_ALMACEN_VACIO   — si retornó del mobile pero sesión aún no cerrada
```

Constraint CHECK:

```sql
ALTER TABLE lg_cylinders ADD CONSTRAINT ck_cylinder_transit_requires_session
    CHECK (
        current_state NOT IN ('CARGA_EN_VEHICULO', 'EN_RUTA')
        OR session_id IS NOT NULL
    );
```

Solo fuerza `session_id` en los estados de tránsito físico. Los demás estados pueden tener `session_id` poblado (trazabilidad) o NULL (sin sesión activa).

### 1.3 Bloquear UPDATE directo de `current_state`

El `current_state` solo debe cambiar a través del state machine (`transition_cylinder`). Para forzarlo:

```python
# En el modelo, marcar current_state como protegido
# En el router de cylinders, rechazar PATCH que incluya current_state
# En transition_cylinder, setear session_id junto con el estado
```

Cambios concretos:

- **Modelo**: sin cambios estructurales (el constraint CHECK ya lo protege)
- **Router**: `PATCH /cylinders/{id}` rechaza si el payload incluye `current_state`
- **State machine**: `transition_cylinder` acepta `session_id` opcional y lo persiste al transicionar. El `session_id` se **mantiene** durante toda la vida de la sesión: carga, ruta, entrega, retorno. Solo se limpia (NULL) al cerrar la sesión (`close_session`).
- **`close_session`**: al cerrar la sesión, limpia `session_id = NULL` en todos los cilindros asociados.
- **`confirm_load_plan` / `start_route` / `confirm_route_operation`**: al transicionar cilindros, pasar `session_id`.

### 1.4 Migración de datos existentes

Los 300 cilindros en `CARGA_EN_VEHICULO` / `EN_RUTA` sin sesión romperían el constraint CHECK. Estrategia:

```sql
-- Resetear a estado de almacén los que no tienen sesión
UPDATE lg_cylinders
SET current_state = 'EN_ALMACEN_VACIO'
WHERE current_state IN ('CARGA_EN_VEHICULO', 'EN_RUTA')
  AND (session_id IS NULL OR session_id NOT IN (SELECT id FROM lg_vehicle_sessions));
```

Esto es seguro porque esos cilindros nunca tuvieron una operación real que los pusiera en ese estado.

---

## Fase 2 — Event backbone (spec futura)

- Tabla `lg_cylinder_events` como fuente de verdad
- `current_state` se convierte en cache derivada del último evento
- Reconstrucción histórica completa

No se implementa en esta spec.

---

## Fase 3 — Estado 100% derivado (spec futura)

- `current_state` deja de ser columna persistida
- Vista materializada o computed property desde `lg_cylinder_events`

No se implementa en esta spec.

---

## Archivos afectados (Fase 1)

```
plugins/logistics/backend/models/cylinder.py              — +session_id FK
plugins/logistics/migrations/035_cylinder_session_fk.py   — NUEVO (FK + CHECK + data migration)
plugins/logistics/backend/services/state_machine.py        — +session_id en transition_cylinder
plugins/logistics/backend/services/load_serials.py         — pasar session_id al cargar
plugins/logistics/backend/services/routes.py               — pasar session_id al iniciar ruta
plugins/logistics/backend/services/sessions.py             — close_session limpia session_id
plugins/logistics/backend/services/cylinders.py            — update_cylinder rechaza current_state
plugins/logistics/backend/router.py                        — PATCH /cylinders/{id} filtra current_state
plugins/logistics/backend/schemas.py                       — CylinderUpdateRequest sin current_state
```

## No incluye

- No reescribe el state machine (solo le agrega `session_id`)
- No crea `lg_cylinder_events` (Fase 2)
- No elimina `current_state` como columna (Fase 3)
- No modifica el seed masivo (se arregla solo con la migración de datos + constraint)

## Criterios de aceptación

1. `INSERT` o `UPDATE` de cilindro con `current_state = 'CARGA_EN_VEHICULO'` y `session_id = NULL` → rechazado por constraint CHECK.
2. `INSERT` o `UPDATE` de cilindro con `current_state = 'EN_RUTA'` y `session_id = NULL` → rechazado por constraint CHECK.
3. `PATCH /cylinders/{id}` con `current_state` en el payload → 422 o campo ignorado.
4. `transition_cylinder` a `CARGA_EN_VEHICULO` con `session_id=S` persiste `session_id = S`.
5. `transition_cylinder` de `EN_RUTA` a `EN_CLIENTE_LLENO` mantiene `session_id = S` (no lo limpia).
6. `close_session(S)` limpia `session_id = NULL` en todos los cilindros asociados.
7. Cilindro con `session_id = NULL` no puede transicionar a `CARGA_EN_VEHICULO` ni `EN_RUTA` (el constraint CHECK lo fuerza a pasar `session_id`).
8. Migración resetea cilindros huérfanos a `EN_ALMACEN_VACIO`.

## Riesgos

- **CILINDROS LEGACY**: los 300 en estados de tránsito sin sesión serán reseteados a `EN_ALMACEN_VACIO`. Esto es correcto porque nunca estuvieron realmente en tránsito.
- **State machine**: agregar `session_id` como parámetro opcional en `transition_cylinder` no rompe llamadores existentes (default None).
- **Cierre de sesión**: `close_session` debe limpiar `session_id` en los cilindros. Si no se implementa, los cilindros retienen una FK a una sesión cerrada — no es incorrecto pero ensucia queries futuras.
- **Rendimiento**: FK + CHECK son operaciones O(1). Limpiar `session_id` en masa al cerrar sesión son N updates (N = cilindros en la sesión), aceptable.

## Referencias

- `plugins/logistics/backend/models/cylinder.py` — modelo actual
- `plugins/logistics/backend/services/catalog.py:50-54` — transiciones CARGA_EN_VEHICULO, EN_RUTA
- `plugins/logistics/backend/services/load_serials.py:454-502` — transiciones con seriales
- `plugins/logistics/backend/services/routes.py:360-403` — transiciones en ruta
- Seed masivo — origen del problema (datos sin sesión)
