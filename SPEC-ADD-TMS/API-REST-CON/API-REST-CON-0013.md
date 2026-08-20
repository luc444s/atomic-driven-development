# A.SPEC API-REST-CON-0013 — Endpoint GET /api/almacenes

## WHY
TMS/logistics necesita los almacenes del legacy. El legacy los modela con
`Almacen` (hay 2: OXIPUR EIRL, REPARTIDOR); se exponen vía API, no por acceso
directo a BD.

## WHAT
`GET /api/almacenes` retorna array JSON de almacenes (`Almacen`):
`cod, descripcion` (y `razon_social` si aplica).

## SCOPE
- Lectura de `Almacen`.

## OUT OF SCOPE
- Creación/edición de almacenes.
- Autenticación (A.SPEC 0004).

## CONTRACT
- `200 application/json` con array.
- item: `cod` (Cod_Almacen), `descripcion` (Desc_Almacen),
  `razon_social` (Cod_RazonSocial).
- El legacy tiene exactamente **2** almacenes.

## INVARIANTS
- Solo lectura.
- No modifica `Almacen`.

## VERIFICATION (TEST REAL, NO MOCK)
- Contra `ERP-SYSTUTOR.API` real → `GET /api/almacenes` retorna **2**
  almacenes reales:
  - `OXIPUR EMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA` (cod 1)
  - `REPARTIDOR` (cod 2)
- El conteo es 2.
- Prohibido validar con mocks: el endpoint golpea la BD legacy real.

## ROLLBACK
- Quitar handler de la ruta.

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
  - lectura Almacen
indirect:
  - logistics.Warehouse (al consumirse en 0014)
must_not_affect:
  - escritura legacy
  - ERP app
```
