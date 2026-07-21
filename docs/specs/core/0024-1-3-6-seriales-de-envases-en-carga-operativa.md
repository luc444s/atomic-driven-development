---
id: "0024.1.3.6"
title: "Seriales de Envases en Carga Operativa"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-1-3-5-stop-result-minimo-de-parada.md
  - docs/specs/core/0024-1-3-1-route-operation-y-composicion-vigente.md
  - docs/specs/core/0024-3-vehicle-session-hero-console.md
---

# SPEC 0024.1.3.6 - Seriales de Envases en Carga Operativa

## Contexto

La línea `0024.1.3.x` ya cerró la verdad operativa principal de `Jornadas`:

- `VehicleSession` como owner de la ejecución;
- `RouteOperation` como verdad de calle;
- `Movement` como efecto inventariable;
- `CurrentComposition` como estado derivado;
- `StopResult` y `OperationalSummary` como lectura operativa más humana.

Sin embargo, la carga operativa todavía trabaja principalmente a nivel producto/cantidad.

Eso deja un vacío cuando se necesita operar con envases serializados:

- elegir exactamente qué cilindros suben a la jornada;
- capturarlos rápido con scanner o celular;
- impedir doble uso del mismo serial en dos jornadas;
- distinguir entre `seleccionado para esta jornada` y `efectivamente en ruta`.

Además, el volumen esperado puede llegar a cientos de miles de cilindros, por lo que un selector de exploración masiva no es aceptable como UX primaria.

## Frase guía

**Un serial elegido no está en ruta todavía. Solo está comprometido con una jornada hasta que la operación se confirma.**

## Objetivo

Agregar soporte de seriales de envases dentro de `Carga Operativa` con un flujo:

1. `scanner-first`;
2. `mobile-first`;
3. rápido para picking real;
4. consistente con la verdad de inventario y de jornada.

Para productos serializados, la captura de seriales debe ser obligatoria antes de confirmar la carga y antes de permitir avanzar a los siguientes pasos reales de la jornada.

## No objetivos

- no cambiar `lg_cylinders.current_state` a `EN_RUTA` solo por selección;
- no convertir el selector de seriales en catálogo masivo navegable;
- no reemplazar el flujo actual de productos/cantidades en una sola iteración;
- no cerrar todavía toda la UX handheld final de rutas;
- no usar `Carta Porte` como fuente de verdad del serial elegido.

## Problema exacto

Hoy la jornada puede decir:

- qué producto va cargado;
- cuánta cantidad se carga;
- cómo cambia la composición vigente;

pero no puede decir todavía, con suficiente precisión operativa:

- qué seriales exactos fueron comprometidos a esa carga;
- cuáles siguen libres;
- cuáles ya están ocupados por otra jornada o contexto;
- cuáles ya están realmente en ruta por confirmación previa.

Si al seleccionar un serial se lo marca directamente como `EN_RUTA`, el sistema adelanta una verdad que aún no ocurrió.

Eso rompería la arquitectura ya fijada:

```text
selección != hecho confirmado
```

## Decisión de dominio

## 1. Selección de seriales no cambia el estado real del envase

Elegir un cilindro serializado para una jornada no lo vuelve inmediatamente `EN_RUTA`.

Regla fuerte:

```text
seleccionado para jornada
!=
efectivamente en ruta
```

## 2. Se necesita una capa de compromiso operativo previa

Antes de la confirmación real, el serial debe quedar en un estado operativo derivado tipo:

- `ocupado`
- `asignado a jornada`
- `reservado para carga`

Esto es contexto operativo, no necesariamente `current_state` raíz del cilindro.

## 3. `EN_RUTA` solo nace desde confirmación operativa

Un cilindro puede pasar a `EN_RUTA` solo cuando la carga/salida correspondiente ya quedó confirmada dentro del flujo operativo aprobado.

La transición exacta se alinea con el hecho real, no con la intención de selección.

## 4. El flujo principal debe ser `scanner-first`

La UX principal no debe ser una grilla masiva.

Debe partir de:

1. scanner físico como teclado;
2. celular como terminal de captura;
3. input de serial manual como fallback;
4. búsqueda puntual como excepción.

## 5. La exploración masiva queda fuera del camino principal

Con cientos de miles de cilindros, la exploración visual de todos los seriales no es razonable.

La selección manual debe ser:

- acotada;
- filtrada;
- secundaria al escaneo.

