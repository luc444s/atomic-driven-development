# A.SPEC TMS-009 — Exponer datos de transporte en /salidas + seeds drivers (DONE)

> Estado: **done** (2026-08-21). Representa el trabajo ya ejecutado y verificado en esta
> rama TMS como baseline para la jornada viva (TMS-008).

## WHY
Para materializar la salida a cliente como **jornada viva** hicieron falta dos piezas que no
existían: (1) el API legacy no exponía los datos de transporte de la salida (guía,
transportista, origen/destino) que el dominio TMS necesita para la sesión; (2) los choferes
solo existían como `dnichofer` en documentos legacy, sin `User` real con rol `driver` que
`LogisticsVehicleSession` exige. Ambas se resolvieron y se verificaron contra datos reales.

## WHAT (hecho)

### 1. API legacy `GET /salidas` y `GET /salidas/{id}` exponen transporte
`SalidasHandler.vb` ahora agrega al JSON de cada salida:
`nro_guia`, `transportista`, `lugar_inicio`, `lugar_destino`, `dir_inicio`, `dir_destino`,
`empresa_trans`, `ruc_empresa` (además de `placa`/`dnichofer` ya existentes). Los campos
viven en la tabla `Movimiento` (verificado contra INFORMATION_SCHEMA, no requiere join a
`Orden_compra`).

### 2. Campos en OSS
- `SalidaLegacy` (+8 campos) en `plugins/tms/backend/legacy/schemas.py`.
- `materialize_salida()` los propaga a la operación con fallback `lugar_x ?? dir_x`.

### 3. Drivers como Users reales
- `ensure_driver_user()` (`plugins/tms/backend/services/drivers.py`): crea `User` con
  `category=driver`, email `{dni}@oxipur.com`, rol `driver` (idempotente por email).
- `python -m plugins.tms.backend.commands.seed_drivers` con lista fija de 3:
  AYRTOM SALDARRIAGA SALDARRIAGA (46209157), LEON CALDERON HIRVING BENGAMIN YSAIT
  (44973574), REYES POLO GERSON JHOAO (48429083).

## VERIFIED (evidencia)
- `GET /api/salidas?limit=1` → salida #42470 trae `transportista="ARANGO...JL"`,
  `nro_guia="Orden Salida 001-102024"`, `lugar_destino` completo.
- `GET /api/salidas/42470` → detalle con los mismos campos + `items`.
- `seed_drivers` → 3 usuarios en `users` con `category=driver` y rol `driver` en `user_roles`.
- Relación DNI→User: `driver_email(44973574) = 44973574@oxipur.com`.

## SCOPE / OUT OF SCOPE
- En scope: solo exposición de datos y creación de drivers. 
- Fuera: materializar jornada viva (TMS-008), confirmaciones, stock.

## Contract (de esto, ya cumplido)
- Driver resolvible por `dnichofer` → `driver_email()` → queryset por email.
- Driver creado la primera vez que aparece (regla si hay nuevo transportista).

## Definition of Done
- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now (endpoints + BD)
- [x] Invariants preserved
- [x] Verification passed (datos reales)
- [x] Rollback / compensation honest (backup SalidasHandler.vb.bak)
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established (esta spec)