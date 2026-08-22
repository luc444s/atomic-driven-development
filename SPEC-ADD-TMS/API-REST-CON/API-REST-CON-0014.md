# A.SPEC API-REST-CON-0014 — Mapeo almacenes legacy → logistics.Warehouse

## WHY
OSS ya posee almacenes (`logistics.Warehouse`). El legacy es fuente de
lectura; se enlaza, no se duplica.

## WHAT
Servicio de enlace que, desde `AlmacenLegacy` (0013), hace upsert de
`logistics.Warehouse` por `cod` de almacen legacy.

## SCOPE
- Upsert idempotente por `cod` de almacen.
- Registro de correlation id (origen legacy).

## OUT OF SCOPE
- Sincronización inversa (OSS → legacy).
- Edición de reglas de `logistics.Warehouse`.

## CONTRACT
- Idempotente: re-ejecutar no crea duplicados (match por `cod` legacy).
- No borra Warehouses existentes no vinculados al legacy.
- **Criterio de aceptación**: el sistema nuevo cuenta los **2 almacenes**
  del legacy (ver VERIFICATION).

## INVARIANTS
- Legacy dueño; TMS nunca escribe en SQL Server.
- No rompe `logistics` existente.
- La ley de frontera se preserva: solo lectura del API.

## VERIFICATION (TEST REAL, NO MOCK)
Desplegar `ERP-SYSTUTOR.API` (0001/0007) contra `Sys_Gas2_Plus` **real**,
ejecutar el adaptador Python real y el enlace contra OSS **real**; luego, en el
sistema nuevo, verificar que se cuentan **2 almacenes**
(`OXIPUR EIRL` y `REPARTIDOR`) obtenidos **exclusivamente por el llamado al
API REST** (sin seeding local). Re-ejecutar idempotente.
Prohibido usar mocks para este criterio de aceptación.

## ROLLBACK
- Compensación: revertir Warehouses creados por este enlace (por correlation
  id) y registrar auditoría.

## CHANGE SURFACE
```yaml
allowed:
  - plugins/logistics/backend/services/*.py   # o plugins/tms según D4
prohibited:
  - kernel/**
```

## BLAST RADIUS
```yaml
direct:
  - logistics.Warehouse
indirect:
  - logistics (rutas, jornadas)
must_not_affect:
  - SQL Server legacy
  - ERP app
  - auth/tenancy
```
