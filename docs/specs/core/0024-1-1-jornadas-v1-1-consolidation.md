---
id: "0024.1.1"
title: "Jornadas v1.1 — consolidación operativa, absorción y ownership provisional"
domain: logistics
module: jornadas
status: vigente
extends:
  - docs/specs/core/0024-vehicle-session-stepper.md
  - docs/specs/core/0024-0-1-event-driven-stepper.md
  - docs/specs/core/0024-3-vehicle-session-hero-console.md
supersedes:
  - docs/specs/core/0024-1-vehicle-session-ui-architecture.md
---

# SPEC 0024.1.1 — Jornadas v1.1

## Contexto

`VehicleSession` ya dejó de ser solo un detalle de vehículo y empezó a comportarse como la superficie operativa real del reparto.

Con `0024`, `0024.0.1` y `0024.3` quedaron definidos:

- el stepper como eje del flujo;
- las transiciones guiadas por eventos reales;
- la consola hero con modales contextuales.

El siguiente problema ya no es visual sino arquitectónico: **qué módulos de logistics siguen vivos como owners y cuáles quedan absorbidos por `Jornadas` en la versión 1.1**.

La hipótesis operativa del usuario es clara:

> El 90% de la operación diaria se simplifica en jornadas.

Esta spec formaliza esa consolidación sin convertir `Jornadas` en un owner indiscriminado de todos los dominios.

## Frase guía

**Jornadas absorbe la operación. No absorbe automáticamente todo el ownership.**

## Objetivo

Definir para `Jornadas v1.1`:

1. qué submódulos quedan absorbidos como experiencia operativa;
2. qué dominios siguen existiendo como owners o maestros;
3. qué módulos quedan en estado provisional hasta nueva decisión;
4. que vehículos y rutas se crean/seleccionan desde la jornada sin obligar a mantenerlos como pantallas principales para el operador.

## Principios obligatorios

1. `Jornadas` es la superficie principal del trabajo diario.
2. Un módulo puede ser absorbido como UX sin desaparecer como concepto interno.
3. Los dominios maestros y de configuración no deben meterse dentro de `Jornadas` por comodidad visual.
4. `Movimientos` no es absorbible por `Jornadas`; pertenece a la capa técnica de stock.
5. Si un módulo está en duda, se deja provisional; no se fuerza una absorción prematura.
6. `Jornadas` puede consumir o disparar otros dominios sin volverse owner formal de todos.
7. `Jornadas` no persiste estado duplicado de otros dominios.
8. La consola principal debe reducir pantallas, no mezclar ownership de negocio.

## No objetivos

- No definir todavía la unificación final de `Pedidos`.
- No rediseñar la capa técnica de `Movimientos`, cuyo owner sigue siendo `stock`.
- No eliminar el módulo raíz `Logistics`.
- No mover toda la lógica estructural de `Almacenes`, `Envases`, `Equipos` o `Contratos` a `Jornadas`.
- No reescribir el modelo de datos completo en este slice.

## Definición de Jornadas v1.1

`Jornadas` pasa a ser el macro-módulo de ejecución operativa.

Su responsabilidad incluye el loop diario completo:

```text
borrador
-> selección/creación de vehículo
-> selección/creación de ruta
-> carga
-> salida
-> operación diaria
-> retorno
-> conciliación / recepción operativa
```

## Tabla oficial de módulos v1.1

| Módulo actual | Estado en v1.1 | Rol en v1.1 | Owner formal | Superficie principal |
|---|---|---|---|---|
| `Logistics` | se mantiene | módulo raíz | `logistics` | contenedor general |
| `Jornadas` | macro-módulo central | centro operativo diario | `jornadas` | principal |
| `Planificación` | absorbido | reemplazado por borrador de jornada | `jornadas` | eliminada como principal |
| `Agenda` | absorbido | contexto operativo dentro de jornada | `jornadas` | eliminada como principal |
| `Carga` | absorbido | contexto operativo dentro de jornada | `jornadas` | eliminada como principal |
| `Entregas` | absorbido | ejecución operativa dentro de jornada | `jornadas` | eliminada como principal |
| `Recepción` | absorbido | retorno/conciliación operativa | `jornadas` | eliminada como principal |
| `Rutas` | absorbido como UX | entidad derivada/reusable; se abre y crea desde jornada | `rutas` (ligero) | secundaria / embebida |
| `Vehículos` | absorbido como UX | se selecciona y crea desde jornada | provisionalmente `vehículos` | secundaria / embebida |
| `Pedidos` | en duda | posible upstream o parte del borrador | **por decidir** | provisional |
| `Movimientos` | fijo aparte | capa técnica de stock, no absorbible | `stock` | secundaria / técnica |
| `Almacenes` | se mantiene aparte | maestro/configuración | `almacenes` | secundaria |
| `Envases` | se mantiene aparte | dominio fuerte transversal | `envases` | secundaria |
| `Equipos` | se mantiene aparte | soporte/configuración | `equipos` | secundaria |
| `Contratos` | se mantiene aparte | dominio comercial/legal | `contratos` | secundaria |

