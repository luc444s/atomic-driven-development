---
id: "0024.0.1"
title: "Event-Driven Stepper — transiciones automáticas sin confirmación manual"
domain: logistics
module: vehicle-sessions
status: vigente
extends:
  - docs/specs/core/0024-vehicle-session-stepper.md
supersedes:
  - docs/specs/core/0024-1-vehicle-session-ui-architecture.md
absorbed_into: null
---

# SPEC 0024.0.1 — Event-Driven Stepper

## Contexto

`SPEC 0024` implementó el stepper horizontal y eliminó el botón mutante. `SPEC 0024.1` describió la consola operativa con workspace por estado y mapas UI centralizados.

Ambas specs dejaron pendiente un problema de fricción: **el usuario aún confirma transiciones manualmente aunque el sistema ya tenga toda la información para decidir**.

Flujo actual:

```
Carga:  editar plan → guardar → [Confirmar carga] → [Siguiente: Listo para salir]
Ruta:   [Siguiente: En ruta] → [Siguiente: De regreso] → [Retornar remanente]
Concil: contar → [Guardar conteo] → [Siguiente: Cerrar jornada]
```

El stepper centraliza la acción, pero los panels aún exponen botones de transición redundantes y el usuario debe "confirmar" dos veces (panel + stepper).

## Principio central (no negociable)

**El estado cambia por eventos, no por botones.**

- La carga confirmada produce el evento → el sistema transiciona a `READY_TO_DEPART`
- La conciliación sin diferencias produce el evento → el sistema cierra la jornada
- El stepper refleja el estado real; el usuario no elige "avanzar", el sistema avanza cuando las condiciones se cumplen

Esto NO es un cambio visual. Es un cambio de:

```
UI basada en clicks → UI basada en eventos reales
```

## Regla UX mínima (vinculante)

Toda transición automática debe cumplir:

```
if (error) {
  NO cerrar modal
  mostrar error claro
  permanecer abierto hasta que usuario accione explícitamente
}
```

La filosofía del spec es "el sistema confirma al usuario", no "el sistema esconde fallos". Una transición automática que falla y cierra el panel produce el efecto opuesto al deseado: el usuario no sabe si avanzó o no.

**Implementación**:
- El panel (LoadPanel, ReconciliationPanel) solo se cierra si la respuesta es exitosa
- En error: `<Alert>` visible con mensaje del backend (business) o genérico (technical), el panel permanece abierto
- El botón de acción se re-habilita para reintento
- No hay "cierre por timeout" ni "cierre silencioso"

**Frase opcional para el alert de error**:
> "Estado no actualizado — revise la carga"

## Objetivo

Eliminar confirmaciones manuales innecesarias:

| Antes | Después |
|---|---|
| Usuario confirma carga + stepper avanza | Carga confirmada → auto-transición a `READY_TO_DEPART` |
| Usuario guarda conteo + stepper cierra | Conteo sin diferencias → auto-cierre |
| READY_TO_DEPART → OUTBOUND → RETURNING | Botón manual (fallback hasta GPS) |
| Stepper es "el que tiene el botón" | Stepper es "el que muestra el estado" |

## No objetivos

- No crear nuevos estados en `VehicleSession`
- No cambiar el modelo de datos
- No eliminar el stepper ni reemplazar su rol visual
- No implementar GPS (solo se prepara el slot)
- No cambiar los endpoints de conciliación o carga fundamentales
- No cambiar `returnRemaining` (sigue siendo acción manual del stepper)

## 1. 🔥 Eliminar confirmaciones redundantes

### 1.1 LoadPanel — antes vs después

**ANTES:**

```
SessionLoadTab.tsx:
  [Agregar producto] [Guardar plan] [Confirmar carga]   ← 2 botones de acción
                                                           + stepper "Siguiente"
```

**DESPUÉS:**

```
LoadPanel.tsx:
  [Agregar producto] [Guardar y confirmar]               ← 1 botón único
  (sin stepper action duplicada)
```

El botón "Guardar y confirmar" llama a un nuevo endpoint combinado que:
1. `upsert_load_plan` — guarda el plan
2. `confirm_load_plan` — confirma la carga, establece `loaded_weight_kg`
3. `mark_session_ready` — transiciona a `READY_TO_DEPART`

TODO en una sola transacción backend.

### 1.2 ReconciliationPanel — antes vs después

**ANTES:**

```
SessionReconciliationTab.tsx:
  [Guardar conteo] [Cerrar jornada]                       ← 2 botones
                                                           + stepper "Siguiente"
```

