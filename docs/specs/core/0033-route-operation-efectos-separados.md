---
id: "0033"
title: "RouteOperation con Efectos Separados"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-1-3-1-route-operation-y-composicion-vigente.md
  - docs/specs/core/0024-1-3-3-reconciliacion-controlada-sobre-incidencias-de-ruta.md
  - docs/specs/core/0029B-stock-bridge-transactional.md
  - docs/specs/core/0031-route-serial-coherence.md
  - docs/specs/core/0032b-composition-from-serials.md
---

# SPEC 0033 - RouteOperation con Efectos Separados

## Estado

Borrador - v1

## Contexto

El sistema endurecio correctamente el bridge financiero en `SPEC 0029B`: un `IC` financiero ya no puede entrar a stock sin `origin_movement_id` y sin referencia al `sale_out` historico.

Ese cambio hizo visible una ambiguedad que ya existia en jornadas:

- `RouteOperation` modela la realidad de calle;
- `Movement` modela consecuencias inventariables/documentales;
- el flujo actual asumio que toda operacion operativa debe proyectarse de inmediato a un `Movement` con efecto financiero.

Ese supuesto falla en edge cases normales de ruta:

- recojo de vacio sin historia financiera trazable;
- intercambio parcial;
- correccion sobre incidencia;
- envase que vuelve a la jornada sin devolucion contable real.

El error observado en `PICKUP` no demuestra que el modelo global de `stock` este mal. Demuestra que la capa de `RouteOperation` todavia no separa bien sus efectos.

## Frase guia

**RouteOperation es la realidad. Movement es una consecuencia.**

## Objetivo

Redefinir `RouteOperation` como una entidad operativa independiente que puede generar efectos separados:

1. efecto fisico sobre cilindros;
2. efecto financiero sobre stock;
3. efecto documental/auditable sobre la jornada.

La meta es resolver los edge cases de ruta sin reescribir el modelo global de `stock`, sin crear un tipo artificial como `ICP`, y sin degradar las garantias de `SPEC 0029B`.

## No objetivos

- no redisenar el plugin `stock`;
- no cambiar el costeo global del gas;
- no reemplazar `VehicleSession` como aggregate root;
- no crear una segunda fuente de verdad persistida para `MobileStock`;
- no introducir un nuevo `movement_type` global en este slice;
- no volver a `adjust_stock` como fallback silencioso;
- no editar operaciones confirmadas de ruta.

## Alcance

Este slice afecta:

- `RouteOperation` y su confirmacion en jornadas;
- la decision de cuando una operacion de ruta genera o no `Movement`;
- `composition/current` como proyeccion de la realidad fisica vigente;
- auditoria y trazabilidad cuando una operacion no genera `Movement`.

Este slice no cambia el contrato base de `stock` para `sale_out`, `return_in`, `purchase_in`, `damage_out`.

## Decision de dominio

### 1. `RouteOperation` puede generar multiples efectos

Toda operacion confirmada de ruta debe evaluarse por efecto, no por traduccion rigida a `Movement`.

Modelo conceptual:

```ts
type RouteOperationEffects = {
  physical: boolean
  financial: boolean
  documentary: boolean
}
```

La clasificacion puede ser derivada por politica de dominio; esta spec no exige persistir flags nuevos en base de datos.

### 2. `Movement` deja de ser obligatorio para toda operacion de calle

`Movement` sigue siendo obligatorio cuando existe efecto inventariable o documento operativo que deba materializarse como movimiento.

Pero ya no es obligatorio para representar por si solo toda la realidad de ruta.

Regla fuerte:

```text
RouteOperation describe lo que paso.
Movement existe solo cuando una consecuencia inventariable o documental lo exige.
```

### 3. `PICKUP` no implica efecto financiero por defecto

`PICKUP` representa que un cilindro/envase vuelve fisicamente a la jornada o al control del vehiculo.

Por defecto:

- efecto fisico: si;
- efecto financiero: no;
- efecto documental: si.

Por lo tanto, un `PICKUP` puro:

- no requiere `origin_movement_id`;
- no ejecuta `return_in_stock` por defecto;
- no debe romper el bridge financiero;
- debe seguir siendo totalmente trazable.

