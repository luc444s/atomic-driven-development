---
id: "0048"
title: "Carta de porte oficial v1"
domain: logistics
module: session-waybill
status: propuesta
extends:
  - docs/specs/core/0043-cambios-operativos-jornadas-sesion.md
  - docs/specs/core/0047-creacion-atomica-jornada-con-ruta-asignada.md
---

# SPEC 0048 — Carta de porte oficial v1

## Estado

Propuesta — v1

## Frase guía

**Preview viva una cosa. Documento oficial otra cosa.**

## Contexto

El sistema ya tiene una base de carta porte operativa:

- versionado en `lg_session_waybill_versions`;
- snapshot operativo por jornada;
- detección `SYNCED / OUTDATED`;
- regeneración desde runtime;
- visualización simple en `SessionWaybillCard`.

Pero eso todavía es una **preview operacional**. No es aún un documento formal con forma legal/oficial comparable al documento legacy del negocio.

El documento objetivo se parece a:

- cabecera formal con fecha, conductor, matrículas y partes;
- bloque `Expedidor / Transportista`;
- bloque `Destinatario`;
- tabla legal de mercancías con denominación ADR, producto, categoría, tipo de bulto, número de bultos, cantidad neta y cantidad ADR total.

## Alcance de v1

Esta spec cubre la conversión de la carta porte desde preview operativa a **documento oficial emitible**.

### Incluye

- documento oficial emitible y versionado;
- layout formal HTML imprimible;
- reglas de `preview` vs `emitida`;
- emisor/transportista configurable;
- destinatario real o genérico según multi-stop;
- líneas regulatorias ADR por producto transportado;
- emisión explícita y reemisión versionada;
- histórico de documentos emitidos.

### Queda fuera a v2

- DNI conductor;
- NIF/CIF expedidor/transportista;
- firma digital dura;
- PDF binario obligatorio en backend;
- validaciones fiscales profundas.

## Decisión de dominio

La carta porte oficial no debe mutar silenciosamente con la operación viva.

### Dos capas

#### 1. Preview viva

- operativa;
- regenerable;
- puede quedar `OUTDATED`;
- sirve para preparar el documento.

#### 2. Documento emitido

- oficial;
- congelado;
- imprimible;
- no se muta;
- una nueva emisión crea nueva versión, no pisa la anterior.

## Objetivo

Agregar un flujo oficial donde el usuario pueda:

1. ver preview viva de la carta porte;
2. emitir documento oficial desde esa preview;
3. visualizar el documento formal con layout legal;
4. reemitir cuando la preview quede `OUTDATED`;
5. conservar histórico de versiones emitidas.

## No objetivos

- no mover lógica legal al frontend;
- no reusar la card actual como documento final;
- no mezclar documento emitido con preview regenerable;
- no bloquear toda la operación logística si aún no se emitió la carta porte;
- no exigir DNI/NIF en esta versión.

## Datos requeridos v1

### Cabecera

- fecha del documento;
- nombre del conductor;
- matrícula camión;
- matrícula semirremolque opcional/placeholder si aún no existe dato persistido.

### Partes

#### Expedidor / transportista

Debe salir de configuración explícita del sistema, no hardcode eterno en el template.

Campos mínimos v1:

- razón social;
- dirección;
- código postal / localidad / provincia.

#### Destinatario

Regla:

- si la jornada cubre múltiples destinos -> `REPARTO EN RUTA` como destinatario genérico operativo, sin depender de albaranes externos que todavía no existen en el sistema;
- si la jornada cubre un único destino -> cliente y dirección real.

### Future

Cuando el sistema tenga `albaranes` oficiales propios, una versión futura podrá enriquecer la carta de porte multi-stop con referencias explícitas a esos documentos. Eso queda fuera de `v1` y no debe asumirse como dependencia actual.

### Tabla legal de mercancías

Por línea:

- denominación mercancía ADR (`UN xxxx` + descripción);
- producto comercial;
- categoría/clase;
- tipo de bulto;
- número de bultos;
- cantidad neta;
- unidad;
- cantidad ADR total.

## Modelo de documento v1

### `WaybillIssuerRead`

```python
class WaybillIssuerRead(BaseModel):
    legal_name: str
    address_line: str
    postal_city_line: str
```

### `WaybillConsigneeRead`

```python
class WaybillConsigneeRead(BaseModel):
    mode: Literal["SINGLE_DESTINATION", "ROUTE_DISTRIBUTION"]
    legal_name: str | None = None
    address_line: str | None = None
    note: str | None = None
```

### `WaybillRegulatoryLineRead`

```python
class WaybillRegulatoryLineRead(BaseModel):
    adr_goods_description: str
    product_name: str
    adr_category: str | None = None
    package_type_label: str | None = None
    package_count: int | None = None
    net_quantity: float | None = None
    net_unit_label: str | None = None
    adr_total_quantity: float | None = None
    adr_total_unit_label: str | None = None
```