**DESPUÉS:**

```
ReconciliationPanel.tsx:
  [Guardar conteo]                                         ← 1 botón único

  Si POST /reconciliation/count devuelve status=MATCHED
  → frontend invoca POST /close automáticamente
  (sin botón de cierre, sin stepper action)
```

**CRÍTICO:** No es lógica de negocio en frontend. El backend ya determina si la conciliación permite cierre (`can_close`). El frontend solo reacciona al resultado exitoso invocando el endpoint de cierre. Es un orquestador de secuencia, no un decisor de reglas.

Alternativa backend-friendly: modificar `POST /reconciliation/count` para que, si el resultado es `MATCHED`, también ejecute `close_vehicle_session` en la misma transacción. Esta es la opción preferida (ver sección 6).

### 1.3 Stepper button — antes vs después

**ANTES:**

```typescript
const TRANSITION_ACTIONS = {
  DRAFT: startLoading,
  LOADING: ready,            // ← nunca se usa si carga auto-transiciona
  READY_TO_DEPART: depart,   // ← fallback manual
  OUTBOUND: returning,       // ← fallback manual
  RETURNING: returnRemaining,// ← sigue siendo manual
  AWAITING_RECONCILIATION: close, // ← nunca se usa si conciliación auto-cierra
};
```

**DESPUÉS:**

```typescript
const TRANSITION_ACTIONS = {
  DRAFT: startLoading,             // único paso que necesita confirmación inicial
  READY_TO_DEPART: fallbackDepart, // TODO: reemplazar por evento GPS
  OUTBOUND: fallbackReturn,        // TODO: reemplazar por evento GPS
  RETURNING: returnRemaining,      // manual: requiere confirmar remanente
};
```

Los estados `LOADING` y `AWAITING_RECONCILIATION` ya no aparecen en el mapa de acciones del stepper porque su transición la dispara el panel automáticamente.

## 2. ⚡ Stepper como centro operativo (refrase)

Cada step debe renderizar:

```
[Estado]
Frase corta (1 línea)
[Acción]
```

Ejemplo para step actual:

```
● Cargando
  Carga incompleta
  [Cargar]
```

La acción del stepper ya no es "Siguiente: X" sino la acción concreta para el estado actual, usando frases operativas cortas.

## 3. 🧠 Frases operativas (mapa único)

```typescript
const STATUS_PHRASE: Record<string, string> = {
  DRAFT: "Sin carga planificada",
  LOADING: "Carga incompleta",
  READY_TO_DEPART: "Vehículo listo",
  OUTBOUND: "Operación activa",
  RETURNING: "Retorno en curso",
  AWAITING_RECONCILIATION: "Revisar diferencias",
  CLOSED: "Jornada finalizada",
  CANCELLED: "Jornada cancelada",
};
```

## 4. ⚙️ Step actions

```typescript
const STEP_ACTION: Record<string, string> = {
  DRAFT: openLoadModal,
  LOADING: openLoadModal,
  READY_TO_DEPART: fallbackDepart,      // manual hasta GPS
  OUTBOUND: openRouteModal,             // placeholder
  RETURNING: fallbackReturn,            // manual hasta GPS
  AWAITING_RECONCILIATION: openReconciliationModal,
};
```

| Status | Frase | Acción stepper | Acción panel |
|---|---|---|---|
| `DRAFT` | Sin carga planificada | Iniciar carga | Abrir LoadPanel |
| `LOADING` | Carga incompleta | (ninguna, auto) | Guardar y confirmar |
| `READY_TO_DEPART` | Vehículo listo | Salir (fallback) | (ninguna) |
| `OUTBOUND` | Operación activa | Marcar retorno (fallback) | Abrir RoutePanel |
| `RETURNING` | Retorno en curso | Retornar remanente | (ninguna) |
| `AWAITING_RECONCILIATION` | Revisar diferencias | (ninguna, auto si MATCHED) | Guardar conteo |

NOTA: `openLoadModal`, `openRouteModal`, `openReconciliationModal` son acciones de navegación a workspace, no transiciones de estado.

## 5. ❌ Prohibiciones

- ❌ No usar confirm dialogs para transiciones de estado
- ❌ No duplicar lógica de transición (panel + stepper)
- ❌ No usar múltiples botones de acción primaria en un panel
- ❌ No meter lógica de negocio en frontend (reglas de transición)
- ❌ No mostrar más de 1 acción por step en el stepper
- ❌ No mantener `LOADING` ni `AWAITING_RECONCILIATION` en `TRANSITION_ACTIONS` del stepper