## 1. Módulos absorbidos por Jornadas

### `Planificación`

En `v1.1` deja de ser la superficie principal.

Su equivalente operativo pasa a ser:

```text
Jornada en estado borrador
```

Eso implica:

- el operador ya no entra a una pantalla independiente para planificar el turno diario;
- prepara la operación directamente dentro de la jornada;
- el borrador de jornada reemplaza la necesidad de un paso externo de planificación manual para este flujo.

### `Agenda`

Queda absorbida como flujo operativo.

No se trata ya de una tabla separada de tareas para el usuario diario, sino del contexto que la jornada consume o resume.

### `Carga`

Queda absorbida completamente dentro de `Jornadas`.

No debe sobrevivir como superficie principal separada.

### `Entregas`

Se absorbe como ejecución diaria del reparto.

La entrega deja de sentirse como submódulo autónomo y pasa a ser acción dentro de la jornada.

### `Recepción`

Se absorbe como retorno, conteo y conciliación operativa de la jornada.

## 2. Rutas en v1.1

`Rutas` deja de ser la entrada principal del operador diario.
### Regla

La jornada puede:

- seleccionar una ruta existente;
- abrir el contexto de ruta desde la consola principal;
- crear una ruta nueva desde modal;
- usar esa ruta como parte de la jornada.

### Implicación arquitectónica

`Rutas` sigue existiendo como entidad reusable con owner ligero, pero su UX principal queda absorbida por `Jornadas`.

### Resultado

No desaparece como concepto, pero sí como punto de entrada primario para la operación diaria.

## 3. Vehículos en v1.1

`Vehículos` sigue el mismo patrón que `Rutas`, con una absorción aún más fuerte en la experiencia.

### Regla obligatoria

Desde `Jornadas` se debe poder:

- seleccionar un vehículo existente;
- crear un vehículo nuevo desde modal;
- asignarlo a la jornada sin salir del flujo principal.

### Interpretación

Para el operador diario, `Vehículos` ya no es módulo autónomo principal.

Su mantenimiento maestro puede seguir existiendo, pero la UX primaria queda dentro de `Jornadas`.

### Resultado

`Vehículos` queda absorbido como experiencia operativa dentro de `Jornadas v1.1`.

## 4. Módulos en duda

### `Pedidos`

`Pedidos` queda en estado **provisional**.

Todavía no se decide si será:

1. upstream externo que alimenta a `Jornadas`; o
2. parte absorbida del borrador de jornada.

### Regla provisional

En `v1.1`, `Jornadas` puede consumir `Pedidos`, pero no absorbe todavía su ownership.

### `Movimientos`

`Movimientos` **Queda en duda**.

En `v1.1` debe de mantenerse tal como esta

### Regla obligatoria

`Jornadas` puede disparar, resumir o consumir movimientos, pero no debe volverse owner de ese dominio.

La lógica de movimientos pertenece a la consistencia de stock e inventario, no al flujo visual de operación.

## 5. Módulos que se mantienen aparte

### `Almacenes`

Se mantiene fuera de `Jornadas` como dominio maestro y de configuración.

### `Envases`

Se mantiene aparte por ser dominio fuerte, transversal y no reducible solo al flujo diario de jornada.

### `Equipos`

Se mantiene aparte como soporte/configuración operativa.

### `Contratos`

Se mantiene aparte por pertenecer a un dominio comercial/legal, no al núcleo de operación diaria.

## 5.1 Regla de no duplicación de estado

`Jornadas` no debe persistir información que pertenece a otros dominios.

### Solo referencia

- `vehicle_id` para vehículos;
- `route_id` para rutas;
- movimientos vía `stock`;
- pedidos vía su owner cuando aplique.

### Prohibido

No persistir estado duplicado como:

```text
session.vehicle_name
session.route_path
session.stock_snapshot
```

### Permitido

Persistir únicamente referencias e identificadores necesarios para operar:

```text
vehicle_id
route_id
pedido_id (si aplica)
```

Los datos operativos se consultan desde su owner.

### Por qué

Esto evita:

- duplicación de datos;
- inconsistencias silenciosas;
- bugs invisibles;
- acoplamiento indebido entre operación e inventario.

## 6. Semáforo oficial v1.1

### Verde — absorbido por Jornadas

- `Planificación`
- `Agenda`
- `Carga`
- `Entregas`
- `Recepción`
- `Rutas` como UX
- `Vehículos` como UX

### Azul — sigue aparte como owner/soporte

- `Almacenes`
- `Envases`
- `Equipos`
- `Contratos`

### Amarillo — pendiente de decisión arquitectónica

- `Pedidos`

### Gris técnico — fijo fuera de absorción

- `Movimientos` (owner: `stock`)

## 7. Implicación UX

La navegación principal de logistics en `v1.1` debe reflejar esta jerarquía.

### Resultado esperado

`Jornadas` se convierte en la puerta principal de la operación.

