# SPEC 0023R - Contactos y responsables

## Estado

Implementada

## Contexto

`0023D` ya cerro el customer core minimo para:

- identidad fiscal/comercial;
- direcciones base por proposito;
- contactos base enriquecidos;
- busqueda multi-criterio;
- frontera CRM vs `logistics`.

Sin embargo, el legacy y `Grab2` muestran que el negocio necesita una capa mas rica de
personas vinculadas al cliente:

- una empresa puede tener varios responsables;
- un contacto puede pertenecer al cliente general o a una sede concreta;
- una sede puede tener una persona principal de recepcion y otras secundarias;
- oficina necesita ubicar a quien compra, a quien factura y a quien recibe;
- el responsable operativo de una entrega concreta no siempre coincide con el contacto
  base del cliente.

`0023D` resolvio el contacto base minimo. `0023R` abre la capa siguiente: contactos por
contexto y responsables por sede, sin mezclar todavia ownership comercial ni pricing.

## Objetivo

Extender CRM para que pueda modelar:

- contactos base del cliente;
- contactos asociados a una direccion / sede base del cliente;
- responsables principales y secundarios por sede;
- propositos funcionales del contacto (facturacion, cobranza, compras, operaciones,
  recepcion, general);
- una UX clara para que oficina pueda saber a quien llamar segun el contexto.

## No objetivos

Esta spec NO cubre:

- agente comercial asignado al cliente;
- supervisor comercial o de zona;
- comisiones;
- descuentos o condiciones comerciales;
- permisos comerciales especiales para aprobar presupuestos;
- agenda, ruta o recepcion operativa del delivery point en tiempo real;
- pricing, presupuestos o contratos.

Eso vive en `0023S`, `0023U`, `0023V` y specs futuras.

## Alcance

Toca:

- `plugins/crm/backend/models.py`
- `plugins/crm/backend/schemas.py`
- `plugins/crm/backend/router.py`
- `plugins/crm/backend/services/addresses.py` y/o nuevo servicio dedicado a contactos
- `plugins/crm/frontend/types.ts`
- `plugins/crm/frontend/components/ModalDetalleCliente.tsx`
- `plugins/crm/frontend/components/ModalNuevoCliente.tsx` o flujo equivalente de cliente
- `docs/contracts/crm-api.md`
- `apps/api/tests/test_crm_plugin.py`

Puede rozar `plugins/logistics/` solo para aclarar contrato, pero no debe mover ownership
operativo hacia CRM.

## Reglas de negocio

1. Un cliente puede tener muchos contactos.
2. Un contacto puede ser general del cliente o estar vinculado a una direccion base
   concreta mediante `address_id`.
3. Una direccion/sede puede tener varios contactos.
4. Debe poder marcarse un responsable principal por proposito dentro de un mismo scope.
5. Un mismo contacto puede tener telefono y email simultaneamente.
6. El responsable operativo que recibe una entrega concreta sigue siendo dato operativo de
   `logistics`, aunque pueda coincidir con un contacto CRM.
7. CRM modela personas y propositos base; `logistics` modela la ejecucion diaria.
8. Si un contacto esta ligado a una direccion, esa direccion debe pertenecer al mismo cliente.

## Datos

### Evolucion de `crm_customer_contacts`

`crm_customer_contacts` sigue siendo la tabla base, pero deja de ser solo una lista plana
de canales.

Debe soportar al menos:

- `full_name`
- `label`
- `role`
- `phone`
- `email`
- `address_id` nullable
- `contact_type` como compatibilidad liviana
- `is_primary`
- `contact_purpose` nuevo
- `notes` opcional

### `contact_purpose`

Catalogo inicial propuesto:

- `GENERAL`
- `FACTURACION`
- `COBRANZA`
- `COMPRAS`
- `OPERACIONES`
- `RECEPCION`
- `OTRO`

Reglas:

- `GENERAL` cubre contactos sin clasificacion fina;
- `RECEPCION` no reemplaza el dato operativo instantaneo de `logistics`, pero permite
  registrar el responsable usual por sede;
- `FACTURACION` y `COBRANZA` preparan mejor la futura integracion con facturacion/cobros.

### Primary por scope y proposito

`is_primary` deja de leerse como "el unico principal absoluto del cliente".