## 6. 🔧 Cambios backend

### 6.1 Nuevo endpoint combinado: `POST /{session_id}/confirm-and-ready`

Combina `confirm_load_plan` + `mark_session_ready` en una sola transacción atómica.

**Router** (`routers/load_plans.py`):

```python
@router.post("/{session_id}/confirm-and-ready", response_model=VehicleSessionDetailRead)
def post_confirm_and_ready(
    session_id: str,
    payload: ConfirmLoadRequest,
    request: Request,
    db: Session = DB_SESSION,
    tenant_context: TenantContext = TENANT_CONTEXT,
    _: User = REQUIRE_SESSION_MANAGE,
) -> VehicleSessionDetailRead:
    session = _get_session_or_404(db, tenant_id=tenant_context.current_tenant_id, session_id=session_id)
    try:
        # 1. confirmar carga (valida plan, items, capacidad, ejecuta transfer)
        session = confirm_load_plan(db, session=session, notes=payload.notes, action_context=build_action_context(request, tenant_context))
        # 2. marcar ready (valida loaded_weight_kg, cambia status, emite evento)
        session = mark_session_ready(db, session=session, action_context=build_action_context(request, tenant_context))
        db.commit()
        return build_session_snapshot(db, session=session)
    except Exception as exc:
        db.rollback()
        _raise_service_error(exc)
```

**DTO**: Reutiliza `ConfirmLoadRequest` existente.

**Validación**: `mark_session_ready` ya llama `ensure_session_can_be_ready` que verifica `loaded_weight_kg > 0`. Como `confirm_load_plan` lo acaba de setear, la guard pasa.

**Eventos emitidos** (2):
- `logistics.vehicle_session.load_confirmed` (desde `confirm_transfer_out` o nuevo)
- `logistics.vehicle_session.ready` (desde `mark_session_ready`)

### 6.2 Modificar `POST /{session_id}/reconciliation/count` para auto-close

**Opción preferida (backend atómico):**

Modificar `record_reconciliation_count` en `services/reconciliation.py`:

```python
def record_reconciliation_count(
    db, *, session, payload, action_context
) -> SessionReconciliationRead:
    # ... lógica existente: registrar conteo, calcular diferencias ...
    # ... (hasta line 161 del código actual) ...

    # Si el resultado es MATCHED (sin diferencias), cerrar automáticamente
    if reconciliation.status == "MATCHED":
        close_vehicle_session(db, session=session, notes=None, action_context=action_context)
        # close_vehicle_session setea session.status = "CLOSED" y reconciliation.status = "CLOSED"

    return get_reconciliation_view(db, session=session)
```

**Alternativa (frontend secuencial):**

Si el backend retorna `status: "MATCHED"` y `can_close: true`, el frontend llama `POST /close` secuencialmente. Esto es aceptable solo si se documenta como excepción (el frontend no decide la regla, reacciona al resultado).

**Decisión**: Usar opción backend. Una sola llamada, un solo commit, un solo snapshot.

### 6.3 Endpoints que no cambian

| Endpoint | Razón |
|---|---|
| `POST /start-loading` | Sigue siendo acción del stepper (DRAFT necesita confirmación humana) |
| `POST /depart` | Fallback manual hasta GPS |
| `POST /mark-returning` | Fallback manual hasta GPS |
| `POST /return-remaining` | Siempre manual (requiere decisión de destino) |
| `POST /cancel` | Siempre manual |
| `PUT /load-plan` | Sigue siendo llamado desde LoadPanel (antes de confirm) |

## 7. 🔧 Cambios frontend

### 7.1 `SessionLoadTab.tsx` → `LoadPanel.tsx`

**Eliminar:**
- Botón "Confirmar carga"
- Prop `onConfirmLoad`

**Modificar:**
- Botón "Guardar plan" → "Guardar y confirmar"
- `onSavePlan` → llama a `POST /confirm-and-ready` (no a `PUT /load-plan` por separado)

**Nuevo flujo:**
```typescript
async function handleSaveAndConfirm() {
  // Guardar plan (PUT /load-plan)
  await upsertLoadPlan(sessionId, { items: ... });
  // Confirmar + transicionar (POST /confirm-and-ready)
  await confirmAndReady(sessionId);
  // invalidar queries
}
```

O mejor: el botón "Guardar plan" persiste como "guardar borrador", y aparece un botón "Confirmar carga y salir" solo cuando `status === "LOADING"`. Pero para mantener UNA acción por panel, lo óptimo es unificar en "Guardar y confirmar" que hace todo.

