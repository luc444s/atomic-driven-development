# SPEC 0023AD — Contratos de envases

> Estado de vigencia: histórica / superada parcialmente.
> No usar este documento como roadmap activo del modelo contractual actual sin revisar primero `0023AD.2` y `0023AD.3`.
> El criterio vigente hoy es contrato por derecho/cupo y no contrato visible desde cada bombona.

## Estado

Primera versión funcional — 2026-07-07

> Esta spec toma `Sys_GMS_ES` como fuente de verdad operativa actual.
> Cuando la spec proponga capacidades que hoy no están activas en `Sys_GMS_ES`, se marcarán como construcción nueva de OSS sobre el esqueleto legacy existente.

## Problema

`logistics` ya tiene implementación parcial de contratos de envases, pero hoy mezcla supuestos no validados con un modelo incompleto del legacy.

En `Sys_GMS_ES` se verifica que:

1. existe módulo/tablas/SPs/vistas de contratos, historial y agenda asociada;
2. el módulo real está incompleto o poco usado en producción (`CONTRATOS` sin registros en la BD revisada);
3. `TipoDoc` es la fuente de verdad de los tipos documentales de la empresa;
4. hoy `Cod_TipoDoc = 4` (`Contrato de Suministro`) no tiene `PrefijoDoc`, ni filas en `SerieConfiguracion`, ni correlativos preparados;
5. por tanto, la numeración contractual `CT...` no está operativa hoy en `Sys_GMS_ES`, pero sí es una dirección funcional válida para OSS basada en el esquema documental legacy.

Además, el negocio sí requiere:

- contratos diarios, mensuales y anuales;
- alquiler/suministro por tipo de envase, no por una bombona fija;
- trazabilidad de todos los cilindros relacionados durante la vigencia del contrato;
- renovación sin generar nuevo número de contrato;
- agenda operativa de recojo/cambio/renovación;
- sección `Contratos` dentro del catálogo de clientes.

## Objetivo

Construir en OSS una primera versión funcional del submódulo de contratos de envases, apoyada en la estructura legacy, con estas metas:

- contrato visible como documento numerado propio del dominio de suministro;
- numeración alineada al patrón documental legacy basado en `TipoDoc`;
- historial contractual y alertas de renovación;
- relación documental entre contrato y cilindros intercambiados durante su vigencia;
- integración visible en ficha de cliente y ficha de cilindro;
- separación clara entre contrato y albaranes/movimientos (`SC`, `IC`, `IP`, `SP`).

## Fuente de verdad

### 1. Fuente operativa actual

La referencia principal es `Sys_GMS_ES`:

- tabla `CONTRATOS`;
- tabla `CONTRATO_HISTORIAL` (o su semántica deducida por SPs);
- tabla `TipoDoc`;
- tabla `SerieConfiguracion`;
- tabla `CorrelativosDocumento`;
- SPs `CONTRATOS_*`, `CONTRATO_HISTORIAL_*`, `sp_AgendaRepartidor_*`, `sp_Disparador_Contrato`;
- vistas de contratos y alertas.

### 2. Regla de interpretación

Cuando haya tensión entre:

- comportamiento realmente activo en `Sys_GMS_ES`, y
- SQL/código legacy preparado pero no configurado,

la spec debe:

1. reconocer el comportamiento real actual como evidencia de producción;
2. marcar explícitamente como **construcción nueva OSS** lo que aún no está activo, aunque el legacy ya tenga esqueleto parcial.

## Hallazgos verificados en `Sys_GMS_ES`

### 1. Estructura contractual existente

`CONTRATOS` hoy existe como cabecera simple con al menos:

- `Cod_Contrato`;
- `Cod_Cliente`;
- `Cod_Sucursal`;
- `Tipo_Contrato`;
- `Fecha_Firma`;
- `Fecha_Inicio`;
- `Fecha_Vencimiento`;
- `Ruta_Archivo_Contrato`;
- `Firmado_Digital`;
- `Estado`;
- `Observaciones`;
- `Fecha_Registro`;
- `Usuario_Registro`.

### 2. Estados reales actuales

En la BD revisada, los únicos estados persistidos reales son:

- `VIGENTE`
- `ANULADO`

`VENCIDO` es derivado por fecha.
`Firmado_Digital` es un flag separado, no un estado.

### 3. Tipos de contrato

En legacy real hoy `Tipo_Contrato` se comporta como texto libre.

Decisión OSS ya acordada:

- OSS no lo dejará como texto libre en el modelo final;
- OSS introducirá un catálogo propio de tipos de contrato.

Como ese catálogo no existe activo en `Sys_GMS_ES`, se considera construcción nueva OSS.

### 4. Numeración documental legacy

La lógica de numeración documental de la empresa está centralizada en:

- `TipoDoc`
- `SerieConfiguracion`
- `CorrelativosDocumento`
- `sp_GenerarNumeroDocumento`

Patrón base:

`Prefijo + Almacen + Año + '-' + Correlativo`

Ejemplo contractual propuesto para OSS:

- prefijo: `CT`
- almacén: `4UL` o su código normalizado según mapeo decidido
- año: `26`
- correlativo: `000001`

Resultado:

- `CT4UL26-000001`

o, si el almacén se normaliza a un código más corto:

- `CTUL26-000001`

### 5. Estado actual de contratos dentro del esquema documental

En `Sys_GMS_ES` revisado hoy:

- `Cod_TipoDoc = 4` existe como `Contrato de Suministro`;
- `PrefijoDoc` todavía está en `NULL`;
- no hay fila activa en `SerieConfiguracion` para contratos;
- no hay fila activa en `CorrelativosDocumento` para contratos.

Conclusión:

- la numeración `CT...` no está activa hoy en producción en esa BD;
- pero la empresa ya usa `TipoDoc` como marco de todos sus documentos;
- por eso OSS puede y debe implementarla como evolución explícita, no como dato ya operativo en `Sys_GMS_ES`.

### 6. Renovación actual

`CONTRATOS_Renovar` actualiza:

- `Fecha_Vencimiento`
- `Observaciones`

e inserta historial de tipo `RENOVACIÓN`.

No cambia:

- número del contrato;
- `Fecha_Inicio`;
- estado;
- archivo;
- flag de firma.

### 7. Trazabilidad por contrato

Hoy no existe en `Sys_GMS_ES` una tabla puente real contrato-cilindro.

Las vistas disponibles son de:

- resumen por cliente;
- próximos a vencer;
- recientemente vencidos;
- último evento;
- alerta de contacto.

La trazabilidad real de cilindros por contrato es un gap que OSS deberá construir.

## Decisiones OSS de esta v1

### 1. Contrato como documento numerado

OSS tratará el contrato como documento numerado propio del dominio de suministro.

Esto implica:

- `Cod_TipoDoc = 4` debe terminar con `PrefijoDoc = CT`;
- debe existir configuración activa en `SerieConfiguracion`;
- debe existir correlativo por almacén/año en `CorrelativosDocumento`;
- el contrato se mostrará al usuario con número visible tipo `CT...`.

Esta es una construcción nueva OSS sustentada sobre el patrón documental legacy.

### 2. Renovación sin nuevo número

La renovación del contrato:

- no genera nuevo número documental;
- mantiene `contract_number`;
- actualiza fechas y otros campos permitidos;
- registra historial de renovación.

### 3. Contrato por tipo, no por cilindro fijo

El contrato representa alquiler/suministro/reposición por tipo de envase.

Por tanto:

- no queda amarrado a un solo cilindro permanente;
- puede acumular múltiples cilindros relacionados durante su vigencia;
- esa relación debe quedar trazable a nivel documental.

### 4. Catálogo de tipos de contrato

OSS crea catálogo propio de tipos de contrato.

Mínimo esperado:

- diario;
- mensual;
- anual.

La lista final puede ampliarse con otros tipos operativos o comerciales, pero ya no se modelará como texto libre.

### 5. Estado “por firmar”

OSS introduce un estado documental `PENDING_SIGNATURE` / `POR_FIRMAR` para contratos emitidos automáticamente o aún no formalizados.

Esto no existe hoy como estado persistido en `Sys_GMS_ES`; es construcción nueva OSS basada en la necesidad operativa descrita por el usuario.

## No objetivos

Esta primera versión NO cubre:

- firma electrónica avanzada legal;
- generación de PDFs complejos desde plantilla final;
- facturación automática del alquiler;
- reglas fiscales/contables asociadas al contrato;
- automatización completa de correo si aún no existe infraestructura transversal;
- reescritura de todos los flujos de agenda legacy no relacionados directamente con contratos.

## Diseño

### 1. Separación de conceptos

Se distinguen dos capas documentales:

1. **Contrato de suministro**
   - documento comercial/operativo de alquiler o suministro;
   - número propio `CT...`;
   - duración y renovación;
   - trazabilidad documental de cilindros relacionados.
2. **Documentos de movimiento**
   - `SC`, `IC`, `IP`, `SP`;
   - registran entregas, recepciones e intercambios físicos;
   - siguen siendo documentos distintos del contrato.

### 2. Identidad documental

El contrato tendrá identidad documental visible:

| Campo | Tipo | Propósito |
|------|------|-----------|
| `document_type_code` | `int` | `Cod_TipoDoc`, para contratos `4` |
| `document_prefix` | `str` | prefijo visible, `CT` |
| `series` | `str` | prefijo + almacén + año |
| `number` | `int` | correlativo numérico |
| `contract_number` | `str` | representación final visible |

