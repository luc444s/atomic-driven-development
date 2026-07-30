---
id: "0024.1.3"
title: "Carta Porte Operativa en Jornada"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-3-vehicle-session-hero-console.md
  - docs/specs/core/0024-1-2-vehicle-first-jornadas-projection.md
  - docs/specs/core/0023-logistics-operacion-real/0023J-carta-porte-digital.md
---

# SPEC 0024.1.3 — Carta Porte Operativa en Jornada

## Contexto

## Nota de vigencia

`SPEC 0033 - RouteOperation con Efectos Separados` ajusta esta spec en un punto critico:

`Carta Porte` ya no puede depender solo de `movement_ids` ni de cambios financieros.

Desde `0033`, su estado de sincronizacion y su `operational_hash` tambien deben reaccionar a cambios fisicos de composicion en la sesion.

`SPEC 0024.3` consolidó que la jornada se opera desde el stepper y que los contextos reales deben abrirse desde esa consola.

`SPEC 0023J` ya fijó la intención documental de carta porte viva/versionada, pero todavía no aterriza la integración operativa concreta dentro de `Jornada`.

Según `Grab2`, cuando el vehículo ya está en ruta debe existir la posibilidad de cambiar operativamente la carta porte en tiempo real.

Para este caso, el marco regulatorio relevante es Hacienda de España.

## Frase guía

**La carta porte no es un módulo aparte. Es evidencia documental versionada de la jornada en movimiento.**

## Objetivo

Integrar `carta porte` dentro de `Jornada` como contexto operativo/documental activo durante `OUTBOUND`, permitiendo regeneración versionada, trazable y consistente a partir del estado operativo real.

## No objetivos

- no crear un estado nuevo en `VehicleSession`
- no convertir `carta porte` en owner del flujo
- no permitir edición manual libre del documento final
- no mezclar `carta porte` con `albarán`
- no cerrar todavía toda la normativa fiscal/documental española al detalle
- no mover la lógica de consistencia documental al frontend

## Decisión de dominio

`Carta porte` no es un step nuevo ni una pantalla aislada.

`Carta porte` es una fotografía versionada de la operación en movimiento.

Pertenece a la ejecución de la jornada (`vehicle_session`) y se construye desde la composición operativa vigente de la jornada en ruta: cambios financieros y cambios fisicos.

## Principios obligatorios

1. `OUTBOUND` es el contexto operativo principal de carta porte.
2. La jornada expone y opera la carta porte, pero no redefine su verdad.
3. La carta porte no se actualiza in-place: toda mutación crea nueva versión o invalida la actual.
4. La versión activa debe representar un snapshot consistente y autocontenible.
5. La regeneración debe ser determinista: mismo estado operativo, mismo resultado documental.
6. La detección de desincronización debe ser backend-driven.
7. La regeneración debe ser atómica e idempotente.

## Ownership

### `VehicleSession` / Jornada

Responsable de:

- exponer el contexto operativo de carta porte;
- abrir el workspace o modal correspondiente;
- mostrar vigencia, historial y estado de desincronización;
- permitir disparar regeneración controlada.

### `Movements`

Responsable de:

- aportar la verdad operativa base;
- reflejar la porcion financiera/documental de la composicion transportada vigente;
- emitir los cambios operativos relevantes que afectan el snapshot.

### `RouteOperation` + composición vigente

Responsable de:

- reflejar la verdad fisica actual de la jornada;
- incorporar cambios operativos que no generan `Movement`;
- desactualizar la carta porte cuando la composicion fisica cambie.

### Capa documental

Responsable de:

- persistir snapshots versionados;
- mantener lineage entre versiones;
- marcar la versión activa;
- conservar historial auditable;
- renderizar la salida documental.

## Invariantes del sistema

1. Solo puede existir una versión `ACTIVE` por `vehicle_session_id + regulatory_context`.
2. Una versión `SUPERSEDED` o `VOID` no puede volver a `ACTIVE`.
3. Una regeneración no puede mezclar estados operativos intermedios.
4. Si el snapshot regenerado es idéntico al activo, no debe crearse nueva versión.
5. La carta porte activa debe poder reconstruirse sin joins futuros obligatorios.

## Momento operativo

La carta porte vive principalmente en:

- `OUTBOUND`

Puede ser visible en estados anteriores o posteriores en modo lectura, pero su contexto operativo modificable se habilita en ruta.

## Modelo conceptual