Se interpreta como principal dentro de:

- `customer_id`
- `address_id` (nullable)
- `contact_purpose`

Ejemplos:

- un contacto principal de `FACTURACION` para todo el cliente;
- un contacto principal de `RECEPCION` para una sede concreta;
- otro contacto principal de `COBRANZA` a nivel cliente.

## API esperada

### Contactos de cliente

- `GET /customers/{id}/contacts`
- `POST /customers/{id}/contacts`
- `PUT /contacts/{id}`
- `DELETE /contacts/{id}`

### Filtros recomendados para `GET /customers/{id}/contacts`

- `address_id` opcional
- `contact_purpose` opcional
- `active_only` opcional

### Response minima

Cada contacto debe exponer al menos:

- `id`
- `full_name`
- `label`
- `role`
- `phone`
- `email`
- `address_id`
- `contact_purpose`
- `contact_type`
- `is_primary`
- `is_active`

## Frontend esperado

### Ficha de cliente

La ficha debe permitir:

- ver contactos agrupados o filtrados por direccion/sede;
- ver el proposito del contacto;
- distinguir entre contacto general y contacto por sede;
- marcar responsable principal por proposito cuando corresponda.

### UX minima

- no volver al modelo de dropdown simple `PHONE/EMAIL` + `value`;
- usar el modelo enriquecido como base;
- permitir vincular un contacto a una direccion base con `Combobox`.

## Permisos

No requiere permisos nuevos en este corte.

Se mantiene:

- `crm.customer.read`
- `crm.customer.update`

Si mas adelante hay visibilidad restringida de contactos sensibles, se abrira una spec
separada o una ampliacion de permisos.

## Eventos

Agregar eventos CRM explicitos para contactos:

- `crm.customer.contact_added`
- `crm.customer.contact_updated`
- `crm.customer.contact_removed`

Payload minimo sugerido:

```json
{
  "customer_id": "uuid",
  "contact_id": "uuid",
  "address_id": "uuid|null",
  "contact_purpose": "RECEPCION"
}
```

## Migraciones

Requiere al menos una nueva revision Alembic en `apps/api/migrations/versions/` para:

- agregar `contact_purpose`;
- agregar `notes` si aun no existe en contactos;
- endurecer la semantica de `is_primary` por scope/proposito si hace falta con indices
  parciales o validacion en servicio.

## Auditoria y observabilidad

Toda alta, edicion o baja de contacto debe:

- registrar auditoria;
- incluir `customer_id` y `contact_id`;
- incluir `address_id` cuando aplique;
- reflejar cambios relevantes de proposito o principalidad.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Mezclar responsable base con responsable operativo del delivery point | alto | mantener en la spec la frontera CRM vs `logistics` |
| Inflar demasiado el modelo de contactos | medio | limitar este corte a proposito + direccion + principalidad |
| Convertir `is_primary` en un campo ambiguo | medio | definirlo por scope + proposito |
| Repetir personas iguales en varias sedes | medio | permitir reuse logico via UI, pero no exigir deduplicacion automatica en este corte |

## Criterios de aceptacion

1. un cliente puede tener contactos generales y contactos ligados a una direccion base;
2. una sede puede tener varios contactos y uno principal por proposito;
3. CRM puede distinguir al menos contactos de facturacion, cobranza, compras, operaciones
   y recepcion;
4. la API permite crear, editar, listar y eliminar contactos con `contact_purpose`;
5. la ficha de cliente permite ver claramente que contactos pertenecen al cliente y cuales a
   una sede concreta;
6. no se mueve a CRM la responsabilidad operativa diaria de `delivery_points`.

## Pruebas requeridas

- unitarias/servicio para validar `address_id` del mismo cliente;
- unitarias/servicio para principalidad por scope/proposito;
- integración API de crear/listar/editar/eliminar contacto;
- frontend de visualizacion y guardado de contactos por sede.

## Notas para agentes

- no usar `0023R` para introducir agente comercial o supervisor;
- si aparece una necesidad de owner interno del cliente, moverla a `0023S`;
- si aparece una necesidad de precio, comision o presupuesto, moverla a `0023U` / `0023V`;
- si una regla pertenece a recepcion, agenda o ruta diaria, mantenerla en `logistics`.
