# A.SPEC API-REST-CON-0006 — Mapeo clientes legacy → crm.Customer

## WHY
OSS ya posee clientes (`plugins/crm`). El legacy es solo fuente de lectura; se
enlaza, no se duplica. Esto materializa la ley de frontera.

## WHAT
Servicio de enlace que, desde `ClienteLegacy` (0005), hace upsert de
`crm.Customer` por `dni`/`ruc`, e inserta sus puntos de entrega
(`vehiculo_cliente`) como `crm.CustomerAddress` o
`logistics.VehicleDeliveryPoint`.

## SCOPE
- Upsert idempotente de Customer por documento (dni/ruc).
- Creación de direcciones/puntos de entrega asociados.
- Registro de correlation id (origen legacy).

## OUT OF SCOPE
- Sincronización inversa (OSS → legacy): legacy es read-only fuente.
- Edición de reglas de negocio de crm.

## CONTRACT
- Idempotente: re-ejecutar no crea duplicados (match por dni/ruc).
- No borra Customers existentes no vinculados al legacy.
- Guarda correlation id que referencia al `id` legacy.

## INVARIANTS
- Legacy sigue dueño de los datos; TMS nunca escribe en SQL Server.
- No rompe `crm` existente (otros clientes quedan intactos).
- La ley de frontera se preserva: solo lectura del API.

## VERIFICATION (TEST REAL, NO MOCK)
Desplegar `ERP-SYSTUTOR.API` (0001/0007) contra `Sys_Gas2_Plus` **real**,
ejecutar el adaptador Python real (0005) y el enlace contra OSS **real**; luego,
en el sistema nuevo, verificar que aparecen los **1872 clientes** del legacy,
incluyendo específicamente:
- `ASOCIACION IGLESIA ADVENTISTA DEL SEPTIMO DIA PERUANA DEL NORTE`
- `AUTOMOTRIZ FREDY E.I.R.L.`
y que estos clientes aparecen **exclusivamente por el llamado al API REST**
(la única fuente es `ERP-SYSTUTOR.API`; no había seeding local ni datos
precargados en OSS antes del enlace). Re-ejecutar es idempotente (sin
duplicados). Prohibido usar mocks para este criterio de aceptación.

## ROLLBACK
- Compensación: borrar Customers y direcciones creados por este enlace
  (identificables por correlation id), y registrar auditoría.

## CHANGE SURFACE
```yaml
allowed:
  - plugins/crm/backend/services/*.py        # o plugins/tms según D4
  - plugins/crm/backend/schemas.py
prohibited:
  - kernel/**
  - plugins/logistics/**
```

## BLAST RADIUS
```yaml
direct:
  - crm.Customer, crm.CustomerAddress
indirect:
  - logistics.VehicleDeliveryPoint
  - ventas/crm consumers
must_not_affect:
  - SQL Server legacy
  - ERP app
  - auth/tenancy
```
