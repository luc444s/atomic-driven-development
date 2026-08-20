# A.SPEC API-REST-CON-0012 — Mapeo stock legacy → plugins/stock (OSS)

## WHY
OSS ya posee stock (`plugins/stock`: balances, ledger, min/max). El legacy es
fuente de lectura; se enlaza, no se duplica.

## WHAT
Servicio de enlace que, desde `StockLegacy` (0011), hace upsert de balances
por `producto + almacen` en `plugins/stock`, usando el `Saldo` operacional
(vkardex), no el cache.

## SCOPE
- Upsert idempotente de balance por producto+almacen.
- Registro de correlation id (origen legacy).

## OUT OF SCOPE
- Sincronización inversa (OSS → legacy).
- Cálculo de stock operacional (eso lo hace el API, 0011).

## CONTRACT
- Idempotente: re-ejecutar no crea duplicados (match por producto+almacen).
- Conserva el `Saldo` operacional (no el cache `Producto.stock`).
- **Criterio de aceptación**: el sistema nuevo muestra el stock de los
  productos (ver VERIFICATION).

## INVARIANTS
- Legacy dueño; TMS nunca escribe en SQL Server.
- No rompe `plugins/stock` existente.
- La ley de frontera se preserva: solo lectura del API.

## VERIFICATION (TEST REAL, NO MOCK)
Desplegar `ERP-SYSTUTOR.API` (0001/0007) contra `Sys_Gas2_Plus` **real**,
ejecutar el adaptador Python real y el enlace contra OSS **real**; luego, en el
sistema nuevo, verificar que el stock de productos aparece y que fue obtenido
**exclusivamente por el llamado al API REST** (sin seeding local). Ejemplo
real: `ABRAZADERAS` (cod_producto 1868) con stock **53** según el reporte
legacy `PRODUCTO_MOSTRARsoloSTOCK` (filtros `inventario=1, Estado=1,
TipoAtencion=1`); el sistema nuevo debe mostrar ese 53, no el `vkardex` 88 ni
el cache 112. Re-ejecutar idempotente.
Prohibido usar mocks para este criterio de aceptación.

## ROLLBACK
- Compensación: revertir balances creados por este enlace (por correlation id)
  y registrar auditoría.

## CHANGE SURFACE
```yaml
allowed:
  - plugins/stock/backend/services/*.py   # o plugins/tms según D4
prohibited:
  - kernel/**
```

## BLAST RADIUS
```yaml
direct:
  - stock balances
indirect:
  - logistics (cargas), ventas
must_not_affect:
  - SQL Server legacy
  - ERP app
  - auth/tenancy
```
