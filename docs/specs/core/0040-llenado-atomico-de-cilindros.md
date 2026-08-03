---
id: "0040"
title: "Llenado Atómico de Cilindros"
domain: logistics
module: envases
status: implementada
extends:
  - docs/specs/core/0021-cylinder-create-with-initial-movement.md
  - docs/specs/core/0016-2-stock-transactional-gaps.md
  - docs/specs/core/0039-unit-cost-activo-para-ajustes-positivos.md
---

# SPEC 0040 - Llenado Atómico de Cilindros

## Contexto

El sistema ya puede crear cilindros (`lg_cylinders`) y registrar su identidad base:

- serial;
- producto asociado;
- pesos técnicos;
- estado operativo;
- alta inicial con trazabilidad.

Además, el modelo actual ya contiene campos útiles para expresar carga material:

- `content_kg`;
- `volume_m3`;
- `weight_origin` / `weight_current`;
- `current_state`.

El gap real no está en el alta del cilindro.

El gap está en que todavía no existe una operación de negocio explícita y trazable para responder estas preguntas:

1. qué tan lleno está el cilindro;
2. cuándo se llenó o se vació;
3. desde qué almacén salió el contenido;
4. qué impacto tuvo en stock;
5. si el cilindro hoy debe leerse como vacío o cargado.

## Hallazgo de dominio

Para este sistema, el producto del cilindro ya puede representar la unidad comercial/operativa compuesta.

Ejemplos reales del catálogo y del legacy:

- `AIRE COMPRIMIDO B10 / 200BAR`
- `Oxigeno Industrial B2`
- `Oxigeno Industrial B50 / 200BAR`

Es decir:

- no siempre existe un `gas puro` separado del `recipiente` como dos líneas distintas en la operación diaria;
- muchas veces el producto ya expresa el cilindro tipado por servicio, tamaño y presión.

Por eso, para este slice atómico, no se parte todavía el modelo en `producto envase` y `producto contenido` como dos contratos nuevos.

## Frase guía

**Crear el cilindro define qué recipiente es. Llenarlo define cuánto contenido real lleva y descuenta ese contenido del stock libre.**

## Objetivo

Formalizar `Llenado` como operación de primer nivel dentro de `Envases`, usando el modelo ya existente, con estas reglas:

1. el cilindro ya creado conserva su identidad;
2. el llenado actualiza su carga técnica;
3. el llenado descuenta stock desde el almacén origen;
4. el contenido deja de ser stock libre y pasa a estar representado dentro del cilindro;
5. si el cilindro no tiene carga, se considera vacío.

## No objetivos

- no rediseñar la creación de cilindros;
- no partir aún el dominio en `producto envase` y `producto contenido` como contratos separados;
- no introducir un almacén técnico intermedio para el contenido cargado;
- no redefinir todavía la carta porte ni ADR completo a partir del llenado;
- no rehacer todas las jornadas ni el state machine entero.

## Baseline de arquitectura

### 1. Owners

#### `Envases`

Owner de:

- recipiente físico;
- serial;
- estado operativo/material actual;
- trazabilidad del cilindro.

#### `Productos`

Owner de:

- definición del producto asociado al cilindro;
- costo activo;
- datos ADR;
- nombre comercial;
- unidad técnica.

#### `Stock`

Owner de:

- stock libre del producto por almacén.

#### `Llenados`

Submódulo interno de `Envases` que actúa como puente operativo entre:

- cilindro físico;
- carga técnica actual;
- descuento de stock desde almacén origen.

### 2. Opción elegida de arquitectura

Se adopta la opción 1 ya fijada previamente:

```text
el llenado descuenta stock del producto en el almacén origen
y la contrapartida no va a otro stk_balance
sino al propio cilindro cargado
```

En otras palabras:

- antes del llenado, el contenido está en stock libre;
- después del llenado, ese contenido queda representado dentro del cilindro;
- no se duplica como stock libre en otro almacén técnico.

## Decisión de dominio

### 1. El cilindro ya creado define el tipo base del recipiente

El flujo `create_cylinder()` se mantiene como owner de la identidad base.

Para este slice se asume que el `product_id` actual del cilindro ya representa el tipo de cilindro/producto operativo con el que el sistema trabaja hoy.

