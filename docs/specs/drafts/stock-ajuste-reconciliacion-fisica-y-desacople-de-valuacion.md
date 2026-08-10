---
id: "draft-stock-ajuste-reconciliacion-fisica"
title: "Stock Ajuste como Reconciliacion Fisica y Desacople de Valuacion"
domain: stock
module: stock
status: en_discusion
extends:
  - docs/specs/core/0016-2-stock-transactional-gaps.md
  - docs/specs/core/0029B-stock-bridge-transactional.md
  - docs/specs/core/0039-unit-cost-activo-para-ajustes-positivos.md
---

# SPEC (borrador) - Stock Ajuste como Reconciliacion Fisica y Desacople de Valuacion

## Estado documental

Este documento entra en discusion porque cuestiona una suposicion vigente en `0016.2` y `0039`:

- hoy `stock.adjust` se trata como entrada valorizada;
- este draft propone acotarlo a reconciliacion fisica;
- si se acepta, `0039` y la seccion `3.1` de `0016.2` deben marcarse como superadas o recortadas en alcance.

## Contexto

Hoy `stock` en el codigo hace dos trabajos a la vez:

1. contador fisico de inventario;
2. motor de valuacion (`unit_cost`, `total_cost`, `cost_after`).

Eso llevo a formalizar esta regla:

```text
adjust positivo -> necesita unit_cost
```

Primero como costo manual (`0016.2`), y luego como costo activo resuelto desde `productos` (`0039`).

Sin embargo, la necesidad operativa actual es distinta:

- `stock` debe reflejar subidas y bajadas de inventario;
- compras, ventas, llenado, devoluciones y otros flujos de dominio deben ser duenos de la regla economica;
- el ajuste manual no debe depender del costo maestro de `productos` para corregir diferencias fisicas de inventario.

## Frase guia

**`stock` cuenta existencias. Los modulos de negocio valorizan. `adjust` corrige fisico; no da de alta valor comercial por defecto.**

## Objetivo

Desacoplar de forma atomica el ajuste manual de `stock` respecto al costo activo de `productos`, sin romper el ledger ni la consistencia del costo promedio ya existente.

## No objetivos

- no eliminar `unit_cost`, `total_cost` ni `cost_after` del ledger actual;
- no reescribir compras, ventas, transferencias o devoluciones;
- no introducir todavia un modulo contable separado;
- no resolver todavia multiples metodos de costeo;
- no permitir altas desde cero sin politica de valuacion definida.

## Problema exacto

El estado actual acopla `adjust +` a una fuente externa de costo maestro:

```text
stock.adjust positivo
-> busca costo activo en productos
-> si no existe prod_costs.BASE activo
-> ERROR
```

Eso produce un problema de ownership:

1. una correccion fisica de inventario queda bloqueada por un dato comercial faltante;
2. `stock` termina dependiendo de `productos` para una operacion que el usuario entiende como conteo/reconciliacion;
3. se mezcla alta valorizada con ajuste operativo dentro del mismo caso de uso.

## Decision propuesta

### 1. Redefinir el significado de `adjust`

`POST /stock/adjust` pasa a significar:

```text
reconciliacion fisica manual del balance
```

No significa:

- compra;
- ingreso comercial;
- alta inicial valorizada;
- produccion / llenado valorizado.

Esos flujos deben seguir entrando por endpoints de dominio propios, con su politica de costo explicita.

### 2. Quitar dependencia de `prod_costs` en `adjust +`

`adjust_stock` deja de resolver costo activo desde `productos` como regla primaria.

Se elimina esta dependencia conceptual:

```text
stock.adjust -> productos.resolve_active_cost
```

### 3. Regla atomica nueva para `adjust +`

Para `quantity > 0`, la resolucion queda asi:

```text
si payload.unit_cost existe -> usarlo
si payload.unit_cost no existe y balance actual > 0 -> usar costo promedio actual del propio balance
si payload.unit_cost no existe y balance actual == 0 -> ERROR
```

Interpretacion:

- si el flujo dueno trae costo explicito, `stock` lo consume;
- si es reconciliacion de stock ya existente, `stock` conserva su promedio historico local;
- si se pretende crear stock desde cero sin costo explicito, el ajuste se rechaza porque eso ya no es una reconciliacion simple.

### 4. Ownership resultante