```ts
type CartaPorteVersion = {
  id: string
  vehicle_session_id: string
  movement_ids: string[]
  version: number
  previous_version_id?: string | null
  status: "ACTIVE" | "SUPERSEDED" | "VOID"
  regulatory_context: "ES_HACIENDA"
  generated_at: string
  generated_by?: string | null
  operational_hash: string
  snapshot_schema_version: number
  snapshot: {
    vehicle: {
      id: string
      plate: string
      kind?: string | null
    }
    driver: {
      id: string
      name: string
      license?: string | null
    }
    destination: {
      id?: string | null
      name?: string | null
      address?: string | null
    }
    transported_items: Array<{
      product_id: string
      product_name: string
      quantity: number
      unit?: string | null
      weight_kg?: number | null
      adr_points?: number | null
    }>
    totals: {
      total_packages?: number | null
      total_weight_kg?: number | null
      total_adr_points?: number | null
    }
  }
  change_event: "INITIAL_GENERATION" | "MOVEMENT_CHANGED" | "PHYSICAL_COMPOSITION_CHANGED" | "DRIVER_CHANGED" | "VEHICLE_CHANGED" | "DESTINATION_CHANGED"
  change_reason: string
}
```

Reglas complementarias del modelo:

1. `movement_ids` debe normalizarse en orden estable antes de calcular el `operational_hash`.
2. `sync_status` es derivado, no persistido.
3. `snapshot_schema_version` permite evolucionar el payload histórico sin romper lectura futura.
4. `movement_ids` por si solo no representa todo el estado operativo; la composicion fisica vigente tambien forma parte del hash.

## Integridad temporal y consistencia

La carta porte debe generarse sobre una versión consistente del estado operativo.

Reglas:

1. la regeneración debe calcular un `operational_hash` del estado operativo usado para construir el snapshot;
2. `movement_ids` debe ordenarse de forma determinista antes de entrar al hash cuando existan;
3. el hash tambien debe incorporar la composicion fisica vigente de la sesion;
4. el snapshot activo se considera desactualizado cuando el hash operativo vigente difiere del hash de la versión activa;
5. backend debe rechazar o reintentar la regeneración si detecta que el estado operativo cambió durante la operación;
6. la generación debe ejecutarse dentro de una transacción o estrategia equivalente de snapshot consistente.

## Idempotencia

La regeneración debe ser idempotente.

Reglas:

1. la API acepta `idempotency_key`;
2. la misma operación con la misma clave devuelve la misma respuesta;
3. doble click o retry de red no debe crear dos versiones idénticas;
4. si el snapshot resultante es idéntico al activo, la respuesta debe reutilizar la versión vigente en vez de crear una nueva.

## Estados documentales

### `ACTIVE`

Versión vigente de uso operativo.

### `SUPERSEDED`

Versión reemplazada por otra más nueva.

### `VOID`

Versión inválida por error documental, inconsistencia o anulación explícita.

## Eventos causales

La carta porte no reacciona a campos sueltos sino a eventos operativos.

Eventos mínimos:

- `INITIAL_GENERATION`
- `MOVEMENT_CHANGED`
- `PHYSICAL_COMPOSITION_CHANGED`
- `DRIVER_CHANGED`
- `VEHICLE_CHANGED`
- `DESTINATION_CHANGED`

Toda nueva versión debe registrar:

- `change_event`
- `change_reason`
- `previous_version_id` cuando aplique

## Estado de sincronización

La detección de desincronización es responsabilidad del backend.

`sync_status` no se persiste: se calcula siempre a partir del `operational_hash` actual versus el `operational_hash` de la versión activa.

Regla:

```text
is_outdated = operational_hash(actual_state) != operational_hash(snapshot_activo)
```

Donde `actual_state` incluye:

- cambios financieros/materializados por `Movement`;
- cambios fisicos de composicion aunque no existan `movement_ids` nuevos.

La UI no infiere esto por su cuenta.

## Frontend

### Principios UI

1. `Carta Porte` no aparece como step nuevo.
2. Vive dentro del contexto de `route` o como subcontexto documental abierto desde `OUTBOUND`.
3. La UI consume estado documental calculado por backend.
4. El frontend no reconstruye la validez del documento ni calcula `outdated` localmente.

### Estructura esperada

```text
VehicleSessionDetailPage
  -> VehicleSessionConsole
    -> SessionStepper
    -> RouteModal
      -> WaybillPanel
        -> ActiveWaybillCard
        -> WaybillSyncBanner
        -> WaybillHistoryList
```

### Integración con el flujo actual

- `OUTBOUND` sigue siendo un step del flujo;
- al abrir contexto `route`, el usuario encuentra también `Carta Porte`;
- `RouteModal` debe incluir resumen de versión activa, estado `SYNCED/OUTDATED`, CTA de regeneración e historial;
- no debe convertirse en formulario libre de edición del documento.

### Reglas UX críticas

Si la carta porte está `OUTDATED`:

- debe mostrarse warning fuerte;
- la operación no se bloquea automáticamente;
- la acción principal visible pasa a ser `Regenerar carta porte`.

### Acciones visibles

- `Ver carta porte actual`
- `Regenerar carta porte`
- `Ver historial`

### Payload de regeneración