Regla general:

`contract_number = {series}-{correlativo_padded}`

Ejemplo v1:

- `series = CT4UL26`
- `number = 1`
- `contract_number = CT4UL26-000001`

### 3. Mapeo del almacén en la serie

Queda pendiente de cierre exacto cómo representar el almacén en la serie contractual:

1. usar código corto visible (`4UL`);
2. usar código normalizado de 2 caracteres;
3. usar valor interno compatible con `CorrelativosDocumento`.

La v1 de spec permite cualquiera, pero exige:

- consistencia;
- unicidad por almacén;
- misma regla en backend, UI y migraciones.

### 4. Momento de generación del número

Queda pendiente de cierre final si el número se consume:

1. al crear;
2. al emitir;
3. al pasar a `POR_FIRMAR`;
4. al pasar a `VIGENTE`.

Recomendación de esta v1:

- consumir el número cuando el contrato deja de ser borrador interno y pasa a documento emitido (`POR_FIRMAR` o equivalente).

### 5. Modelo `lg_cylinder_contracts`

```python
class LogisticsCylinderContract(Base):
    __tablename__ = "lg_cylinder_contracts"

    id: Mapped[str]
    tenant_id: Mapped[str]
    branch_id: Mapped[str | None]
    warehouse_id: Mapped[str | None]

    legacy_contract_code: Mapped[int | None]

    document_type_code: Mapped[int]          # 4 = Contrato de Suministro
    document_prefix: Mapped[str]             # CT
    series: Mapped[str | None]
    number: Mapped[int | None]
    contract_number: Mapped[str | None]

    contract_type_id: Mapped[str]
    status: Mapped[str]                      # DRAFT | PENDING_SIGNATURE | ACTIVE | EXPIRED | CANCELLED

    customer_id: Mapped[str]

    start_date: Mapped[date]
    end_date: Mapped[date | None]
    signed_at: Mapped[datetime | None]
    signed_by: Mapped[str | None]
    signature_type: Mapped[str | None]
    signed_flag: Mapped[bool]

    contract_file_path: Mapped[str | None]
    notes: Mapped[str | None]
    observations: Mapped[str | None]

    created_by: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    cancelled_at: Mapped[datetime | None]
    cancellation_reason: Mapped[str | None]
```

Notas:

- `contract_number` es identidad documental visible y no debe tratarse como campo transicional a ocultar;
- `signed_flag` replica la intención de `Firmado_Digital`;
- `status` puede ser más rico que en `Sys_GMS_ES`, pero debe documentarse como extensión OSS.

### 6. Catálogo `contract_types`

OSS crea catálogo propio, por ejemplo:

```python
class LogisticsContractType(Base):
    __tablename__ = "lg_contract_types"

    id: Mapped[str]
    tenant_id: Mapped[str]
    code: Mapped[str]               # DAILY | MONTHLY | ANNUAL | ...
    name: Mapped[str]               # Diario | Mensual | Anual
    duration_unit: Mapped[str]      # DAY | MONTH | YEAR
    duration_value: Mapped[int]
    is_active: Mapped[bool]
```

### 7. Relación contrato-cilindro

OSS agrega tabla puente para trazabilidad documental por contrato:

```python
class LogisticsCylinderContractLink(Base):
    __tablename__ = "lg_cylinder_contract_links"

    id: Mapped[str]
    tenant_id: Mapped[str]
    contract_id: Mapped[str]
    cylinder_id: Mapped[str]
    movement_id: Mapped[str | None]
    linked_at: Mapped[datetime]
    unlinked_at: Mapped[datetime | None]
    link_reason: Mapped[str]        # DELIVERY | EXCHANGE | RETURN | MANUAL
    notes: Mapped[str | None]
```

Esto cubre un gap real del legacy actual.

### 8. Historial contractual

```python
class LogisticsCylinderContractHistory(Base):
    __tablename__ = "lg_cylinder_contract_history"

    id: Mapped[str]
    tenant_id: Mapped[str]
    contract_id: Mapped[str]
    event_type: Mapped[str]         # CREATED | RENEWED | CANCELLED | FILE_UPDATED | SIGNED
    description: Mapped[str | None]
    occurred_at: Mapped[datetime]
    created_by: Mapped[str | None]
```

Compatibilidad mínima con legacy:

- modificación;
- renovación;
- anulación.

### 9. Endpoints

