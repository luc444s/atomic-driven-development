---
id: "0036"
title: "Evento de Ruta Unificado y Contexto Operativo Explícito"
domain: logistics
module: jornadas
status: en-progreso
extends:
  - docs/specs/core/0033-route-operation-efectos-separados.md
  - docs/specs/core/0024-1-3-3-reconciliacion-controlada-sobre-incidencias-de-ruta.md
  - docs/specs/core/0024-1-3-2-exchange-incidencias-y-progreso-real-de-stop.md
---

# SPEC 0036 - Evento de Ruta Unificado y Contexto Operativo Explícito

## Estado

En progreso — v2

Cambios en v2 respecto a v1:
- Se define explícitamente `RoutesPage` como panel de control de rutas (deja de ser "secundario")
- Se define el modal de ruta (`SessionRouteTab`) como hub de asignación/creación rápida de rutas
- Se agrega `RouteControlMapPanel` con toolbar de asignación de ruta

## Contexto

`SPEC 0033` corrigió la semántica de fondo:

- `RouteOperation` describe la realidad de calle;
- `Movement` ya no es obligatorio para todo hecho operativo;
- `PICKUP` puro puede ser físico/documental sin efecto financiero.

`SPEC 0024.1.3.2` y `0024.1.3.3` corrigieron otra base importante:

- la incidencia no reemplaza a la operación;
- una corrección no edita la operación confirmada;
- la reconciliación real se modela como una nueva `RouteOperation`.

Pero el cierre actual deja dos fricciones fuertes:

1. la UX separa demasiado `Operación de ruta` e `Incidencia`, obligando al usuario a saltar entre dos flujos para documentar un solo hecho real;
2. `RouteOperation` todavía queda corta cuando no existe `route_stop_id`, porque no exige contexto explícito de cliente o almacén para justificar desde dónde salió o hacia dónde entró físicamente el cilindro.

El resultado práctico es incómodo y semánticamente débil:

```text
el operador registra el hecho real en un lugar
y la explicación/incidencia en otro
sin que el contexto mínimo quede necesariamente explicitado en la operación misma
```

## Frase guía

**La calle se captura una sola vez. La incidencia acompaña al hecho; no compite con él.**

## Objetivo

Definir un slice de UX y contrato operativo donde:

1. `RouteOperation` siga siendo el owner del hecho físico;
2. `RouteIncident` pase a ser un contexto complementario y opcional dentro del mismo flujo principal de captura;
3. las emergencias sin parada obliguen contexto explícito de `customer` o `warehouse` para que ningún cilindro quede "en el aire";
4. una sola confirmación pueda crear de forma atómica:
   - solo `RouteOperation`, o
   - `RouteOperation + RouteIncident`, o
   - `RouteOperation` correctiva + cierre de incidencia.
5. las incidencias puramente documentales y sin movimiento físico sigan existiendo, pero como flujo secundario y no como entry point principal.

## No objetivos

- no reemplazar `RouteOperation` por un aggregate nuevo;
- no convertir `RouteIncident` en owner de stock ni de composición;
- no permitir editar operaciones confirmadas;
- no rediseñar todo el shell de jornadas fuera del composer operacional;
- no cerrar todavía handheld avanzada offline;
- no fusionar tablas `lg_route_operations` y `lg_route_incidents`.
- no forzar `RouteOperation` artificiales para incidencias sin movimiento físico (`CUSTOMER_ABSENT`, `FAILED_DELIVERY`, etc.);
- no convertir este slice en rediseño de `loading`, `return`, `reception` o `stock` fuera del contexto de jornada en calle.

## Problema exacto

Hoy el usuario puede vivir este flujo extraño:

1. registra la operación real de calle;
2. baja a otra sección para registrar o corregir la incidencia;
3. vuelve a subir a operaciones para completar la compensación.

Eso genera tres problemas:

### 1. Fragmentación mental del mismo hecho

El operador piensa en un solo evento:

```text
pasó esto en la calle
```

No piensa en dos entidades separadas ni en dos bandejas distintas.