### 3.1 Carrier fisico obligatorio del `PICKUP` puro

La identidad fisica del cilindro recogido no puede quedar implicita.

En este slice, el carrier fisico vigente sera `lg_load_serial_assignments` reutilizado como registro de presencia fisica en la sesion.

Reglas:

1. si un cilindro es recogido en ruta y pasa a estar bajo control de la jornada, debe existir un registro activo en `lg_load_serial_assignments` para esa `session_id`;
2. un `PICKUP` puro agrega o reactiva esa presencia fisica aunque no genere `Movement` financiero;
3. el registro debe quedar visible para composicion con `assignment_status = CONFIRMED`;
4. el cilindro recogido queda en estado `EN_RUTA` mientras sigue bajo control de la sesion en calle;
5. el retorno/descarga posterior sera quien lo lleve a `EN_ALMACEN_VACIO` fuera de calle.

Esto evita crear una fuente nueva de verdad fisica y mantiene una sola proyeccion de cilindros presentes en la sesion.

### 3.2 Discriminador explicito: `PICKUP` puro vs devolucion financiera real

Para una linea `IN`, el discriminador vigente de este slice sera:

```text
si existe origin_movement_id valido -> devolucion financiera real
si no existe origin_movement_id -> PICKUP puro (solo fisico)
```

Regla fuerte:

```text
nunca inferir efecto financiero desde operation_type
siempre evaluar condiciones de dominio concretas
```

No se permite inferir devolucion financiera solo por `operation_type = PICKUP` ni solo por `direction = IN`.

Cuando la operacion sea correctiva o de intercambio, la misma regla aplica por linea o por la porcion `IN` correspondiente.

### 4. La devolucion financiera real sigue existiendo y sigue siendo estricta

Cuando la operacion representa una devolucion financiera real de gas con historia trazable:

- efecto fisico: si;
- efecto financiero: si;
- efecto documental: si.

En ese caso el flujo financiero vigente de `SPEC 0029B` se mantiene intacto:

- `Movement` tipo `IC`;
- `origin_movement_id` obligatorio;
- `return_in_stock` con costo historico del `sale_out` original.

Esta spec no debilita `0029B`. La preserva, pero la acota solo a los casos financieros reales.

### 5. `DELIVERY` sigue con triple efecto

`DELIVERY` mantiene el comportamiento fuerte ya esperado:

- efecto fisico: si;
- efecto financiero: si;
- efecto documental: si.

Materializacion esperada:

- cambio de estado del cilindro;
- `sale_out_stock`;
- `Movement` tipo `SC`.

### 6. `EXCHANGE` se resuelve por linea/efecto, no como bloque magico

`EXCHANGE` no es un caso especial monolitico.

Debe poder descomponerse en al menos dos efectos:

- la parte `OUT` que puede generar `SC` + `sale_out`;
- la parte `IN` que puede ser solo fisica o puede convertirse en devolucion financiera real si existe historia trazable.

## Matriz operativa minima

| Caso | Efecto fisico | Efecto financiero | Efecto documental | Consecuencia esperada |
|---|---|---|---|---|
| `DELIVERY` | Si | Si | Si | `SC` + `sale_out_stock` |
| `PICKUP` puro | Si | No | Si | sin `Movement` financiero obligatorio |
| `REAL_RETURN` / devolucion real | Si | Si | Si | `IC` + `origin_movement_id` + `return_in_stock` |
| `EXCHANGE OUT` | Si | Si | Si | `SC` + `sale_out_stock` |
| `EXCHANGE IN` fisico | Si | No | Si | sin `return_in_stock` obligatorio |
| `EXCHANGE IN` financiero | Si | Si | Si | `IC` con origen |

## Reglas de negocio

1. Una `RouteOperation` confirmada es inmutable.
2. Una correccion no edita la operacion original; crea una nueva `RouteOperation`.
3. Ningun `PICKUP` puro debe requerir `origin_movement_id`.
4. Ninguna devolucion financiera real puede ejecutarse sin `origin_movement_id`.
5. `SPEC 0029B` sigue aplicando a todos los casos financieros `IC`.
6. La falta de `Movement` no puede implicar falta de trazabilidad.
7. Una operacion de ruta puede terminar con `movement_ids = []` y seguir siendo valida.
8. `composition/current` debe reflejar la realidad fisica de la jornada, no solo el ledger financiero.

