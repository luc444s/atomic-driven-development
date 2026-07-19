---
id: "0024.1.2"
title: "Vehicle-First Jornadas Projection — entrada por vehículo, ejecución por jornada"
domain: logistics
module: jornadas
status: vigente
extends:
  - docs/specs/core/0024-vehicle-session-stepper.md
  - docs/specs/core/0024-0-1-event-driven-stepper.md
  - docs/specs/core/0024-3-vehicle-session-hero-console.md
  - docs/specs/core/0024-1-1-jornadas-v1-1-consolidation.md
---

# SPEC 0024.1.2 — Vehicle-First Jornadas Projection

## Principio central

**El sistema gira alrededor de la operación real.**

- la unidad operativa visible es el `Vehicle`;
- la unidad de ejecución real es la `VehicleSession` (`Jornada`).

Esta regla no se rompe.

## Contexto

Las specs `0024`, `0024.0.1`, `0024.3` y `0024.1.1` ya consolidaron:

- el stepper como controlador del flujo;
- la jornada como consola operativa principal;
- la absorción UX de varios submódulos dentro de `Jornadas`.

Sin embargo, la entrada del sistema sigue partiendo desde la lista de jornadas.

Eso todavía obliga al usuario a pensar primero en sesiones, cuando en la operación real piensa primero en **vehículos**.

La siguiente evolución no cambia el backend ni el dominio. Cambia la **proyección principal de entrada**.

## Frase guía

**No cambié el sistema. Cambié la forma en la que el usuario entra a él.**

## Objetivo

Definir una arquitectura de UX donde:

1. la entrada principal de `Jornadas` sea una vista por `Vehículo`;
2. cada card represente un vehículo más el resumen de sus jornadas;
3. `VehicleSession` siga siendo la entidad ejecutable del día;
4. el backend actual se mantenga estable;
5. la UI sea una proyección agrupada por `vehicle_id`, no una reinvención del dominio.

## Modelo final

### Dominio principal visible

```text
Vehicle
```

### Entidad operativa ejecutable

```text
VehicleSession
```

### Relación real

```text
1 vehículo
 ├ 0 o 1 jornada activa
 ├ N jornadas pendientes
 └ N jornadas históricas
```

## Invariante crítica

Un vehículo solo puede tener **1 jornada no cerrada**.

Esto no se redefine en frontend.

La UI solo lo proyecta.

## Responsabilidades

### `Vehicle` (estable)

Hace:

- identidad operativa (`plate`);
- configuración básica;
- punto de entrada visible del sistema.

No hace:

- no contiene estado operativo del día;
- no posee lógica de flujo;
- no reemplaza la jornada.

### `VehicleSession` / `Jornada` (operativa)

Hace:

- estado (`DRAFT -> CLOSED`);
- flujo controlado por stepper;
- ejecución del día;
- carga, ruta, retorno, conciliación.

### `Stock` (se mantiene igual)

Hace:

- balances;
- movimientos;
- trazabilidad;
- ownership técnico de inventario.

Relación:

```text
Jornada -> dispara acciones
Stock   -> ejecuta y es dueño
```

### Dominios fuertes que no se rompen

- `Envases`
- `Contratos`
- `Almacenes`
- `Equipos`

### Upstream opcional

- `Pedidos` permanece opcional / no absorbido en esta spec.

## Estructura lógica

### Backend

Se mantiene:

```text
vehicle_sessions (tabla actual)
vehicles (tabla actual)
```

### No crear

- no event sourcing;
- no nuevas tablas complejas;
- no snapshots persistidos nuevos;
- no refactor masivo de backend.

## Proyección principal

La vista principal de entrada debe ser:

```text
Vehículos (cards)
```

Cada card representa:

- vehículo;
- estado de jornada activa si existe;
- cantidad de jornadas pendientes;
- cantidad de jornadas históricas.

## Contenido mínimo de la card de vehículo

Cada card debe mostrar como mínimo:

- placa;
- badge o frase de estado operativo actual;
- resumen de jornada activa si existe;
- contador de pendientes;
- contador de históricas;
- acción principal de abrir.

Ejemplo conceptual:

```text
TRK-123
Jornada activa: Cargando
Pendientes: 1
Históricas: 8

[ Abrir ]
```

## Navegación

### Entrada principal

```text
Vehículos -> Card -> Abrir
```

### Dentro del vehículo

La vista del vehículo debe mostrar:

1. jornada activa (si existe);
2. lista de jornadas pendientes;
3. lista de jornadas históricas.

## Flujo operativo

No cambia.

```text
DRAFT
↓
LOADING
↓
READY_TO_DEPART
↓
OUTBOUND
↓
RETURNING
↓
AWAITING_RECONCILIATION
↓
CLOSED
```

Controlado por:

```text
SessionStepper
```

## Principio de minimalismo técnico

- no cambiar backend;
- no duplicar datos;
- no recalcular lógica de negocio;
- solo cambiar proyección principal de UI.

## Queries

### Base

La fuente puede seguir siendo:

```sql
SELECT * FROM vehicle_sessions
```

### Agrupación

Permitido:

- agrupar en frontend por `vehicle_id`; o
- exponer luego un agregado backend simple si hace falta performance.

### Derivados UI

```text
activa = status IN (
  DRAFT,
  LOADING,
  READY_TO_DEPART,
  OUTBOUND,
  RETURNING,
  AWAITING_RECONCILIATION
)

pendientes = sesiones no cerradas EXCLUYENDO la activa

históricas = status == CLOSED
```

La UI no inventa más semántica que esa sin decisión explícita.

## Orden dentro del vehículo

La proyección por vehículo debe ordenar sus jornadas así:

1. jornada activa (si existe);
2. jornadas pendientes, más recientes primero;
3. jornadas históricas, más recientes primero.

Esto evita ambigüedad en la apertura y mantiene consistencia visual.

## Fallback cuando no hay jornada activa

Si un vehículo no tiene jornada activa:

```text
mostrar CTA: Crear jornada
```

Ese CTA debe abrir el flujo normal de creación de jornada.

No se inventa un modo alterno especial.

## Reglas que no se pueden romper

1. un vehículo tiene máximo una jornada activa;
2. el backend sigue siendo dueño del estado;
3. la UI no inventa lógica;
4. no duplicar datos de otros dominios;
5. el stepper sigue siendo el único controlador de estado;
6. las cards son solo proyección.

## Validación de la invariante

La regla de una sola jornada activa por vehículo se valida en backend.

El frontend:

- no intenta resolver conflictos;
- no intenta reconciliar múltiples activas;
- no inventa fallback si la invariante se rompe.

Si existiera conflicto, debe tratarse como error de integridad/backend.

## Lo que esta arquitectura NO hace

- no event sourcing;
- no microservicios;
- no nuevos modelos complejos;
- no refactor masivo del core del dominio.

## Lo que esta arquitectura sí hace

- cambia el punto de entrada;
- alinea la UI con la operación real;
- simplifica la experiencia de uso;
- mantiene estable el sistema actual.

## Nombre arquitectónico

```text
Projection-driven UX over stable domain
```

## Arquitectura objetivo de frontend

```text
VehicleCardsPage (o evolución de VehicleSessionsPage)
  -> VehicleCard[]
       -> vehicle summary
       -> active session summary
       -> pending count
       -> historical count
       -> open vehicle action

VehicleDetailProjection
  -> active session block
  -> pending sessions list
  -> historical sessions list

VehicleSessionDetailPage
  -> hero console existente
  -> session stepper
  -> modales operativos
```

## Implementación incremental propuesta

### Paso 1 - Cambiar la proyección principal de `VehicleSessionsPage`

- dejar de listar jornadas planas como tabla principal;
- agrupar jornadas por `vehicle_id`;
- renderizar cards por vehículo.

### Paso 2 - Definir el agregado visual por vehículo

- calcular jornada activa;
- calcular pendientes;
- calcular históricas;
- mostrar resumen operativo mínimo.

### Paso 3 - Definir apertura por vehículo

- click en card o botón `Abrir`;
- si hay jornada activa, mostrarla primero;
- si no hay activa, mostrar lista de jornadas del vehículo.

### Paso 4 - Mantener `VehicleSessionDetailPage` como unidad ejecutable

- no romper `SessionStepper`;
- no alterar la lógica de flujo.

### Paso 5 - Si hace falta, agregar agregación backend simple

Solo si la performance o la complejidad del frontend lo exige.

No es requisito inicial.

### Regla de performance

Para inicio, la agrupación por `vehicle_id` puede hacerse en frontend.

Si el volumen supera aproximadamente:

```text
> 1000 sesiones
```

la agregación debe moverse a un endpoint backend simple, sin cambiar el dominio.

## Riesgos reales

### 1. Meter estado operativo dentro de `Vehicle`

Sería un error. `Vehicle` es estable, no la entidad del flujo diario.

### 2. Duplicar estado en cards

La card no debe persistir ni derivar más de lo necesario.

### 3. Perder la jornada como unidad ejecutable

La entrada cambia, pero el flujo real sigue ocurriendo dentro de `VehicleSession`.

### 4. Recalcular lógica de negocio en frontend

La UI solo agrupa y resume. No redefine reglas del backend.

### 5. Forzar backend nuevo demasiado pronto

La agrupación puede empezar en frontend. No hace falta crear endpoints complejos en esta fase.

### 6. Dejar crecer demasiado la card de vehículo

Si la card empieza a absorber demasiada información, deja de ser proyección y se convierte en dashboard desordenado.

## Señales de fallo

- la card empieza a mostrar estado que no existe en backend;
- `Vehicle` empieza a tener lógica de jornada en vez de ser identidad operativa;
- el usuario ya no entiende cuál es la jornada ejecutable;
- se agregan snapshots persistidos de UI innecesarios;
- la tabla de jornadas sigue siendo la verdadera entrada principal;
- la UI rompe la regla de una sola jornada activa por vehículo.

## Qué NO muestra la card

La card de vehículo no debe mostrar:

- stock;
- lista de operaciones;
- documentos;
- métricas detalladas.

La card resume y dirige.

No reemplaza ni la jornada ni otras vistas de detalle.

## Criterios de aceptación

- [ ] la entrada principal de la operación se vuelve una vista por vehículo
- [ ] cada vehículo muestra resumen de jornadas en una sola card
- [ ] la jornada activa, pendientes e históricas se distinguen con claridad
- [ ] `VehicleSession` sigue siendo la unidad ejecutable del flujo
- [ ] `SessionStepper` no cambia su rol
- [ ] no se crean nuevas tablas complejas
- [ ] no se duplican datos de otros dominios
- [ ] la UI respeta la invariante de una sola jornada activa por vehículo

## Archivos afectados

### Principalmente frontend

- `plugins/logistics/frontend/pages/VehicleSessionsPage.tsx`
- posible extracción a `VehicleCard.tsx`
- posible extracción a `VehicleProjectionDetail.tsx`
- `plugins/logistics/frontend/pages/VehicleSessionDetailPage.tsx` como destino de ejecución

### Posible apoyo posterior

- `plugins/logistics/frontend/api/sessions.ts`
- backend simple de agregación solo si hiciera falta más adelante

## Veredicto

Esta arquitectura es:

- correcta;
- minimalista;
- escalable sin romper nada;
- lista para implementación.