**Decisión**: Renombrar a "Guardar y confirmar". Un solo botón. Si el usuario quiere guardar sin confirmar (borrador), el auto-save existe vía `useEffect` + debounce, o puede editar en DRAFT antes de iniciar la jornada.

### 7.2 `SessionReconciliationTab.tsx` → `ReconciliationPanel.tsx`

**Eliminar:**
- Botón "Cerrar jornada"
- Prop `onCloseSession`

**Modificar:**
- `onSaveCount` → llama a `POST /reconciliation/count`
- En `onSuccess` de countMutation, si el resultado `can_close === true`, la respuesta del backend ya cerró la jornada (opción backend) o se llama `POST /close` secuencialmente

Para opción backend (preferida): el `countMutation.onSuccess` simplemente invalida queries. El estado ya es `CLOSED`.

### 7.3 `SessionStepper.tsx`

**Modificar `TRANSITION_ACTIONS` en `VehicleSessionDetailPage.tsx`:**

```typescript
const TRANSITION_ACTIONS: Partial<Record<string, () => Promise<unknown>>> = {
  DRAFT: startLoadingMutation.mutateAsync,
  READY_TO_DEPART: departMutation.mutateAsync,     // fallback manual
  OUTBOUND: returningMutation.mutateAsync,          // fallback manual
  RETURNING: returnMutation.mutateAsync,
};
```

`LOADING` y `AWAITING_RECONCILIATION` ya no tienen acción en el stepper.

**Modificar labels:**

Reemplazar `NEXT_LABELS` por:

```typescript
const NEXT_LABELS: Record<string, string> = {
  DRAFT: "Iniciar carga",
  READY_TO_DEPART: "Iniciar ruta",
  OUTBOUND: "Marcar retorno",
  RETURNING: "Finalizar ruta",
  CANCELLED: "Jornada cancelada",
};
```

**Agregar frases operativas:**

```typescript
const STATUS_PHRASE: Record<string, string> = {
  DRAFT: "Sin carga planificada",
  LOADING: "Carga incompleta",
  READY_TO_DEPART: "Vehículo listo",
  OUTBOUND: "Operación activa",
  RETURNING: "Retorno en curso",
  AWAITING_RECONCILIATION: "Revisar diferencias",
};
```

**Renderizado del stepper:**

```
[●] Borrador     [●] Cargando     [○] Listo para salir     ...
    Sin carga         Carga
    planificada       incompleta
                      [Cargar panel abierto]
```

El stepper muestra:
1. Número + label (existente)
2. Frase operativa debajo (nuevo)
3. Indicador de si la acción es automática o manual

Para estados auto-transicionados (`LOADING`, `AWAITING_RECONCILIATION`):
- No mostrar botón en el stepper
- Mostrar texto: "Acción automática en {panel}"

### 7.4 `VehicleSessionDetailPage.tsx`

**Modificar:**
- `TRANSITION_ACTIONS` (eliminar LOADING, AWAITING_RECONCILIATION)
- Pasar `confirmAndReadyMutation` al LoadPanel
- Eliminar `confirmLoadMutation` (reemplazado por `confirmAndReadyMutation`)
- Eliminar `closeMutation` de las props del stepper (se dispara desde reconciliation o ya no existe como botón)
- `closeMutation` solo se usa si el backend no hace auto-close (fallback)

### 7.5 Nuevo archivo: `session-ui-map.ts`

Centralizar mapas:

```typescript
// session-ui-map.ts
export const STEPS = [
  { status: "DRAFT", label: "Borrador", tab: "load", phrase: "Sin carga planificada" },
  { status: "LOADING", label: "Cargando", tab: "load", phrase: "Carga incompleta" },
  { status: "READY_TO_DEPART", label: "Listo para salir", tab: "load", phrase: "Vehículo listo" },
  { status: "OUTBOUND", label: "En ruta", tab: "route", phrase: "Operación activa" },
  { status: "RETURNING", label: "De regreso", tab: "route", phrase: "Retorno en curso" },
  { status: "AWAITING_RECONCILIATION", label: "Pend. conciliación", tab: "reconciliation", phrase: "Revisar diferencias" },
] as const;

export const STEP_ACTION: Record<string, () => void> = {
  DRAFT: openLoadModal,
  LOADING: openLoadModal,
  READY_TO_DEPART: fallbackDepart,
  OUTBOUND: openRouteModal,
  RETURNING: fallbackReturn,
  AWAITING_RECONCILIATION: openReconciliationModal,
};

export const STATUS_PHRASE: Record<string, string> = {
  DRAFT: "Sin carga planificada",
  LOADING: "Carga incompleta",
  READY_TO_DEPART: "Vehículo listo",
  OUTBOUND: "Operación activa",
  RETURNING: "Retorno en curso",
  AWAITING_RECONCILIATION: "Revisar diferencias",
  CLOSED: "Jornada finalizada",
  CANCELLED: "Jornada cancelada",
};
```

