---
id: "0039"
title: "Unit Cost Activo para Ajustes Positivos"
domain: stock
module: stock
status: borrador
extends:
  - docs/specs/core/0016-2-stock-transactional-gaps.md
  - docs/specs/core/0029B-stock-bridge-transactional.md
  - docs/specs/core/0015-productos-plugin/index.md
---

# SPEC 0039 - Unit Cost Activo para Ajustes Positivos

## Contexto

El endpoint `POST /stock/adjust` ya exige `unit_cost` cuando el ajuste es positivo.

Esa validación es correcta porque un ingreso manual de stock agrega no solo cantidad, sino también valor al inventario.

El problema actual no es la regla de negocio, sino la fuente del dato:

- `stock` exige `unit_cost`;
- `productos` ya es owner del costo activo (`prod_costs`);
- pero el flujo de ajuste todavía no está formalmente alineado para tratar ese costo activo como fuente canónica.

Hoy eso produce una experiencia incoherente:

- el sistema ya tiene costo en `productos`;
- pero el ajuste positivo puede terminar pidiéndolo como si no existiera o depender de ingreso manual sin contrato claro.

## Frase guía

**Si `productos` es dueño del costo, `stock` no debe inventarlo ni pedirlo como verdad primaria.**

## Objetivo

Formalizar una solución atómica ADD para ajustes positivos:

1. `unit_cost` se resuelve primero desde el costo activo del producto en `productos`;
2. `stock` consume ese valor como costo canónico de entrada;
3. si no existe costo activo resoluble, el sistema bloquea el ajuste con mensaje claro.

## No objetivos

- no rediseñar toda la valoración de stock;
- no cambiar transferencias ni salidas;
- no introducir un motor nuevo de costos;
- no duplicar costos dentro de `stock` como configuración paralela;
- no rehacer la UI completa de productos/costos.

## Problema exacto

En el estado actual, la regla funcional correcta ya existe:

```text
ajuste positivo -> necesita unit_cost
```

Pero falta singularizar la procedencia de ese dato.

Sin una fuente canónica explícita, el sistema corre el riesgo de caer en uno de estos dos errores:

1. pedir costo manual aunque `productos` ya tenga costo activo;
2. permitir que `stock` invente un costo desde otra fuente no dueña del dato.

## Decisión de dominio

### 1. Fuente canónica

Para `POST /stock/adjust` con `quantity > 0`, la fuente real de `unit_cost` pasa a ser:

1. costo activo del producto en `productos`;
2. si no existe costo activo válido, error y no continuar.

Regla fuerte:

```text
unit_cost de ajuste positivo
=
costo activo de productos
```

### 2. Ownership

`productos` mantiene ownership sobre el costo.

`stock` no calcula ni adivina el costo de ingreso a partir de:

- stock actual;
- promedio histórico implícito;
- último ledger de salida;
- cualquier heurística local.

### 3. Error operativo esperado

Si el producto no tiene costo activo resoluble, el ajuste debe rechazarse con mensaje claro de negocio.

Ejemplo esperado:

```text
El producto no tiene costo unitario activo. No puedes continuar.
```

## Alcance

### Backend

1. Extraer helper mínima para resolver costo activo del producto desde `prod_costs`.
2. Reutilizar la misma prioridad ya aceptada en `0029B` para entradas que necesitan costo.
3. En `adjust_stock`, cuando `quantity > 0`, resolver `unit_cost` automáticamente si el payload no lo trae explícito.
4. Si el costo activo no existe, bloquear con error claro.

### Frontend

1. El flujo de ajuste positivo debe mostrar el costo unitario resuelto desde `productos`.
2. La UI no debe presentar el costo como inventado por `stock`.
3. Si no existe costo activo, debe mostrarse un error claro y no dejar continuar.

## Regla de resolución

Para ajustes positivos, la resolución mínima queda así:

```text
si payload.unit_cost existe -> puede usarse solo si la política explícita del flujo lo permite
si no existe payload.unit_cost -> resolver costo activo desde productos
si productos no tiene costo activo -> ERROR
```

## Nota de diseño

Esta spec deja abierto si el payload manual puede sobrevivir como override administrativo.

Pero incluso si sobrevive, no reemplaza la fuente canónica:

```text
canon = productos
override = excepción explícita, no default implícito
```

## Archivos esperados

| Archivo | Cambio esperado |
|---|---|
| `plugins/productos/backend/services/pricing.py` o helper equivalente | resolver costo activo por producto |
| `plugins/stock/backend/services/operations.py` | usar costo activo en ajustes positivos |
| `plugins/stock/frontend/components/ModalAjusteStock.tsx` | mostrar/consumir costo activo en ajuste positivo |
| `apps/api/tests/...` | cubrir ajuste positivo con costo activo y caso sin costo |

## Riesgos

1. que existan múltiples costos activos ambiguos;
2. que el flujo dependa de un tipo de costo no canonizado (`BASE`, `ACTUAL`, etc.);
3. que algunos productos legacy no tengan costo cargado todavía.

## Mitigación

1. usar la misma convención ya establecida en `0029B` para elegir costo activo;
2. fallar fuerte si no hay costo resoluble;
3. mantener el slice pequeño y auditable.

## Criterios de aceptación

1. Ajuste positivo de un producto con costo activo en `productos` -> el sistema resuelve `unit_cost` desde ese costo y completa el ajuste.
2. Ajuste positivo de un producto sin costo activo -> el sistema bloquea con mensaje claro.
3. Ajuste negativo -> sigue funcionando sin costo manual.
4. `stock` no inventa costo desde balances o ledger previos para este flujo.
5. El comportamiento queda alineado con ownership de `productos` sobre costos.

## Encaje con ADD

Este slice se considera `ADD` porque:

- resuelve una sola decisión de diseño;
- mantiene ownership claro;
- evita refactor masivo;
- deja una fuente canónica singular para una pregunta concreta:

```text
de donde viene el unit_cost de un ajuste positivo?
```

Respuesta:

```text
del costo activo del producto en productos
```
