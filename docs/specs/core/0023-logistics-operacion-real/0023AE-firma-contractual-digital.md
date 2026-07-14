# SPEC 0023AE — Firma contractual digital obligatoria

## Estado

Primera version — 2026-07-08

> Esta spec toma como base operativa lo observado en `Grab2`: hoy la firma contractual puede ser fisica o diferida.
> OSS decide elevar ese comportamiento a un modelo nuevo: **la firma contractual digital sera obligatoria**.

## Problema

La v1 de contratos (`0023AD`) ya introdujo:

- contrato numerado `CT...`;
- estado `PENDING_SIGNATURE`;
- archivo contractual asociado;
- campos `signed_at`, `signed_by`, `signature_type`, `signed_flag`.

Pero todavia no existe un modelo canonico para:

1. generar el PDF contractual desde el sistema;
2. capturar firma digital dentro de la aplicacion;
3. validar la identidad del firmante;
4. bloquear activacion operativa si el contrato no fue firmado digitalmente;
5. reutilizar el flujo de firma en otros modulos sin duplicar logica en `logistics`.

En `Grab2` la operacion actual todavia contempla:

- contrato enviado por correo para impresion/firma/escaneo;
- eventual firma digital futura validada por un tercero;
- contrato visible al repartidor cuando deba formalizarse;
- contrato como PDF generado por el sistema.

OSS no debe quedarse en esa solucion intermedia. Debe convertir la firma digital en obligatoria y trazable.

## Objetivo

Construir la firma contractual digital como capacidad transversal del sistema con estas reglas:

1. el sistema genera el PDF contractual oficial;
2. el contrato solo puede pasar a `ACTIVE` cuando tenga firma digital valida;
3. la captura de firma y el flujo de verificacion viven en **core**, no en `logistics`;
4. `logistics` solo define el contrato, la plantilla y los metadatos de negocio;
5. el mismo motor debe poder reutilizarse luego en carta porte, albaran u otros documentos firmables.

## Evidencia de Grab2

### 1. El contrato debe poder generarse antes o despues de la entrega

- `20 de mayo 2025_transcripcion.txt:75-79`

### 2. El contrato debe aparecer al repartidor cuando toque firmarlo

- `20 de mayo 2025_transcripcion.txt:80`

### 3. El contrato se entiende como PDF

- `20 de mayo 2025_transcripcion.txt:80-81`

### 4. La firma digital era una necesidad futura con validacion de tercero

- `20 de mayo 2025_transcripcion.txt:82-85`

### 5. El contrato es parte fundamental de la integracion operativa

- `20 de mayo 2025_transcripcion.txt:89-90`

## Decision OSS

### 1. La firma digital es obligatoria

En OSS no existira modo operativo normal de contrato firmado solo en papel.

Esto implica:

- `signature_type = DIGITAL` como modo por defecto y esperado;
- `signed_flag = true` solo cuando exista firma digital valida;
- un contrato `PENDING_SIGNATURE` no puede considerarse `ACTIVE`;
- la activacion manual sin firma digital queda prohibida salvo flujo excepcional auditado con permiso administrativo especifico futuro.

### 2. El PDF oficial lo genera el sistema

El documento contractual no se sube primero como archivo externo cualquiera.

Flujo normal:

1. `logistics` crea/actualiza borrador contractual;
2. core renderiza el PDF oficial desde plantilla y payload estructurado;
3. core abre una sesion de firma;
4. el cliente o firmante autorizado firma digitalmente;
5. core sella el PDF firmado y devuelve referencia versionada;
6. `logistics` marca el contrato como firmado/activo.

### 3. Todo lo generico vive en core

Como la firma digital, el render PDF y la verificacion del firmante son capacidades reutilizables, deben vivir fuera del plugin.

## Alcance arquitectonico

### Core (nuevo ownership generico)

Core sera dueño de:

1. definicion de `DocumentTemplate` reutilizable;
2. renderizado PDF generico;
3. almacenamiento de versiones de documento firmable;
4. sesiones de firma digital;
5. captura de firma en app/web;
6. adaptador a proveedor externo de verificacion/firma si aplica;
7. auditoria y evidencia de firma;
8. estados genericos de documento firmable.

### Logistics (owner de negocio)

`logistics` sera dueño de:

1. datos del contrato;
2. reglas de cuando debe existir contrato;
3. relacion cliente/contrato/envases;
4. evento que dispara solicitud de firma;
5. condiciones para activacion y renovacion.

## Diseno

### 1. Componentes genericos nuevos en core

#### 1.1 `core/documents/templates`

Define plantillas reutilizables.

Ejemplo inicial:

- `CONTRACT_SUPPLY_V1`

#### 1.2 `core/documents/render`

Servicio generico para convertir payload estructurado en PDF.

```python
render_document_pdf(template_code: str, payload: dict, *, tenant_id: str) -> RenderedDocument
```

#### 1.3 `core/signatures`

Servicio generico de firma digital.

Responsabilidades:

- abrir sesion de firma;
- registrar firmante esperado;
- recibir evidencia de firma;
- validar codigo/token/proveedor externo si aplica;
- sellar version final del PDF;
- emitir resultado firmado.

#### 1.4 `core/media/documents`

Storage canonico de PDFs borrador y firmados, versionados por documento.

### 2. Modelo minimo en core

```python
class CoreDocumentVersion(Base):
    __tablename__ = "core_document_versions"

    id: Mapped[str]
    tenant_id: Mapped[str]
    module: Mapped[str]                # logistics
    entity_type: Mapped[str]           # cylinder_contract
    entity_id: Mapped[str]
    template_code: Mapped[str]         # CONTRACT_SUPPLY_V1
    version_number: Mapped[int]
    status: Mapped[str]                # DRAFT | PENDING_SIGNATURE | SIGNED | VOID
    file_path: Mapped[str]
    sha256: Mapped[str]
    created_by: Mapped[str | None]
    created_at: Mapped[datetime]
```

```python
class CoreSignatureSession(Base):
    __tablename__ = "core_signature_sessions"

    id: Mapped[str]
    tenant_id: Mapped[str]
    document_version_id: Mapped[str]
    signer_name: Mapped[str | None]
    signer_email: Mapped[str | None]
    signer_phone: Mapped[str | None]
    signer_role: Mapped[str | None]    # CLIENT_REP | INTERNAL_USER
    provider: Mapped[str]              # INTERNAL | THIRD_PARTY
    status: Mapped[str]                # PENDING | SENT | COMPLETED | FAILED | EXPIRED
    verification_channel: Mapped[str]  # EMAIL | SMS | IN_APP
    verification_ref: Mapped[str | None]
    completed_at: Mapped[datetime | None]
    created_at: Mapped[datetime]
```

```python
class CoreSignatureEvidence(Base):
    __tablename__ = "core_signature_evidence"

    id: Mapped[str]
    tenant_id: Mapped[str]
    signature_session_id: Mapped[str]
    evidence_type: Mapped[str]         # OTP_OK | DRAWN_SIGNATURE | PROVIDER_RECEIPT
    payload_json: Mapped[dict]
    created_at: Mapped[datetime]
```

### 3. Extensiones minimas en logistics

`lg_cylinder_contracts` mantiene:

- `signed_flag`
- `signed_at`
- `signed_by`
- `signature_type`

Y agrega/usa semanticamente:

- `document_version_id` o referencia equivalente al PDF canonico firmado;
- `status = PENDING_SIGNATURE | ACTIVE` como flujo real.

### 4. Flujo funcional

#### 4.1 Crear contrato

1. usuario crea contrato;
2. contrato queda en `DRAFT`;
3. sistema genera PDF borrador `CONTRACT_SUPPLY_V1`;
4. usuario emite contrato;
5. estado pasa a `PENDING_SIGNATURE`.

#### 4.2 Firmar contrato

1. core crea `CoreSignatureSession`;
2. se notifica al firmante por canal configurado;
3. firma se captura dentro de app/web o via proveedor externo integrado;
4. core registra evidencia;
5. PDF final firmado queda versionado;
6. `logistics` recibe callback/resultado y marca:
   - `signed_flag = true`
   - `signed_at = now`
   - `signature_type = DIGITAL`
   - `status = ACTIVE`

#### 4.3 Renovacion

1. renovacion contractual actualiza datos permitidos;
2. si requiere nueva formalizacion documental, se crea nueva version PDF;
3. se abre nueva sesion de firma digital;
4. el numero de contrato `CT...` no cambia.

### 5. UI esperada