## 8. 📋 Archivos afectados

### Modificados — Frontend

| Archivo | Cambio |
|---|---|
| `plugins/logistics/frontend/components/vehicle-sessions/SessionLoadTab.tsx` | Eliminar botón "Confirmar carga". Renombrar "Guardar plan" → "Guardar y confirmar". Cambiar callback a `confirmAndReady`. |
| `plugins/logistics/frontend/components/vehicle-sessions/SessionReconciliationTab.tsx` | Eliminar botón "Cerrar jornada". `onSaveCount` ahora auto-cierra. |
| `plugins/logistics/frontend/components/vehicle-sessions/SessionStepper.tsx` | Agregar frases operativas por status. Ocultar botón para LOADING y AWAITING_RECONCILIATION. Nuevos labels. |
| `plugins/logistics/frontend/pages/VehicleSessionDetailPage.tsx` | Eliminar `confirmLoadMutation` → agregar `confirmAndReadyMutation`. Eliminar LOADING/AWAITING_RECONCILIATION de TRANSITION_ACTIONS. Eliminar `closeMutation` del stepper. Eliminar `onConfirmLoad` y `onCloseSession` de los panels. |

### Nuevos — Frontend

| Archivo | Contenido |
|---|---|
| `plugins/logistics/frontend/components/vehicle-sessions/session-ui-map.ts` | Centralizar STEPS, STATUS_PHRASE, STEP_ACTION, NEXT_LABELS |

### Modificados — Backend

| Archivo | Cambio |
|---|---|
| `plugins/logistics/backend/routers/load_plans.py` | Nuevo endpoint `POST /{session_id}/confirm-and-ready` que combina confirm + ready en una transacción. |
| `plugins/logistics/backend/services/reconciliation.py` | Modificar `record_reconciliation_count`: si resultado es MATCHED, ejecutar `close_vehicle_session` automáticamente. |

### Sin cambios

| Archivo | Razón |
|---|---|
| `plugins/logistics/backend/services/rules.py` | Reglas de transición no cambian |
| `plugins/logistics/backend/services/sessions.py` | Funciones individuales se reutilizan |
| `plugins/logistics/backend/services/load_plans.py` | `confirm_load_plan` se reutiliza |
| `plugins/logistics/backend/routers/sessions.py` | Endpoints individuales se conservan |
| `plugins/logistics/backend/dto/*` | DTOs existentes se reutilizan |
| `plugins/logistics/backend/models/*` | Sin cambios de modelo |
| `plugins/logistics/frontend/api/*.ts` | Solo agregar `confirmAndReady` api function |

### Eliminar del frontend

| Concepto | Dónde |
|---|---|
| Botón "Confirmar carga" | `SessionLoadTab.tsx` |
| Botón "Cerrar jornada" | `SessionReconciliationTab.tsx` |
| Prop `onConfirmLoad` | `SessionLoadTab.tsx` + `VehicleSessionDetailPage.tsx` |
| Prop `onCloseSession` | `SessionReconciliationTab.tsx` + `VehicleSessionDetailPage.tsx` |
| Estado `LOADING` en `TRANSITION_ACTIONS` | `VehicleSessionDetailPage.tsx` |
| Estado `AWAITING_RECONCILIATION` en `TRANSITION_ACTIONS` | `VehicleSessionDetailPage.tsx` |
| `confirmLoadMutation` | `VehicleSessionDetailPage.tsx` |
| Labels "Siguiente: Cargando", "Siguiente: Listo para salir", "Siguiente: Pend. conciliación", "Siguiente: Cerrar jornada" | `SessionStepper.tsx` |

## 9. 🧪 Plan de refactor incremental

### Paso 1: Backend — nuevo endpoint confirm-and-ready

**Qué**: Agregar `POST /{session_id}/confirm-and-ready` en `routers/load_plans.py`.

**Por qué solo esto**: No rompe nada existente. Los endpoints viejos siguen funcionando.

