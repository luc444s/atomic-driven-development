---
id: "0025"
title: "Planificacion Calendar-First y Reserva de Capacidad"
domain: logistics
module: planificacion
status: propuesta
extends:
  - docs/specs/core/0024-1-1-jornadas-v1-1-consolidation.md
  - docs/specs/core/0024-1-2-vehicle-first-jornadas-projection.md
  - docs/specs/core/0020-logistics-planificacion-parciales.md
---

# SPEC 0025 - Planificacion Calendar-First y Reserva de Capacidad

## Estado

Propuesta

## Ajuste de vigencia

Esta spec reemplaza la interpretacion operativa de `Planificacion` definida en `SPEC 0024.1.1`.

Desde esta decision:

- `Jornadas` sigue siendo la consola de ejecucion viva;
- `Planificacion` vuelve a existir como dominio/superficie propia;
- `Planificacion` ya no se interpreta como simple borrador de jornada;
- `Planificacion` se interpreta como **reserva persistida de capacidad operativa** upstream a `Jornadas`.

No invalida el rol central de `Jornadas` para operar. Corrige solamente la separacion entre plan futuro y ejecucion real.

## Contexto

La UI actual de `PlanningPage` es transicional y responde a otra necesidad:

- stock disponible;
- pedidos pendientes;
- precargas;
- acciones auxiliares de planificacion.

Mientras tanto, `Jornadas` ya quedo consolidada como runtime operativo vivo del reparto.

El problema es que faltaba una capa clara para responder algo distinto a la ejecucion:

```text
que vehiculo reservo
en que ventana horaria
con que carga esperada
```

Sin esa capa, el sistema mezcla:

- intencion futura;
- capacidad comprometida;
- uso real del vehiculo;
- cierre operativo.

## Precision conceptual obligatoria

`Planificacion` no es solo calendario.

`Planificacion` es una **reserva de capacidad**:

```text
vehiculo + tiempo + carga esperada
```

Consecuencia:

1. el calendario es la superficie principal de UX;
2. la entidad de negocio no es un evento generico;
3. la disponibilidad no se mide solo por horario libre;
4. la reserva debe validar capacidad, compatibilidad y solapes antes de convertirse en jornada.

## Frase guia

**Calendar-first en UX. Capacity-first en dominio. Jornadas-first en ejecucion.**

## Objetivo

Definir un submodulo de `Planificacion` donde:

1. la entrada principal sea un calendario operacional;
2. cada bloque represente una reserva de capacidad por vehiculo;
3. el vehiculo muestre su `carga planificada` antes de tener jornada activa;
4. `Jornadas` siga siendo la entidad de operacion viva;
5. al cerrar una jornada, el uso real del vehiculo retroalimente la planificacion original;
6. el backend actual de `vehicles`, `routes`, `warehouses`, `planning` y `vehicle_sessions` se reutilice tanto como sea razonable.

## No objetivos

- No convertir `Planificacion` en un clon generico de Google Calendar.
- No mover ownership de stock a `Planificacion`.
- No reemplazar `VehicleSession` como owner del flujo vivo.
- No duplicar estado detallado de carga real dentro de la planificacion.
- No forzar que toda planificacion cree una jornada inmediatamente.
- No redisenar en esta spec toda la agenda comercial o de tareas de CRM.

## Modelo de dominio

### `CapacityReservation` / Planificacion

Nueva entidad operativa futura de planificacion.

Representa una reserva persistida de capacidad del vehiculo.

Campos minimos esperados:

- `id`
- `tenant_id`
- `vehicle_id`
- `origin_warehouse_id`
- `planned_start_at`
- `planned_end_at`
- `expected_load_summary`
- `expected_weight_total`
- `expected_volume_total` cuando aplique
- `service_type` o clasificacion operativa
- `route_id` opcional
- `driver_id` opcional
- `adr_required` derivado o persistido segun necesidad tecnica final
- `notes`
- `status`
- `conflict_reason` opcional
- `permit_override`
- `override_reason` opcional
- `linked_session_id` opcional
- `actual_start_at` opcional
- `actual_end_at` opcional
- `actual_load_summary` opcional y resumido

