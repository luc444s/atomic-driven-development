# A.SPEC TMS-006 — Listar borradores de jornada vía API

## WHY
Los borradores de jornada se materializan en `tms_jornada`, pero ningún endpoint los expone: no hay `GET`, solo `PATCH`. Por eso la pantalla "Jornadas" anda vacía pese a que la data existe.

## WHAT
Existe `GET /api/tms/jornadas` que devuelve los borradores de jornada (filtrables y paginados), y `GET /api/tms/jornadas/{id}` que devuelve el detalle de una.

## SCOPE
- `GET /tms/jornadas` → lista (filtros: `estado`, `desde`, `hasta`; paginación `limit`/`offset`).
- `GET /tms/jornadas/{id}` → detalle de una jornada.
- Reusa el registro de router y permiso `tms.jornada.edit` (read se da con un permiso de lectura: `tms.jornada.read`).

## OUT OF SCOPE
- Frontend/UI (A.SPEC aparte).
- Promoción a `LogisticsVehicleSession`.
- Búsqueda por texto libre.

## CONTRACT
- `GET /tms/jornadas` devuelve `[{id, cod_movimiento_legacy, estado, fecha, placa, chofer_dni, cliente, direccion_llegada, tipo_transaccion, ...}]` paginado.
- `GET /tms/jornadas/{id}` devuelve la jornada completa incluyendo `items` (ya parseado).
- 404 si el id no existe.

## INVARIANTS
```yaml
invariants:
  - "listar no muta tms_jornada"
  - "items se devuelven como lista JSON, no string crudo"
  - "la lectura respeta tenant (scope del router del plugin)"
```

## VERIFICATION
- Unit/integration: crear jornadas en sesión SQLite → `GET` devuelve las filas con filtro por estado.
- 404 en id inexistente.

## ROLLBACK
- Reversible: remover el endpoint no afecta los datos de `tms_jornada`.

## Change Surface
```yaml
change_surface:
  allowed:
    - "agregar GET en plugins/tms/backend/routers/jornadas.py"
    - "agregar permiso tms.jornada.read en plugin.py + plugin.json"
  prohibited:
    - "modificar el sync ni el modelo"
```

## Blast Radius
```yaml
blast_radius:
  direct:
    - "nuevo endpoint GET de solo lectura"
  indirect:
    - "nuevo permiso de lectura en el registro"
  must_not_affect:
    - "flujo de sync (escritura)"
    - "tabla tms_jornada"
```

## Composition
```yaml
composition:
  requires_aspecs:
    - "TMS-001"
    - "TMS-004"
  must_compose_with:
    - "TMS-004 (reusa router y permiso tms.jornada.*)"
  systemic_invariants: []
  composition_checks:
    - "GET lista lo que el sync escribió (mismas filas)"
```

## Structural Constraints
```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/tms/backend/routers/jornadas.py"
```

## Traceability
- Requirement: exponer borradores de jornada
- Commit: pendiente
- Deployment: rama TMS
## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now
- [x] Invariants preserved
- [x] Verification passed
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established