**Validación**: `ensure_session_can_be_ready` se ejecuta después de `confirm_load_plan`, garantizando que `loaded_weight_kg > 0`.

**Tests**: Probar que una llamada exitosa:
- Deja session en `READY_TO_DEPART`
- Emite evento `logistics.vehicle_session.ready`
- Incrementa `loaded_weight_kg`

**Riesgo**: Bajo. Es composición de dos funciones existentes.

### Paso 2: Backend — auto-close en record_reconciliation_count

**Qué**: Modificar `record_reconciliation_count` para llamar `close_vehicle_session` si `reconciliation.status == "MATCHED"`.

**Por qué solo esto**: No rompe nada. `close_vehicle_session` tiene sus propias guards que se ejecutarán.

**Validación**: `ensure_session_can_close` verifica `AWAITING_RECONCILIATION`, `MATCHED` y sin discrepancias abiertas. Si `record_reconciliation_count` acaba de setear `MATCHED` sin discrepancias, debe pasar.

**Tests**: Probar que:
- Conteo exacto → session pasa a `CLOSED`
- Conteo con diferencias → session queda en `AWAITING_RECONCILIATION` (no cierra)

**Riesgo**: Medio. Cambia el comportamiento del endpoint de conteo. Verificar que `get_reconciliation_view` devuelva el snapshot correcto post-cierre.

### Paso 3: Frontend — API function confirmAndReady

**Qué**: Agregar `confirmAndReady()` en `api/load-plans.ts`.

```typescript
export function confirmAndReady(sessionId: string, payload: ConfirmLoadPayload = {}) {
  return apiRequest<{ session_id: string; status: string }>(
    `${API_PREFIX}/vehicle-sessions/${sessionId}/confirm-and-ready`,
    { method: "POST", body: JSON.stringify(payload) }
  );
}
```

**Validación**: La función consume el endpoint del Paso 1.

### Paso 4: Frontend — SessionLoadTab.tsx simplificado

**Qué**: 
- Renombrar botón "Guardar plan" → "Guardar y confirmar"
- Cambiar handler: guarda plan (PUT) + llama confirmAndReady (POST)
- Eliminar botón "Confirmar carga"
- Eliminar prop `onConfirmLoad`

**Validación**: El botón único hace toda la secuencia.

### Paso 5: Frontend — SessionReconciliationTab.tsx simplificado

**Qué**:
- Eliminar botón "Cerrar jornada"
- `onSaveCount` llama count, en success el backend ya cerró
- Eliminar prop `onCloseSession`

**Validación**: Guardar conteo cierra la jornada si todo coincide. Si hay diferencias, queda en AWAITING_RECONCILIATION.

### Paso 6: Frontend — SessionStepper.tsx + VehicleSessionDetailPage.tsx

**Qué**:
- Eliminar `confirmLoadMutation` y `closeMutation` de la page
- Eliminar `LOADING` y `AWAITING_RECONCILIATION` de `TRANSITION_ACTIONS`
- Agregar frases operativas al stepper (STATUS_PHRASE)
- Ocultar botón del stepper para estados auto-transicionados
- Actualizar labels de botones restantes

**Validación**: Stepper no muestra botón para LOADING ni AWAITING_RECONCILIATION.

### Paso 7: Frontend — crear session-ui-map.ts

**Qué**: Extraer STEPS, STATUS_PHRASE, STEP_ACTION a archivo central.

**Validación**: Stepper, workspace y otros componentes importan del mismo lugar.

### Paso 8: Frontend — limpiar props y código muerto

**Qué**: 
- Eliminar `confirmLoadMutation` del JSX
- Eliminar `closeMutation` donde ya no se use
- Verificar que `VehicleSessionDetailPage` no tenga referencias a `onConfirmLoad` ni `onCloseSession`

## 10. 🧪 Validaciones por etapa

### Paso 1 (backend confirm-and-ready)
- [ ] Endpoint responde 200 con `VehicleSessionDetailRead`
- [ ] Session pasa de LOADING a READY_TO_DEPART
- [ ] `loaded_weight_kg` > 0
- [ ] `next_transition_allowed` es true
- [ ] Endpoint viejo `POST /confirm-load` sigue funcionando
- [ ] Endpoint viejo `POST /ready` sigue funcionando

### Paso 2 (backend auto-close)
- [ ] Conteo exacto (MATCHED) → session pasa a CLOSED
- [ ] Conteo con diferencias (HAS_DIFF) → session queda en AWAITING_RECONCILIATION
- [ ] Snapshot post-cierre tiene `status: CLOSED` y `closed_at` poblado
- [ ] Endpoint viejo `POST /close` sigue funcionando (para diferencias manuales)