```json
{
  "reason": "Entrega parcial en ruta",
  "event": "MOVEMENT_CHANGED",
  "idempotency_key": "uuid"
}
```

## Backend

### Modelo persistido esperado

```ts
type CartaPorteVersionRecord = {
  id: string
  vehicle_session_id: string
  movement_ids_json: string
  version: number
  previous_version_id: string | null
  status: "ACTIVE" | "SUPERSEDED" | "VOID"
  regulatory_context: "ES_HACIENDA"
  generated_at: datetime
  generated_by: string | null
  operational_hash: string
  snapshot_schema_version: number
  snapshot_json: string
  change_event: "INITIAL_GENERATION" | "MOVEMENT_CHANGED" | "DRIVER_CHANGED" | "VEHICLE_CHANGED" | "DESTINATION_CHANGED"
  change_reason: string
  idempotency_key: string | null
}
```

### Restricciones obligatorias

1. `UNIQUE(vehicle_session_id, regulatory_context) WHERE status = 'ACTIVE'`
2. `UNIQUE(vehicle_session_id, idempotency_key) WHERE idempotency_key IS NOT NULL`
3. `SUPERSEDED` y `VOID` son terminales.
4. `movement_ids_json` debe persistirse ya normalizado en orden estable.

### Snapshot autocontenible

El snapshot debe contener todo lo necesario para renderizar la carta porte sin depender de joins futuros obligatorios.

Debe incluir como mínimo:

- vehículo;
- conductor;
- destino;
- items transportados;
- totales operativos/documentales.

No debe limitarse a guardar solo IDs.

### Regeneración

Reglas:

1. debe ser atómica;
2. debe correr sobre snapshot consistente del estado operativo;
3. debe ser idempotente por `idempotency_key`;
4. debe reutilizar la versión activa si el snapshot resultante es idéntico;
5. si crea nueva versión, debe marcar la anterior como `SUPERSEDED` dentro de la misma operación transaccional.

Secuencia esperada:

```text
lock jornada/documento activo
-> calcular estado operativo consistente
-> construir snapshot
-> calcular operational_hash
-> verificar idempotency_key
-> comparar contra ACTIVE actual
-> si hash igual: devolver ACTIVE actual
-> si hash distinto: crear nueva versión ACTIVE
-> marcar anterior como SUPERSEDED
-> auditar
-> responder
```

### Endpoints mínimos

- `GET /vehicle-sessions/{id}/carta-porte`
- `GET /vehicle-sessions/{id}/carta-porte/history`
- `POST /vehicle-sessions/{id}/carta-porte/regenerate`

## Relación con albarán

`Carta porte` y `albarán` permanecen separados.

### Carta porte

Responde:

- qué se transporta ahora;
- con qué vehículo;
- con qué conductor;
- hacia qué destino;
- bajo qué snapshot vigente.

### Albarán

Responde:

- qué se entregó o retiró realmente;
- a quién;
- en qué cantidad;
- como evidencia de ejecución frente al cliente.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Mezclar ownership entre jornada y movement | alto | fijar `vehicle_session` como owner de ejecución y `movements` como source operativo |
| Crear versiones basura | medio | no regenerar si el snapshot es idéntico |
| Doble creación por retry | medio | `idempotency_key` + control transaccional |
| Snapshot inconsistente | alto | `operational_hash` + generación atómica |
| Frontend decidiendo desincronización | alto | exponer `sync_status` desde backend |
| Snapshot incompleto | alto | exigir snapshot autocontenible |

## Criterios de aceptación

1. desde la jornada, en `OUTBOUND`, el operador puede abrir `Carta Porte`;
2. no se agrega un nuevo estado al stepper;
3. existe una única versión `ACTIVE` por jornada y contexto regulatorio;
4. el backend expone si la carta porte está `SYNCED` u `OUTDATED`;
5. regenerar crea nueva versión solo si el snapshot cambió materialmente;
6. la regeneración es idempotente y atómica;
7. existe historial con `previous_version_id`, `change_event` y `change_reason`;
8. el snapshot es suficiente para renderizar sin depender de joins futuros obligatorios;
9. el flujo queda alineado con contexto regulatorio de España.

## Dependencias

- `docs/specs/core/0024-3-vehicle-session-hero-console.md`
- `docs/specs/core/0024-1-2-vehicle-first-jornadas-projection.md`
- `docs/specs/core/0023-logistics-operacion-real/0023J-carta-porte-digital.md`
- `docs/specs/core/0023-logistics-operacion-real/0023E/0023E2-vehicle-session-almacen-movil-v2.md`
- `docs/contracts/logistics-api.md`

## Archivos candidatos

- `plugins/logistics/frontend/pages/VehicleSessionDetailPage.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/modals/RouteModal.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/session-ui-map.ts`
- `plugins/logistics/backend/router.py`
- `plugins/logistics/backend/services/documents.py`
- `plugins/logistics/backend/services/movements.py`
