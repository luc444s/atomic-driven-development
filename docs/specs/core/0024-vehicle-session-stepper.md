---
id: "0024"
title: "Vehicle Session Stepper — UX del ciclo operativo"
domain: logistics
module: vehicle-sessions
status: vigente
supersedes:
  - docs/specs/drafts/session-stepper-v2.md
  - docs/specs/drafts/session-stepper-v3.md
  - docs/specs/drafts/stepper-and-vehicle-release.md
---

# SPEC 0024 — Vehicle Session Stepper

## Contexto

La página de detalle de jornada (`VehicleSessionDetailPage`) usa actualmente un botón mutante en el header que cambia de texto y acción según `session.status`. Esto genera confusión operativa: el usuario no sabe en qué paso del flujo está, cuántos faltan, ni qué viene después.

Además, las validaciones de transición están dispersas: el frontend las calcula con lógica propia mientras el backend también valida. Esto duplica reglas y puede desincronizarse.

## Solución

Reemplazar el botón mutante por un **stepper horizontal de 6 pasos** con un botón determinista "Siguiente: {nombre del paso}". Las reglas de transición las decide exclusivamente el backend y se exponen en el snapshot.

---

## 1. Stepper visual

```
┌──────────────────────────────────────────────────────────────────┐
│  [1]────[2]────[3]────[4]────[5]────[6]                        │
│   ● ─── ● ─── ● ─── ○ ─── ○ ─── ○                              │
│  Borrador Cargando  Listo   En ruta De regreso  Pend. conc.     │
│                     salir                                        │
│                                                                  │
│                    [ Siguiente: Cargando ]                       │
└──────────────────────────────────────────────────────────────────┘
```

- Flex horizontal con `overflow-x-auto` para scroll en mobile (no wrap, no reducir font)
- `bg-card rounded-lg border p-4`
- Círculos: `w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold`
- Completado: `bg-green-500 text-white` + conector `bg-green-500`
- Actual: `bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2`
- Futuro: `bg-muted text-muted-foreground`
- Conectores: `h-0.5 flex-1 min-w-4`

---

## 2. Mapeo de pasos

| Status API | Paso | Label |
|---|---|---|
| `DRAFT` | 0 | Borrador |
| `LOADING` | 1 | Cargando |
| `READY_TO_DEPART` | 2 | Listo para salir |
| `OUTBOUND` | 3 | En ruta |
| `RETURNING` | 4 | De regreso |
| `AWAITING_RECONCILIATION` | 5 | Pend. conciliación |
| `CLOSED` | 6 | Cerrada |
| `CANCELLED` | — | Congelado en paso actual |

---

## 3. Botón "Siguiente"

Aparece debajo del stepper, centrado.

| Status | Texto del botón |
|---|---|
| `DRAFT` | `Siguiente: Cargando` |
| `LOADING` | `Siguiente: Listo para salir` |
| `READY_TO_DEPART` | `Siguiente: En ruta` |
| `OUTBOUND` | `Siguiente: De regreso` |
| `RETURNING` | `Siguiente: Pend. conciliación` |
| `AWAITING_RECONCILIATION` | `Siguiente: Cerrar jornada` |
| `CLOSED` | No renderizar. Mostrar texto `"Jornada finalizada el {closed_at}"` |
| `CANCELLED` | Botón `disabled`, texto `"Jornada cancelada"` |

---

## 4. Mapa de acciones determinista (sin switch)

**En el frontend**, reemplazar el bloque `if/else` por un lookup:

```typescript
const TRANSITION_ACTIONS: Record<string, () => Promise<unknown>> = {
  DRAFT: startLoadingMutation.mutateAsync,
  LOADING: readyMutation.mutateAsync,
  READY_TO_DEPART: departMutation.mutateAsync,
  OUTBOUND: returningMutation.mutateAsync,
  RETURNING: returnMutation.mutateAsync,
  AWAITING_RECONCILIATION: closeMutation.mutateAsync,
};

// Llamada:
onNext={() => runAction(TRANSITION_ACTIONS[session.status])}
```

No hay `if`, `switch`, ni `case`. Solo un lookup de una fuente única.

---

## 5. Bloqueos determinados por el backend (CRÍTICO)

El frontend **no calcula reglas de negocio**. El backend expone dos campos en el snapshot de la sesión:

| Campo | Tipo | Descripción |
|---|---|---|
| `next_transition_allowed` | `boolean` | `true` si se cumplen las invariantes para avanzar |
| `next_transition_blocker` | `string \| null` | `null` si permitido; si no, mensaje exacto de la regla incumplida |

### Backend: `get_next_transition_blocker()`

Nueva función en `plugins/logistics/backend/services/rules.py`:

```python
def get_next_transition_blocker(
    session: LogisticsVehicleSession,
    *,
    has_open_discrepancies: bool = False,
) -> str | None:
    try:
        if session.status == "DRAFT":
            pass
        elif session.status == "LOADING":
            ensure_session_can_be_ready(session)
        elif session.status == "READY_TO_DEPART":
            ensure_session_can_depart(session)
        elif session.status == "OUTBOUND":
            pass
        elif session.status == "RETURNING":
            pass
        elif session.status == "AWAITING_RECONCILIATION":
            ensure_session_can_close(session, has_open_discrepancies=has_open_discrepancies)
        return None
    except ValueError as e:
        return str(e)
```

