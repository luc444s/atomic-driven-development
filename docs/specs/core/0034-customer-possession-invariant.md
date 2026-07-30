---
id: "0034"
title: "Invariante de Posesión Cliente para Cilindros"
domain: logistics
module: envases
status: borrador
extends:
  - docs/specs/core/0021-cylinder-create-with-initial-movement.md
  - docs/specs/core/0031-route-serial-coherence.md
  - docs/specs/core/0033-route-operation-efectos-separados.md
---

# SPEC 0034 - Invariante de Posesión Cliente para Cilindros

## Estado

Borrador - v1

## Contexto

Se detectó un caso grave de incoherencia operacional: cilindros en estado `EN_CLIENTE_VACIO` o `EN_CLIENTE_LLENO` sin cliente trazable.

Ejemplo real observado:

- cilindro `HI-002077`
- estado `EN_CLIENTE_VACIO`
- `session_id` asociado a una jornada en `LOADING`
- sin registros en `lg_cylinder_ownership`
- sin registros en `lg_customer_cylinder_ledger`
- sin `state_log` útil para reconstruir el cliente

Este caso mostró dos cosas al mismo tiempo:

1. el seeder puede crear datos incoherentes porque el backend no protege el invariante;
2. el backend admite transiciones a estados `EN_CLIENTE_*` sin exigir ownership ni cliente trazable.

Por lo tanto, el problema principal no es el seed. El problema principal es un invariante de dominio no protegido en backend.

## Frase guía

**Un cilindro no puede estar “en cliente” si el sistema no puede decir en qué cliente está.**

## Objetivo

Endurecer el backend para que todo cilindro en estados de posesión de cliente:

- `EN_CLIENTE_LLENO`
- `EN_CLIENTE_VACIO`

quede siempre acompañado de trazabilidad mínima obligatoria:

1. cliente identificable;
2. ownership persistido;
3. evidencia operacional o documental que justifique la posesión;
4. consistencia de lectura para summary, traceability y route operations.

## No objetivos

- no rediseñar todo el modelo de contratos de envases;
- no reescribir el customer summary completo;
- no corregir automáticamente todos los datos históricos en esta spec;
- no mover ownership al frontend;
- no permitir “cliente implícito” por heurística silenciosa;
- no tratar el seeder como fuente de verdad de dominio.

## Alcance

Este cambio afecta:

- transiciones de cilindro hacia `EN_CLIENTE_*`;
- confirmación de movimientos que lleven cilindros a cliente;
- escaneo que cambie posesión de cliente;
- route operations que proyecten posesión de cliente;
- seed masivo y cualquier seed futuro;
- detectores/auditorías que ya reportan `ownership_inconsistent`.

## Reglas de negocio

### 1. Invariante principal

Si `current_state in {EN_CLIENTE_LLENO, EN_CLIENTE_VACIO}` entonces debe existir simultáneamente:

1. `customer_id` trazable por contexto de operación o movimiento;
2. un ownership vigente para ese cilindro;
3. un evento de posesión en `lg_customer_cylinder_ledger` o evidencia operacional equivalente;
4. una transición/state log que explique cómo llegó a cliente.

Si alguna de esas piezas falta, la operación debe fallar.

### 1.1 Definición de ownership vigente

En esta versión del modelo, `lg_cylinder_ownership` no usa flag `is_active`.

Por lo tanto, la definición canónica es:

```text
ownership vigente = último registro de lg_cylinder_ownership
por (change_date DESC, created_at DESC)
```

Consecuencias:

1. la lectura de ownership vigente debe ser determinista;
2. no se permite tener ambigüedad semántica entre múltiples registros “vigentes”;
3. cualquier validación de estados `EN_CLIENTE_*` debe usar exactamente esa definición.

### 2. No se permite transición directa ciega a `EN_CLIENTE_*`

La API o servicio no puede aceptar una transición a `EN_CLIENTE_LLENO` o `EN_CLIENTE_VACIO` solo con `to_state`.

Debe exigir contexto suficiente, por ejemplo:

- `movement_id` válido con `customer_id`;
- `route_operation` confirmada con delivery point/customer resuelto;
- `scan` con cliente/contrato/contexto explícito;
- otro contexto de dominio aprobado que identifique el cliente.

