---
id: "0024.1.3.3"
title: "Reconciliacion Controlada sobre Incidencias de Ruta"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-1-3-2-exchange-incidencias-y-progreso-real-de-stop.md
  - docs/specs/core/0024-1-3-1-route-operation-y-composicion-vigente.md
  - docs/specs/core/0024-1-3-carta-porte-operativa-en-jornada.md
---

# SPEC 0024.1.3.3 - Reconciliacion Controlada sobre Incidencias de Ruta

## Contexto

`SPEC 0024.1.3.1` fijo la base correcta:

- `VehicleSession` como aggregate root operativo;
- `RouteOperation` como hecho de calle;
- `Movement` como via obligatoria para tocar stock;
- `Composicion Vigente` como fuente downstream de `Carta Porte`.

`SPEC 0024.1.3.2` agrego el siguiente endurecimiento necesario:

- `EXCHANGE` guiado;
- incidencias operativas;
- progreso real de `RouteStop` derivado desde operaciones e incidencias.

Ese slice ya permite documentar desvio y visibilizarlo.

Pero todavia falta cerrar el circuito mas delicado de la calle:

```text
que pasa cuando una operacion confirmada fue real,
pero dejo una realidad actual incorrecta o incompleta
```

Ejemplos:

- se entregaron 3 y debian ser 2;
- se retiro menos de lo esperado;
- se entrego producto equivocado;
- la operacion quedo confirmada, pero la reconciliacion inventariable real exige una compensacion posterior.

Si el sistema responde editando la operacion confirmada o ajustando stock desde la incidencia, rompe la arquitectura ya fijada.

## Frase guia

**No corriges lo que paso. Registras lo que paso despues para que el resultado sea correcto.**

## Objetivo

Definir la reconciliacion controlada de desvíos operativos en ruta mediante:

1. incidencias con tipos explicitos y estados semanticos fuertes;
2. separacion entre incidencia documentada y correccion efectiva;
3. correccion siempre modelada como nueva `RouteOperation`;
4. trazabilidad completa desde la operacion original hasta la realidad vigente resultante.

## No objetivos

- no editar `RouteOperation` confirmadas;
- no permitir que una incidencia ajuste stock por si sola;
- no introducir un aggregate root nuevo fuera de `VehicleSession`;
- no mover `Carta Porte` hacia arriba en la cadena de verdad;
- no cerrar todavia toda la taxonomia de resultados de parada no inventariables;
- no rediseñar el stepper ni el shell general de jornada en esta spec.

## Problema exacto

Hoy el sistema ya puede modelar:

- una operacion confirmada de calle;
- una incidencia abierta;
- una incidencia resuelta;
- un progreso derivado por parada.

Sin embargo, todavia falta distinguir dos situaciones que son radicalmente distintas:

### 1. Incidencia explicativa sin efecto posterior

La calle produjo un desvio, pero no hace falta una compensacion inventariable.

Ejemplo:

- el operador confirma una diferencia observada, se documenta y se cierra como evidencia.

### 2. Incidencia reconciliable con efecto posterior

La operacion confirmada ya no debe tocarse,
pero la realidad actual necesita una operacion compensatoria posterior.

Ejemplo:

- se entregaron 3 y debian ser 2 -> nueva `PICKUP` correctiva de 1;
- se registro producto equivocado -> nueva operacion para retirar el producto incorrecto y/o entregar el correcto segun corresponda.

Sin esta distincion, la incidencia queda a mitad de camino:

```text
detecta el desvio
pero no modela como se reconcilia la realidad
```

## Decisión de dominio

## 1. La incidencia detecta, no corrige

`RouteIncident` no es la correccion.

`RouteIncident` representa la deteccion de una desviacion entre:

- lo que se esperaba operacionalmente;
- lo que quedo confirmado;
- lo que debe pasar despues para que la realidad vigente sea correcta.

Regla fuerte:

```text
Incident -> dispara decision
Decision -> crea nueva RouteOperation
```

No:

```text
Incident -> modifica stock
Incident -> edita operacion confirmada
```

## 2. Incident Correction es reconciliacion controlada

Este slice no debe entenderse como "arreglar el pasado".

Debe entenderse como:

```text
reconciliar controladamente la realidad presente
sin corromper la historia operacional
```

Eso acerca el modelo a un ledger:

```text
RouteOperation original
-> RouteIncident
-> RouteOperation correctiva
-> Movements
-> Composicion Vigente corregida
```

## 3. Documentos nunca gobiernan la operacion

Principio explicito:

**Los documentos nunca gobiernan la operacion. La operacion genera documentos.**

Cadena correcta:

```text
VehicleSession
-> RouteOperation
-> Movement
-> Composicion Vigente
-> Carta Porte
```

Nunca:

```text
Carta Porte
-> Route
-> VehicleSession
```

## 4. `CORRECTED` no equivale a `RESOLVED`

Una incidencia cerrada por documentacion no es lo mismo que una incidencia cerrada por compensacion operativa.

Por eso esta spec separa:

- `RESOLVED` = cerrada sin operacion correctiva;
- `CORRECTED` = cerrada mediante nueva `RouteOperation` confirmada.

## Invariantes obligatorios

1. Una `RouteOperation` confirmada es inmutable.
2. Una incidencia nunca genera `Movement` por si sola.
3. Una incidencia nunca cambia stock por si sola.
4. Una realidad corregida solo puede surgir de una nueva `RouteOperation` confirmada.
5. `CORRECTED` solo puede alcanzarse cuando existe `corrective_operation_id` y esa operacion esta `CONFIRMED`.
6. `RESOLVED` no puede implicar cambios de composicion.
7. `Carta Porte` solo reacciona si cambia la composicion vigente por una operacion correctiva confirmada.
8. La realidad vigente debe poder reconstruirse como secuencia de hechos, no como updates destructivos.

## Modelo conceptual

```ts
type RouteIncident = {
  id: string
  session_id: string
  route_stop_id?: string | null
  related_operation_id?: string | null

  type:
    | "QUANTITY_MISMATCH"
    | "WRONG_PRODUCT"
    | "EXCESS_DELIVERY"
    | "MISSING_PICKUP"

  status:
    | "OPEN"
    | "RESOLVED"
    | "CORRECTED"

  corrective_operation_id?: string | null
  notes?: string | null

  created_by: string
  created_at: string
  closed_by?: string | null
  closed_at?: string | null
}
```

### Significado de `type`

#### `QUANTITY_MISMATCH`

La cantidad confirmada y la cantidad operativamente correcta no coinciden.

#### `WRONG_PRODUCT`

Se confirmo un producto que no correspondia al resultado real esperado.

#### `EXCESS_DELIVERY`

Salio mas producto del que debia salir.

#### `MISSING_PICKUP`

No entro al camion parte o todo lo que debia recogerse.

## Ciclo de vida de la incidencia

```text
OPEN
-> RESOLVED
o
OPEN
-> CORRECTED
```

Reglas:

1. `OPEN -> RESOLVED` se usa cuando el desvio queda documentado y no exige compensacion operativa.
2. `OPEN -> CORRECTED` se usa cuando una nueva `RouteOperation` confirmada cerro la reconciliacion.
3. `CORRECTED` no puede alcanzarse desde una operacion `DRAFT`.
4. `RESOLVED` y `CORRECTED` son estados terminales para este slice.
5. Si la operacion correctiva se crea en borrador y no se confirma, la incidencia sigue `OPEN`.

## Relacion con `RouteOperation`

### Operacion original

La incidencia puede apuntar a la operacion que explico el desvio:

- `related_operation_id`

Esto responde:

1. que operacion confirmada dio origen a la divergencia;
2. que desvio se detecto sobre ella;
3. como se cerro despues.

### Operacion correctiva

La reconciliacion operativa debe expresarse como nueva `RouteOperation`.

Puede ser:

- `DELIVERY`
- `PICKUP`
- `EXCHANGE`

segun el efecto real necesario para compensar la realidad.

Regla fuerte:

```text
la operacion correctiva no reescribe la original
la complementa
```

## Relacion con `Movement`

La incidencia no toca inventario.

La operacion correctiva, una vez confirmada, sigue exactamente el mismo flujo ya aprobado:

```text
RouteOperation confirmada
-> Movement(s) confirmado(s)
-> Stock / posesion / composicion cambian
```

Eso evita caminos especiales o atajos por fuera del dominio principal.

## Relacion con `Composicion Vigente`

`Composicion Vigente` solo cambia si existe una nueva operacion correctiva confirmada.

Consecuencia:

- una incidencia `RESOLVED` no altera composicion;
- una incidencia `CORRECTED` si puede alterar composicion;
- el resultado vigente siempre se calcula desde la secuencia completa de operaciones confirmadas.

## Relacion con `Carta Porte`

`Carta Porte` sigue siendo downstream.

Reglas:

1. una incidencia `OPEN` no cambia `Carta Porte` por si sola;
2. una incidencia `RESOLVED` tampoco;
3. una incidencia `CORRECTED` puede dejar `Carta Porte` `OUTDATED` si la composicion cambio realmente;
4. el documento nunca decide como reconciliar la operacion.

## Progreso real de `RouteStop`

Esta spec no reemplaza `0024.1.3.2`, pero refina su semantica.

### Regla minima derivada