Esta función **reutiliza las `ensure_*` existentes**. No duplica lógica.

### Backend: snapshot

En `plugins/logistics/backend/services/snapshots.py`, agregar al snapshot:

```python
{
    # ...campos existentes...
    "next_transition_allowed": get_next_transition_blocker(session, ...) is None,
    "next_transition_blocker": get_next_transition_blocker(session, ...),
}
```

Optimización: llamar `get_next_transition_blocker` una sola vez y reusar ambos valores.

### Frontend: type

En `plugins/logistics/frontend/api/sessions.ts`, agregar al type `VehicleSession`:

```typescript
next_transition_allowed: boolean;
next_transition_blocker: string | null;
closed_at: string | null;
```

El stepper recibe:

```typescript
disabled={!session.next_transition_allowed}
title={session.next_transition_blocker ?? undefined}
```

Cero lógica de negocio en el frontend.

---

## 6. Distinción de errores

Cuando una acción falla:

| Código HTTP | Tipo | UX |
|---|---|---|
| `4xx` (400, 422) | `business` | Mostrar el mensaje exacto del backend |
| `5xx` (500, 502, 503) | `technical` | Mostrar "Error del servidor. Intente nuevamente." |

El stepper recibe:

```typescript
error: { type: "technical" | "business"; message: string } | null;
```

---

## 7. CANCELLED: stepper congelado

Mostrar el stepper **congelado** en el paso donde ocurrió la cancelación. No ocultarlo.

Agregar `Badge variant="destructive"` con texto "Cancelada" sobre el stepper.

---

## 8. CLOSED: timestamp de cierre

En lugar de solo "Jornada finalizada", mostrar:

```
Jornada finalizada el 15/7/2026, 14:30
```

Usar `session.closed_at` formateado con `toLocaleString()`.

---

## 9. Click en paso = navegación a tab (no muta estado)

| Paso clickeado | Tab |
|---|---|
| Borrador / Cargando / Listo para salir | `"load"` |
| En ruta / De regreso | `"route"` |
| Pend. conciliación / Cerrada | `"reconciliation"` |

Pasos futuros atenuados y no clickeables. Solo los pasos ya alcanzados pueden abrir su contexto. Nunca disparan transiciones de estado.

---

## 10. Feedback de acción

1. Botón entra en `isPending` inmediatamente al click (disabled + spinner)
2. Anti-doble-click: el botón se deshabilita al primer click
3. En éxito: `invalidateAll()` refresca queries, stepper se re-renderiza
4. En error: `<Alert>` con distinción business vs technical

---

## 11. Props del componente SessionStepper

```typescript
type SessionStepperProps = {
  status: string;
  nextTransitionAllowed: boolean;
  nextTransitionBlocker: string | null;
  closedAt: string | null;
  isPending: boolean;
  error: { type: "technical" | "business"; message: string } | null;
  onNext: () => void;
  onNavigateTab: (tab: string) => void;
};
```

---

## 12. Archivos afectados

### Nuevos

| Archivo | Contenido |
|---|---|
| `plugins/logistics/frontend/components/vehicle-sessions/SessionStepper.tsx` | Componente stepper |

### Modificados — Frontend

| Archivo | Cambio |
|---|---|
| `plugins/logistics/frontend/pages/VehicleSessionDetailPage.tsx` | Reemplazar `actionButtons`/`primaryLabel` por `<SessionStepper>` |
| `plugins/logistics/frontend/api/sessions.ts` | Agregar `next_transition_allowed`, `next_transition_blocker`, `closed_at` a `VehicleSession` |

### Modificados — Backend

| Archivo | Cambio |
|---|---|
| `plugins/logistics/backend/services/rules.py` | Agregar `get_next_transition_blocker()` |
| `plugins/logistics/backend/services/snapshots.py` | Incluir `next_transition_allowed` y `next_transition_blocker` en snapshot |

### Eliminar del frontend

De `VehicleSessionDetailPage.tsx`:

- Variable `primaryLabel`
- JSX `actionButtons`
- Lógica de `if/else` por status (reemplazada por `TRANSITION_ACTIONS` map)

---

## 13. Criterios de aceptación

- [ ] El stepper renderiza 6 pasos con estado visual correcto (completado/actual/futuro)
- [ ] El botón "Siguiente" muestra el nombre del paso destino
- [ ] Si `next_transition_allowed === false`, el botón está deshabilitado con tooltip del blocker
- [ ] Las transiciones usan `TRANSITION_ACTIONS` (mapa determinista), no `if/switch`
- [ ] El backend expone `next_transition_allowed` y `next_transition_blocker`
- [ ] El frontend no contiene ninguna regla de negocio sobre transiciones
- [ ] CLOSED: stepper todo verde, sin botón, muestra `closed_at`
- [ ] CANCELLED: stepper congelado + badge destructive
- [ ] Click en paso navega a la tab correcta
- [ ] Error business (4xx) muestra mensaje exacto del backend
- [ ] Error técnico (5xx) muestra mensaje genérico
- [ ] Anti-doble-click funcional
- [ ] Mobile: scroll horizontal, no wrap
- [ ] Funciona en modo embebido (dialog)
- [ ] Tests: `get_next_transition_blocker` cubre todos los status
- [ ] Tests: snapshot incluye los dos campos nuevos