### Contrato minimo de `expected_load_summary`

No puede quedar como payload totalmente libre.

Contrato minimo esperado:

```json
{
  "total_products": 3,
  "total_units": 120,
  "total_weight_kg": 950
}
```

Puede extenderse luego con detalle por producto o grupo, pero este minimo debe mantenerse para consistencia entre frontend, backend, auditoria y validacion.

### `VehicleSession` / Jornada

Sigue siendo la entidad de ejecucion real.

No cambia su ownership:

- estado vivo;
- carga real;
- salida;
- ruta;
- retorno;
- conciliacion.

### Relacion oficial

```text
Planificacion (reserva futura)
    -> puede seguir como reserva
    -> puede materializarse -> Jornada pendiente
    -> puede dispararse -> Jornada viva
Jornada (ejecucion viva)
    -> al cerrar -> actualiza tiempos y resultado de la Planificacion
```

## Convivencia con jornadas pendientes

El sistema actual ya expone `Jornadas pendientes` por vehículo.

Esta spec las conserva, pero les da semantica mas precisa.

### Regla correcta

1. un vehículo puede tener `1` jornada viva usando realmente el vehículo;
2. puede tener `N` jornadas pendientes en cola para ese mismo vehículo;
3. puede tener `N` planificaciones futuras que todavía no se materializaron como jornada.

### Distincion obligatoria

#### `Planificacion`

Reserva de capacidad futura todavía no materializada en `VehicleSession`.

#### `Jornada pendiente`

`VehicleSession` ya creada o materializada para ese vehículo, no cerrada, excluyendo la activa, y esperando su turno de ejecución.

#### `Jornada viva`

Sesión que actualmente está usando el vehículo en runtime.

### Regla de disparo siguiente

Cuando termina la jornada viva/no cerrada en uso, la jornada pendiente más próxima debe quedar como siguiente candidata a dispararse.

La política exacta puede ser automática o asistida, pero la prioridad de la más próxima debe mantenerse.

## Regla de separacion

### `Planificacion`

Hace:

- reservar capacidad futura;
- bloquear o advertir conflictos de uso del vehiculo;
- mostrar ocupacion prevista por dia/semana/mes;
- registrar la carga esperada;
- servir como upstream para crear una jornada.

No hace:

- no representa inventario real;
- no ejecuta movimientos de stock;
- no confirma salida ni retorno;
- no reemplaza la conciliacion;
- no contiene el lifecycle vivo del reparto.

### `Jornadas`

Hace:

- ejecutar la operacion real;
- usar o materializar una planificacion previa;
- registrar tiempos reales;
- cerrar el uso del vehiculo.

No hace:

- no reemplaza la vista calendario de ocupacion futura;
- no absorbe otra vez toda la idea de plan futuro;
- no persiste el plan como si fuera solo un estado `DRAFT` interno cuando todavia no existe una ejecucion real.

## Relacion entre planificaciones y jornadas pendientes

No toda `Planificacion` debe convertirse inmediatamente en `Jornada pendiente`.

Secuencia permitida:

1. `Planificacion` futura en calendario;
2. materialización opcional a `Jornada pendiente` cuando el flujo operativo lo requiera;
3. disparo de esa jornada cuando quede libre el vehículo;
4. ejecución viva en `Jornadas`.

Esto evita confundir:

- reservas futuras;
- cola de jornadas ya preparadas;
- operación viva actual.

## Calendar-first en UX

La pantalla principal de `Planificacion` debe ser un calendario de recursos.

### Vista Mes

Sirve para:

- ocupacion general de vehiculos;
- saturacion por dias;
- huecos de capacidad;
- conflictos visibles;
- carga operativa por almacen o flota.

### Vista Semana

Sirve para:

- planificacion operativa principal;
- reasignaciones;
- comparacion de ventanas por vehiculo;
- visualizacion de carga planificada por bloque.

### Vista Dia

Sirve para:

- detalle fino por vehiculo;
- ventanas exactas de uso;
- capacidad reservada vs disponible;
- accion de activar o convertir a jornada.

