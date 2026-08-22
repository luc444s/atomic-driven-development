# A.SPEC API-REST-CON-0015 — Endpoint POST /api/stock/movement (write-back egreso legacy)

## WHY
El flujo exige que al cargar un envase a un almacén móvil (OSS Postgres), el
stock del legacy se descuente. El stock legacy es **computado**
(`PRODUCTO_MOSTRARsoloSTOCK`), no almacenado; descontarlo = insertar un
`Movimiento`/`DetalleMovimiento` de EGRESO que cumpla los filtros
(`inventario=1, Estado=1, TipoAtencion=1`).

## WHAT
`POST /api/stock/movement` recibe
`{ cod_producto, almacen, cantidad, idempotency_key }` y crea un egreso en
legacy (`StkEgreso = cantidad`) vía el API, de forma que el stock computado
del legacy disminuya.

## SCOPE
- Inserción de `Movimiento` + `DetalleMovimiento` (egreso) en legacy por el API.
- Validación para que el egreso afecte el reporte (filtros correctos).

## OUT OF SCOPE
- Lectura de stock (A.SPEC 0011).
- Modelo de almacén móvil (OSS, ver TMS-DOMAIN).

## CONTRACT
- `201` al crear; `200` si ya existía (misma `idempotency_key`).
- El egreso cumple `inventario=1, Estado=1, TipoAtencion=1`.
- No permite egreso arbitrario que deje stock negativo sin regla de negocio.

## INVARIANTS
- Solo vía API; Python nunca toca SQL Server directo.
- Idempotente por `idempotency_key` (no doble descuento).
- Solo descuenta lo que OSS origina (despacho/carga).

## VERIFICATION (TEST REAL, NO MOCK)
Contra API real + BD real: tras `POST` para `ABRAZADERAS` cod 1868, almacén 1,
cantidad 5, key K, el reporte `PRODUCTO_MOSTRARsoloSTOCK` pasa de **53 → 48**.
Re-enviar misma key K → sigue **48** (idempotente). Prohibido mock.

## ROLLBACK
- Compensación: endpoint para anular el egreso (revertir el `Movimiento`) por
  `idempotency_key`.

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
  - escritura Movimiento/DetalleMovimiento legacy
indirect:
  - stock legacy, stock fijo OSS
must_not_affect:
  - ERP app
  - auth/tenancy
```