### 2. Riesgo de operación semánticamente incompleta

Cuando la operación no viene de una parada planificada, hoy puede depender demasiado de `notes` libres para explicar:

- de qué cliente salió el envase;
- en qué almacén terminó o desde qué almacén salió;
- si fue emergencia de cliente, emergencia de almacén o calle normal.

### 3. Acoplamiento de workflow más fuerte que el acoplamiento de dominio

En dominio sí tiene sentido que:

- una incidencia referencie una operación original;
- una incidencia referencie una operación correctiva.

Pero en UX no tiene sentido obligar a que esa relación se capture navegando entre dos flujos principales distintos.

### 4. Incidencias no físicas siguen siendo válidas

Existen desvíos reales que no siempre producen una operación física:

- `CUSTOMER_ABSENT`;
- `FAILED_DELIVERY`;
- otros cierres documentales equivalentes.

Esas incidencias no deben desaparecer ni obligar al sistema a inventar una `RouteOperation` falsa.

La simplificación de UX de esta spec aplica al flujo principal de hechos físicos y correcciones operativas, no a la existencia del modelo de incidencias puramente documentales.

## Decisión de dominio

### 1. `RouteOperation` sigue siendo la verdad operacional primaria

Regla fuerte:

```text
si algo movió físicamente cilindros, primero existe una RouteOperation
```

`RouteIncident` no reemplaza esa verdad.

### 2. `RouteIncident` pasa a ser contexto complementario del mismo evento

Regla fuerte:

```text
la incidencia acompaña o clasifica el desvío
pero no compite con la operación como flujo principal
```

Por eso el sistema debe permitir que, desde un mismo composer, el usuario marque:

- que el evento genera una incidencia nueva;
- que el evento corrige una incidencia existente;
- o que el evento no tiene incidencia asociada.

### 3. Emergencia sin parada exige contexto explícito

Cuando `route_stop_id` es `null`, ya no alcanza con `notes`.

Debe existir un `operation_context` explícito.

Modelo conceptual mínimo:

```ts
type RouteOperationContextType =
  | "STOP"
  | "CUSTOMER_EMERGENCY"
  | "WAREHOUSE_EMERGENCY"
```

Reglas:

1. si `route_stop_id` existe, `context_type = STOP`;
2. si `route_stop_id` no existe y la operación ocurre contra cliente, `context_type = CUSTOMER_EMERGENCY` y `customer_id` es obligatorio;
3. si `route_stop_id` no existe y la operación ocurre contra almacén, `context_type = WAREHOUSE_EMERGENCY` y `warehouse_id` es obligatorio.

### 4. La operación debe cargar snapshots legibles del contexto

Para auditoría operativa y lectura histórica rápida, la operación debe persistir snapshot mínimo del contexto seleccionado:

- `customer_name_snapshot` cuando aplique;
- `warehouse_name_snapshot` cuando aplique.

Regla fuerte:

```text
notes explican
pero customer/warehouse contextualizan de forma estructurada
```

### 5. La interconexión incidencia-operación se conserva, pero como relación débil

Esto sí vale la pena conservar:

- `related_operation_id` en incidencia;
- `corrective_operation_id` en incidencia.

Esto no debe crecer:

- la operación no debe necesitar una incidencia para ser válida;
- la incidencia no debe ser obligatoria para cada operación;
- la corrección no debe obligar al usuario a abandonar el flujo principal de operación.

### 6. `WAREHOUSE_EMERGENCY` queda acotado al contexto de calle

`WAREHOUSE_EMERGENCY` no convierte `RouteOperation` en reemplazo de carga, retorno o recepción.

Solo cubre eventos extraordinarios ocurridos mientras la jornada está operando en `OUTBOUND` o `RETURNING` y que alteran la realidad física/composición de la sesión.

No cubre:

- carga inicial normal;
- retorno formal de jornada;
- recepción operativa de almacén;
- ajustes internos del plugin `stock`.

## Nota de no regresión respecto a `0033`

