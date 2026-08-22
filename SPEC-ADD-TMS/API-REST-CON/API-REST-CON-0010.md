# A.SPEC API-REST-CON-0010 — Mapeo productos legacy → productos (OSS)

## WHY
OSS ya posee productos (`plugins/productos`). El legacy es fuente de lectura;
se enlaza, no se duplica. Este es el paso que materializa "mostrar los 4671
productos en el sistema nuevo".

## WHAT
Servicio de enlace que, desde `ProductoLegacy` (0008/0009), hace upsert de
`productos.Product` por `cod_producto`/`nro`, incluyendo campos físicos de
transporte (`m3`, `peso_kg`) para TMS/logistics.

## SCOPE
- Upsert idempotente de `Product` por código legacy.
- Mapeo de línea/unidad/marca a catálogos OSS.
- Registro de correlation id (origen legacy).

## OUT OF SCOPE
- Sincronización inversa (OSS → legacy): legacy es read-only fuente.
- Edición de reglas de negocio de `productos`.

## CONTRACT
- Idempotente: re-ejecutar no crea duplicados (match por código legacy).
- No borra `Product` existentes no vinculados al legacy.
- Campos físicos de transporte (`m3`, `peso_kg`) se conservan para logistics.
- Campos `ADR_*` **NO** se mapean en esta rama (ADR es norma europea; en
  Perú rige otro marco — candidatos a desaparecer).
- **Criterio de aceptación**: el sistema nuevo lista los **4671 productos**
  reales del legacy (ver VERIFICATION).

## INVARIANTS
- Legacy dueño; TMS nunca escribe en SQL Server.
- No rompe `productos` existente.
- La ley de frontera se preserva: solo lectura del API.

## VERIFICATION (TEST REAL, NO MOCK)
Desplegar `ERP-SYSTUTOR.API` (0001/0007) contra `Sys_Gas2_Plus` **real**,
ejecutar el adaptador Python real (estilo 0005 para productos) y el enlace
contra OSS **real**; luego, en el sistema nuevo, listar productos y verificar
que aparecen los **4671 productos** del legacy, con sus campos físicos de
transporte (`m3`, `peso_kg`) presentes y SIN campos `ADR_*`.
- Re-ejecutar es idempotente (siguen 4671, sin duplicados).
- **Prohibido usar mocks** para este criterio de aceptación: debe ser
  end-to-end contra API legacy y OSS reales.

## ROLLBACK
- Compensación: borrar `Product` creados por este enlace (identificables por
  correlation id) y registrar auditoría.

## CHANGE SURFACE
```yaml
allowed:
  - plugins/productos/backend/services/*.py   # o plugins/tms según D4
  - plugins/productos/backend/schemas.py
prohibited:
  - kernel/**
```

## BLAST RADIUS
```yaml
direct:
  - productos.Product
indirect:
  - logistics (cargas ADR)
must_not_affect:
  - SQL Server legacy
  - ERP app
  - auth/tenancy
```