### Regla visual obligatoria

Cada bloque del calendario representa una `Planificacion` real, no un recordatorio suelto.

Debe hacer visibles, como minimo:

- vehiculo;
- horario previsto;
- carga esperada resumida;
- estado;
- severidad de conflicto o saturacion;
- acceso a abrir/editar/activar.

## Vehicle-first + carga planificada

La entrada por vehiculo definida en `SPEC 0024.1.2` se mantiene y se enriquece.

Cada vehiculo debe poder mostrar:

1. jornada activa, si existe;
2. seccion de `Carga planificada` o `Planificaciones`; 
3. reservas futuras del dia o proximas ventanas;
4. historico resumido cuando aplique.

Esto no cambia el principio `vehicle-first`; lo completa con una capa upstream.

## Estados minimos de Planificacion

Estados sugeridos:

- `PLANNED`: reserva guardada y valida.
- `READY`: reserva suficientemente preparada para activarse.
- `IN_PROGRESS`: existe jornada viva asociada y el vehiculo esta en uso.
- `COMPLETED`: la jornada cerro y la reserva ya tiene uso real consolidado.
- `CANCELLED`: reserva anulada antes de ejecucion.
- `CONFLICT`: reserva persistida pero con incompatibilidad que requiere resolucion humana.
- `EXPIRED`: la ventana planificada ya termino y nunca se activo runtime real.

La implementacion puede ajustar nombres, pero no debe perder estas semanticas.

### Definicion fuerte de `READY`

`READY` significa:

- carga esperada valida;
- sin conflictos activos;
- datos minimos completos;
- vehiculo y ventana temporal listos para activacion.

Si falta cualquiera de estas condiciones, la planificacion no puede presentarse como `READY`.

### `conflict_reason`

Cuando `status = CONFLICT`, debe existir motivo explicito y machine-readable.

Valores minimos esperados:

- `TIME_OVERLAP`
- `CAPACITY_EXCEEDED`
- `ADR_INCOMPATIBLE`
- `VEHICLE_IN_USE`

## Reglas de negocio

1. Una planificacion debe quedar persistida; no vive solo en memoria UI.
2. Toda planificacion requiere `vehicle_id` y ventana temporal valida.
3. Toda planificacion requiere una forma de `expected_load_summary`, aunque sea resumida.
4. El vehiculo no puede quedar con reservas solapadas incompatibles.
5. La carga esperada no puede exceder capacidad declarada del vehiculo sin advertencia o bloqueo explicito.
6. Si el contexto es ADR, la planificacion debe advertir incompatibilidades antes de activarse.
7. Una jornada puede nacer desde una planificacion, pero una planificacion no equivale automaticamente a jornada.
8. Al iniciar la jornada asociada, la planificacion pasa a `IN_PROGRESS`.
9. Al cerrar la jornada, la planificacion debe registrar `actual_start_at`, `actual_end_at` y resultado final.
10. La planificacion no debe duplicar el detalle fino de movimientos o seriales; solo referencia o resume.
11. Si `planned_end_at < now` y no existe jornada asociada ni uso real, la planificacion debe pasar a `EXPIRED` o exponer un derivado equivalente `is_expired = true`.
12. Un vehículo puede tener múltiples `jornadas pendientes`, siempre que solo una esté usando realmente el vehículo en runtime.
13. La jornada pendiente más próxima debe priorizarse como siguiente disparo al terminar la jornada viva.

## Constraint formal de solapamiento

La proteccion contra doble booking no puede depender solo del frontend o de validaciones blandas.

Debe existir restriccion formal en base de datos equivalente a:

```sql
EXCLUDE USING gist (
  vehicle_id WITH =,
  tsrange(planned_start_at, planned_end_at) WITH &&
)
WHERE status IN ('PLANNED', 'READY', 'IN_PROGRESS')
```

Objetivo:

- impedir doble reserva activa del mismo vehiculo;
- cerrar condiciones de carrera;
- hacer consistente el dominio aun si existen multiples clientes o procesos.