Esta spec no cambia el discriminador de `PICKUP` definido en `0033`.

Regla fuerte:

```text
CUSTOMER_EMERGENCY + PICKUP
no implica por sí solo devolución financiera real
```

Se mantiene:

- con `origin_movement_id` válido -> devolución financiera real;
- sin `origin_movement_id` -> `PICKUP` puro físico/documental.

## Invariantes obligatorios

1. Todo movimiento físico de cilindros en calle se registra primero como `RouteOperation`.
2. Una incidencia nunca sustituye a la operación real.
3. Una operación confirmada sigue siendo inmutable.
4. Una corrección sigue siendo una nueva `RouteOperation`, no una edición de la original.
5. Si `route_stop_id` es `null`, el contexto manual de cliente o almacén debe ser explícito.
6. `notes` no pueden ser la única fuente de verdad para justificar una emergencia sin parada.
7. La incidencia puede crearse, vincularse o cerrarse desde el mismo composer del evento.
8. La operación puede existir sin incidencia; la incidencia no puede reemplazar una operación física ausente.
9. El submit operacional debe ser idempotente por jornada.
10. No puede existir `incident_mode = CREATE` sin `RouteOperation`, salvo en el flujo secundario explícito `REGISTER_INCIDENT_ONLY`.

## Modelo conceptual

### Composer unificado de evento de ruta

```ts
type RouteEventComposer = {
  route_stop_id?: string | null

  context_type: "STOP" | "CUSTOMER_EMERGENCY" | "WAREHOUSE_EMERGENCY"

  customer_id?: string | null
  customer_name_snapshot?: string | null

  warehouse_id?: string | null
  warehouse_name_snapshot?: string | null

  operation_type: "DELIVERY" | "PICKUP" | "EXCHANGE"
  notes?: string | null
  items: RouteOperationItemRequest[]

  incident_mode: "NONE" | "CREATE" | "CORRECT_EXISTING"
  type?: string | null
  related_operation_id?: string | null
  target_incident_id?: string | null
  incident_notes?: string | null
}
```

### Persistencia mínima esperada en `RouteOperation`

```ts
type RouteOperation = {
  id: string
  session_id: string
  route_stop_id?: string | null

  context_type: "STOP" | "CUSTOMER_EMERGENCY" | "WAREHOUSE_EMERGENCY"

  customer_id?: string | null
  customer_name_snapshot?: string | null

  warehouse_id?: string | null
  warehouse_name_snapshot?: string | null

  operation_type: "DELIVERY" | "PICKUP" | "EXCHANGE"
  status: "DRAFT" | "CONFIRMED" | "CANCELLED"
  movement_ids: string[]
  notes?: string | null
  idempotency_key: string
}
```

### Persistencia de incidencia se mantiene separada

```ts
type RouteIncident = {
  id: string
  session_id: string
  route_stop_id?: string | null
  related_operation_id?: string | null
  corrective_operation_id?: string | null
  type: string
  status: "OPEN" | "RESOLVED" | "CORRECTED"
  notes?: string | null
}
```

## Superficies UX explícitas

Dónde vive cada pieza de esta spec en la UI real.

### A. `RoutesPage` — Panel de control de rutas

**Archivo**: `plugins/logistics/frontend/pages/RoutesPage.tsx`

Deja de ser "Rutas (secundario)". Es el panel central de gestión de rutas. La ejecución (entregar, iniciar, agenda) se traslada completamente a la jornada activa.

Responsabilidades:
- Listar todas las rutas con filtro por fecha/estado
- Seleccionar una ruta → ver detalle: datos + paradas
- **Crear ruta** (conservado)
- **Agregar parada** a la ruta seleccionada (conservado). El diálogo se extrae como `AddStopDialog` reutilizable
- **Mapa de contexto de ruta**: `LocationMap` con los stops de la ruta seleccionada, usando `buildRouteControlMapView`. Solo lectura (sin arrive/depart)
- **Asignar ruta a sesión activa**: selector de sesiones activas (`OUTBOUND`, `RETURNING`) + botón. Usa `POST /vehicle-sessions/{session_id}/assign-route`

