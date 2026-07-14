# SPEC 0023J — Carta porte digital viva por movimiento

## Estado

Primera version — 2026-07-09

## Problema

El sistema nuevo ya acerto una parte clave: la carta porte vive por `movement`, no por ruta global.

Hoy eso existe solo como una primera vista de migracion:

- `waybill` nace desde `movement`;
- el backend ya calcula datos base de transporte y ADR;
- el frontend ya puede visualizar una salida base.

Pero todavia falta el comportamiento operativo real que `Grab2` describe:

1. la carta porte debe poder cambiar durante la ruta;
2. debe seguir el estado real de lo cargado, entregado, retirado o devuelto;
3. debe poder verse digitalmente sin depender de un papel fijo;
4. debe quedar versionada y trazable;
5. no debe romper el ownership actual de `movements`.

El error seria mover la carta porte fuera de `movements` o duplicar la verdad operativa en otra tabla documental paralela.

## Evidencia directa de Grab2

### 1. Hace falta un modulo de carga de vehiculo

`Grabación28ENE2025_transcripcion.txt`

- `[80:00] ... va a tener que hacerse un modulo de carga de vehiculo ...`
- `[81:40] ... un modulo de carga donde me aparezcan aqui a la izquierda todos los cilindros que ya estan autorizados para cargar ...`

### 2. El repartidor debe ver lo listo para despacho y cargar su camion

`Grabación28ENE2025_transcripcion.txt`

- `[64:10] ... el repartidor seria que empiece a visualizar todo lo que ya esta listo para despacho ...`
- `[65:00] ... el repartidor en este caso veria todo esto de aqui y tendrian que empezar a cargar su camion para el reparto ...`

### 3. El camion se trata como almacen movil

`Grabación28ENE2025_transcripcion.txt`

- `[110:50] ... si la trataremos ... como un almacen ...`
- `[110:50] ... al cargar esta haciendo el traspaso al almacen movil ...`

`AUDIO_PROBERTON_1_fix_transcripcion.txt`

- `[18:20] ... agregar un almacen que seria el almacen movil ...`
- `[19:10] ... al momento que esta escaneando para subir al camion es como que esta haciendo un traslado ...`
- `[19:10] ... realmente es una furgoneta es un un almacen ...`

### 4. La carta porte debe cambiar en tiempo real durante la ruta

`6agosto2024Reportes Grabación (51)_transcripcion.txt`

- `[14:10] ... esa carta porte vale ... ahora mismo lo va a arrestar yo me lo voy a tener carta porte electronica ...`
- `[15:00] ... esa carta porte debe a cambiarse ...`
- `[15:50] ... el conductor debe tener medios de cambiarla esta carta porte en el tiempo real ...`

### 5. Existe umbral regulatorio fuerte de 1000 kg/litros

`6agosto2024Reportes Grabación (51)_transcripcion.txt`

- `[17:30] ... todo lo que supera o igual 1000 kg o 1000 litros de gas transportado entra como mercancia peligrosa ...`
- `[18:20] ... te obliga al final de ano presentarlo un informe ...`

## Objetivo

Construir la carta porte como documento digital vivo derivado de `movement`, con estas reglas:

1. `movement` sigue siendo la fuente de verdad operativa;
2. `core/documents` guarda las versiones documentales de la carta porte;
3. si cambia lo transportado o el contexto operativo relevante, la carta porte puede regenerarse como nueva version;
4. el conductor o la operacion ven siempre la ultima version vigente;
5. la experiencia debe servir tanto para vista en sistema/tablet como para descarga controlada.

## Decision

### 1. `movements` sigue siendo el owner de la carta porte

La carta porte no se mueve a `planning` ni a un submodulo documental separado.

`logistics/movements` mantiene ownership sobre:

- vehiculo;
- conductor;
- origen y destino;
- items transportados;
- cantidades transportadas vigentes en el movimiento;
- pesos y puntos ADR;
- estado operativo del traslado/reparto.

### 2. `core/documents` es owner del artefacto documental

La carta porte PDF versionada vive en `core_document_versions`.

Eso implica:

- `movement` = verdad operativa;
- `core_document_versions` = snapshot documental versionado;
- signed URLs / viewer / historial = responsabilidad de core.

### 3. Carta porte viva, no PDF estatico

La version inicial puede generarse al confirmar carga o crear el movimiento de salida.

Si luego cambia algo relevante, se genera nueva version.

Ejemplos de cambios relevantes:

1. cambio de vehiculo;
2. cambio de conductor;
3. cambio de items/cantidades cargadas;
4. entrega parcial que altera la composicion transportada vigente;
5. retiro o devolucion relevante;
6. cambio material en peso total o puntos ADR.

## Alcance

### Incluye

1. modelar la carta porte como documento versionado por `movement`;
2. definir cuando se genera o regenera version;
3. exponer ultima version vigente y su historial;
4. dejar preparado el flujo digital-first para tablet/sistema;
5. separar claramente carta porte viva de albaran operativo;
6. mantener la base actual de `waybill` por movimiento.

### No incluye

1. cerrar en esta spec la firma del conductor o aceptacion final;
2. modelar aqui albaran valorado/no valorado;
3. cerrar numeracion por delegacion;
4. resolver todo el reporte ADR >1000 kg;
5. mover ownership de `movement` a `planning`.

## Ownership arquitectonico

### `logistics`

Responsable de:

1. datos operativos del `movement`;
2. reglas de cuando la carta porte nace o se invalida;
3. payload estructurado que alimenta el documento;
4. eventos operativos que disparan regeneracion;
5. distincion futura entre carta porte interna/externa.

### `core`

Responsable de:

1. versionado de documento;
2. render PDF;
3. signed URLs;
4. viewer/descarga segura;
5. historial de versiones;
6. futura firma digital del documento si aplica.

## Diseno funcional

### 1. Entidad operativa base

La carta porte se deriva de:

- `MovementRead`;
- items del movimiento;
- vehiculo y conductor asignados;
- pesos y ADR calculados;
- contexto de origen/destino;
- estado de carga/descarga si aplica.

### 2. Documento canonico

`core_document_versions` usa algo como:

- `module = logistics`
- `entity_type = movement_waybill`
- `entity_id = movement_id`
- `template_code = WAYBILL_INTERNAL_V1` o equivalente

Desde esta spec se reserva explicitamente una dimension de variante documental para no bloquear `0023J-A/B`.

La implementacion debe contemplar una de estas dos estrategias canonicas:

1. `entity_type = movement_waybill_internal | movement_waybill_external`; o
2. `entity_type = movement_waybill` + `template_code` o `document_kind = INTERNAL | EXTERNAL`.

Regla obligatoria: solo puede existir una version `ACTIVE` por `movement_id + variante documental`.

### 3. Regeneracion de version

La carta porte no debe reescribirse en el mismo registro PDF.

Cada cambio relevante crea una nueva version:

1. `v1` — carga/salida inicial
2. `v2` — cambio de composicion o conductor
3. `v3` — actualizacion posterior

La UI siempre muestra:

- ultima version vigente;
- historial de versiones anteriores;
- motivo operativo del cambio si existe.

La regeneracion no cambia la verdad operativa del `movement`; solo emite un nuevo snapshot documental.

### 4. Estado documental sugerido

Estados minimos sugeridos para la carta porte:

- `DRAFT`
- `ACTIVE`
- `SUPERSEDED`
- `VOID`

`ACTIVE` significa ultima version vigente para mostrar/usar.

## Reglas de negocio

1. una carta porte nace por `movement`, no por ruta global;
2. `movement` sigue siendo la fuente de verdad, no el PDF;
3. si cambia lo transportado de forma relevante, la carta porte debe poder cambiar;
4. el sistema debe preservar historial de versiones, no sobrescribir el PDF anterior;
5. la ultima version vigente debe ser visible desde el contexto operativo;
6. la carta porte y el albaran son documentos distintos aunque compartan parte del origen de datos;
7. la generacion documental no debe crear una segunda semantica de stock o carga;
8. si el documento cambia, debe poder reconstruirse por auditoria que evento genero la nueva version.

## Frontera con 0023K — Albaran / nota de entrega

La frontera documental queda fijada asi:

### Carta porte (`0023J`)

La carta porte representa la composicion transportada vigente del vehiculo o movimiento.

Responde preguntas como:

1. que sale cargado legalmente en este movimiento;
2. con que vehiculo y conductor sale;
3. desde donde sale y hacia que destino operativo va;
4. cuanto peso y cuanto ADR transporta en este momento;
5. cual es la ultima version vigente del documento de transporte.

La carta porte puede regenerarse durante la ruta si cambia materialmente la composicion transportada vigente.

### Albaran / nota de entrega (`0023K`)

El albaran es la nota de entrega o retiro ejecutada contra un cliente o destinatario.

Responde preguntas como:

1. que se entrego realmente;
2. que se retiro realmente;
3. que vacias se recogieron;
4. que excepciones ocurrieron;
5. si el documento es valorado o no valorado.

### Regla de separacion obligatoria

1. la carta porte no es owner del detalle final de entrega o retiro por cliente;
2. el albaran no es owner de la composicion legal del transporte vigente del vehiculo;
3. una entrega parcial puede disparar una nueva version de carta porte si cambia la composicion transportada restante, pero el hecho de entrega pertenece semanticamente al albaran o nota de entrega;
4. retiros, devoluciones y excepciones se registran operativamente en sus owners y solo impactan `0023J` cuando alteran la composicion transportada vigente.

## Endpoints esperados

### Core

- `GET /core/documents/{id}/signed-url` — acceso temporal a una version concreta
- `GET /core/documents/{id}/signed-download` — descarga/vista segura
- `GET /core/documents/by-entity?module=logistics&entity_type=movement_waybill&entity_id=...`

### Logistics

- Compatibilidad: en la primera implementacion debe preservarse la ruta actual basada en `/waybill/{movement_id}` mientras se agrega o migra la nueva lectura documental.
- Si se introducen rutas nuevas bajo `/movements/{id}/waybill*`, debe documentarse deprecacion explicita y compatibilidad temporal en `docs/contracts/logistics-api.md`.
- `GET /waybill/{movement_id}` o equivalente compatible — ultima version vigente + metadata documental
- `GET /waybill/{movement_id}/history` o ruta versionada nueva — historial de versiones
- `POST /waybill/{movement_id}/regenerate` o ruta versionada nueva — regeneracion controlada cuando haga falta

## Payload documental sugerido

La generacion del documento debe incluir, como minimo:

1. identificador del movimiento;
2. serie/numero documental si aplica;
3. fecha y hora de salida;
4. origen y destino;
5. conductor;
6. vehiculo;
7. items transportados;
8. cantidades y unidades;
9. peso total;
10. puntos ADR / estado ADR si aplica;
11. ultima razon de regeneracion si no es `v1`.

## Eventos sugeridos

### Logistics

- `logistics.movement.waybill_generated`
- `logistics.movement.waybill_regenerated`
- `logistics.movement.waybill_superseded`

Payload minimo sugerido:

- `movement_id`
- `document_version_id`
- `document_kind`
- `reason`
- `previous_document_version_id` cuando aplique

### Core

- `core.document.rendered`

## Permisos y auditoria

No se proponen permisos nuevos en esta spec.

Se reutiliza el arbol actual de `movements`.

Minimo contractual:

1. ver version vigente de carta porte reutiliza el permiso actual de lectura de movimientos;
2. ver historial de versiones reutiliza el permiso actual de lectura de movimientos;
3. regenerar carta porte requiere el mismo o mayor nivel que modificar el movimiento que le da origen;
4. toda regeneracion debe quedar auditada con `movement_id`, `document_version_id`, `document_kind` y `reason`.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Duplicar la verdad en una tabla `waybill` nueva | alto | usar `movement` como source of truth y `core_document_versions` como snapshot |
| Regenerar demasiado y volver el flujo ruidoso | medio | definir disparadores relevantes y no cada cambio menor |
| Mezclar carta porte con albaran | alto | separar spec y endpoints desde ahora |
| Hacer que planning se vuelva owner documental | alto | planning solo prepara contexto operativo |
| Perder trazabilidad de que cambio genero nueva version | medio | registrar razon/evento de regeneracion |

## Criterios de aceptacion

1. existe una spec activa `0023J` para carta porte digital viva;
2. queda explicitado que `movement` sigue siendo la fuente operativa de verdad;
3. queda explicitado que `core/documents` es owner del versionado documental;
4. la carta porte puede tener multiples versiones por un mismo movimiento;
5. queda definido el criterio de regeneracion por cambios operativos relevantes;
6. la UI objetivo contempla ultima version vigente + historial;
7. queda separada conceptualmente de `0023K` albaran operativo;
8. la solucion es digital-first y no depende de papel como contrato del flujo.

## Dependencias

- `docs/specs/core/0023-logistics-operacion-real/index.md`
- `docs/specs/core/0023-logistics-operacion-real/0023AE-firma-contractual-digital.md`
- `docs/contracts/logistics-api.md`
- `plugins/logistics/backend/services/planning.py`
- `plugins/logistics/backend/services/movements.py`
- `apps/api/app/kernel/documents/*`