### 3. `session_id` no reemplaza al cliente

Asociar un cilindro a una `session_id` jamás es suficiente para justificar `EN_CLIENTE_*`.

Regla fuerte:

```text
session_id describe custodia operativa temporal
customer ownership describe posesion de cliente
no son intercambiables
```

### 4. Estados de cliente sin ownership deben considerarse datos inválidos

Todo cilindro existente en `EN_CLIENTE_LLENO` o `EN_CLIENTE_VACIO` sin ownership correcto debe clasificarse como inconsistencia crítica.

Eso ya aparece parcialmente en `customer_cylinder_summary`; esta spec lo convierte en invariante de backend, no solo en alerta de lectura.

### 6. Consistencia estado ↔ ownership

El ownership vigente debe ser consistente con el estado del cilindro.

Reglas:

1. si `current_state in {EN_CLIENTE_LLENO, EN_CLIENTE_VACIO}`:
   - debe existir exactamente un ownership vigente resoluble por la regla canónica;
   - ese ownership define el cliente actual del cilindro.
2. si `current_state not in {EN_CLIENTE_LLENO, EN_CLIENTE_VACIO}`:
   - no puede existir ownership vigente apuntando a una posesión actual de cliente sin que exista un estado `EN_CLIENTE_*` que lo respalde;
   - cualquier ownership previo debe entenderse como histórico.

### 6.1 Consistencia entre operación y ownership

El `customer_id` del ownership vigente debe coincidir con el cliente de la operación que puso el cilindro en `EN_CLIENTE_*`.

Regla fuerte:

```text
no puede existir cilindro en cliente A
con ownership vigente de cliente B
```

Si la operación intenta dejar `EN_CLIENTE_*` con un cliente distinto al ownership que terminaría vigente, la operación debe fallar.

### 6.2 Salida de cliente

Cuando un cilindro sale de `EN_CLIENTE_LLENO` o `EN_CLIENTE_VACIO`, el ownership previo debe dejar de representar posesión actual de cliente.

En este modelo, eso no implica borrar registros históricos.

Implica que:

1. el nuevo ownership vigente debe pasar a un contexto no cliente (por ejemplo `customer_id = NULL`, `customer_name = ALMACEN`) cuando el cilindro vuelve al control de almacén;
2. si el cilindro pasa a tránsito operativo (`EN_RUTA`) por recojo, el ownership vigente no puede seguir afirmando una posesión actual del cliente una vez que la operación de salida de cliente quedó confirmada;
3. la historia previa se conserva como ownership histórico por orden temporal.

Esto evita lecturas ambiguas con múltiples ownerships aparentemente activos.

### 5. El seeder debe obedecer el dominio

`seed_massive.py` y cualquier seed futuro:

- no pueden crear `EN_CLIENTE_*` con `customer_id` desconocido;
- no pueden asignar `session_id` aleatoria para simular “cliente”; 
- no pueden dejar ownership vacío si el cilindro queda en cliente;
- idealmente deben usar servicios de dominio o una rutina de siembra que materialice ownership + ledger + state log.

## Permisos

No requiere permisos nuevos.

Reutiliza permisos existentes de:

- transición de cilindros;
- movimientos;
- jornadas/ruta;
- escaneo.

## Eventos

No exige nuevos eventos para la primera implementación.

Pero refuerza que toda entrada a `EN_CLIENTE_*` debe seguir emitiendo o registrando al menos:

- `logistics.cylinder.ownership_changed`
- evidencia de transición de estado
- evidencia de posesión cliente

## Datos

Entidades involucradas:

- `lg_cylinders`
- `lg_cylinder_ownership`
- `lg_customer_cylinder_ledger`
- `lg_cylinder_state_log`
- `lg_movements`
- `lg_movement_items`
- `lg_vehicle_sessions`
- `lg_route_operations`
- `lg_delivery_points`

Archivos de seed/dominio involucrados:

- `apps/api/app/commands/seed_massive.py`
- servicios de transición/ownership/scan/route operations

## Migraciones

No requiere migración estructural obligatoria para la primera implementación.

Sí requiere:

- cleanup o diagnóstico masivo de datos inválidos existentes;
- posible script de reparación separado para cilindros `EN_CLIENTE_*` sin ownership.