### Paso 3-4 (frontend load)
- [ ] Botón "Guardar y confirmar" llama PUT /load-plan + POST /confirm-and-ready
- [ ] En caso de error en upsert, no se llama confirm-and-ready
- [ ] En éxito, stepper refleja READY_TO_DEPART
- [ ] No hay botón "Confirmar carga" visible

### Paso 5 (frontend reconciliation)
- [ ] Botón "Guardar conteo" llama POST /reconciliation/count
- [ ] En éxito con MATCHED, stepper refleja CLOSED
- [ ] En éxito con HAS_DIFF, stepper queda en AWAITING_RECONCILIATION
- [ ] No hay botón "Cerrar jornada" visible

### Paso 6-8 (stepper limpieza)
- [ ] TRANSITION_ACTIONS solo tiene DRAFT, READY_TO_DEPART, OUTBOUND, RETURNING
- [ ] Stepper no muestra botón para LOADING y AWAITING_RECONCILIATION
- [ ] Frases operativas se muestran en cada step
- [ ] session-ui-map.ts existe y es usado por stepper y workspace

## 11. 🚨 Riesgos reales

### Riesgo 1: Transición disparada dos veces

Si el frontend llama `confirmAndReady` y el usuario también hace clic en el stepper, la transición puede ejecutarse dos veces.

**Mitigación**: 
- `mark_session_ready` llama `ensure_session_can_be_ready` que verifica `session.status == "LOADING"`. Si ya está en `READY_TO_DEPART`, lanza ValueError.
- El botón del stepper para LOADING se elimina (no hay doble vía).

### Riesgo 2: UI desincronizada

El stepper puede no reflejar el nuevo estado inmediatamente después de la transición automática.

**Mitigación**: 
- `onSuccess` del mutation invalida todas las queries (`invalidateAll`).
- La respuesta del endpoint combinado devuelve el snapshot completo.

### Riesgo 3: Modal cerrándose sin transición

Si el panel cierra pero la transición falla, el usuario no ve el error.

**Mitigación**:
- El panel NO se cierra automáticamente. Espera la respuesta exitosa.
- En error, muestra alerta y permanece abierto.
- Solo en éxito → invalidate queries → stepper se re-renderiza → el panel puede cerrarse.

### Riesgo 4: count + close en misma transacción falla parcialmente

Si `record_reconciliation_count` tiene éxito pero `close_vehicle_session` falla, la base de datos queda inconsistente.

**Mitigación**:
- Ambas operaciones ocurren en la misma transacción de SQLAlchemy.
- Si alguna falla, `db.rollback()` deshace todo.
- No hay estado intermedio visible.

### Riesgo 5: close_vehicle_session falla por discrepancias abiertas

Si `record_reconciliation_count` setea MATCHED pero hay discrepancias recién creadas por otro proceso, `close_vehicle_session` puede rechazar el cierre.

**Mitigación**:
- `has_open_discrepancies` se evalúa dentro de `close_vehicle_session`.
- Si falla, la transacción entera se revierte (incluyendo el conteo).
- El usuario ve el error y puede resolver.

### Riesgo 6: Regresión en embedded mode

El flujo embebido (dialog) podría romperse si el auto-close intenta navegar.

**Mitigación**:
- El cierre automático sigue usando el mismo `closeMutation.onSuccess` que ya maneja el caso embebido vs standalone.
- No se agrega lógica de navegación nueva.

## 12. 🔍 Señales de fallo (monitorear en QA)

- ❌ Sigue habiendo botón "Confirmar carga" o "Cerrar jornada" en la UI
- ❌ El usuario tiene que hacer clic en el stepper para avanzar desde LOADING
- ❌ El estado no cambia automáticamente después de guardar conteo sin diferencias
- ❌ El stepper muestra botón "Siguiente" para LOADING o AWAITING_RECONCILIATION
- ❌ `TRANSITION_ACTIONS` contiene LOADING o AWAITING_RECONCILIATION
- ❌ El panel se cierra antes de que la transición se complete
- ❌ Aparece un ConfirmDialog para confirmar la transición

## 13. ✅ Criterios de aceptación

