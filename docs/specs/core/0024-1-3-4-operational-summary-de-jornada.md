---
id: "0024.1.3.4"
title: "Operational Summary de Jornada"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-3-vehicle-session-hero-console.md
  - docs/specs/core/0024-1-3-3-reconciliacion-controlada-sobre-incidencias-de-ruta.md
  - docs/specs/core/0024-1-3-2-exchange-incidencias-y-progreso-real-de-stop.md
  - docs/specs/core/0024-1-3-1-route-operation-y-composicion-vigente.md
  - docs/specs/core/0024-1-3-carta-porte-operativa-en-jornada.md
---

# SPEC 0024.1.3.4 - Operational Summary de Jornada

## Contexto

`SPEC 0024.1.3.1` fijo la base operacional correcta:

- `VehicleSession` como root de jornada;
- `RouteOperation` como hecho de calle;
- `Movement` como via obligatoria para tocar stock;
- `Composicion Vigente` como estado derivado.

`SPEC 0024.1.3.2` agrego dos piezas que faltaban para que la calle pudiera leerse semanticamente:

- incidencias operativas;
- progreso real de `RouteStop` derivado desde operaciones e incidencias.

`SPEC 0024.1.3.3` cerro el circuito de reconciliacion inventariable:

- incidencia como desvio documentado;
- correccion como nueva `RouteOperation`;
- composicion y carta porte downstream de hechos confirmados.

Con eso ya existe la verdad operativa.

Lo que todavia falta es volverla legible a nivel jornada sin obligar al usuario a entrar al detalle fino de ruta para responder preguntas basicas:

- como va realmente la jornada;
- cuantas paradas estan completas, parciales o fallidas;
- si hay incidencias abiertas;
- si la jornada esta sana, desviada o bloqueada;
- si el documento operativo acompaña o quedo atras.

## Frase guia

**La jornada necesita un pulso operativo visible, no solo hechos correctos escondidos en el detalle.**

**No basta con que el sistema sea correcto. Debe ser legible para quien lo opera.**

## Objetivo

Agregar un `Operational Summary` shell-level para `VehicleSession` que:

1. resuma el estado operativo real de la jornada a partir de datos derivados existentes;
2. haga visible la salud de ejecucion sin entrar al `RouteTab`;
3. mantenga una separacion clara entre lectura ejecutiva y detalle operativo;
4. preserve la regla de que el summary no crea verdad nueva, solo condensa la ya derivada.

## No objetivos

- no crear otro aggregate root distinto de `VehicleSession`;
- no mover logica de calle al frontend;
- no duplicar manualmente estados ya derivables desde `RouteStopProgress`, `RouteIncident`, `RouteOperation` o `Carta Porte`;
- no reemplazar el `RouteTab` como workspace operativo detallado;
- no convertir el summary en dashboard BI historico;
- no cerrar todavia la taxonomia final de `stop results` no reconciliables.

## Problema exacto

Hoy el shell de jornada muestra bien contexto general:

- vehiculo;
- conductor;
- origen;
- peso;
- stock movil;
- ultima actividad.

Pero eso no alcanza para leer la salud operacional de la ejecucion.

Dos jornadas pueden verse similares en datos generales y, sin embargo, estar en situaciones totalmente distintas:

- una con la ruta avanzando normalmente;
- otra con varias paradas parciales;
- otra con incidencias abiertas sin resolver;
- otra con carta porte desactualizada respecto de la realidad operativa.

Sin `Operational Summary`, la verdad existe pero queda distribuida en varios paneles:

```text
RouteStopProgress
+ RouteIncidents
+ RouteOperations
+ CurrentComposition
+ Waybill sync state
```

Eso obliga a inspeccion manual cuando lo que falta es una lectura ejecutiva inmediata.

## Decisión de dominio

## 1. El summary es lectura derivada, no fuente de verdad

`Operational Summary` no define estados operativos por su cuenta.

Debe construirse desde la cadena ya aprobada:

```text
VehicleSession
-> RouteOperation
-> RouteStopProgress
-> RouteIncident
-> Composicion Vigente
-> Carta Porte
```

Regla fuerte:

```text
summary = interpretacion condensada de estado derivado
summary != owner de la operacion
```

## 2. Debe vivir visible en el shell de jornada

`Operational Summary` es importante para lectura rapida de la jornada.

Por eso no debe esconderse solo detras de un boton + modal.

Decision UI:

1. debe existir una version inline compacta visible en la consola de jornada;
2. puede existir un `Ver detalle` para abrir modal o panel expandido;
3. el detalle amplia, pero no reemplaza, la lectura inline;
4. el CTA de detalle no vive dentro de `OperationalSummaryInline` si eso contradice el contrato visual de `0024.3`; debe vivir en un wrapper shell o zona contigua.