## Ajustes obligatorios del slice

### 1. `composition/current` debe evolucionar a modelo mixto

Hoy la composicion ya no puede depender solo de `stk_balance` ni solo de la lectura simplificada actual.

Regla grabada en piedra de este slice:

```text
composition/current = verdad fisica de la jornada
no verdad financiera
```

Debe consolidar una verdad mixta:

- seriales/estado fisico para productos serializados o recogidos en ruta;
- stock para productos no serializados o agregados sin identidad fisica unitaria.

Regla minima:

```text
si una operacion fisica hace que un cilindro vuelva a la jornada,
ese cilindro debe aparecer en composition/current
aunque no haya ocurrido movimiento financiero
```

`SPEC 0032b` queda como base parcial valida, pero insuficiente para este caso: contar seriales asignados no alcanza si el recojo agrega realidad fisica nueva a la sesion sin asiento financiero asociado.

La implementacion de este slice debe ampliar la proyeccion para que `composition/current` reaccione a cambios de presencia fisica en sesion, no solo a balances ni a `movement_ids`.

Si `stock` y la presencia fisica de cilindros divergen, `composition/current` debe reflejar la presencia fisica.

### 2. Auditoria autonoma de `RouteOperation`

Si una operacion no genera `Movement`, debe seguir pudiendo auditarse de forma completa por si sola.

Toda confirmacion de `RouteOperation` debe dejar trazabilidad minima de:

- tipo de operacion;
- items y cantidades;
- stop/ruta/jornada afectada;
- efectos ejecutados (`physical`, `financial`, `documentary`);
- razon por la cual el efecto financiero fue omitido, si aplica;
- usuario, fecha y correlacion con incidencias/correcciones cuando corresponda.

Persistencia minima obligatoria:

- `effect_summary` debe quedar grabado en `audit_log.details` como superficie canonica estable;
- `financial_omission_reason` debe quedar grabado cuando no exista efecto financiero;
- esa evidencia no puede depender de recalcular reglas futuras sobre datos viejos.

## Permisos

No se requieren permisos nuevos en esta version.

Se reutilizan los permisos existentes de jornadas/ruta para:

- crear operacion de ruta;
- confirmar operacion de ruta;
- registrar y corregir incidencias.

## Eventos

No se exige un evento nuevo obligatorio para aprobar esta spec.

Si el runtime ya emite auditoria/eventos de confirmacion de jornada, deben ampliarse para incluir el resumen de efectos ejecutados.

En particular:

- una operacion con efecto financiero sigue encadenando eventos de `stock` via `Movement`;
- una operacion solo fisica debe emitir o registrar evidencia equivalente en la capa de `logistics`.

## Datos

Entidades y proyecciones involucradas:

- `RouteOperation`
- `RouteOperationItem`
- `VehicleSession`
- `Movement`
- `MovementItem`
- `lg_load_serial_assignments` y/o relacion fisica equivalente de cilindros en jornada
- `stk_balance` y `stk_ledger`
- `composition/current`

## Migraciones

No obligatorias en esta version si la politica de efectos se deriva desde:

- `operation_type`;
- contexto de la operacion;
- presencia o ausencia de referencia financiera valida.

Si la auditoria existente no soporta persistir `effect_summary` y `financial_omission_reason`, esa brecha si requerira una migracion o extension explicita del mecanismo de auditoria.

## Auditoria y observabilidad

Debe quedar registrado:

1. que operacion de ruta ocurrio;
2. que efectos se ejecutaron;
3. que efectos se omitieron;
4. por que se omitieron;
5. si existio o no `Movement` derivado;
6. si la composicion vigente cambio.

Los errores deben ser mas expresivos que hoy.

Ejemplo de error correcto:

```text
La operacion requiere devolucion financiera real pero no tiene origin_movement_id valido.
```

Ejemplo de no error correcto:

```text
PICKUP confirmado sin efecto financiero por politica operativa.
```

## Riesgos

1. Si `composition/current` no se adapta, los recojos fisicos desapareceran de la composicion visible.
2. Si la auditoria depende implicitamente de `Movement`, los `PICKUP` puros quedaran opacos.
3. Si se deja semantica ambigua entre `PICKUP` y devolucion financiera, volvera el mismo bug con otro nombre.
4. Algunos tests actuales pueden asumir que toda operacion confirmada tiene al menos un `movement_id`.

## Relacion con specs vigentes

### `SPEC 0029B`

Sigue vigente sin cambios para casos financieros.

### `SPEC 0024.1.3.1`

Queda superada en este punto la regla:

```text
cada RouteOperation confirmada debe quedar asociada a uno o mas movements reales
```

Nueva lectura vigente:

```text
RouteOperation puede confirmar sin Movement
si la realidad operativa no exige consecuencia financiera/documental via Movement

PICKUP -> efecto fisico obligatorio
PICKUP -> efecto financiero solo cuando aplique como devolucion real
```

### `SPEC 0031`

Se supera la asuncion:

```text
PICKUP -> return_in_stock
```

Nueva lectura vigente:

```text
PICKUP fisico != return_in financiero por defecto
```

### `SPEC 0032b`

Permanece vigente como base de composicion mixta, pero debe ampliarse para cubrir ingresos fisicos a jornada sin asiento financiero asociado.

### `SPEC 0024.1.3` Carta Porte operativa

Se amplian sus eventos causales y su hash operativo.

Nueva lectura vigente:

```text
MOVEMENT_CHANGED ya no es suficiente por si solo
PHYSICAL_COMPOSITION_CHANGED tambien debe desactualizar Carta Porte
```

El `operational_hash` no puede depender unicamente de `movement_ids`; debe reaccionar tanto a cambios financieros como a cambios fisicos de composicion en sesion.

Regla fuerte:

```text
Carta Porte depende de cambios financieros y cambios fisicos
```

## Criterios de aceptacion

1. Un `PICKUP` puro puede confirmarse sin `origin_movement_id` y sin error de `IC movement requires origin_movement_id`.
2. Un `PICKUP` puro no ejecuta `return_in_stock` por defecto.
3. Una devolucion financiera real sigue exigiendo `origin_movement_id` y sigue ejecutando `return_in_stock` con costo historico.
4. `DELIVERY` no cambia su comportamiento actual esperado.
5. `EXCHANGE` puede combinar lineas financieras y no financieras sin romper la confirmacion completa.
6. `composition/current` muestra la realidad fisica vigente de la jornada aunque parte de esa realidad no haya generado stock.
7. Una `RouteOperation` confirmada sin `Movement` sigue siendo totalmente auditable.
8. `Carta Porte` pasa a estado desactualizado cuando cambia la composicion fisica de la sesion aunque no existan `movement_ids` nuevos.
9. Ninguna implementacion de esta spec puede reintroducir fallback silencioso a `adjust_stock` para resolver el caso de ruta.

## Pruebas requeridas

1. test de integracion: `PICKUP` puro confirma sin `Movement` financiero.
2. test de integracion: devolucion real sigue fallando sin `origin_movement_id`.
3. test de integracion: devolucion real con origen valido ejecuta `return_in_stock`.
4. test de integracion: `composition/current` incluye cilindro recogido aunque no exista asiento financiero.
5. test de integracion: auditoria de `RouteOperation` persiste evidencia suficiente aun con `movement_ids=[]`.
6. test de integracion: `EXCHANGE` mixto no rompe la composicion ni la trazabilidad.
7. test de integracion: un `PICKUP` puro deja `Carta Porte` en estado `OUTDATED` por cambio fisico de composicion.

## Notas para agentes

- no resolver este problema creando un `movement_type` nuevo como atajo inicial;
- no debilitar `SPEC 0029B` para hacer pasar `PICKUP`;
- no usar `adjust_stock` como salida facil;
- atacar el bug en la capa de `RouteOperation`, no en todo el modelo global;
- tratar `composition/current` y auditoria como parte obligatoria del cambio, no como follow-up opcional.