| Método | Ruta | Estado deseado |
|--------|------|----------------|
| `GET` | `/cylinders/contracts` | existe |
| `GET` | `/cylinders/contracts/{id}` | existe |
| `POST` | `/cylinders/contracts` | existe |
| `PATCH` | `/cylinders/contracts/{id}` | existe |
| `POST` | `/cylinders/contracts/{id}/issue` | falta |
| `POST` | `/cylinders/contracts/{id}/sign` | falta |
| `POST` | `/cylinders/contracts/{id}/renew` | falta |
| `POST` | `/cylinders/contracts/{id}/cancel` | existe/parcial |
| `GET` | `/cylinders/contracts/{id}/history` | falta |
| `GET` | `/cylinders/contracts/{id}/cylinders` | falta |
| `GET` | `/customers/{customer_id}/contracts` | falta |

### 10. Reglas de negocio

1. `TipoDoc` es la fuente de verdad del tipo documental del contrato;
2. el contrato usa documento propio `CT...` como construcción nueva OSS alineada al patrón legacy de numeración;
3. `SC`, `IC`, `IP` y `SP` no son contratos, sino documentos de movimiento distintos;
4. la renovación no genera nuevo `contract_number`;
5. la firma posterior no cambia el número del contrato;
6. el contrato puede estar `PENDING_SIGNATURE` antes de quedar firmado;
7. el contrato no está amarrado a un cilindro fijo;
8. el contrato debe poder reportar todos los cilindros relacionados durante su vigencia;
9. terminar/cancelar contrato no implica por sí solo liberar físicamente cilindros;
10. la agenda de recojo/cambio/renovación debe dispararse por reglas operativas, evitando duplicados.

### 11. Agenda

Esta v1 reconoce tres grupos de tareas relevantes:

- renovación de contrato;
- formalización/firma pendiente;
- recojo/cambio derivado de intercambios o recepciones.

Regla mínima:

- no duplicar tareas activas equivalentes para el mismo contrato o evento.

### 12. Frontend

La sección `Contratos` debe existir en catálogo de clientes, con al menos:

- número de contrato;
- tipo de contrato;
- fecha de firma;
- fecha de inicio;
- fecha de vencimiento;
- estado;
- firmado sí/no;
- archivo del contrato;
- observaciones;
- acciones: crear, editar, renovar, anular, ver archivo.

Además:

- la ficha de cilindro debe mostrar contratos relacionados;
- el detalle del contrato debe mostrar historial y cilindros vinculados;
- la UI debe distinguir contrato de documentos `SC`/`IC`/`IP`/`SP`.

### 13. Vistas legacy a replicar primero

Prioridad de replicación funcional:

1. `Vista_Resumen_Contratos_PorCliente`
2. `Vista_Contratos_ProximosAVencer`
3. `Vista_Contratos_UltimoEvento`
4. `Vista_Contratos_Alerta_Contacto`
5. `Vista_Contratos_RecientementeVencidos`

## Eventos

- `logistics.cylinder_contract.created`
- `logistics.cylinder_contract.issued`
- `logistics.cylinder_contract.signed`
- `logistics.cylinder_contract.updated`
- `logistics.cylinder_contract.renewed`
- `logistics.cylinder_contract.cancelled`
- `logistics.cylinder_contract.cylinder_linked`
- `logistics.cylinder_contract.cylinder_unlinked`

## Criterios de aceptación

1. la spec distingue explícitamente entre evidencia real de `Sys_GMS_ES` y construcción nueva OSS;
2. el contrato se modela como documento `CT...` y no se confunde con `SC`/`IC`/`IP`/`SP`;
3. la renovación no genera nuevo número de contrato;
4. el contrato puede existir por tipo de servicio/envase, no por bombona fija;
5. existe catálogo de tipos de contrato en OSS;
6. existe historial contractual visible;
7. existe base de trazabilidad documental de cilindros por contrato;
8. la ficha del cliente tiene apartado `Contratos`;
9. la agenda contractual evita duplicados de tareas activas equivalentes;
10. la implementación deja claro qué partes copian `Sys_GMS_ES` y qué partes completan gaps del legacy.

## Dependencias

- `0023C` para profundizar timeline/trazabilidad documental si se quiere una vista unificada;
- módulo de clientes/CRM para la sección `Contratos` del cliente;
- agenda/logística operativa para tareas de recojo, cambio y renovación.

## Migración

Cambios necesarios sobre la implementación actual:

1. reintroducir y consolidar `contract_number` como identidad documental visible del contrato;
2. agregar `document_type_code`, `document_prefix`, `series`, `number` y `warehouse_id`;
3. dejar de tratar `contract_number` como campo transicional a ocultar;
4. reemplazar `contract_type` libre por catálogo propio de contratos;
5. agregar estado `PENDING_SIGNATURE` y flujo de emisión/firma;
6. agregar historial contractual explícito;
7. agregar relación contrato-cilindro trazable;
8. implementar `renew` sin nuevo número;
9. revisar agenda contractual y deduplicación;
10. actualizar frontend para presentar contratos como documentos `CT...` dentro del catálogo de clientes.