#### En logistics/contracts

- boton `Generar PDF`
- boton `Enviar a firma`
- estado visible: `BORRADOR`, `POR FIRMAR`, `FIRMADO`, `ACTIVO`
- visor del PDF generado
- historial de versiones del documento
- historial de sesiones de firma

#### En agenda/repartidor

- si un contrato necesita formalizacion en campo, la tarea lo debe indicar;
- el repartidor ve que el contrato esta pendiente de firma;
- si la firma digital ocurre dentro de la app, usa el flujo core de firma, no una implementacion local del plugin.

## Reglas de negocio

1. un contrato emitido sin firma digital queda en `PENDING_SIGNATURE`.
2. un contrato sin `signed_flag` no puede activarse operativamente.
3. toda firma debe dejar PDF versionado y evidencia verificable.
4. la identidad del firmante debe quedar trazable por nombre, canal y evidencia.
5. `signature_type = DIGITAL` es el flujo normal y obligatorio en OSS.
6. el plugin no guarda PDFs arbitrarios como version oficial firmada sin pasar por core.
7. si existe excepcion administrativa futura, debe quedar super auditada y no es parte de esta spec.

## Endpoints esperados

### Core

| Metodo | Ruta | Proposito |
|---|---|---|
| `POST` | `/core/documents/render` | generar PDF desde plantilla |
| `POST` | `/core/signatures/sessions` | abrir sesion de firma |
| `POST` | `/core/signatures/sessions/{id}/complete` | completar firma |
| `GET` | `/core/documents/{id}/download` | descargar PDF versionado |
| `GET` | `/core/signatures/sessions/{id}` | ver estado de firma |

### Logistics

| Metodo | Ruta | Proposito |
|---|---|---|
| `POST` | `/cylinders/contracts/{id}/issue` | pasar a `PENDING_SIGNATURE` y generar PDF |
| `POST` | `/cylinders/contracts/{id}/sign` | consumir resultado de firma digital |
| `GET` | `/cylinders/contracts/{id}` | incluir estado y documento actual |
| `GET` | `/cylinders/contracts/{id}/history` | incluir eventos `SIGNED`, `FILE_UPDATED`, `SIGNATURE_REQUESTED` |

## Permisos

### Core genericos

- `core.documents.render`
- `core.signature.request`
- `core.signature.complete`
- `core.documents.view`

### Logistics

- `logistics.contract.view`
- `logistics.contract.create`
- `logistics.contract.update`
- `logistics.contract.activate`

No se debe crear un permiso plugin-specific para logica de firma si el capability es transversal.

## Eventos

### Core

- `core.document.rendered`
- `core.signature.session_created`
- `core.signature.completed`
- `core.signature.failed`

### Logistics

- `logistics.cylinder_contract.issued`
- `logistics.cylinder_contract.signed`

## No objetivos

- no resolver aun la integracion legal exacta con un proveedor tercero concreto;
- no diseñar aqui la facturacion automatica de renovaciones;
- no imponer que el repartidor sea siempre quien capture la firma;
- no mover contratos fuera de `logistics`.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Implementar firma solo dentro de logistics | alto | mover capacidad a core desde el dia 1 |
| Guardar PDF manual subido como oficial | alto | core debe versionar y sellar el documento canónico |
| Confundir renovacion con vencimiento duro | medio | modelar `renewal_date` y estados operativos con claridad |
| Acoplarse demasiado pronto a un proveedor tercero | medio | abstraer por `core/signatures` |
| Bloquear operacion si falla proveedor externo | medio | permitir sesion pendiente/reintento sin perder borrador |

## Criterios de aceptacion

1. existe una spec activa `0023AE` para firma contractual digital.
2. la firma digital queda definida como obligatoria en OSS.
3. el PDF contractual oficial se genera desde el sistema, no por carga manual externa como flujo principal.
4. las capacidades genericas de PDF/firma viven en core y no en `logistics`.
5. un contrato `PENDING_SIGNATURE` no puede considerarse `ACTIVE` sin evidencia de firma digital.
6. queda definido un modelo minimo de documentos versionados y sesiones de firma.
7. la UI esperada de contratos contempla generar PDF, enviar a firma y ver estado de firma.
8. el index de `0023` deja de tratar `0023AE` como diferido ambiguo y lo reconoce como sub-spec activa.