## 6. La obligatoriedad vive en `Carga Operativa`

La captura de seriales no es un ajuste cosmético ni una tarea documental posterior.

Debe formar parte del cierre de `Carga Operativa`.

Regla fuerte:

```text
producto serializado sin seriales completos
=
carga incompleta
```

Consecuencia:

1. el usuario puede preparar otras partes del flujo;
2. pero no puede confirmar la carga si faltan seriales requeridos;
3. por lo tanto tampoco debe avanzar al siguiente paso real de la jornada mientras la carga serializada siga incompleta.

## Invariantes obligatorios

1. Un serial seleccionado para carga no cambia a `EN_RUTA` por ese solo hecho.
2. Un serial ocupado por otra jornada/contexto no puede seleccionarse.
3. La disponibilidad operativa del serial debe derivarse en backend.
4. El frontend no debe decidir solo por color si un serial es seleccionable.
5. El producto sigue siendo el primer eje del flujo; el serial refina, no reemplaza, la línea de carga.
6. El selector principal de seriales debe funcionar bien en móvil.

## Modelo conceptual

```ts
type SessionLoadSerialAssignment = {
  id: string
  session_id: string
  product_id: string
  cylinder_id: string
  cylinder_serial: string

  assignment_status:
    | "SELECTED"
    | "CONFIRMED"
    | "RELEASED"

  selected_by: string
  selected_at: string
  confirmed_by_operation_id?: string | null
  confirmed_at?: string | null
  released_at?: string | null
  release_reason?: "MANUAL" | "TIMEOUT" | "OPERATION_CANCELLED" | null
}
```

### Significado mínimo

- `SELECTED`: comprometido con la jornada, pero no todavía `EN_RUTA`.
- `CONFIRMED`: la carga/operación correspondiente ya lo volvió parte real de la jornada.
- `RELEASED`: se liberó de la selección sin consumar la carga.

### Constraint fuerte obligatorio

Debe existir una restricción efectiva equivalente a:

```text
UNIQUE(cylinder_id)
WHERE assignment_status IN ('SELECTED', 'CONFIRMED')
```

Objetivo:

```text
un mismo cilindro no puede quedar comprometido en dos jornadas activas a la vez
```

## Relación con `Envases`

Dentro del módulo de envases, el cilindro conserva su estado real principal.

Además puede mostrar contexto operativo secundario:

- libre;
- ocupado en jornada;
- en ruta confirmada.

Regla:

```text
estado real del cilindro = dónde está de verdad
contexto operativo = en qué jornada está comprometido
```

### Disponibilidad derivada

La disponibilidad operativa del cilindro no debe resolverse desde un flag manual suelto.

Debe comportarse como derivación de backend.

Ejemplo conceptual:

```text
is_available =
  NOT EXISTS active_assignment
  AND current_state compatible
```

Donde `active_assignment` significa al menos `SELECTED` o `CONFIRMED` vigente.

## Relación con `Load`

La selección de seriales debe vivir dentro de `Carga Operativa`.

No como pantalla aparte.

El flujo queda:

```text
producto elegido
-> abrir selector de seriales
-> escanear / capturar seriales
-> confirmar selección
-> luego confirmar carga real
```

### Regla de obligatoriedad por línea

1. si el producto no es serializado, la línea sigue operando por cantidad;
2. si el producto es serializado, la línea no queda completa hasta capturar todos los seriales requeridos;
3. la cantidad planificada/confirmada de la línea serializada debe poder reconciliarse con la cantidad de seriales seleccionados válidos.

## Relación con `CurrentComposition`

La composición vigente sigue siendo derivada.

Los seriales enriquecen el detalle operativo, pero no reemplazan la regla de composición por hechos confirmados.

## Relación con futura `Carta Porte v2`

Este slice es preparatorio para `0024.1.4`.

Su valor es dejar claro:

- qué seriales fueron solo seleccionados;
- cuáles quedaron realmente confirmados en la jornada.

Solo los confirmados deben poder entrar más adelante al snapshot documental enriquecido de `Carta Porte`.

## Frontend

## Flujo UX principal

1. el usuario elige producto;
2. pulsa `Seleccionar seriales`;
3. se abre un modal/workspace grande de captura;
4. el foco primario está en `Escanear o escribir serial`;
5. cada serial válido se agrega de inmediato a la selección;
6. el usuario confirma cuando llega a la cantidad objetivo.

## Principios UI