1. una incidencia `OPEN` reconciliable mantiene la parada en `PARTIAL` mientras no exista cierre suficiente;
2. una incidencia `RESOLVED` puede permitir volver a `COMPLETED` si no quedan incidentes abiertos y existe actividad confirmada aceptada;
3. una incidencia `CORRECTED` puede permitir volver a `COMPLETED` si la operacion correctiva ya quedo confirmada y no quedan incidentes abiertos;
4. la parada no debe mostrarse "todo verde" mientras la reconciliacion siga abierta.

## Frontera con resultados de parada no inventariables

`0024.1.3.2` abrio un catalogo mas amplio de desvio operativo.

Esta spec no intenta cerrar toda esa taxonomia.

En este slice, el foco esta en incidencias reconciliables mediante compensacion operacional.

Queda permitido que en evoluciones posteriores se separe con mas claridad:

- resultados de parada o falla operacional pura;
- incidencias reconciliables que pueden terminar en `CORRECTED`.

## Backend esperado

Se requiere soporte explicito para:

1. persistir `RouteIncident` con `type`, `status`, `related_operation_id` y `corrective_operation_id`;
2. resolver una incidencia sin efecto inventariable (`RESOLVED`);
3. lanzar una operacion correctiva desde el contexto de una incidencia abierta;
4. marcar una incidencia como `CORRECTED` solo al confirmar la operacion correctiva;
5. impedir reconciliaciones destructivas sobre operaciones ya confirmadas.

### Estrategia minima recomendada

Sin crear otro aggregate root:

1. el frontend abre la operacion correctiva desde una incidencia `OPEN`;
2. esa nueva operacion se crea como `RouteOperation` normal, con contexto de incidencia;
3. al confirmarse, el backend actualiza la incidencia a `CORRECTED` y guarda `corrective_operation_id` en la misma transaccion logica o con consistencia equivalente.

## Frontend esperado

`SessionRouteTab` o su evolucion inmediata debe distinguir dos salidas claras para una incidencia `OPEN`:

1. `Resolver`
2. `Corregir`

### `Resolver`

Cierra la incidencia como `RESOLVED` cuando el desvio no exige operacion compensatoria.

### `Corregir`

No edita la operacion original.

Abre un flujo de nueva `RouteOperation` precontextualizado con:

- la parada;
- la operacion relacionada;
- la incidencia origen;
- notas de reconciliacion.

## Auditoria y trazabilidad

Debe poder reconstruirse:

1. que operacion original ocurrio;
2. que incidencia se abrio;
3. si se resolvio sin compensacion o con correccion;
4. que operacion correctiva se confirmo;
5. que `movement(s)` materializaron esa correccion;
6. como cambio la composicion vigente despues.

Eventos/auditoria minima esperada:

- apertura de incidencia;
- resolucion sin correccion;
- confirmacion de operacion correctiva;
- cierre `CORRECTED` vinculado a la operacion correctiva.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| usar incidencia para tocar stock directo | critico | solo `RouteOperation -> Movement` puede alterar inventario |
| editar operacion confirmada para "corregirla" | critico | inmutabilidad obligatoria de confirmadas |
| marcar `CORRECTED` con operacion aun en borrador | alto | `CORRECTED` solo con correctiva confirmada |
| mezclar documento con owner operativo | alto | mantener `Carta Porte` estrictamente downstream |
| esconder reconciliacion en notas sin modelo explicito | alto | `type`, `status` y `corrective_operation_id` obligatorios |

## Criterios de aceptacion

1. existe una spec explicita para reconciliacion controlada de incidencias de ruta;
2. queda prohibido modelar la correccion como edicion de la operacion confirmada;
3. queda prohibido usar la incidencia para modificar stock o composicion directamente;
4. `RouteIncident` tiene tipos reconciliables explicitos;
5. `RouteIncident` distingue `OPEN`, `RESOLVED` y `CORRECTED`;
6. `CORRECTED` implica una nueva `RouteOperation` confirmada y trazable;
7. `Composicion Vigente` y `Carta Porte` solo reaccionan por la operacion correctiva, no por la incidencia sola;
8. queda explicito que los documentos nunca gobiernan la operacion.

## Dependencias

- `docs/specs/core/0024-1-3-carta-porte-operativa-en-jornada.md`
- `docs/specs/core/0024-1-3-1-route-operation-y-composicion-vigente.md`
- `docs/specs/core/0024-1-3-2-exchange-incidencias-y-progreso-real-de-stop.md`
- `plugins/logistics/backend/services/route_operations.py`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx`

## Archivos candidatos

- `plugins/logistics/backend/models/route_incidents.py`
- `plugins/logistics/backend/dto/route_operations.py`
- `plugins/logistics/backend/services/route_operations.py`
- `plugins/logistics/backend/routers/route_operations.py`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx`
- `apps/api/tests/test_logistics_vehicle_sessions_v1.py`