Eliminado de esta página (se ejecuta desde la jornada):
- ~~Iniciar ruta~~ → el operador inicia desde el stepper de la jornada
- ~~Entregar parada~~ → el operador registra el evento de ruta desde el composer
- ~~Agenda~~ → reemplazado por planificación (`PlanningReservation`)

Regla: `RoutesPage` no ejecuta. Solo planifica y asigna.

### B. `SessionRouteTab` — Hub de ruta en jornada activa

**Archivo**: `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx`

Se accede desde el stepper de `VehicleSessionDetailPage` → clic en paso "En ruta" o "De regreso" → `RouteModal` → `SessionRouteTab`.

Responsabilidades:
- **Muestra la ruta asignada** como texto (solo lectura, asignada desde `RoutesPage` o al crear la jornada)
- **Botón "Registrar evento de ruta"** → abre el composer unificado (`RouteOperationForm`)
- Resto de botones: Composición, Progreso, Operaciones, Resultados, Incidencias, Mapa de contexto
- **Waybill** en columna izquierda

Regla arquitectónica fuerte:
```text
La ruta planificada no se edita en ejecución.
La realidad se registra como operación.
```
Si al operador "le falta una parada", no modifica la ruta: registra una `RouteOperation` con `context_type = CUSTOMER_EMERGENCY` desde el composer. El hecho queda trazado sin alterar el plan.

### C. `RouteControlMapPanel` — Mapa de contexto de ejecución

**Archivo**: `plugins/logistics/frontend/components/vehicle-sessions/RouteControlMapPanel.tsx`

Se abre desde el botón "Mapa de contexto" en `SessionRouteTab`.

Responsabilidades:
- Mapa con stops planificados, posición del vehículo, ruta viajada
- **Marcar llegada / Marcar salida** sobre la parada activa
- **Indicadores**: estado, paradas completadas, progreso, parada activa
- Si no hay ruta asignada, alerta informativa

No tiene controles de edición de ruta. La ruta planificada no se modifica desde aquí: la realidad se registra como `RouteOperation` desde el composer.

### D. `AddStopDialog` — Diálogo de parada

**Archivo**: `plugins/logistics/frontend/components/vehicle-sessions/AddStopDialog.tsx` (nuevo, extraído de `RoutesPage`)

Usado exclusivamente por `RoutesPage` durante la planificación. No se usa en ejecución: durante la jornada, las paradas no planificadas se registran como `RouteOperation` con `CUSTOMER_EMERGENCY`.

Props:
- `open`, `onClose`
- `routeId` — ruta a la que se agrega
- `onSuccess` — callback post-creación

Internamente: `<Select>` de delivery points + `<Input>` de orden + `POST /routes/{routeId}/stops`.

### D. `RouteOperationForm` — Composer unificado de evento

**Archivo**: `plugins/logistics/frontend/components/vehicle-sessions/RouteOperationForm.tsx`

Se abre desde el botón "Registrar evento de ruta" en `SessionRouteTab`. También desde "Corregir" en `RouteIncidentsPanel`.

Campos:
1. **Tipo**: DELIVERY | PICKUP | EXCHANGE
2. **Parada**: selector de stops de la ruta. `Sin parada` activa contexto manual
3. **Contexto operativo** (sin parada): `Cliente emergencia` o `Almacén emergencia`
4. **Notas**: texto libre
5. **Productos**: búsqueda + cantidades + seriales
6. **Bloque de incidencia** (opcional, toggle):
   - Checkbox "Marcar como incidencia/desvío"
   - Tipo de incidencia (select)
   - Notas de incidencia

Flujos del composer:
- `incident_mode = NONE` → solo `RouteOperation`
- `incident_mode = CREATE` → `RouteOperation` + `RouteIncident`
- `incident_mode = CORRECT_EXISTING` → `RouteOperation` correctiva + cierre de incidencia

### E. `RouteIncidentsPanel` — Bandeja de incidencias