- [ ] No existe botón "Confirmar carga" en LoadPanel
- [ ] No existe botón "Cerrar jornada" en ReconciliationPanel
- [ ] LoadPanel tiene un solo botón de acción: "Guardar y confirmar"
- [ ] ReconciliationPanel tiene un solo botón de acción: "Guardar conteo"
- [ ] Stepper no tiene botón para LOADING ni AWAITING_RECONCILIATION
- [ ] TRANSITION_ACTIONS solo mapea DRAFT, READY_TO_DEPART, OUTBOUND, RETURNING
- [ ] Confirmar carga + ready ocurre en una sola transacción backend
- [ ] Conteo MATCHED cierra la jornada automáticamente
- [ ] Conteo HAS_DIFF deja la jornada en AWAITING_RECONCILIATION
- [ ] Stepper muestra frase operativa para cada status
- [ ] Botones restantes (DRAFT, READY_TO_DEPART, OUTBOUND, RETURNING) tienen labels descriptivos
- [ ] session-ui-map.ts centraliza todos los mapas
- [ ] No hay confirm dialogs en el flujo de transición
- [ ] Flujo completo funciona: DRAFT → LOADING → READY_TO_DEPART → OUTBOUND → RETURNING → AWAITING_RECONCILIATION → CLOSED
- [ ] Flujo con diferencias: ... → AWAITING_RECONCILIATION (HAS_DIFF) → usuario ajusta → CLOSED
- [ ] Modo embebido funciona sin cambios de navegación
- [ ] Tests backend: confirm-and-ready endpoint
- [ ] Tests backend: auto-close en record_reconciliation_count

## 14. 📊 Flujo completo — antes vs después

### DRAFT

| | Antes | Después |
|---|---|---|
| Stepper | "Siguiente: Cargando" | "Iniciar carga" |
| Panel | Load: [Guardar plan] | Load: [Guardar plan] (solo borrador) |
| Transición | Click stepper | Click stepper |

### LOADING

| | Antes | Después |
|---|---|---|
| Stepper | "Siguiente: Listo para salir" | (sin botón — texto: "Carga incompleta") |
| Panel | [Guardar plan] [Confirmar carga] | [Guardar y confirmar] |
| Transición | Click confirmar + click stepper | Click "Guardar y confirmar" → automático a READY_TO_DEPART |

### READY_TO_DEPART

| | Antes | Después |
|---|---|---|
| Stepper | "Siguiente: En ruta" | "Iniciar ruta" (fallback GPS) |
| Panel | Load: solo vista | Load: solo vista |
| Transición | Click stepper | Click stepper (manual hasta GPS) |

### OUTBOUND

| | Antes | Después |
|---|---|---|
| Stepper | "Siguiente: De regreso" | "Marcar retorno" (fallback GPS) |
| Panel | Route: placeholder | Route: placeholder |
| Transición | Click stepper | Click stepper (manual hasta GPS) |

### RETURNING

| | Antes | Después |
|---|---|---|
| Stepper | "Siguiente: Pend. conciliación" | "Finalizar ruta" |
| Panel | Route: placeholder | Route: placeholder |
| Transición | Click stepper (returnRemaining) | Click stepper (returnRemaining) |

### AWAITING_RECONCILIATION

| | Antes | Después |
|---|---|---|
| Stepper | "Siguiente: Cerrar jornada" | (sin botón — texto: "Revisar diferencias") |
| Panel | [Guardar conteo] [Cerrar jornada] | [Guardar conteo] |
| Transición | Click guardar + click stepper | Click "Guardar conteo" → si MATCHED, automático a CLOSED |

## 15. 🔗 Dependencias

- SPEC 0024 (stepper base) — implementado
- SPEC 0024.1 (UI architecture) — superceded parcialmente por este spec (los principios de workspace se mantienen, pero la centralización de mapas y auto-transición se definen aquí)

Este spec no depende de:
- GPS tracking (solo prepara el slot)
- Route operations V2 (solo placeholder)
- Mobile mode

## 16. 📝 Notas para agentes

1. No eliminar endpoints viejos (`POST /confirm-load`, `POST /ready`, `POST /close`). Se conservan para backward compat y casos borde (ej. cierre manual con diferencias).
2. No modificar `TRANSITION_ACTIONS` hasta que el paso 2 del backend esté listo. El orden correcto es: backend → frontend API → panels → stepper.
3. `session-ui-map.ts` debe crearse ANTES de modificar los componentes que lo usan. Seguir el principio "crear archivo, importar, eliminar duplicado".
4. Verificar que el embed mode (VehicleSessionsPage dialog) siga funcionando. El auto-close debe cerrar el dialog si `embedded === true`.
