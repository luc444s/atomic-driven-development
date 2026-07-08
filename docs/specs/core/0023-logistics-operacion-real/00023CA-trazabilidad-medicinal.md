# SPEC 00023CA — Trazabilidad medicinal sobre la ficha del envase

## Estado

Primera version — 2026-07-08

## Problema

Hoy la ficha del envase ya tiene una entrada llamada `Trazabilidad de estado` con la descripcion `Transiciones registradas sobre el envase.`. Esa vista usa `GET /cylinders/{id}/trace` y solo muestra `StateLog` en una tabla plana con `Fecha`, `Cambio`, `Origen`, `Notas`.

Al mismo tiempo, backend ya dispone de `GET /cylinders/{id}/traceability`, que unifica multiples fuentes del cilindro: cambios de estado, escaneos, PH, retimbrados, servicios, garantias, custodia y etiquetas.

Ademas:

- `is_medical` ya existe en `lg_cylinders` como booleano no nulo y se muestra en la ficha;
- el listado general de envases todavia no permite filtrar por `is_medical`;
- `medical_flag_changed` sigue listado en `0023C` pero no esta implementado en el trazador;
- la persistencia real del flag medicinal debe quedar documentada como `true | false`, no como estado ambiguo.

El gap real no es crear un modulo nuevo de trazabilidad, sino enriquecer la vista existente de `Trazabilidad de estado` para que permita reconstruir mejor el recorrido del cilindro, especialmente cuando es medicinal.

## Objetivo

1. Mantener la entrada UX existente `Trazabilidad de estado` y su descripcion `Transiciones registradas sobre el envase.`
2. Enriquecer esa vista para que deje de mostrar solo `StateLog` y pase a mostrar eventos relevantes del cilindro usando `GET /cylinders/{id}/traceability`
3. Agregar un buscador dentro de esa misma vista para filtrar la trazabilidad del cilindro cuando el historial crece
4. Documentar e implementar la persistencia real de `is_medical` como booleano `true | false`
5. Agregar filtro `is_medical` en el listado general de envases para ubicar cilindros medicinales y entrar a revisar su trazabilidad

## Relacion con specs existentes

- `0023C` sigue siendo la spec base de trazabilidad operativa extendida.
- `00023CA` no reemplaza `0023C`; la aterriza para el caso medicinal y para la UX concreta de la ficha del envase.
- `0023D` permanece reservado para CRM (`cliente comercial/fiscal y direcciones`).

## Diseno

### 1. Backend — persistencia real de `is_medical`

`lg_cylinders.is_medical` es la fuente de verdad y debe permanecer como:

- tipo `BOOLEAN`;
- `NOT NULL`;
- valor posible solo `true` o `false`;
- default `false` para filas nuevas cuando el cliente no envia el campo.

Reglas de persistencia:

1. `create_cylinder()` debe persistir el valor recibido en `is_medical`; si el payload no lo envia, se guarda `false`.
2. `update_cylinder()` debe persistir cambios explicitos de `is_medical` cuando el payload envie `true` o `false`.
3. `medical_notes` se mantiene como campo descriptivo opcional y no sustituye al booleano.
4. No existe estado `null`, `unknown` ni tri-state para el flag medicinal.
5. No se requiere migracion de datos para la columna, porque ya existe y su default actual cubre filas existentes.

### 2. Backend — enriquecer `GET /cylinders/{id}/traceability`

**Archivo:** `plugins/logistics/backend/services/traceability.py`

La vista `Trazabilidad de estado` deja de consumir solo `GET /cylinders/{id}/trace` y pasa a consumir `GET /cylinders/{id}/traceability`.

Se agregan estas colecciones de eventos faltantes:

```python
_collect_medical_flag_changes(db, cylinder_id, events)
_collect_contract_events(db, cylinder_id, events)
```

#### `medical_flag_changed`

| campo | fuente |
|-------|--------|
| `timestamp` | registro de auditoria del cambio o, si no existe historial, momento del cambio persistido en adelante |
| `event_type` | `"medical_flag_changed"` |
| `description` | `"Flag medicinal: false -> true"` o `"Flag medicinal: true -> false"` |
| `actor` | usuario que ejecuto el cambio |
| `metadata` | `{"old_value": false, "new_value": true}` |

Alcance historico:

- la auditoria del flag medicinal es **forward-only** desde que se implemente;
- no se inventa backfill historico de cambios pasados que no existieron en auditoria.

#### `contract_assigned` / `contract_released`

| campo | fuente real |
|-------|-------------|
| `timestamp` | `delivered_at` o `returned_at` del item contractual |
| `event_type` | `"contract_assigned"` o `"contract_released"` |
| `description` | `"Asignado a contrato"` o `"Liberado de contrato"` |
| `actor` | quien ejecuto la accion si esta disponible |
| `metadata` | `{"contract_id": "..."}` |

Si el usuario tambien tiene `logistics.contract.view`, la metadata puede incluir `contract_number`. Si no, no debe exponerse ese dato documental.

### 3. Backend — filtro `is_medical` en listado de envases

**Archivos:**

- `plugins/logistics/backend/services/cylinders.py`
- `plugins/logistics/backend/router.py`

Se agrega `is_medical: bool | None = None` a `list_cylinders()` y a `GET /cylinders`.

