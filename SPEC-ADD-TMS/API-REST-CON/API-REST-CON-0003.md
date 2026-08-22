# A.SPEC API-REST-CON-0003 — Endpoint GET /api/clientes/{id}/puntos

## WHY
Los puntos de entrega del cliente (`vehiculo_cliente`) alimentan las rutas de
TMS (OSS ya tiene `VehicleDeliveryPoint` / `crm.CustomerAddress`).

## WHAT
`GET /api/clientes/{id}/puntos` retorna JSON de los puntos de entrega de un
cliente legacy (tabla `vehiculo_cliente` filtrada por `cliente`).

## SCOPE
- Lectura de `vehiculo_cliente`: `cliente, direccion, telefono, contacto,
  ubigeo, zonaresp, correoresp`.
- Parámetro `id` = `Cod_Persona` del cliente.

## OUT OF SCOPE
- Creación/modificación de puntos en OSS (A.SPEC 0006).
- Otros catálogos.

## CONTRACT
- `200 application/json` con array de puntos.
- `404` si el cliente no existe o no tiene puntos.
- Cada punto expone `direccion, telefono, ubigeo, zona` (sin IDs crudos como
  etiqueta; usar `direccion` o `Sin dirección`).

## INVARIANTS
- Solo lectura.
- No expone el esquema interno de `vehiculo_cliente` más allá de los campos
  canónicos.

## VERIFICATION
- Cliente con puntos (legacy tiene 732 clientes con 769 filas) → array no vacío.
- Cliente inexistente → `404`.
- Respuesta `application/json`.

## ROLLBACK
- Quitar el handler de la ruta.

## CHANGE SURFACE
```yaml
allowed:
  - ERP-SYSTUTOR.API/Program.vb
prohibited:
  - plugins/**
```

## BLAST RADIUS
```yaml
direct:
  - lectura vehiculo_cliente
indirect:
  - logistics.VehicleDeliveryPoint / crm.CustomerAddress
must_not_affect:
  - escritura legacy
```