La implementacion final puede ajustar nombres o usar `tstzrange` si los timestamps quedan timezone-aware, pero la semantica de exclusión es obligatoria.

## Politica de conflictos

### Conflicto temporal

Dos planificaciones del mismo vehiculo no pueden ocupar la misma ventana de uso sin resolucion explicita.

### Conflicto por capacidad

Aunque no exista conflicto temporal total, una planificacion debe advertir si la carga esperada excede:

- peso util;
- volumen;
- restriccion ADR;
- otras limitaciones declaradas del vehiculo.

### Conflicto por runtime vivo

Si existe una jornada activa del vehiculo:

- nuevas planificaciones en la misma ventana deben bloquearse o quedar en conflicto;
- el calendario debe reflejar que el vehiculo esta efectivamente en uso.

## Politica de override

El sistema debe contemplar override explicito para casos operativos excepcionales.

Campos minimos:

- `permit_override: boolean`
- `override_reason: string`

Reglas:

1. el override nunca puede ser silencioso;
2. debe quedar auditado con actor, fecha y motivo;
3. no reemplaza el constraint fuerte de base de datos cuando la colision es estructuralmente invalida;
4. sirve para conflictos advertibles o excepciones controladas, no para corromper la consistencia del sistema.

## Activacion hacia Jornada

Flujo objetivo:

```text
Crear planificacion
-> validar reserva
-> preparar contexto
-> activar
-> crear o vincular Jornada
-> operar en Jornadas
-> cerrar Jornada
-> actualizar uso real de la Planificacion
```

### Resultado esperado al activar

- se crea o vincula una `VehicleSession`;
- la planificacion conserva el link (`linked_session_id`);
- el usuario pasa desde calendario a la consola viva de `Jornadas`.

### Activacion atomica obligatoria

`POST /planning/reservations/{id}/activate` debe ejecutarse atomicamente.

Secuencia minima dentro de una sola transaccion:

1. lock de la planificacion;
2. revalidacion de conflictos y disponibilidad;
3. creacion de `VehicleSession` o vinculacion segura;
4. persistencia de `linked_session_id`;
5. cambio de estado a `IN_PROGRESS`;
6. commit.

Objetivo:

- evitar doble activacion;
- evitar dos jornadas para una misma planificacion;
- evitar que el link session/reservation quede parcial.

## Datos y ownership

### `Planificacion` puede persistir

- referencias (`vehicle_id`, `route_id`, `driver_id`, `origin_warehouse_id`);
- tiempos planificados y reales;
- resumen esperado/real de carga;
- flags de capacidad o ADR;
- notas y estado.

### `Planificacion` no puede volverse owner de

- inventario real;
- movimientos de stock;
- seriales confirmados;
- conciliacion final;
- lifecycle operativo de jornada.

## API y backend

### Reutilizar primero

- catalogos de `vehicles`, `warehouses`, `routes`;
- endpoints de `vehicle_sessions` para apertura y detalle;
- helpers actuales de planificacion/stock/preload cuando aporten contexto operativo;
- validaciones de capacidad/ADR ya existentes donde apliquen.

### Nuevo contrato esperado

Se espera una API propia de planificaciones de capacidad, por ejemplo:

- `GET /planning/calendar`
- `GET /planning/reservations`
- `POST /planning/reservations`
- `PATCH /planning/reservations/{id}`
- `POST /planning/reservations/{id}/activate`
- `POST /planning/reservations/{id}/cancel`

Los paths exactos pueden ajustarse, pero la separacion conceptual no.

## Permisos

No asumir permisos nuevos hasta definir el contrato final, pero la spec requiere como minimo separar:

- lectura de planificaciones;
- creacion/edicion de planificaciones;
- activacion hacia jornada;
- cancelacion/reprogramacion.

La implementacion debe seguir `tenant_id`, `branch_id` y `warehouse_id` segun `ADR 0003`.

## Eventos y auditoria

Toda accion importante debe ser auditable.

Eventos candidatos:

- `logistics.planning.reservation_created`
- `logistics.planning.reservation_updated`
- `logistics.planning.reservation_activated`
- `logistics.planning.reservation_completed`
- `logistics.planning.reservation_cancelled`

Minimo de auditoria:

- actor;
- tenant;
- vehiculo;
- ventana horaria;
- carga esperada/resumida;
- jornada vinculada si existe;
- resultado de activacion o cierre.

## Impacto en frontend

### Rehacer desde cero

Conviene rehacer casi por completo la UX de `PlanningPage`.

Se reemplaza la logica centrada en:

- tabla de stock;
- tabla de pedidos pendientes;
- tabla de precargas como centro de la experiencia.

### Reutilizar

- componentes shared UI;
- queries y contratos utiles;
- piezas de `Jornadas` para navegacion y activacion;
- tooling backend ya existente.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Convertir la spec en una agenda generica | alto | mantener `expected_load` y reglas de capacidad como requisito obligatorio |
| Duplicar ownership entre Planificacion y Jornadas | alto | fijar `Planificacion = upstream`, `Jornadas = runtime vivo` |
| Duplicar stock o movimientos | alto | limitar `Planificacion` a resumen y referencias |
| Rehacer frontend sin contrato de dominio claro | medio | cerrar primero modelo, estados y activacion |
| Mantener viva la pantalla actual como si fuera final | medio | marcarla como transicional y reemplazarla por calendario |

## Criterios de aceptacion

1. `Planificacion` existe como superficie propia distinta de `Jornadas`.
2. La pantalla principal de planificacion es un calendario operacional.
3. Cada bloque del calendario representa una reserva persistida de capacidad.
4. Cada reserva tiene como minimo vehiculo, ventana temporal y carga esperada.
5. El vehiculo muestra `carga planificada` o reservas futuras en su proyeccion principal.
6. El sistema distingue claramente entre `planificaciones`, `jornada activa` y `jornadas pendientes`.
7. Una planificacion puede activarse hacia jornada sin romper el flujo vivo actual.
8. Una jornada cerrada devuelve tiempos reales y estado final a la planificacion vinculada.
9. La planificacion no se vuelve owner de inventario ni de movimientos.
10. El sistema puede advertir conflictos de horario, capacidad y ADR antes de activar.
11. Existe constraint formal de no solapamiento para reservas activas del mismo vehiculo.
12. `READY` tiene definicion fuerte y verificable.
13. `conflict_reason` y `override_reason` permiten diagnostico y UX claros.
14. La activacion de planificacion a jornada es atomica.
15. El sistema distingue reservas vencidas no ejecutadas.
16. La jornada pendiente más próxima se reconoce como siguiente candidata tras el cierre de la jornada viva.

## Pruebas requeridas

1. unitarias para conflictos de solape temporal;
2. unitarias para validacion de capacidad esperada;
3. unitarias para transicion `PLANNED/READY -> IN_PROGRESS -> COMPLETED`;
4. integracion para activacion atomica de planificacion a jornada;
5. integracion para retroalimentacion de `actual_start_at` y `actual_end_at` al cerrar jornada;
6. integracion para constraint de no solapamiento en base de datos;
7. frontend para vistas dia/semana/mes y estados de conflicto.

## Modulos y archivos afectados esperados

- `plugins/logistics/frontend/pages/PlanningPage.tsx`
- `plugins/logistics/frontend/register.ts`
- `plugins/logistics/frontend/pages/VehicleSessionsPage.tsx`
- `plugins/logistics/backend/services/planning.py`
- `plugins/logistics/backend/router.py`
- futuros schemas y contratos de planificacion de capacidad

## Notas para agentes

1. No implementar desde esta spec una agenda generica sin semantica de capacidad.
2. No usar el calendario como excusa para duplicar el dominio de `Jornadas`.
3. No copiar ownership de stock, seriales o conciliacion a `Planificacion`.
4. Si hace falta una tabla nueva, debe modelar reserva de capacidad, no un evento UI vacio.
5. `SPEC 0024.1.1` debe leerse desde ahora como superada solo en la parte que absorbia `Planificacion` dentro de `Jornadas`.