**Archivo**: `plugins/logistics/frontend/components/vehicle-sessions/RouteIncidentsPanel.tsx`

Acciones:
- **Resolver**: cierra incidencia sin compensación física
- **Corregir**: abre el composer unificado en modo `CORRECT_EXISTING`
- **Registrar incidencia sin movimiento**: acción secundaria para casos como `CUSTOMER_ABSENT`, `FAILED_DELIVERY`. No crea `RouteOperation`.

## Reglas de UX

### 1. Un solo entry point principal

La pantalla de calle debe ofrecer como acción principal:

```text
Registrar evento de ruta
```

No:

```text
registrar operación por un lado
registrar incidencia por otro lado
```

Esto aplica al flujo principal de hechos físicos.

Las incidencias sin movimiento físico pueden seguir existiendo como acción secundaria explícita del stop o de la bandeja, pero ya no deben competir visualmente con la captura principal de la calle.

### 2. La incidencia vive como bloque opcional del mismo formulario

Dentro del composer principal debe existir un bloque opcional:

- `Marcar como incidencia/desvío`
- `Tipo de incidencia`
- `Operación relacionada` cuando aplique
- `Notas de incidencia`

### 3. `Corregir ahora` reutiliza el mismo composer

Desde la lista de incidencias abiertas debe existir una acción:

```text
Corregir ahora
```

Esa acción no abre un flujo conceptual distinto.

Debe abrir el mismo composer unificado prellenado con:

- `incident_mode = CORRECT_EXISTING`
- `target_incident_id`
- `route_stop_id` o contexto heredado;
- notas base de corrección.

### 4. La lista de incidencias deja de ser punto principal de captura

La bandeja de incidencias queda para:

- seguimiento;
- cierre documental (`RESOLVED`);
- lanzamiento de corrección (`Corregir ahora`).

Adicionalmente, desde un stop o desde la misma bandeja puede existir una acción secundaria:

- `Registrar incidencia sin movimiento`

Solo para casos donde no exista hecho físico que deba materializarse como `RouteOperation`.

Pero la captura principal del hecho de calle ocurre en el composer operacional.

### 5. `Parada` y `contexto manual` no pueden competir silenciosamente

Si el usuario selecciona una parada:

- el formulario debe derivar cliente desde esa parada;
- el contexto pasa a `STOP`.

Si el usuario deja `Sin parada`:

- el formulario debe obligar a elegir `Cliente emergencia` o `Almacén emergencia` según el caso.

## Reglas backend

### 1. Confirmación atómica por modo

El composer unificado de esta spec es un flujo de confirmación operacional, no un editor de borradores intermedios.

Regla fuerte:

```text
si el composer se confirma
la RouteOperation resultante queda CONFIRMED en el mismo flujo
```

El submit del composer debe soportar tres resultados atómicos:

#### `incident_mode = NONE`

Resultado:

- crear y confirmar `RouteOperation`.

#### `incident_mode = CREATE`

Resultado:

- crear y confirmar `RouteOperation`;
- crear `RouteIncident` vinculada a esa operación.

#### `incident_mode = CORRECT_EXISTING`

Resultado:

- crear y confirmar `RouteOperation` correctiva;
- marcar incidencia destino como `CORRECTED`;
- setear `corrective_operation_id`.

Si la operación no puede quedar `CONFIRMED`, la incidencia debe permanecer `OPEN`.

### 2. La incidencia no puede existir sin semántica clara

Si `incident_mode = CREATE`, el backend debe exigir:

- `type` válido;
- operación recién creada o relacionada explícita.

La taxonomía vigente de incidencias sigue siendo la del modelo actual, con distinción de subconjunto reconciliable:

- tipos válidos generales = catálogo vigente de `RouteIncident`;
- tipos reconciliables = subconjunto que admite `CORRECT_EXISTING`.

### 3. Contexto explícito obligatorio sin parada

Si `route_stop_id` es `null`:

- `context_type` no puede ser `STOP`;
- `customer_id` o `warehouse_id` deben cumplir la regla del contexto elegido.

