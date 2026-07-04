# SPEC 0023S - Gestion comercial

## Estado

Implementada

## Contexto

El legacy y `Grab2` muestran una capa comercial clara que hoy no existe en CRM:

- el cliente o la sede pertenecen a un agente/comercial;
- puede existir un supervisor por zona o por conjunto de agentes;
- oficina necesita saber a quien pertenece comercialmente una cuenta;
- el comercial puede negociar, pero no siempre puede grabar condiciones finales;
- la propiedad comercial no es lo mismo que el responsable que recibe o que el contacto de
  facturacion.

`0023D` ya cerro customer core y `0023R` abre la capa de personas de contacto.
`0023S` debe modelar la **propiedad comercial interna** del cliente, separada de:

- personas externas del cliente;
- usuarios operativos de reparto;
- motor de precios o presupuestos.

## Objetivo

Agregar una capa minima de ownership comercial en CRM para saber:

- que agente/comercial atiende un cliente;
- si una sede concreta tiene owner comercial distinto del cliente general;
- que supervisor interno cubre ese cliente o sede;
- que usuario puede ver o reclamar propiedad comercial de una cuenta.

## No objetivos

Esta spec NO cubre:

- descuentos;
- tarifas o precios especiales;
- presupuesto/cotizacion;
- comisiones calculadas;
- workflow de aprobacion comercial completo;
- remesas o cuentas por cobrar;
- permisos finos para modificar precios.

Todo eso se posterga a `0023U`, `0023V`, `0023X` y specs futuras.

## Alcance

Toca:

- `plugins/crm/backend/models.py`
- `plugins/crm/backend/schemas.py`
- `plugins/crm/backend/router.py`
- servicio nuevo o ampliado en `plugins/crm/backend/services/`
- `plugins/crm/frontend/types.ts`
- ficha de cliente y/o detalle de cliente en frontend CRM
- `docs/contracts/crm-api.md`
- `apps/api/tests/test_crm_plugin.py`

No debe mover `agent_user_id` operativo de `logistics` a CRM.

## Reglas de negocio

1. El owner comercial es un usuario interno (`users`), no un contacto externo del cliente.
2. Debe soportarse ownership a nivel cliente y override por direccion/sede cuando haga falta.
3. Debe distinguirse al menos entre:
   - `AGENT`
   - `SUPERVISOR`
4. Un cliente puede tener un agente principal y un supervisor principal.
5. Una sede puede heredar el owner comercial del cliente o definir uno propio.
6. `agent_user_id` en `lg_delivery_points` sigue siendo operativo y puede no coincidir con el
   owner comercial CRM.
7. Esta capa no define todavia precios ni descuentos; solo ownership y visibilidad.

## Datos

### Nueva tabla sugerida: `crm_customer_commercial_assignments`

Campos minimos:

- `id`
- `tenant_id`
- `customer_id`
- `address_id` nullable
- `user_id`
- `assignment_role`
- `is_primary`
- `is_active`
- `notes` nullable
- `created_at`
- `updated_at`

### `assignment_role`

Valores iniciales:

- `AGENT`
- `SUPERVISOR`

Opcionalmente puede reservarse `ACCOUNT_OWNER` para futura expansion, pero no es obligatorio
en este primer corte.

### Semantica de `address_id`

- `address_id = null` -> asignacion a nivel cliente
- `address_id != null` -> asignacion especifica para esa sede/direccion base

Si una sede no tiene asignacion propia, hereda visualmente la del cliente general.

## API esperada

### Asignaciones comerciales de cliente

- `GET /customers/{id}/commercial-assignments`
- `POST /customers/{id}/commercial-assignments`
- `PUT /commercial-assignments/{id}`
- `DELETE /commercial-assignments/{id}`

### Filtros recomendados

- `address_id` opcional
- `assignment_role` opcional
- `active_only` opcional

### Response minima

- `id`
- `customer_id`
- `address_id`
- `user_id`
- `assignment_role`
- `is_primary`
- `is_active`
- `notes`

No es obligatorio duplicar datos completos del usuario en la tabla; basta `user_id` y,
si conviene a la UX, un campo derivado `user_display_name` en responses.

## Frontend esperado

La ficha del cliente debe mostrar:

- agente comercial principal del cliente;
- supervisor principal del cliente;
- overrides por sede cuando existan;
- diferencia clara entre contacto del cliente y owner comercial interno.

No debe usar el mismo formulario visual para contactos externos y owners internos.

## Permisos

Agregar permisos nuevos:

- `crm.commercial.read`
- `crm.commercial.manage`

Razon:

- la propiedad comercial puede ser mas sensible que editar un telefono o una direccion;
- permite abrir despues reglas de visibilidad o gestion separadas sin romper contrato.

## Eventos

Agregar eventos:

- `crm.customer.commercial_assignment_added`
- `crm.customer.commercial_assignment_updated`
- `crm.customer.commercial_assignment_removed`

Payload minimo sugerido:

```json
{
  "customer_id": "uuid",
  "address_id": "uuid|null",
  "assignment_id": "uuid",
  "user_id": "uuid",
  "assignment_role": "AGENT"
}
```

## Migraciones

Requiere nueva revision Alembic en `apps/api/migrations/versions/` para crear la tabla
`crm_customer_commercial_assignments` con sus indices y FKs.

## Auditoria y observabilidad

Toda alta, cambio o baja de asignacion comercial debe:

- registrar auditoria;
- incluir `customer_id`, `address_id`, `user_id` y `assignment_role`;
- dejar trazabilidad de cambios de owner principal.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Mezclar contacto externo con owner interno | alto | usar tabla separada y UX separada |
| Usar `agent_user_id` de logistics como owner comercial | alto | dejar explicitamente que ese campo sigue siendo operativo |
| Querer meter descuentos/comisiones en esta spec | medio/alto | dejar pricing y comisiones fuera del alcance |
| Sobredisenar la jerarquia comercial | medio | limitar este corte a `AGENT` y `SUPERVISOR` |

## Criterios de aceptacion

1. un cliente puede tener agente y supervisor comercial en CRM;
2. una sede puede opcionalmente tener override comercial propio;
3. la API permite crear, editar, listar y eliminar asignaciones comerciales;
4. el frontend distingue entre contacto del cliente y owner comercial interno;
5. no se reutiliza `agent_user_id` de `logistics` como sustituto del owner comercial CRM;
6. no se introducen precios, descuentos ni comisiones dentro de esta spec.

## Pruebas requeridas

- integración API de CRUD de asignaciones comerciales;
- validacion de tenant para `user_id`, `customer_id` y `address_id`;
- pruebas de visibilidad de asignacion general vs override por sede;
- pruebas de permisos `crm.commercial.read/manage`.

## Notas para agentes

- no usar `0023S` para persistir precios o descuentos;
- no modelar comision calculada aqui;
- si una regla depende de quien recibe la mercancia en una entrega concreta, moverla a
  `logistics` o cruzarla con `0023R`, no con ownership comercial.
