# A.SPEC API-REST-CON-0002 — Endpoint GET /api/clientes

## WHY
TMS/crm necesita el catálogo de clientes del legacy para enlazarlo con
`crm.Customer` (OSS ya posee clientes; esto solo los expone).

## WHAT
`GET /api/clientes` retorna un array JSON de clientes legacy
(`Persona WHERE Cod_TipoPersona = 1`) con campos canónicos:
`id, dni, ruc, nombre, direccion, telefono, email`.

## SCOPE
- Lectura de `Persona` filtrada por tipo Cliente.
- Serialización JSON (Newtonsoft.Json, ya usado en `nubefact/`).

## OUT OF SCOPE
- Puntos de entrega del cliente (A.SPEC 0003).
- Autenticación (A.SPEC 0004).

## CONTRACT
- `200 application/json` con array de objetos.
- Cada item: `id` (Cod_Persona), `dni` (Dni_Persona), `ruc` (Ruc_Persona),
  `nombre` (Nom_Persona), `direccion`, `telefono`, `email` (mail_Persona).
- Si `nombre` falta → `"Sin asignar"` (no exponer ID crudo como nombre).

## INVARIANTS
- Solo lectura.
- No expone tablas internas ni otras personas (solo TipoPersona=1).
- No modifica `Persona`.

## VERIFICATION (TEST REAL, NO MOCK)
- Contra `ERP-SYSTUTOR.API` desplegada en Win10 apuntando a `Sys_Gas2_Plus`
  **real**, `GET /api/clientes` retorna el array con los **1872 clientes**
  reales del legacy (la respuesta incluye el total: 1872).
- El array contiene, entre otros, estos clientes reales del legacy:
  - `ASOCIACION IGLESIA ADVENTISTA DEL SEPTIMO DIA PERUANA DEL NORTE`
  - `AUTOMOTRIZ FREDY E.I.R.L.`
- Cada item con `id` y `nombre` presentes.
- Test: cliente con nombre nulo → `"Sin asignar"`.
- Prohibido validar con mocks: el endpoint debe golpear la BD legacy real.

## ROLLBACK
- Quitar el handler de la ruta en el listener. Sin efecto en BD.

## CHANGE SURFACE
```yaml
allowed:
  - ERP-SYSTUTOR.API/Program.vb
prohibited:
  - plugins/**
  - kernel/**
```

## BLAST RADIUS
```yaml
direct:
  - lectura Persona (Cliente) en SQL Server
indirect:
  - crm.Customer (al consumirse en 0006)
must_not_affect:
  - escritura de datos legacy
  - ERP app
```
