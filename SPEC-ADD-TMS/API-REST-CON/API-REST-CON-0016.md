# A.SPEC API-REST-CON-0016 — Orquestación: carga móvil descuenta legacy

## WHY
Al subir un envase a un almacén móvil (OSS Postgres), el stock legacy debe
descontarse. OSS orquesta ambos lados: movimiento local + write-back al API
legacy.

## WHAT
Servicio OSS que, al registrar la carga de un envase en almacén móvil:
1. decrementa almacén fijo e incrementa móvil en OSS
   (`plugins/stock` + `plugins/logistics`);
2. llama `POST /api/stock/movement` (0015) para descontar legacy, con
   `idempotency_key` = id de la carga.

## SCOPE
- Orquestación en OSS; llamada HTTP al API legacy.

## OUT OF SCOPE
- Modelo de almacén móvil (TMS-DOMAIN).

## CONTRACT
- La operación es atómica en OSS; el write-back es idempotente (key = load id).
- Si el API legacy falla, OSS marca pendiente y reintenta (no deja legacy sin
  descontar ni lo descuenta dos veces).

## INVARIANTS
- Legacy solo vía API (nunca SQL Server directo).
- No doble descuento (idempotency).
- Legacy sigue dueño del stock de almacenes fijos.

## VERIFICATION (TEST REAL, NO MOCK)
Flujo real: cargar 5 `ABRAZADERAS` a móvil → OSS muestra fijo−5 / móvil+5 Y el
reporte legacy baja de **53 → 48** vía API. Re-intentar la carga (misma key)
no vuelve a descontar. Prohibido mock.

## ROLLBACK
- Compensación: revertir movimiento OSS + anular egreso legacy por key.

## CHANGE SURFACE
```yaml
allowed:
  - plugins/logistics/backend/services/*.py   # o plugins/tms según D4
  - plugins/stock/backend/services/*.py
prohibited:
  - kernel/**
```

## BLAST RADIUS
```yaml
direct:
  - OSS stock, llamada API legacy
indirect:
  - legacy stock, jornadas/logistics
must_not_affect:
  - SQL Server directo
  - ERP app
```