1. `scanner-first`;
2. `mobile-first`;
3. sin grilla masiva como vista principal;
4. búsqueda manual como respaldo usando `Combobox` compartido del core;
5. feedback inmediato por cada scan.

## Modal esperado

Debe incluir:

- producto actual;
- cantidad objetivo;
- contador seleccionados;
- input siempre enfocado para scanner;
- botón para escaneo con cámara cuando exista integración handheld;
- lista de seriales ya seleccionados;
- búsqueda puntual manual por serial mediante `Combobox` del core.

No debe cargar 300k registros para navegar.

## Estados visuales mínimos del serial

- `disponible`
- `ocupado`
- `seleccionado`

`en ruta` puede seguir existiendo como causa interna de `ocupado`, pero no necesita ser una categoría principal del picker visual.

## Backend

## Endpoints mínimos esperados

Ejemplo orientativo:

- `GET /vehicle-sessions/{id}/load-serials?product_id=...&query=...`
- `GET /vehicle-sessions/{id}/load-serials/selected?product_id=...`
- `PUT /vehicle-sessions/{id}/load-serials/select`
- `PUT /vehicle-sessions/{id}/load-serials/release`

## Reglas backend

1. la disponibilidad del serial debe resolverse server-side;
2. la selección debe ser idempotente;
3. el sistema debe impedir seleccionar un serial ya ocupado por otra jornada/contexto incompatible;
4. el backend debe distinguir `SELECTED` de `CONFIRMED`.
5. el backend debe impedir confirmar la carga si una línea serializada no tiene completos sus seriales requeridos.
6. al pasar a `CONFIRMED`, la asignación debe guardar `confirmed_by_operation_id` para poder reconstruir `serial -> RouteOperation -> Movement`.

### Concurrencia real de scanner

Caso crítico:

```text
dos usuarios escanean el mismo cilindro casi al mismo tiempo
```

La implementación debe resolver esto con una estrategia fuerte, por ejemplo:

1. `SELECT ... FOR UPDATE`; o
2. optimistic lock + retry controlado.

Regla fuerte:

```text
no se aceptan duplicados fantasma por carrera de escaneo
```

### Liberación de selección

`RELEASED` no debe ser opaco.

Debe registrar causa:

- `MANUAL`
- `TIMEOUT`
- `OPERATION_CANCELLED`

Esto mejora debugging, auditoría y lectura de por qué un serial dejó de estar comprometido.

## Performance

Con volúmenes altos de cilindros:

1. la búsqueda debe ser server-side;
2. no listar universos completos;
3. límite de resultados corto por consulta;
4. índices en serial, estado y disponibilidad operativa;
5. el scanner debe poder trabajar con lookups puntuales por serial exacto o prefijo.

## Permisos

Lectura y captura operativa heredan permisos de jornada/carga actuales.

Si en implementación aparece una separación clara de permiso, proponerla explícitamente.

## Migraciones

Sí requiere persistencia nueva si se modela la selección/compromiso de seriales.

No debe reciclarse una estructura vieja de ruta si contradice el ownership actual de `VehicleSession`.

## Riesgos

1. marcar seriales `EN_RUTA` demasiado temprano;
2. usar UI de exploración masiva para un problema de captura rápida;
3. permitir doble uso del mismo serial por jornadas concurrentes;
4. mezclar compromiso operativo con estado real del cilindro.

## Criterios de aceptación

1. el producto sigue siendo el primer eje de la carga operativa;
2. existe captura de seriales dentro de `Carga Operativa`;
3. la UX principal es `scanner-first`;
4. un serial seleccionado queda ocupado para la jornada sin volverse todavía `EN_RUTA`;
5. solo un hecho confirmado posterior puede llevar el serial a estado real de ruta;
6. el celular puede actuar como terminal de captura.
7. una carga con productos serializados no puede confirmarse si faltan seriales obligatorios.

## Pruebas requeridas

1. validación backend de disponibilidad y selección idempotente;
2. prueba de bloqueo de serial ya ocupado;
3. prueba de que `SELECTED` no implica `EN_RUTA`;
4. prueba de captura rápida de seriales en frontend cuando se implemente la UI.

## Notas para agentes

1. No resolver este slice marcando `EN_RUTA` desde la selección UI.
2. Priorizar consistencia de dominio sobre atajo visual.
3. Diseñar primero para escaneo rápido, no para exploración exhaustiva.