No se reinterpreta el cilindro en cada jornada.

### 2. El llenado no crea el cilindro; cambia su carga material

El submódulo de llenado no reemplaza el alta.

Hace tres cosas:

1. registra que el cilindro recibió contenido;
2. actualiza la carga técnica actual del cilindro;
3. descuenta stock libre en el almacén origen.

### 3. El estado vacío/lleno se deriva desde la carga actual

Regla operativa mínima de este slice:

```text
sin carga actual -> cilindro vacío
con carga actual > 0 -> cilindro cargado
```

La UI debe poder mostrar al menos:

- vacío;
- cargado.

La gradación fina (`parcial`, `% lleno`, etc.) puede derivarse después desde los mismos campos técnicos.

### 4. El llenado consume stock del mismo producto operativo del cilindro

Para mantener el slice atómico y coherente con el catálogo actual:

- el llenado consume stock del producto ya asociado al cilindro;
- no introduce todavía un segundo `content_product_id` obligatorio;
- no exige un bridge nuevo entre dos SKUs distintos.

Esto mantiene consistencia con productos reales del sistema como:

- `AIRE COMPRIMIDO B10 / 200BAR`
- `Oxigeno Industrial B2`
- `Nitrógeno Industrial B10`

donde el producto ya expresa la unidad operativa que el negocio usa en stock, jornada y documentación.

### 5. El descuento ocurre en el momento del llenado

No al crear cilindro.

No al seleccionar serial.

No al cargarlo en una jornada.

Sí cuando se registra el llenado.

Ejemplo:

```text
antes:
  stock libre en Málaga de AIRE COMPRIMIDO B10 / 200BAR = 100
  cilindro X = vacío

después de llenar 25 m3:
  stock libre en Málaga = 75
  cilindro X = cargado con 25 m3
```

## Capacidades mínimas del submódulo

### A. Registrar llenado

Debe permitir:

- elegir almacén origen del contenido;
- registrar cantidad técnica cargada;
- actualizar la carga actual del cilindro;
- descontar stock libre del producto en origen;
- dejar traza auditada del hecho.

### B. Registrar vaciado

Debe permitir:

- dejar la carga actual en cero;
- marcar el cilindro como vacío.

La política exacta de si el vaciado devuelve o no stock al sistema queda fuera de este slice.

### C. Consultar carga actual

La ficha del cilindro debe poder responder:

- está vacío o cargado;
- cuánto contenido actual tiene;
- en qué unidad técnica;
- cuándo fue el último llenado;
- desde qué almacén se llenó.

## Archivos esperados

| Archivo | Rol esperado |
|---|---|
| `plugins/logistics/backend/models/cylinder.py` | reutiliza campos actuales del cilindro para carga material actual |
| `plugins/logistics/backend/models/fillings.py` | historial de llenados/vaciados si se decide tabla propia |
| `plugins/logistics/backend/services/fillings.py` | operación de llenar/vaciar cilindro |
| `plugins/logistics/backend/router.py` o router dedicado | endpoints del submódulo |
| `plugins/logistics/frontend/.../Envases` | sección visual de llenado en la ficha del cilindro |

## Invariantes obligatorios

1. Un cilindro vacío no puede conservar una carga técnica positiva.
2. Un llenado debe descontar stock libre del almacén origen.
3. El contenido cargado en cilindro no puede seguir contando como stock libre en el mismo almacén.
4. Crear un cilindro no consume stock por sí solo.
5. Seleccionar un serial en jornada no equivale a llenarlo.
6. El llenado debe ser auditable.

## Criterios de aceptación

1. Existe una operación explícita para llenar un cilindro desde `Envases`.
2. Al llenar un cilindro, baja el stock del producto en el almacén origen.
3. El cilindro queda visible como cargado con cantidad técnica actual.
4. Si la carga actual queda en cero, el cilindro se lee como vacío.
5. La operación no usa un almacén intermedio artificial para representar el contenido.
6. No se rompe el flujo actual de alta de cilindro.

## Qué une esta spec

Esta spec une dos mundos ya presentes pero hoy desconectados:

1. `Alta de cilindro` ya implementada.
2. `Consumo de stock` ya implementado.

El submódulo de `Llenados` se define como la pieza atómica que conecta ambas sin rehacer el modelo completo.