Regla formal mínima:

```text
IF context_type = STOP
    route_stop_id REQUIRED
    customer_id FORBIDDEN
    warehouse_id OPTIONAL

IF context_type = CUSTOMER_EMERGENCY
    route_stop_id FORBIDDEN
    customer_id REQUIRED

IF context_type = WAREHOUSE_EMERGENCY
    route_stop_id FORBIDDEN
    warehouse_id REQUIRED
```

Notas:

- en `STOP`, `customer_id` no entra desde payload libre; se deriva desde la parada;
- `customer_id` explícito en `STOP` debe rechazarse para evitar mezcla silenciosa de contextos;
- `warehouse_id` en `STOP` puede existir solo si la operación necesita snapshot complementario, pero no reemplaza la parada como owner del contexto.

### 4. `delivery_point` deja de ser la única forma de resolver cliente de calle

Para confirmación de efectos y trazabilidad de posesión cliente:

- si hay `route_stop_id`, se resuelve desde `delivery_point`;
- si no hay `route_stop_id`, se resuelve desde el contexto manual persistido en la operación.

Esto es obligatorio para que un pickup o delivery de emergencia no dependa de texto libre.

### 5. Incidencias sin movimiento físico conservan flujo propio mínimo

Para casos como `CUSTOMER_ABSENT` o `FAILED_DELIVERY` sin mutación física:

- el sistema puede crear `RouteIncident` sin `RouteOperation` nueva;
- ese flujo sigue siendo válido;
- pero debe vivir como acción secundaria y no como entry point principal de la pantalla.

Ese flujo debe ser explícito y separado del composer principal:

```text
REGISTER_INCIDENT_ONLY
```

Regla fuerte:

```text
incident_mode = CREATE dentro del composer principal
siempre implica RouteOperation confirmada en el mismo submit
```

No se permite:

```text
incident_mode = CREATE
sin RouteOperation
```

salvo en `REGISTER_INCIDENT_ONLY`.

### 6. Idempotencia dura del composer

El composer principal debe tratar cada submit como un evento operacional único dentro de la jornada.

Restricción mínima obligatoria:

```text
UNIQUE (session_id, idempotency_key)
```

Regla fuerte:

```text
doble submit del mismo composer
no puede crear 2 RouteOperation
ni 2 RouteIncident
ni 2 enlaces correctivos
```

Comportamiento esperado:

1. si `(session_id, idempotency_key)` no existe, el backend procesa normalmente;
2. si ya existe, el backend retorna el mismo resultado lógico del primer submit;
3. el segundo submit nunca debe materializar una nueva operación paralela ni una nueva incidencia duplicada.

### 7. Validación cruzada de `incident_mode`

El backend debe validar combinaciones de forma dura antes de persistir.

Reglas mínimas:

#### `incident_mode = NONE`

- `type` debe venir vacío;
- `target_incident_id` debe venir vacío.

#### `incident_mode = CREATE`

- `type` es obligatorio;
- `target_incident_id` debe venir vacío;
- la operación confirmada del mismo submit es obligatoria.

#### `incident_mode = CORRECT_EXISTING`

- `target_incident_id` es obligatorio;
- la incidencia destino debe existir en la misma jornada;
- la incidencia destino debe estar `OPEN`;
- `type` no redefine la incidencia existente salvo decisión futura explícita.

Ejemplo de fallo obligatorio:

```text
incident_mode = CORRECT_EXISTING
sin target_incident_id
=> request inválido
```

## Relación con specs previas

### Respecto a `0033`

Esta spec no cambia la separación de efectos.

Solo agrega dos cierres operativos que `0033` dejó abiertos:

1. cómo se captura UX sin fragmentar operación e incidencia;
2. cómo se justifica estructuralmente una operación sin parada.

### Respecto a `0024.1.3.3`

Esta spec mantiene intacta la regla fuerte:

```text
incidencia detecta
operación correctiva reconcilia
```

Lo que cambia es el punto de captura UX:

- la corrección ya no debe sentirse como salto a otro flujo;
- debe sentirse como variante del mismo composer operacional.

## Criterios de aceptación

1. El operador puede registrar una operación de ruta y, en el mismo formulario, marcar que genera incidencia.
2. El operador puede corregir una incidencia desde la misma acción principal de captura, sin navegar a un flujo conceptual distinto.
3. Una operación sin parada no puede confirmarse sin `customer_id` o `warehouse_id` estructurado según el contexto.
4. Un pickup de emergencia desde cliente queda trazable sin depender solo de `notes`.
5. Una incidencia sin movimiento físico todavía puede registrarse sin inventar una `RouteOperation` falsa.
6. La relación entre incidencia y operación sigue siendo visible en historial, pero ya no obliga a UX duplicada.
7. La composición vigente y la carta porte siguen reaccionando a `RouteOperation`, no a la incidencia directamente.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Mezclar demasiado operación e incidencia en backend | medio | mantener tablas y lifecycle separados; unificar solo el composer y el comando de confirmación |
| Crear demasiados campos opcionales ambiguos | alto | obligar `context_type` y validaciones fuertes cuando no hay `route_stop_id` |
| UI demasiado cargada | medio | mostrar el bloque de incidencia solo cuando el usuario lo activa |
| Duplicar lógica entre `create_route_operation` y `correct_route_incident` | alto | extraer un comando común de `RouteEventComposer` y dejar la incidencia como post-efecto controlado |

## Implementación

### Ya implementado (cambios no commiteados)

1. `context_type`, `customer_id`, `customer_name_snapshot`, `warehouse_id`, `warehouse_name_snapshot` en `lg_route_operations` (migración 037)
2. `RouteEventConfirmRequest` DTO con `incident_mode` y contexto manual
3. `confirm_route_event()` en backend — confirma atómicamente operación + incidencia opcional
4. `POST /{session_id}/route-events/confirm` endpoint
5. `_resolve_operation_context()` — valida STOP vs CUSTOMER_EMERGENCY vs WAREHOUSE_EMERGENCY
6. `RouteOperationForm` con campos de contexto (parada, contexto manual, customer, warehouse)
7. `confirmRouteEvent()` en API frontend
8. `useSessionRouteTabController.createAndConfirmMutation` — wired al form
9. `RouteControlMapPanel` con mapa, arrive/depart (archivo untracked)
10. `route-control-view.ts` — buildRouteControlMapView (archivo untracked)
11. `LocationMap` en `shared/ui/`

### Pendiente — Fase 1: Backend + RoutesPage

**Backend**:
1. `AssignRouteRequest` DTO en `dto/sessions.py`
2. `assign_route_to_session()` en `services/sessions.py`
3. `POST /vehicle-sessions/{session_id}/assign-route` en `routers/sessions.py`

**Frontend API**:
4. `assignRouteToSession()` en `api/sessions.ts`

**RoutesPage**:
5. Título: `"Rutas (secundario)"` → `"Rutas"` con descripción profesional
6. Agregar `LocationMap` con stops de la ruta seleccionada (usa `buildRouteControlMapView`)
7. Agregar selector de sesiones activas + botón "Asignar ruta"
8. Extraer diálogo de parada a `AddStopDialog.tsx` (reutilizable)
9. Quitar `deliverRouteStop`, `startRoute`, agenda — imports, mutations, y botones
10. Quitar `deliverRouteStop` y `startRoute` de `api/routes.ts` si no se usan en otro lado

### Pendiente — Fase 2: Composer unificado completo

1. `RouteOperationForm`: agregar bloque opcional de incidencia (checkbox, tipo, notas)
2. `useSessionRouteTabUiState`: `incidentMode`, `incidentType`, `incidentNotes`
3. `useSessionRouteTabController`: soportar `incident_mode = CREATE` en el submit
4. `RouteIncidentsPanel`: botón secundario "Registrar incidencia sin movimiento" → `REGISTER_INCIDENT_ONLY`