### `WaybillOfficialSnapshotRead`

```python
class WaybillOfficialSnapshotRead(BaseModel):
    issue_date: date
    vehicle_plate: str
    trailer_plate: str | None = None
    driver_name: str
    issuer: WaybillIssuerRead
    consignee: WaybillConsigneeRead
    regulatory_lines: list[WaybillRegulatoryLineRead]
    totals: SessionWaybillTotalsRead
```
```

## Persistencia

Se reutiliza `lg_session_waybill_versions`.

La tabla ya soporta:

- `version`;
- `status`;
- `snapshot_json`;
- `change_event`;
- `change_reason`.

### Estados sugeridos de documento

- `ACTIVE_PREVIEW`
- `ISSUED`
- `SUPERSEDED`

Si no se quiere nueva columna/enum todavía, v1 puede mapearse dentro de `status` string.

## Render oficial

V1 usa **HTML imprimible** como primer documento canónico.

### Razón

- implementación más rápida;
- suficiente para A4 e impresión legal operativa;
- luego se puede agregar PDF sin reescribir contrato de datos.

### Endpoint sugerido

- `GET /vehicle-sessions/{session_id}/carta-porte/document`

Retorno:

- `text/html` con layout oficial.

## Reglas de negocio

1. Preview viva y documento emitido no son la misma cosa.
2. Emitir documento es acción explícita del usuario.
3. El documento emitido es inmutable.
4. Si la operación cambia después de emitir, el estado pasa a `OUTDATED` en la preview, no se muta la emitida.
5. Reemitir crea nueva versión oficial y deja la anterior como histórica.
6. Multi-stop usa destinatario genérico de reparto dentro del alcance real actual del sistema.
7. Single-stop usa destinatario real.
8. Sin datos ADR mínimos por línea no se emite documento oficial.
9. `DNI/NIF` no bloquean v1; quedan marcados como pendientes v2.

## Backend esperado

### Servicio

Ampliar `plugins/logistics/backend/services/session_waybills.py` con:

- `build_waybill_official_snapshot()`;
- `build_waybill_regulatory_lines()`;
- `emit_session_waybill_document()`;
- `render_waybill_html()`.

### Router

Ampliar `plugins/logistics/backend/routers/session_waybills.py` con:

- endpoint para emitir;
- endpoint para ver documento oficial HTML.

## Frontend esperado

### `SessionWaybillCard`

Agregar acciones:

- `Emitir`;
- `Ver documento`;
- `Reemitir` cuando corresponda.

Mostrar claramente:

- preview viva;
- documento emitido actual;
- versiones históricas.

## Validaciones mínimas v1

- vehículo con matrícula;
- conductor con nombre;
- emisor configurado;
- al menos una línea regulatoria válida;
- destinatario resuelto por reglas de single/multi-stop.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| mezclar preview y emitida | alto | separación dura de estados |
| render sin contrato legal claro | alto | PR inicial de contrato de datos |
| hardcode eterno de emisor | medio | config explícita |
| multi-stop ambiguo | medio | regla `REPARTO EN RUTA` fija, sin dependencia a albaranes |
| líneas ADR incompletas | alto | validación y error explícito |

## Criterios de aceptación

1. Existe contrato de snapshot oficial distinto de la preview viva.
2. El usuario puede emitir una carta porte oficial desde una jornada.
3. El documento emitido tiene layout formal HTML imprimible.
4. Multi-stop y single-stop resuelven destinatario correctamente sin requerir albaranes inexistentes.
5. La tabla legal muestra líneas regulatorias con estructura oficial.
6. Una reemisión crea nueva versión y no muta la anterior.

## Plan de implementación por commits

### added: contract legal

Alcance:

- nuevos DTOs legales;
- issuer / consignee / regulatory lines;
- snapshot oficial separado;
- validaciones base.

Resultado:

- contrato de documento oficial claro.

### added: emit official

Alcance:

- acción `emit`;
- transición a estado emitido;
- nueva versión inmutable;
- histórico oficial.

Resultado:

- preview ya puede convertirse en documento oficial.

### added: render official html

Alcance:

- template HTML A4;
- endpoint documento;
- bloque cabecera/partes/tabla legal.

Resultado:

- documento visualmente oficial.

### mod: frontend waybill

Alcance:

- `SessionWaybillCard` con `Emitir`, `Ver documento`, `Reemitir`;
- distinción visual preview vs emitida.

Resultado:

- operación usable desde frontend.

### hardening: legal rules

Alcance:

- tests;
- fallback ADR;
- multi-stop consignee rule sin dependencia a albaranes;
- errores claros;
- config emisor.

Resultado:

- carta porte oficial v1 sólida.

## Orden obligatorio

```text
added: contract legal
-> added: emit official
-> added: render official html
-> mod: frontend waybill
-> hardening: legal rules
```