#### `stock`

- cantidad actual;
- trazabilidad de movimientos;
- costo derivado para consistencia del ledger;
- promedio historico del propio balance.

#### `productos`

- catalogo;
- identidad del producto;
- precios;
- costos maestros si el negocio quiere mantenerlos.

#### `compras` / `ventas` / `llenado` / otros dominios

- documento origen;
- costo o precio del hecho de negocio;
- politica economica del movimiento que luego impacta `stock`.

## Alcance del slice

### Backend

1. Cambiar `adjust_stock` para que no consulte `resolve_active_cost` cuando `quantity > 0`.
2. Reusar el balance bloqueado para resolver costo promedio local cuando aplique.
3. Mantener rechazo en `adjust +` con balance cero y sin `unit_cost` explicito.
4. Mantener `adjust -` como hoy, usando costo promedio del balance.

### Frontend

1. El modal de ajuste deja de presentar "costo activo de producto" como verdad primaria.
2. Si el sistema usa costo promedio del balance, debe explicarlo como contexto operativo.
3. Si el balance esta en cero y falta `unit_cost`, debe mostrarse error claro indicando que ese caso requiere flujo valorizado o costo explicito.

## Error esperado

Si se intenta `adjust +` con balance cero y sin costo explicito:

```text
No se puede crear stock desde cero con un ajuste sin costo explicito.
Usa un flujo valorizado o proporciona unit_cost.
```

## Riesgo que evita

Este cambio evita dos extremos incorrectos:

1. depender del costo maestro de `productos` para toda reconciliacion;
2. dejar entrar ajustes positivos sin costo y diluir artificialmente el promedio a cero.

## Riesgos nuevos

1. que se abuse de `adjust` para simular compras o altas iniciales;
2. que usuarios no distingan reconciliacion fisica vs ingreso valorizado;
3. que algunos flujos existentes hoy dependan implicitamente de `0039`.

## Mitigacion

1. endurecer copy y ayuda contextual del modal de ajuste;
2. dejar mensaje fuerte cuando `balance == 0`;
3. mantener endpoints valorizados separados (`purchase_in`, `return_in`, `transfer_in`, futuros flujos de llenado);
4. agregar tests de regresion para distinguir reconciliacion vs alta valorizada.

## Criterios de aceptacion

1. Ajuste positivo de producto con stock previo y sin `unit_cost` explicito -> usa costo promedio actual del balance y completa el ajuste.
2. Ajuste positivo de producto con stock previo y con `unit_cost` explicito -> usa el `unit_cost` provisto.
3. Ajuste positivo de producto sin stock previo y sin `unit_cost` -> se rechaza.
4. Ajuste positivo ya no falla por ausencia de costo activo en `prod_costs` cuando el producto ya tiene balance valorizado.
5. Ajuste negativo sigue funcionando con costo promedio del balance.
6. `stock` deja de consultar `productos` para resolver costo en `adjust +`.

## Impacto documental esperado si se acepta

1. `docs/specs/core/0039-unit-cost-activo-para-ajustes-positivos.md` -> marcar `superada por` o recortar a flujos valorizados no reconciliatorios.
2. `docs/specs/core/0016-2-stock-transactional-gaps.md` -> ajustar seccion `3.1` para distinguir:
   - `adjust` reconciliacion;
   - `purchase_in` / `initial` / `production_in` como entradas valorizadas.
3. `docs/avances/stock.md` -> actualizar la nota de que ajuste positivo toma costo activo de productos.

## Archivos tocados si se implementa

| Archivo | Cambio esperado |
|---|---|
| `plugins/stock/backend/services/operations.py` | cambiar fuente de `unit_cost` en `adjust +` |
| `plugins/stock/backend/router.py` / schemas | revisar copy y contrato segun mensaje final |
| `apps/api/tests/test_stock_plugin.py` | nuevos casos de reconciliacion positiva con y sin balance |
| `plugins/stock/frontend/...` | ajustar copy del modal y errores |

## Decision abierta de fase 2

Este draft no separa todavia ledger fisico y ledger economico.

Eso queda para una fase posterior, si el sistema confirma esta direccion:

1. `stock` como contador fisico y trazabilidad;
2. valorizacion como capa o dominio separado;
3. eventos de negocio que impactan a ambos segun corresponda.
