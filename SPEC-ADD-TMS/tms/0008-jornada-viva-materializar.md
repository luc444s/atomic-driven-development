# A.SPEC TMS-008 — Materializar salida a cliente como Jornada Viva (LogisticsVehicleSession)

## WHY
Hasta hoy el sync solo escribe un snapshot plano (`tms_jornada`). El operador necesita una
jornada **viva y funcional**: una `LogisticsVehicleSession` real del plugin logistics, con
state machine (DRAFT→LOADING→READY_TO_DEPART→OUTBOUND→…→CLOSED), para que la entrega se
trabaje en el flujo real (carga, ruta, confirmaciones). El legacy ya expone los datos de
transporte (`GET /salidas` expone desde 2026-08-21: `nro_guia`, `transportista`,
`lugar_inicio`, `lugar_destino`, `dir_inicio`, `dir_destino`, `empresa_trans`, `ruc_empresa`)
y los choferes existen como `User` con rol `driver` (seed_drivers).

## WHAT
Existe un servicio `sync_salidas_hoy` que, para cada salida legacy del día con `placa` y
`dnichofer` presentes, resuelve (creando si falta) `LogisticsVehicle` por placa y `User`
driver por `dnichofer`, y crea/actualiza idempotentemente (1 por vehículo+chofer+fecha) una
`LogisticsVehicleSession` en `DRAFT`. NO crea `LogisticsRouteOperation` (eso se hace siempre
desde sesión admin). NO toca stock (el stock se altera en legacy en el IC).

## SCOPE
- `ensure_driver_user(dnichofer)` → `User` (reusa `services/drivers.py`).
- `ensure_vehicle(placa)` → `LogisticsVehicle` por `plate` (crea si falta, tenant).
- `create_vehicle_session()` de logistics con `opened_at=salida.fecha`.
- Agrupación: misma `(placa, dnichofer, fecha)` → misma sesión (upsert/omitir).
- Campos de contexto guardados en la sesión/operación de lectura: origen=warehouse del
  `almacen`, llegada=`lugar_destino ?? dir_destino ?? cliente.direccion`.

## OUT OF SCOPE
- Crear `LogisticsRouteOperation` automáticamente (se hace desde sesión admin).
- Confirmar la sesión ni operaciones (stock queda intacto; el IC legacy altera stock).
- Toquetear stock OSS (`apply_stock_for_movement` queda fuera de esta rama).
- Wire-back OSS→legacy.

## CONTRACT
- Postcondición: por cada salida del día con `placa` y `dnichofer`, existe una sesión
  `DRAFT` en `lg_vehicle_sessions` con `vehicle_id` (resuelto/creado por placa) y
  `driver_id` (resuelto/creado por `dnichofer`).
- Idempotente: re-correr el sync no duplica sesiones ni vehículos ni drivers.
- Sesión única por `(placa, dnichofer, fecha)` el mismo día (regla single live session).
- Salida sin `placa` o sin `dnichofer` → NO crea sesión viva; queda solo en `tms_jornada`
  (snapshot) como `pendiente`.

## INVARIANTS
```yaml
invariants:
  - "solo salidas del día con placa Y dnichofer crean sesión"
  - "una sesión por vehiculo+chofer+fecha (no por salida)"
  - "ensure_driver_user y ensure_vehicle son idempotentes"
  - "no se confirma ni se avanza la sesión en el sync"
  - "no se llama a stock_bridge desde este flujo"
```

## VERIFICATION
- Test de integración SQLite: mock `get_salidas` con 2 salidas mismas `(placa, dnichofer,
  fecha)` + 1 sin placa → 1 sesión creada + vehículo creado + driver resuletoo; la sin placa
  no crea sesión.
- Re-corrrer el sync → misma sesión/vehículo/driver (counts estables).
- `ensure_driver_user(44973574)` devuelve el user existente `44973574@oxipur.com`.
- E2E opcional contra BD real: `link_legacy`-style run → `lg_vehicle_sessions` +1 para
  salida real, `lg_vehicles` con placa nueva.

## ROLLBACK
- Reversible: borrar la sesión creada (y vehículo/driver si recién creados) no afecta legacy
  ni stock. El snapshot `tms_jornada` sigue existiendo.

## Change Surface
```yaml
change_surface:
  allowed:
    - "editar plugins/tms/backend/services/sync.py"
    - "editar plugins/tms/backend/services/materialize.py"
    - "usar plugins/logistics/backend/services/sessions.create_vehicle_session"
    - "crear plugins/tms/backend/services/vehicles.py (ensure_vehicle)"
  prohibited:
    - "confirmar/avanzar sesión (status/ready/depart) en el sync"
    - "llamar stock_bridge o confirm_route_operation"
    - "modificar tablas de otros plugins directamente"
```

## Blast Radius
```yaml
blast_radius:
  direct:
    - "filas nuevas en lg_vehicle_sessions"
    - "posibles filas nuevas en lg_vehicles y users (si no existen)"
  indirect:
    - "sesión visible en UI logistics de inmediato (DRAFT)"
  must_not_affect:
    - "stock OSS ni legacy"
    - "tms_jornada (snapshot) existente"
    - "estado de salidas en legacy"
```

## Composition
```yaml
composition:
  requires_aspecs:
    - "TMS-002 (sync existente)"
    - "drivers seed (ensure_driver_user)"
    - "API legacy /salidas expone datos de transporte"
  must_compose_with:
    - "TMS-003 (tarea cron dispara el mismo sync)"
  systemic_invariants: []
  composition_checks:
    - "sync produce sesiones vivas y mantiene snapshot tms_jornada sin romper"
    - "una salida ya materializada no duplica sesión al re-ejecutar"
```

## Structural Constraints
```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/tms/backend/services/sync.py"
    - "plugins/tms/backend/services/vehicles.py"
```

## Traceability
- Requirement: materializar salida a cliente como jornada viva
- Commit: pendiente (junto a spec de lo hecho el 2026-08-21)
- Deployment: rama TMS

## Definition of Done
- [ ] Objective satisfied
- [ ] Scope respected
- [ ] Contract satisfied
- [ ] Independent falsable truth exists now
- [ ] Invariants preserved
- [ ] Verification passed
- [ ] Rollback / compensation is honest
- [ ] Composition checks passed when applicable
- [ ] No unrelated changes
- [ ] Structural constraints respected
- [ ] Traceability established