Módulos absorbidos dejan de competir como menú principal diario.

### Esto implica

- `Jornadas` primero;
- `Rutas` y `Vehículos` embebidos o secundarios;
- `Agenda`, `Carga`, `Recepción`, `Entregas` dejan de presentarse como universos separados para el operador;
- `Pedidos` permanece visible solo si todavía se necesita como transición funcional;
- `Movimientos` permanece fuera de la absorción como capa técnica o superficie secundaria de trazabilidad.

## 8. Reglas para implementación v1.1

1. No crear duplicados de entidades maestras dentro de `Jornadas`.
2. `Jornadas` puede abrir modales de selección/creación para `Rutas` y `Vehículos`.
3. El borrador de jornada reemplaza la necesidad de `Planificación` como pantalla principal.
4. `Agenda`, `Carga`, `Recepción` y `Entregas` deben migrar a contextos internos del flujo de jornada.
5. `Pedidos` no debe eliminarse mientras su ownership siga en duda.
6. `Movimientos` no debe eliminarse ni absorberse: pertenece a `stock`.
7. `Jornadas` no persiste duplicados de estado de `Vehículos`, `Rutas`, `Stock` o `Pedidos`.
8. Si un módulo absorbido aún conserva pantalla standalone, esa pantalla pasa a ser secundaria o transicional, no principal.

## 9. Riesgos reales

### 1. Convertir Jornadas en monolito

Si `Jornadas` empieza a poseer la lógica estructural completa de todos los subdominios, se degrada la modularidad.

### 2. Eliminar demasiado pronto `Pedidos`

Forzar la absorción antes de entender su forma final generaría deuda estructural difícil de revertir.

### 3. Dejar que Jornadas se apropie de Movimientos

Si `Jornadas` empieza a poseer movimientos, duplica lógica de stock, rompe consistencia y acopla operación con inventario.

### 4. Mantener menús viejos sin jerarquía nueva

Si `Agenda`, `Carga`, `Recepción` o `Entregas` siguen compitiendo al mismo nivel que `Jornadas`, la consolidación queda a medias.

### 5. Duplicar creación de rutas/vehículos fuera y dentro de la jornada sin criterio

Debe haber una sola UX principal. Lo demás queda como soporte administrativo.

### 6. Duplicar estado de otros dominios dentro de Jornadas

Persistir `vehicle_name`, `route_path` o snapshots propios de stock dentro de jornada degradaría integridad y mantenimiento.

## 10. Señales de fallo

- el operador sigue entrando a `Planificación` para abrir un turno diario;
- `Agenda` sigue sintiéndose como módulo principal paralelo a `Jornadas`;
- `Carga`, `Recepción` y `Entregas` siguen como pantallas centrales del loop diario;
- no se puede crear o seleccionar vehículo desde `Jornadas`;
- no se puede crear o seleccionar ruta desde `Jornadas`;
- `Pedidos` se elimina antes de decidir su ownership final;
- `Jornadas` empieza a persistir o poseer `Movimientos`;
- `Jornadas` persiste `vehicle_name`, `route_path` o snapshots propios de stock;
- `Jornadas` empieza a reimplementar lógica maestra de almacenes/envases/contratos.

## 11. Criterios de aceptación

- [ ] `Jornadas` queda documentada como superficie principal de operación diaria
- [ ] `Planificación` queda reemplazada por borrador de jornada
- [ ] `Agenda`, `Carga`, `Entregas` y `Recepción` quedan absorbidas como flujo operativo
- [ ] `Rutas` puede seleccionarse y crearse desde `Jornadas`
- [ ] `Vehículos` puede seleccionarse y crearse desde `Jornadas`
- [ ] `Almacenes`, `Envases`, `Equipos` y `Contratos` permanecen aparte
- [ ] `Pedidos` queda explícitamente provisional
- [ ] `Jornadas` no persiste estado duplicado de otros dominios
- [ ] La jerarquía del producto refleja que `Jornadas` es el 90% de la operación diaria

## 12. Archivos y superficies afectadas

### Afecta principalmente

- `plugins/logistics/frontend/pages/VehicleSessionsPage.tsx`
- `plugins/logistics/frontend/pages/VehicleSessionDetailPage.tsx`
- `plugins/logistics/frontend/pages/VehiclesPage.tsx`
- `plugins/logistics/frontend/pages/RoutesPage.tsx`
- `plugins/logistics/frontend/pages/AgendaPage.tsx`
- superficies operativas relacionadas con carga/recepción/entrega

### Implica cambios futuros de navegación

- menú principal de logistics;
- entrypoints de operador diario;
- modales o flujos embebidos para crear/seleccionar ruta y vehículo;
- status documental de módulos absorbidos.

## 13. Nota de vigencia

Esta spec no reemplaza el comportamiento del stepper ni la consola hero definidos por:

1. `0024`
2. `0024.0.1`
3. `0024.3`

Los extiende con una capa nueva:

```text
 consolidación del mapa de módulos y ownership de Logistics v1.1
```