## 3. El summary expresa salud operacional, no solo inventario

El summary debe responder en una sola vista:

1. cuantas paradas siguen `PENDING`;
2. cuantas estan `IN_PROGRESS`;
3. cuantas quedaron `PARTIAL`;
4. cuantas quedaron `COMPLETED`;
5. cuantas quedaron `FAILED`;
6. cuantas incidencias abiertas existen;
7. si la carta porte activa esta `SYNCED` o `OUTDATED`;
8. cual fue la ultima actividad operacional relevante.

## 4. El summary tambien expresa confiabilidad de lectura

No toda jornada tiene siempre informacion completa para emitir una lectura fuerte.

Por eso el summary debe declarar si su lectura esta construida con contexto completo o parcial.

Regla fuerte:

```text
si faltan piezas estructurales del contexto
el summary debe decirlo antes de sugerir una conclusion fuerte
```

Ejemplos:

- sin ruta asignada -> `PARTIAL`
- sin waybill donde ya deberia existir -> `PARTIAL`
- otras lagunas estructurales relevantes -> `PARTIAL`

## 5. El summary puede clasificar la jornada, pero no inventar workflow nuevo

Se admite una clasificacion ejecutiva de salud de jornada para mejorar lectura humana.

Ejemplo:

- `HEALTHY`
- `ATTENTION`
- `BLOCKED`

Pero esa clasificacion:

- es derivada;
- no persiste workflow nuevo;
- no reemplaza `session.status`;
- no cambia permisos ni transiciones.

## Invariantes obligatorios

1. El summary no persiste verdad operativa nueva si ya puede derivarse de entidades existentes.
2. El frontend no calcula por su cuenta el estado documental de carta porte.
3. La clasificacion ejecutiva no reemplaza `VehicleSession.status`.
4. El detalle expandido debe explicar el por que de una jornada parcial o en atencion.
5. Una incidencia abierta debe reflejarse en el summary aunque no cambie stock.
6. Una correccion confirmada solo impacta el summary por sus efectos derivados reales.
7. El summary inline debe priorizar legibilidad inmediata sobre exhaustividad.
8. El `RouteTab` sigue siendo el workspace de ejecucion fina; el summary no absorbe sus acciones.

## Modelo conceptual

```ts
type BlockingReason =
  | "FAILED_STOP"
  | "WAYBILL_MISSING"
  | "NO_ROUTE_ASSIGNED"

type AttentionReason =
  | "PARTIAL_STOP"
  | "OPEN_INCIDENT"
  | "WAYBILL_OUTDATED"

type SessionOperationalSummary = {
  session_id: string
  session_status: string

  data_completeness:
    | "FULL"
    | "PARTIAL"

  health_status:
    | "HEALTHY"
    | "ATTENTION"
    | "BLOCKED"

  stop_counters: {
    total: number
    pending: number
    in_progress: number
    partial: number
    completed: number
    failed: number
  }

  incidents: {
    open_total: number
    corrected_total: number
    resolved_total: number
  }

  route_activity: {
    confirmed_operations: number
    last_activity?: {
      type: "OPERATION" | "INCIDENT" | "DOCUMENT"
      label: string
      at: string
    } | null
  }

  composition: {
    total_products: number
    total_units: number
    total_weight_kg?: number | null
  }

  waybill: {
    has_active_version: boolean
    sync_status: "SYNCED" | "OUTDATED" | "MISSING"
    active_version?: number | null
  }

  blocking_reasons: BlockingReason[]
  attention_reasons: AttentionReason[]
}
```

## Reglas de derivacion

## 1. Contadores de paradas

`stop_counters` debe salir de `RouteStopProgress`.

Reglas:

1. `total` es el total de stops de la ruta asignada;
2. cada stop cuenta exactamente en una categoria de progreso;
3. si no hay ruta asignada, el summary debe explicitarlo en vez de simular progreso.

## 1.1. `data_completeness`

`data_completeness` expresa si el summary esta leyendo una jornada con contexto operativo suficiente.

Reglas:

1. `FULL` cuando existen los insumos estructurales esperados para esa jornada;
2. `PARTIAL` cuando faltan piezas base que pueden distorsionar la lectura ejecutiva;
3. `PARTIAL` no anula el summary, pero obliga a que el backend explique la laguna en razones visibles;
4. `data_completeness` y `health_status` no son lo mismo: una jornada puede estar en `ATTENTION` con datos `FULL`, o en `HEALTHY` provisionalmente pero marcada `PARTIAL` por contexto faltante.

## 2. Conteo de incidencias

`incidents.open_total` debe contar incidencias `OPEN`.

Reglas:

1. incidencias abiertas deben elevar al menos `ATTENTION`;
2. incidencias `RESOLVED` no bloquean por si solas;
3. incidencias `CORRECTED` cuentan como historial de compensacion, no como problema activo.

## 3. Salud ejecutiva de jornada

### `HEALTHY`

Se usa cuando la jornada no presenta desvio operativo relevante visible.

Ejemplos compatibles:

- sin incidencias abiertas;
- sin stops `FAILED`;
- sin desincronizacion documental critica.

### `ATTENTION`

Se usa cuando la jornada sigue operable pero requiere mirada.

Ejemplos:

- incidencias `OPEN`;
- stops `PARTIAL`;
- carta porte `OUTDATED`;
- desvio pendiente de revision operativa.

### `BLOCKED`

Se usa cuando existe señal fuerte de jornada trabada o con ejecucion fallida material.

Ejemplos:

- uno o mas stops `FAILED`;
- ausencia de version documental cuando la operacion ya deberia tenerla;
- otra condicion de negocio fuerte definida por backend.

Regla fuerte:

```text
health_status no cambia la jornada
solo la hace legible
```

### Precedencia obligatoria de `health_status`

Para evitar implementaciones ambiguas, la derivacion debe seguir este orden:

1. `BLOCKED` si existe al menos un `FAILED`;
2. `BLOCKED` si `waybill.sync_status = MISSING` en una jornada `OUTBOUND` o `RETURNING` con ruta asignada;
3. `ATTENTION` si existe al menos un stop `PARTIAL` y no aplica un bloqueo superior;
4. `ATTENTION` si existe al menos una incidencia `OPEN` y no aplica un bloqueo superior;
5. `ATTENTION` si `waybill.sync_status = OUTDATED` y no aplica un bloqueo superior;
6. `HEALTHY` si no se activa ninguna condicion anterior.

Casos complementarios:

1. jornada sin ruta asignada no debe fingir salud operacional plena; debe devolver `ATTENTION` con razon explicita `NO_ROUTE_ASSIGNED` si ya se esperaba contexto de ruta;
2. `RESOLVED` y `CORRECTED` no elevan estado por si solos;
3. si conviven varias razones, `blocking_reasons` y `attention_reasons` deben conservarlas aunque la clasificacion final sea una sola.

Mapeo minimo esperado de razones:

- stop `FAILED` -> `FAILED_STOP`
- waybill `MISSING` en contexto exigible -> `WAYBILL_MISSING`
- jornada sin ruta cuando ya se esperaba ruta -> `NO_ROUTE_ASSIGNED`
- stop `PARTIAL` -> `PARTIAL_STOP`
- incidencia `OPEN` -> `OPEN_INCIDENT`
- waybill `OUTDATED` -> `WAYBILL_OUTDATED`

### Regla de `last_activity`

La ultima actividad no debe modelarse como texto libre opaco.

Debe indicar:

1. tipo de hecho (`OPERATION`, `INCIDENT`, `DOCUMENT`);
2. etiqueta legible;
3. timestamp del hecho.

Eso evita hacks posteriores y permite ordenar, filtrar o renderizar iconografia consistente.

## 4. Carta porte en el summary

El summary no reconstruye la carta porte.

Solo expone una lectura ejecutiva de su estado:

- `SYNCED`
- `OUTDATED`
- `MISSING`

`MISSING` aplica cuando la jornada ya opera en contexto donde deberia existir version activa y no la hay.

## 5. Inline primero, detalle despues

### Inline compacto

Debe mostrar como minimo:

1. salud general;
2. contadores de stops;
3. incidencias abiertas;
4. ultima actividad;
5. estado documental resumido.

### Detalle expandido

Debe ampliar con:

1. razones de `ATTENTION` o `BLOCKED`;
2. stops problematicos;
3. incidencias abiertas relevantes;
4. estado documental y de composicion con mas contexto.

## Frontend

### Estructura esperada

```text
VehicleSessionDetailPage
  -> VehicleSessionConsole
    -> OperationalSummaryShell
      -> OperationalSummaryInline
      -> OperationalSummaryDetailTrigger
      -> OperationalSummaryDetailModal | Sheet
```

### Regla UX principal

No esconder informacion critica dentro de modal como unica via.

El modal o panel existe para inspeccion.
La lectura ejecutiva debe vivir inline.

`OperationalSummaryInline` sigue siendo una banda pasiva de contexto, en continuidad con `0024.3`.

## Backend

## API esperada

Se recomienda un endpoint derivado dedicado, por ejemplo:

```text
GET /api/v1/plugins/logistics/vehicle-sessions/{session_id}/operational-summary
```

Razones:

1. evita reensamblar verdad de negocio en frontend;
2. centraliza la heuristica de salud operacional;
3. permite evolucionar criterios sin romper varios clientes.

## Reglas backend

1. el backend debe calcular `health_status`;
2. el backend debe calcular `attention_reasons` y `blocking_reasons`;
3. el backend debe reutilizar derivaciones ya existentes donde aplique (`RouteStopProgress`, `CurrentComposition`, `Waybill sync`);
4. el backend no debe introducir persistencia nueva si la informacion ya es reconstruible.

## Performance

Este endpoint debe tratarse como lectura operacional frecuente.

Reglas:

1. priorizar agregaciones y derivaciones compactas en backend;
2. evitar N+1 al calcular stops, incidencias, operaciones y waybill;
3. si la carga real lo exige, admitir cache corto en Redis para el payload derivado;
4. cualquier cache debe ser de vida corta y consistente con eventos operativos recientes;
5. performance no justifica duplicar persistencia de verdad si la derivacion sigue siendo razonable.

## Permisos

No requiere permiso nuevo si el usuario ya puede ver la jornada.

Hereda visibilidad desde `logistics.session.read`.

Si en implementacion se expone fuera del detalle de jornada, revisar si hace falta permiso de lectura separado.

## Eventos

No requiere evento nuevo como condicion de V1.

El summary reacciona a eventos/efectos ya existentes:

- confirmacion de `RouteOperation`;
- apertura/cierre/correccion de `RouteIncident`;
- cambios en composicion vigente;
- regeneracion o invalidacion documental.

## Datos

Entidades y fuentes involucradas:

- `VehicleSession`
- `RouteStop`
- `RouteStopProgress`
- `RouteOperation`
- `RouteIncident`
- `CurrentComposition`
- `Carta Porte` / `SessionWaybillState`

Componente actual impactado:

- `plugins/logistics/frontend/components/vehicle-sessions/OperationalSummaryInline.tsx`

## Migraciones

No requiere migracion de base de datos en principio.

Si en implementacion aparece una necesidad de persistencia adicional, debe justificarse aparte porque esta spec parte de derivacion, no de almacenamiento nuevo.

## Auditoría y observabilidad

1. no hace falta auditar la lectura del summary como hecho de negocio principal;
2. si el usuario abre el detalle expandido, puede registrarse telemetria UI no bloqueante;
3. cualquier razon de bloqueo o atencion debe ser explicable desde datos reconstruibles.

## Riesgos

1. mezclar estado ejecutivo con `session.status` y terminar creando dos workflow paralelos;
2. llevar demasiada logica de salud al frontend;
3. producir un summary ambiguo que diga "mal" sin explicar por que;
4. esconder el summary tras modal y perder valor operacional;
5. duplicar consultas y degradar performance si no se centraliza derivacion.

## Criterios de aceptación

1. La jornada muestra un `Operational Summary` inline visible sin entrar al `RouteTab`.
2. El summary muestra contadores reales de stops por estado derivado.
3. El summary muestra cantidad de incidencias abiertas.
4. El summary muestra estado documental resumido de carta porte sin recalcularlo en frontend.
5. El summary clasifica la salud de la jornada como minimo en `HEALTHY | ATTENTION | BLOCKED`.
6. Cuando la jornada queda en `ATTENTION` o `BLOCKED`, el usuario puede abrir un detalle que explique las razones.
7. El `RouteTab` sigue siendo el workspace de ejecucion y no pierde ownership operativo.
8. No se agregan migraciones si toda la informacion sigue siendo derivable.
9. `OperationalSummaryInline` no incorpora acciones internas si eso contradice el contrato visual de `0024.3`; el detalle expandido se abre desde un wrapper shell compatible.

## Pruebas requeridas

1. pruebas backend para derivacion de `health_status`;
2. pruebas backend para contadores de stops e incidencias;
3. pruebas frontend para rendering inline de estados sanos, en atencion y bloqueados;
4. pruebas frontend para detalle expandido con razones visibles;
5. prueba manual de jornada con ruta normal, parcial, fallida y carta porte desactualizada.

## Notas para agentes

1. No implementar esta feature solo sumando mas datos estaticos al `OperationalSummaryInline` actual.
2. El valor de esta spec esta en resumir ejecucion real, no en repetir metadata de la jornada.
3. Preferir un payload backend dedicado antes que recomponer varias fuentes en frontend.
4. Mantener la regla fuerte del dominio: la operacion genera documentos; los documentos no gobiernan la operacion.
5. La arquitectura esperada queda explicitamente asi: `RouteOperation -> verdad`, `Movement -> efecto`, `Composition -> estado`, `Carta Porte -> documento`, `Incident -> desviacion`, `Correction -> reconciliacion`, `Summary -> lectura humana`.
