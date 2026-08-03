---
id: "0038"
title: "Ubicacion Actual Atomica para Jornadas"
domain: logistics
module: jornadas
status: borrador
extends:
  - docs/specs/core/0024-1-3-6-seriales-de-envases-en-carga-operativa.md
  - docs/specs/core/0023-logistics-operacion-real/0023C-trazabilidad-operativa.md
  - docs/specs/core/0021-cylinder-create-with-initial-movement.md
---

# SPEC 0038 - Ubicacion Actual Atomica para Jornadas

## Contexto

`Jornadas` hoy usa dos lecturas distintas para responder ubicacion/disponibilidad de envases serializados:

- `Control de envases` infiere `En almacen: ...` desde el ultimo movimiento con `warehouse_id`.
- `Carga operativa` y el buscador de seriales (`load-serials`) validan almacen origen solo desde `lg_cylinders.location`.

Esto produce contradicciones operativas reales.

Caso reportado por usuario:

- envase `LU93FJ`
- producto `AIRE COMPRIMIDO B10 / 200BAR`
- estado `EN_ALMACEN_VACIO`
- `Control de envases` lo muestra en `FUENTE DE PIEDRA-MALAGA`
- `Carga operativa` muestra para el producto `0 serializados`
- el buscador puede tratar el mismo serial como fuera del almacen origen

La contradiccion no viene de stock. El usuario aclaro explicitamente que:

```text
stock != envase serializado
```

El problema real es que la ubicacion actual del envase no se resuelve con una sola regla compartida.

## Frase guia

**Si dos vistas responden "donde esta este envase" de forma distinta, la trazabilidad operativa no es confiable.**

## Objetivo

Introducir una regla central minima de backend para resolver el `almacen actual` de un envase y reutilizarla en `Jornadas` para:

1. conteo de `serializados` por almacen origen;
2. buscador de seriales en carga operativa;
3. validacion de pertenencia al almacen origen durante seleccion de seriales.

La solucion debe ser atomica:

- sin migraciones nuevas;
- sin rehacer el modelo completo de trazabilidad;
- sin cambiar la semantica de `stock`;
- sin romper el flujo actual de `Control de envases`.

## No objetivos

- no redefinir toda la arquitectura de ubicacion fisica del cilindro;
- no convertir `lg_cylinder_events` en fuente unica en esta iteracion;
- no reescribir `stock` ni equipararlo a serializacion;
- no cambiar estados de cilindro;
- no introducir nuevas tablas.

## Problema exacto

Hoy existe esta divergencia:

```text
Control de envases -> ultimo movimiento / warehouse_id
Jornadas serializados -> cylinder.location
Buscador load-serials -> cylinder.location
```

Cuando `cylinder.location` esta vacio pero el ultimo movimiento si conoce el almacen, la UI se contradice.

## Decision de dominio

### 1. Se define una regla central minima para `almacen actual del envase`

Backend debe exponer una helper reutilizable con esta prioridad minima:

1. si hay ultimo movimiento con `warehouse_id`, ese almacen manda;
2. si no hay ultimo movimiento util, `cylinder.location` queda como fallback textual para intentar mapear almacen;
3. si ninguna fuente resuelve almacen, el envase queda sin almacen actual resoluble.

## Importante

Esta spec se limita al caso `almacen actual` porque es el dato que hoy necesitan `Jornadas` y el buscador.

No redefine todavia cliente/vehiculo como contrato completo de ubicacion general del cilindro.

### 2. `stock` y `serializados` siguen siendo capas distintas

Regla fuerte:

```text
stock positivo no implica seriales
seriales no implican stock positivo
```

Esta spec no altera esa separacion. Solo corrige la lectura de `serializados` por almacen.

### 3. `Jornadas` debe dejar de depender exclusivamente de `cylinder.location`

El conteo de serializados y el buscador de seriales no pueden rechazar o esconder un envase solo porque `location` este vacio si el ultimo movimiento ya deja trazado el almacen.

## Alcance

### Backend

1. Crear helper central de lectura para resolver `almacen actual` de un cilindro.
2. Reusar esa helper en `summarize_serialized_cylinders_by_warehouse`.
3. Reusar esa helper en `_warehouse_matches_cylinder` dentro de `load_serials.py`.
4. Mantener `cylinder.location` como fallback, no como verdad principal.
5. No cambiar contratos HTTP existentes salvo el comportamiento correcto de disponibilidad.

### Frontend

No requiere nuevos componentes ni cambios de layout.

El impacto esperado en frontend es indirecto:

- `Disponibilidad en origen` debe contar mejor los serializados.
- el buscador de seriales debe ofrecer `AVAILABLE` para un serial cuyo almacen actual sea el origen aunque `location` este vacio.

## Regla operativa minima

Para los casos de esta spec, un envase serializado pertenece al almacen origen si:

1. su ultimo movimiento conocido tiene `warehouse_id = origen`; o
2. en ausencia de lo anterior, `cylinder.location` mapea a ese almacen.

Si ninguna de las dos condiciones se cumple:

```text
el envase no debe contarse ni aparecer como disponible en ese almacen origen
```

## Archivos esperados

| Archivo | Cambio esperado |
|---|---|
| `plugins/logistics/backend/services/cylinder_location.py` | helper minima de ubicacion/almacen actual |
| `plugins/logistics/backend/services/cylinders.py` | reutiliza helper para resumen de serializados |
| `plugins/logistics/backend/services/load_serials.py` | reutiliza helper para buscador y validacion de origen |
| `apps/api/tests/test_logistics_plugin.py` | cobertura de conteo serializado por ultimo movimiento |
| `apps/api/tests/test_logistics_vehicle_sessions_v1.py` | cobertura del buscador de seriales por ultimo movimiento |

## Riesgos

1. la helper puede introducir N+1 si se usa ingenuamente en listados masivos;
2. la lectura por ultimo movimiento puede seguir siendo incompleta en cilindros sin historial ni `location`;
3. la arquitectura global de ubicacion sigue pendiente para otra iteracion mas amplia.

## Mitigacion

1. mantener el cambio pequeno y acotado a jornadas;
2. priorizar correccion funcional antes que una refactorizacion grande;
3. cubrir con tests el caso reportado por usuario.

## Criterios de aceptacion

1. `AIRE COMPRIMIDO B10 / 200BAR` aparece con `serializados > 0` en `Disponibilidad en origen` cuando existe un serial como `LU93FJ` cuyo ultimo movimiento pertenece al almacen origen aunque `cylinder.location` este vacio.
2. El buscador de seriales de la jornada devuelve `LU93FJ` como `AVAILABLE` cuando el `source_warehouse_id` coincide con ese ultimo almacen.
3. Si el mismo serial pertenece por ultimo movimiento a otro almacen, debe seguir apareciendo como no disponible para el origen actual.
4. El conteo de `serializados` no cambia la semantica de `stock`.
5. No se agregan tablas ni migraciones nuevas.
6. `ruff check` y tests dirigidos pasan.

## Test funcional pedido por usuario

La validacion manual minima de esta spec queda definida asi:

1. Abrir una jornada con origen `FUENTE DE PIEDRA-MALAGA`.
2. Revisar `Disponibilidad en origen`.
3. Confirmar que `AIRE COMPRIMIDO B10 / 200BAR` aparece contado con su serial.
4. Abrir el buscador de seriales para esa linea.
5. Confirmar que el serial correspondiente aparece disponible en el buscador.
