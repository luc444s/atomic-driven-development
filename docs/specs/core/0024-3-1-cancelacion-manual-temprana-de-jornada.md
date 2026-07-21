---
id: "0024.3.1"
title: "Cancelacion Manual Temprana de Jornada"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-3-vehicle-session-hero-console.md
  - docs/specs/core/0024-0-1-event-driven-stepper.md
---

# SPEC 0024.3.1 - Cancelacion Manual Temprana de Jornada

## Contexto

`VehicleSession` ya soporta cancelacion en backend:

- endpoint `POST /vehicle-sessions/{session_id}/cancel`;
- permiso `logistics.session.manage`;
- auditoria `vehicle_session.cancel`;
- evento `logistics.vehicle_session.cancelled`.

Tambien existe una regla de dominio clara:

```text
DRAFT / LOADING / READY_TO_DEPART -> CANCELLED
```

Sin embargo, la consola principal de jornada todavia no expone esta accion de forma visible.

Eso deja una brecha practica:

- el sistema sabe cancelar;
- el operador/administrador no puede hacerlo desde la interfaz principal.

## Frase guia

**Si una jornada aun no entro en ejecucion irreversible, la consola debe permitir anularla con claridad y trazabilidad.**

## Objetivo

Exponer la cancelacion manual de jornada temprana dentro de `VehicleSessionDetailPage` / `VehicleSessionConsole`, reutilizando el backend ya existente y sin alterar la regla de dominio actual.

## No objetivos

- no permitir cancelar jornadas `OUTBOUND`, `RETURNING`, `AWAITING_RECONCILIATION` o `CLOSED`;
- no cambiar la logica backend de cancelacion en este slice;
- no introducir un nuevo permiso;
- no convertir la cancelacion en accion primaria del stepper;
- no agregar un workflow de aprobacion extra.

## Decisión de dominio

## 1. La cancelacion sigue siendo excepcional y temprana

La cancelacion no compite con el flujo principal de la jornada.

Solo aplica cuando la jornada todavia no entro en ejecucion real irreversible.

Estados validos:

- `DRAFT`
- `LOADING`
- `READY_TO_DEPART`

Estados invalidos:

- `OUTBOUND`
- `RETURNING`
- `AWAITING_RECONCILIATION`
- `CLOSED`
- `CANCELLED`

## 2. La accion es manual y explicita

No debe dispararse desde el stepper como transicion principal.

Debe vivir como accion secundaria destructiva de la consola.

## 3. La UI debe confirmar antes de destruir

Como se trata de una accion destructiva y fuera del flujo principal, se permite `ConfirmDialog`.

Esto no contradice `0024.0.1`, porque la prohibicion de confirm dialogs aplica a transiciones primarias del stepper, no a cancelacion excepcional.

## Frontend

## Ubicacion

La accion debe vivir en `VehicleSessionConsole` como accion secundaria visible, no dentro de `OperationalSummaryInline` ni como CTA principal del stepper.

## Comportamiento

1. si la jornada esta en `DRAFT`, `LOADING` o `READY_TO_DEPART`, se muestra boton `Cancelar jornada`;
2. al click, se abre `ConfirmDialog` destructivo;
3. al confirmar, el frontend llama `cancelSession(sessionId)`;
4. al exito, se invalidan queries de la jornada y el snapshot vuelve con `status = CANCELLED`;
5. el stepper queda congelado en estado cancelado como ya define la linea `0024`.

## Backend

No requiere cambios de comportamiento.

Reutiliza:

- `POST /api/v1/plugins/logistics/vehicle-sessions/{session_id}/cancel`
- `logistics.session.manage`

## Auditoría y eventos

Se mantiene el contrato existente:

- auditoria `vehicle_session.cancel`
- evento `logistics.vehicle_session.cancelled`

## Riesgos

1. ubicar la accion como primaria y degradar la jerarquia operativa del stepper;
2. permitir visualizarla en estados donde backend igual la rechazaria, generando ruido;
3. esconderla en tabs o modales y perder operatividad administrativa.

## Criterios de aceptación

1. La consola muestra `Cancelar jornada` solo en `DRAFT`, `LOADING` y `READY_TO_DEPART`.
2. La accion pide confirmacion destructiva antes de ejecutar.
3. La accion reutiliza el endpoint backend existente.
4. Al cancelar, la UI refleja `CANCELLED` sin recargar manualmente la pagina.
5. La accion no aparece como CTA principal del stepper.

## Pruebas requeridas

1. prueba frontend de visibilidad por estado si existe cobertura de componentes;
2. validacion manual de cancelacion desde la pagina de jornada en estados tempranos;
3. confirmacion de que en estados no permitidos el boton no aparece.

## Notas para agentes

1. No reescribir la regla backend de cancelacion en este slice.
2. Si en el futuro se quiere cancelar jornadas en ruta, eso requiere nueva spec de negocio.