Comportamiento:

- `is_medical=true` -> solo cilindros medicinales;
- `is_medical=false` -> solo cilindros no medicinales;
- `is_medical` ausente -> no filtra por este campo.

### 4. Frontend — mantener `Trazabilidad de estado`, pero enriquecida

**Archivo:** `plugins/logistics/frontend/cylinders/dialogs/cylinder-view-section-dialog.tsx`

No se renombra el boton ni la seccion. Debe seguir mostrandose como:

- titulo: `Trazabilidad de estado`
- descripcion: `Transiciones registradas sobre el envase.`

Lo que cambia es el contenido interno: en lugar de una tabla solo de `StateLog`, la vista se enriquece con la trazabilidad unificada del cilindro.

La prioridad visual sigue siendo el cambio de estado, pero alrededor de ese estado se muestran tambien eventos complementarios del cilindro cuando existan: creacion, escaneo, PH, retimbrado, servicio, garantia, custodia, impresion de etiqueta, contrato y cambio de flag medicinal.

Ejemplo visual esperado:

```text
Trazabilidad de estado
Transiciones registradas sobre el envase.

[Buscar en trazabilidad]

10:58:52 | Cambio de estado | Nuevo -> Disponible | Origen: - | Notas: -
10:54:41 | Creacion         | Inicio -> Nuevo     | Origen: PLUGIN_CREATE | Notas: Initial cylinder registration
09:30:00 | Etiqueta         | Impresion           | Origen: LABEL_PRINT   | Notas: 3 copias
08:00:00 | Escaneo          | Validacion campo    | Origen: SCAN          | Notas: GPS 37.38,-5.99
07:00:00 | Medicinal        | false -> true       | Origen: UPDATE        | Notas: cambio de flag medicinal
```

### 5. Buscador dentro de `Trazabilidad de estado`

El buscador forma parte de esta spec y se define asi:

- vive dentro de la misma vista `Trazabilidad de estado`;
- filtra por `event_type`, `description`, `actor`, `origin` y texto visible de notas;
- opera en cliente sobre los eventos ya cargados en memoria;
- la paginacion sigue existiendo y el usuario puede cargar mas eventos para ampliar la base de busqueda.

Fase 1 no agrega `q` al backend de trazabilidad. Si se necesita buscar sobre todo el historial remoto sin cargar mas paginas, eso queda para una fase posterior.

### 6. Frontend — filtro `Solo medicinales`

**Archivo:** `plugins/logistics/frontend/LogisticsPage.tsx`

Se agrega un filtro visible en el buscador del modulo de envases:

```text
[Solo medicinales]
```

Ese control agrega `is_medical=true` a `listCylinders()` y permite localizar rapido cilindros medicinales para entrar a su ficha y revisar su trazabilidad.

### 7. Archivos afectados

| Archivo | Cambio |
|---------|--------|
| `plugins/logistics/backend/services/cylinders.py` | Persistir `is_medical` en create/update y agregar filtro `is_medical` en `list_cylinders()` |
| `plugins/logistics/backend/router.py` | Agregar query param `is_medical` en `GET /cylinders` |
| `plugins/logistics/backend/services/traceability.py` | Agregar `medical_flag_changed` y eventos contractuales con fuentes reales |
| `plugins/logistics/frontend/api/cylinders.ts` | Agregar `is_medical` a `listCylinders()` y adaptar consumo de `traceability` |
| `plugins/logistics/frontend/cylinders/hooks/use-cylinder-data.ts` | Consumir `GET /cylinders/{id}/traceability` |
| `plugins/logistics/frontend/cylinders/dialogs/cylinder-view-section-dialog.tsx` | Mantener `Trazabilidad de estado`, enriquecer contenido y agregar buscador |
| `plugins/logistics/frontend/LogisticsPage.tsx` | Agregar filtro `Solo medicinales` |
| `docs/specs/core/0023-logistics-operacion-real/index.md` | Actualizar referencias y realidad del codigo |

## No objetivos

- no renombrar la entrada UX `Trazabilidad de estado`;
- no crear una seccion global nueva de trazabilidad en el menu;
- no inventar historial retroactivo del flag medicinal;
- no cambiar ownership de contratos, PH, retimbrados o servicios fuera de sus modulos actuales.

## Criterios de aceptacion

1. `00023CA` no colisiona con la numeracion CRM existente.
2. La ficha sigue mostrando `Trazabilidad de estado` con la descripcion `Transiciones registradas sobre el envase.`.
3. Esa vista consume `GET /cylinders/{id}/traceability` y ya no depende solo de `GET /cylinders/{id}/trace`.
4. `GET /cylinders/{id}/traceability` incluye `medical_flag_changed` y eventos contractuales usando `delivered_at` / `returned_at` o la fuente historica real equivalente.
5. `create_cylinder()` y `update_cylinder()` persisten `is_medical` como booleano `true | false`.
6. `GET /cylinders` acepta `?is_medical=true/false` y filtra correctamente.
7. El listado de envases muestra filtro `Solo medicinales`.
8. La vista `Trazabilidad de estado` tiene buscador local sobre eventos cargados.
9. Se agregan pruebas para persistencia de `is_medical`, filtro `is_medical` y eventos nuevos del trazador.