Si luego se decide persistir un puntero explícito a “current_customer_id” en `lg_cylinders`, eso requerirá otra spec/migración.

## Auditoría y observabilidad

El sistema debe poder responder para cualquier cilindro en `EN_CLIENTE_*`:

1. en qué cliente está;
2. por qué evento/operación llegó ahí;
3. cuándo cambió;
4. qué ownership vigente lo respalda.

Y para cualquier cilindro fuera de `EN_CLIENTE_*` debe poder responder:

5. cuál fue el último ownership histórico de cliente;
6. qué evento lo sacó de posesión de cliente.

### Detector obligatorio

Debe existir verificación automática o consulta operativa para detectar:

- `EN_CLIENTE_*` sin ownership;
- ownership sin evento de posesión;
- `session_id` en estados de cliente sin cliente respaldado;
- seeds incoherentes.

Las inconsistencias deben clasificarse como `CRITICAL`.

## Riesgos

1. Endurecer transiciones puede romper flujos hoy tolerados pero incorrectos.
2. El seed masivo actual probablemente falle hasta ser alineado.
3. Puede aflorar volumen alto de datos inválidos históricos ya existentes.
4. Algunos tests actuales pueden asumir que un simple cambio de estado basta para simular “cliente”.
5. La salida de cliente en flujos de ruta puede requerir ajustar ownership en momentos donde antes solo se cambiaba `current_state`.

## Relación con el problema actual

Esta spec fija explícitamente que casos como `HI-002077` no deben poder existir.

Lectura correcta:

- si el seed genera `EN_CLIENTE_VACIO` sin ownership -> el backend debió rechazarlo;
- si una transición directa deja `EN_CLIENTE_VACIO` sin ownership -> el backend está débil;
- el seed es consecuencia de esa debilidad, no la causa primaria.

## Criterios de aceptación

1. Una transición a `EN_CLIENTE_LLENO` falla si no hay cliente/contexto trazable.
2. Una transición a `EN_CLIENTE_VACIO` falla si no hay cliente/contexto trazable.
3. Toda operación válida que deje un cilindro en `EN_CLIENTE_*` crea o actualiza `lg_cylinder_ownership` de forma que el ownership vigente coincida con el cliente de la operación.
4. Toda operación válida que deje un cilindro en `EN_CLIENTE_*` deja evidencia en `lg_customer_cylinder_ledger` o mecanismo equivalente definido.
5. Cuando un cilindro sale de `EN_CLIENTE_*`, el ownership vigente deja de representar posesión actual de cliente.
6. El seed masivo ya no puede dejar cilindros `EN_CLIENTE_*` sin ownership.
7. `customer_cylinder_summary` deja de depender solo de detección tardía; el backend previene la incoherencia en origen.
8. Un cilindro en `EN_CLIENTE_*` debe poder reconstruir su cliente actual desde datos persistidos sin heurísticas.

## Pruebas requeridas

1. test de integración: transición directa a `EN_CLIENTE_LLENO` sin cliente/contexto -> `400`.
2. test de integración: transición directa a `EN_CLIENTE_VACIO` sin cliente/contexto -> `400`.
3. test de integración: movimiento/scan/route path válido hacia `EN_CLIENTE_*` crea ownership.
4. test de integración: path válido hacia `EN_CLIENTE_*` registra ledger de posesión.
5. test de integración: salida de `EN_CLIENTE_*` deja ownership vigente consistente con un estado no cliente.
6. test de integración: ownership vigente nunca apunta a cliente distinto al de la operación que dejó el cilindro en cliente.
7. test de integración: seed o helper de seed no deja `EN_CLIENTE_*` sin ownership.
8. test de integración: detector reporta `CRITICAL` para datos históricos inconsistentes existentes.

## Notas para agentes

- no “arreglar” este problema solo parcheando el seed;
- el backend debe fallar duro ante estados `EN_CLIENTE_*` sin cliente trazable;
- no usar `session_id` como sustituto de `customer_id`;
- si hay que reparar histórico, hacerlo con script/plan explícito, no con lógica silenciosa en lecturas;
- cualquier ruta nueva que lleve cilindros a cliente debe entrar ya alineada con ownership + ledger.
